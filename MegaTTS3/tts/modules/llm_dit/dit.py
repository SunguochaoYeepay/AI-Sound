import torch
from torch import nn
import torch.nn.functional as F

from tts.modules.llm_dit.cfm import ConditionalFlowMatcher
from tts.modules.ar_dur.commons.layers import Embedding
from tts.modules.ar_dur.commons.nar_tts_modules import PosEmb
from tts.modules.ar_dur.commons.rel_transformer import RelTransformerEncoder
from tts.modules.ar_dur.ar_dur_predictor import expand_states
from tts.modules.llm_dit.transformer import Transformer
from tts.modules.llm_dit.time_embedding import TimestepEmbedding
from tts.modules.llm_dit.config import config


class Diffusion(nn.Module):
    def __init__(self, in_channels, out_channels, num_timesteps=1000):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_timesteps = num_timesteps
        
        hidden_size = config.hidden_size
        
        # 初始化网络组件
        self.x_prenet = nn.Linear(in_channels, hidden_size)
        self.local_cond_prenet = nn.Linear(in_channels, hidden_size)
        self.prenet = nn.Linear(hidden_size * 2, hidden_size)
        
        # 使用RelTransformerEncoder
        self.encoder = RelTransformerEncoder(
            n_vocab=0,  # 不使用词表
            out_channels=hidden_size,
            hidden_channels=hidden_size,
            filter_channels=hidden_size * 4,  # 使用hidden_size的4倍
            n_heads=config.n_heads,
            n_layers=config.n_layers,
            kernel_size=config.kernel_size,
            p_dropout=config.dropout,
            window_size=None,  # 全局注意力
            block_length=None,
            in_channels=hidden_size,
            pre_ln=True
        )
        
        self.postnet = nn.Linear(hidden_size, out_channels)
        self.time_embed = TimestepEmbedding(hidden_size)
        
        # 添加语言特征处理组件
        self.ph_encoder = RelTransformerEncoder(
            n_vocab=302,  # 音素词表大小
            out_channels=hidden_size,
            hidden_channels=hidden_size,
            filter_channels=hidden_size * 4,  # 使用hidden_size的4倍
            n_heads=config.n_heads,
            n_layers=config.n_layers,
            kernel_size=config.kernel_size,
            p_dropout=config.dropout,
            window_size=None,
            block_length=None,
            in_channels=hidden_size,
            pre_ln=True
        )
        
        # 音调嵌入
        self.tone_embed = Embedding(32, hidden_size)  # 32个音调类型
        self.ph_pos_embed = PosEmb(hidden_size)  # 位置嵌入层
        
    def _forward(self, x, local_cond, x_ling, t_emb=None, ctx_mask=None):
        """
        前向传播函数
        Args:
            x: 输入特征 [B, T, C]
            local_cond: 局部条件 [B, T, C]
            x_ling: 语言特征 [B, T', C]
            t_emb: 时间嵌入 [B, C]
            ctx_mask: 上下文掩码 [B, T, 1]
        """
        try:
            # 1. 预处理输入
            x = self.x_prenet(x)
            local_cond = self.local_cond_prenet(local_cond)
            
            # 2. 合并特征
            cond = torch.cat([local_cond, x_ling], dim=-1)
            cond = self.prenet(cond)
            
            # 3. 应用掩码
            if ctx_mask is not None:
                cond = cond * ctx_mask
                x = x * ctx_mask
            
            # 4. 编码器处理
            if t_emb is not None:
                # 添加时间信息到条件中
                t_emb = t_emb.unsqueeze(1).expand(-1, cond.shape[1], -1)
                cond = cond + t_emb
            
            # 使用RelTransformerEncoder
            x = self.encoder(x, other_embeds=cond)
            
            # 5. 后处理
            x = self.postnet(x)
            
            return x
            
        except Exception as e:
            print(f"前向传播错误: {e}")
            return None
        
    def inference(self, inputs, timesteps=20, seq_cfg_w=[1.0, 1.0], **kwargs):
        """
        推理函数
        Args:
            inputs: 输入字典，包含必要的特征
            timesteps: 扩散步数
            seq_cfg_w: CFG权重 [phone_weight, tone_weight]
        """
        try:
            device = inputs['phone'].device
            batch_size = inputs['phone'].shape[0]
            
            # 1. 准备输入
            ctx_feature = inputs.get('lat_ctx')
            if ctx_feature is None:
                raise ValueError("缺少lat_ctx特征")
            
            # 打印上下文特征的统计信息
            print(f"\\nVAE特征统计: mean={ctx_feature.mean().item():.4f}, std={ctx_feature.std().item():.4f}")
                
            # 创建上下文掩码
            ctx_mask = torch.ones_like(ctx_feature[:, :, 0:1])
            
            # 2. 处理音素和音调特征
            ph_tokens = inputs['phone']  # [B, T]
            print(f"ph_tokens 形状: {ph_tokens.shape}, 数据类型: {ph_tokens.dtype}")
            
            # 获取音素嵌入
            ph_enc_oembed = self.tone_embed(inputs.get('tone', torch.zeros_like(ph_tokens)))  # [B, T, C]
            print(f"ph_enc_oembed 形状: {ph_enc_oembed.shape}, 数据类型: {ph_enc_oembed.dtype}")
            
            # 添加位置编码
            ph_enc_oembed = ph_enc_oembed + self.ph_pos_embed(
                torch.arange(0, ph_tokens.shape[1])[None,].to(ph_tokens.device))
            
            # 3. 编码语言特征
            x_ling = self.ph_encoder(ph_tokens, other_embeds=ph_enc_oembed)  # [B, T, C]
            print(f"x_ling 形状: {x_ling.shape}, 数据类型: {x_ling.dtype}")
            
            # 4. 扩散过程
            x = torch.randn_like(ctx_feature) * 0.005  # 初始噪声
            
            # 逐步去噪
            for t in range(timesteps):
                # 添加时间编码
                t_emb = self.time_embed(torch.tensor([t], device=device).float())
                
                # 前向传播
                x = self._forward(x, ctx_feature, x_ling, t_emb, ctx_mask)
                
                # 应用CFG
                if seq_cfg_w[0] != 1.0 or seq_cfg_w[1] != 1.0:
                    x_uncond = self._forward(x, ctx_feature, torch.zeros_like(x_ling), t_emb, ctx_mask)
                    x = x_uncond + (x - x_uncond) * torch.tensor(seq_cfg_w).mean()
            
            return x
            
        except Exception as e:
            print(f"DiT推理过程出错: {e}")
            # 返回一个安全的输出
            return torch.zeros_like(ctx_feature)

    def forward_ling_encoder(self, txt_tokens, tone_tokens):
        ph_tokens = txt_tokens
        ph_nonpadding = (ph_tokens > 0).float()[:, :, None]  # [B, T_phone, 1]

        # enc_ph
        ph_enc_oembed = self.tone_embed(tone_tokens)
        ph_enc_oembed = ph_enc_oembed + self.ph_pos_embed(
            torch.arange(0, ph_tokens.shape[1])[None,].to(ph_tokens.device))
        ph_enc_oembed = ph_enc_oembed * ph_nonpadding
        
        # 使用RelTransformerEncoder
        x_ling = self.ph_encoder(ph_tokens, other_embeds=ph_enc_oembed) * ph_nonpadding
        
        # 打印调试信息
        print(f"ph_tokens 形状: {ph_tokens.shape}, 数据类型: {ph_tokens.dtype}")
        print(f"ph_enc_oembed 形状: {ph_enc_oembed.shape}, 数据类型: {ph_enc_oembed.dtype}")
        print(f"x_ling 形状: {x_ling.shape}, 数据类型: {x_ling.dtype}")
        
        return x_ling

    def forward_diffusion(self, x, cond, timesteps=None):
        """
        前向扩散过程
        """
        if timesteps is None:
            timesteps = self.num_timesteps
            
        # 创建CFM
        cfm = ConditionalFlowMatcher()
        
        # 生成时间步
        t = torch.randint(0, timesteps, (x.shape[0],), device=x.device).float()
        t_emb = self.time_embed(t)
        
        # 生成噪声
        z = torch.randn_like(x)
        
        # 计算扩散后的x
        x_t = cfm.forward_marginal(x, z, t / timesteps)
        
        # 预测噪声
        pred = self._forward(x_t, cond, t_emb)
        
        if pred is None:
            return None
            
        # 计算损失
        loss = F.mse_loss(pred, z)
        
        return loss