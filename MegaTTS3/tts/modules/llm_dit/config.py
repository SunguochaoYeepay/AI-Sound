class ModelConfig:
    def __init__(self, hidden_size=1024):  # 修改为1024以匹配预训练模型
        self.hidden_size = hidden_size
        self.ffn_hidden_size = hidden_size * 2
        self.n_heads = 8
        self.n_layers = 6
        self.dropout = 0.1
        self.kernel_size = 1
        
    @property
    def filter_channels(self):
        return self.hidden_size * 4

# 创建默认配置实例
config = ModelConfig()