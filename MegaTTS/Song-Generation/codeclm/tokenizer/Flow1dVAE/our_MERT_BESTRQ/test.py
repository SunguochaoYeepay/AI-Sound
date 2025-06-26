import torch
from dataclasses import dataclass
from logging import getLogger
import torch.nn.functional as F

logger = getLogger(__name__)

@dataclass
class UserDirModule:
    user_dir: str

def load_model(model_dir, checkpoint_dir):
    '''Load Fairseq SSL model - Mock implementation'''
    
    logger.warning(f"Mock load_model called with model_dir={model_dir}, checkpoint_dir={checkpoint_dir}")
    
    # 返回一个简单的mock模型，避免fairseq依赖
    class MockModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(1, 1)
            
        def forward(self, x):
            return self.linear(x)
    
    return MockModel()
