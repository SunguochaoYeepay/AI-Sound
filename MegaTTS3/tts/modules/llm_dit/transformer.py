import math
from typing import Any, Optional, Tuple

import torch
import torch.nn.functional as F
from torch import nn
from .config import config


def precompute_freqs_cis(dim: int, end: int, theta: float = 10000.0):
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2)[: (dim // 2)].float() / dim))
    t = torch.arange(end, device=freqs.device)
    freqs = torch.outer(t, freqs).float()
    freqs_cis = torch.polar(torch.ones_like(freqs), freqs)  # complex64
    return freqs_cis


def reshape_for_broadcast(freqs_cis: torch.Tensor, x: torch.Tensor):
    ndim = x.ndim
    assert 0 <= 1 < ndim
    assert freqs_cis.shape == (x.shape[1], x.shape[-1])
    shape = [d if i == 1 or i == ndim - 1 else 1 for i, d in enumerate(x.shape)]
    return freqs_cis.view(*shape)


def apply_rotary_emb(
        xq: torch.Tensor,
        xk: torch.Tensor,
        freqs_cis: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    xq_ = torch.view_as_complex(xq.float().reshape(*xq.shape[:-1], -1, 2))
    xk_ = torch.view_as_complex(xk.float().reshape(*xk.shape[:-1], -1, 2))
    freqs_cis = reshape_for_broadcast(freqs_cis, xq_)
    xq_out = torch.view_as_real(xq_ * freqs_cis).flatten(3)
    xk_out = torch.view_as_real(xk_ * freqs_cis).flatten(3)
    return xq_out.type_as(xq), xk_out.type_as(xk)


class AdaLNZero(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.silu = nn.SiLU()
        self.linear = nn.Linear(dim, dim * 6)
        self.norm = nn.LayerNorm(dim, elementwise_affine=False, eps=1e-6)

    def forward(self, x, emb=None):
        emb = self.linear(self.silu(emb))
        shift_msa, scale_msa, gate_msa, shift_mlp, scale_mlp, gate_mlp = torch.chunk(emb, 6, dim=1)
        x = self.norm(x) * (1 + scale_msa[:, None]) + shift_msa[:, None]
        return x, gate_msa, shift_mlp, scale_mlp, gate_mlp


class AdaLNZero_Out(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.silu = nn.SiLU()
        self.linear = nn.Linear(dim, dim * 2)
        self.norm = nn.LayerNorm(dim, elementwise_affine=False, eps=1e-6)

    def forward(self, x, emb):
        emb = self.linear(self.silu(emb))
        scale, shift = torch.chunk(emb, 2, dim=1)
        x = self.norm(x) * (1 + scale)[:, None, :] + shift[:, None, :]
        return x


class Attention(nn.Module):
    def __init__(self, encoder_dim, encoder_n_heads, max_seq_len):
        super().__init__()
        self.encoder_n_kv_heads = encoder_n_heads
        model_parallel_size = 1
        self.n_local_heads = encoder_n_heads // model_parallel_size
        self.n_local_kv_heads = self.encoder_n_kv_heads // model_parallel_size
        self.n_rep = self.n_local_heads // self.n_local_kv_heads
        self.head_dim = encoder_dim // encoder_n_heads

        self.wq = nn.Linear(
            encoder_dim,
            encoder_n_heads * self.head_dim,
        )
        self.wk = nn.Linear(
            encoder_dim,
            self.encoder_n_kv_heads * self.head_dim,
        )
        self.wv = nn.Linear(
            encoder_dim,
            self.encoder_n_kv_heads * self.head_dim,
        )
        self.wo = nn.Linear(
            encoder_n_heads * self.head_dim,
            encoder_dim,
        )

    def forward(
            self,
            x: torch.Tensor,
            start_pos: int,
            freqs_cis: torch.Tensor,
            mask: Optional[torch.Tensor],
    ):
        bsz, seqlen, _ = x.shape
        xq, xk, xv = self.wq(x), self.wk(x), self.wv(x)
        xq = xq.view(bsz, seqlen, self.n_local_heads, self.head_dim)
        xk = xk.view(bsz, seqlen, self.n_local_kv_heads, self.head_dim)
        xv = xv.view(bsz, seqlen, self.n_local_kv_heads, self.head_dim)

        xq, xk = apply_rotary_emb(xq, xk, freqs_cis=freqs_cis)
        xq = xq.transpose(1, 2)  # (bs, n_local_heads, seqlen, head_dim)
        keys = xk.transpose(1, 2)  # (bs, n_local_heads, cache_len + seqlen, head_dim)
        values = xv.transpose(1, 2)  # (bs, n_local_heads, cache_len + seqlen, head_dim)

        output = F.scaled_dot_product_attention(xq, keys, values, mask[:, None, None, :], is_causal=False)
        output = output.transpose(1, 2).contiguous().view(bsz, seqlen, -1)
        return self.wo(output)


class FeedForward(nn.Module):
    def __init__(
            self,
            dim: int,
            hidden_dim: int,
            multiple_of: int = None,
            ffn_dim_multiplier: Optional[float] = None,
    ):
        super().__init__()
        if ffn_dim_multiplier is not None:
            hidden_dim = int(ffn_dim_multiplier * hidden_dim)
        if multiple_of:
            hidden_dim = multiple_of * ((hidden_dim + multiple_of - 1) // multiple_of)
        else:
            hidden_dim = dim * 4  # 使用输入维度的4倍作为隐藏层大小

        self.w1 = nn.Linear(dim, hidden_dim)
        self.w2 = nn.Linear(hidden_dim, dim)

    def forward(self, x):
        return self.w2(F.silu(self.w1(x)))


class TransformerBlock(nn.Module):
    def __init__(self, encoder_dim, encoder_n_heads, max_seq_len):
        super().__init__()
        self.encoder_n_heads = encoder_n_heads
        self.encoder_dim = encoder_dim
        self.head_dim = encoder_dim // encoder_n_heads
        self.attention = Attention(encoder_dim, encoder_n_heads, max_seq_len)
        self.feed_forward = FeedForward(
            dim=encoder_dim,
            hidden_dim=2 * encoder_dim,
        )
        self.attention_norm = AdaLNZero(encoder_dim)
        self.ffn_norm = nn.LayerNorm(encoder_dim, elementwise_affine=False, eps=1e-6)

    def forward(
            self,
            x: torch.Tensor,
            t: torch.Tensor,
            start_pos: int,
            freqs_cis: torch.Tensor,
            mask: Optional[torch.Tensor],
    ):
        # pre-norm & modulation for attention input
        norm, gate_msa, shift_mlp, scale_mlp, gate_mlp = self.attention_norm(x, emb=t)

        # attention
        attn_output = self.attention(norm, start_pos, freqs_cis, mask=mask)

        # process attention output for input x
        h = x + gate_msa.unsqueeze(1) * attn_output

        norm = self.ffn_norm(h) * (1 + scale_mlp[:, None]) + shift_mlp[:, None]
        ff = self.feed_forward(norm)
        h = h + gate_mlp.unsqueeze(1) * ff

        return h


class Transformer(nn.Module):
    def __init__(self, encoder_n_layers, encoder_dim, encoder_n_heads, max_seq_len):
        super().__init__()
        self.encoder_n_layers = encoder_n_layers
        self.encoder_dim = encoder_dim
        self.encoder_n_heads = encoder_n_heads
        self.max_seq_len = max_seq_len

        self.freqs_cis = precompute_freqs_cis(
            self.encoder_dim // self.encoder_n_heads, self.max_seq_len * 2
        )

        self.layers = torch.nn.ModuleList()
        for layer_id in range(encoder_n_layers):
            self.layers.append(TransformerBlock(encoder_dim, encoder_n_heads, max_seq_len))

        self.norm_out = AdaLNZero_Out(encoder_dim)

    def forward(self, x, t, attn_mask, start_pos=0):
        freqs_cis = self.freqs_cis[start_pos: start_pos + x.shape[1]]
        for layer in self.layers:
            x = layer(x, t, start_pos, freqs_cis, attn_mask)
        x = self.norm_out(x, t)
        return x