#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TangoFlux Environment Sound Client
AI-Sound平台的环境音合成客户端
"""

import requests
import base64
import json
import time
import logging
from typing import Optional, Dict, Any, Union
import tempfile
import os

logger = logging.getLogger(__name__)

class TangoFluxClient:
    """TangoFlux环境音合成客户端"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:7928", timeout: int = 120):
        """
        初始化TangoFlux客户端
        
        Args:
            base_url: TangoFlux API服务地址
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def check_health(self) -> Dict[str, Any]:
        """
        检查TangoFlux服务健康状态
        
        Returns:
            Dict: 健康状态信息
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'data': response.json()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f"HTTP {response.status_code}",
                    'data': None
                }
                
        except Exception as e:
            logger.error(f"TangoFlux health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'data': None
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        获取TangoFlux服务信息
        
        Returns:
            Dict: 服务信息
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/info",
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'data': None
                }
                
        except Exception as e:
            logger.error(f"Failed to get TangoFlux service info: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def generate_environment_sound(
        self,
        prompt: str,
        duration: float = 10.0,
        steps: int = 50,
        cfg_scale: float = 3.5,
        return_type: str = 'base64'
    ) -> Dict[str, Any]:
        """
        生成环境音
        
        Args:
            prompt: 环境音描述文本（英文）
            duration: 音频时长（秒，1-30）
            steps: 推理步数（1-200）
            cfg_scale: CFG引导强度（1.0-10.0）
            return_type: 返回类型 ('base64' 或 'file')
            
        Returns:
            Dict: 生成结果
        """
        # 参数验证
        if not prompt or not isinstance(prompt, str):
            return {
                'success': False,
                'error': 'prompt must be a non-empty string'
            }
        
        if not (1 <= duration <= 30):
            return {
                'success': False,
                'error': 'duration must be between 1 and 30 seconds'
            }
        
        if not (1 <= steps <= 200):
            return {
                'success': False,
                'error': 'steps must be between 1 and 200'
            }
        
        if not (1.0 <= cfg_scale <= 10.0):
            return {
                'success': False,
                'error': 'cfg_scale must be between 1.0 and 10.0'
            }
        
        # 构建请求
        payload = {
            'prompt': prompt,
            'duration': duration,
            'steps': steps,
            'cfg_scale': cfg_scale
        }
        
        # 选择端点
        if return_type == 'file':
            endpoint = f"{self.base_url}/api/v1/audio/generate_file"
        else:
            endpoint = f"{self.base_url}/api/v1/audio/generate"
        
        try:
            logger.info(f"Generating environment sound: {prompt[:50]}...")
            start_time = time.time()
            
            response = self.session.post(
                endpoint,
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=self.timeout
            )
            
            request_time = time.time() - start_time
            
            if response.status_code == 200:
                if return_type == 'file':
                    # 文件返回模式
                    return {
                        'success': True,
                        'audio_data': response.content,
                        'content_type': 'audio/wav',
                        'prompt': prompt,
                        'parameters': payload,
                        'request_time': round(request_time, 2),
                        'size_bytes': len(response.content)
                    }
                else:
                    # Base64返回模式
                    result = response.json()
                    if result.get('success'):
                        return {
                            'success': True,
                            'audio_base64': result['audio_base64'],
                            'content_type': result['content_type'],
                            'prompt': result['prompt'],
                            'parameters': result['parameters'],
                            'audio_info': result['audio_info'],
                            'request_time': round(request_time, 2)
                        }
                    else:
                        return {
                            'success': False,
                            'error': result.get('error', 'Unknown error')
                        }
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f'HTTP {response.status_code}')
                except:
                    error_msg = f'HTTP {response.status_code}: {response.text}'
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': f'Request timeout after {self.timeout} seconds'
            }
        except Exception as e:
            logger.error(f"Environment sound generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_audio_to_file(
        self, 
        audio_data: Union[str, bytes], 
        filename: str, 
        is_base64: bool = True
    ) -> Dict[str, Any]:
        """
        保存音频数据到文件
        
        Args:
            audio_data: 音频数据（base64字符串或字节）
            filename: 保存的文件名
            is_base64: 数据是否为base64格式
            
        Returns:
            Dict: 保存结果
        """
        try:
            if is_base64:
                # 解码base64数据
                audio_bytes = base64.b64decode(audio_data)
            else:
                audio_bytes = audio_data
            
            with open(filename, 'wb') as f:
                f.write(audio_bytes)
            
            file_size = os.path.getsize(filename)
            
            return {
                'success': True,
                'filename': filename,
                'size_bytes': file_size
            }
            
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_and_save(
        self,
        prompt: str,
        output_path: str,
        duration: float = 10.0,
        steps: int = 50,
        cfg_scale: float = 3.5
    ) -> Dict[str, Any]:
        """
        生成环境音并保存到文件
        
        Args:
            prompt: 环境音描述文本
            output_path: 输出文件路径
            duration: 音频时长
            steps: 推理步数
            cfg_scale: CFG引导强度
            
        Returns:
            Dict: 生成和保存结果
        """
        # 生成音频
        result = self.generate_environment_sound(
            prompt=prompt,
            duration=duration,
            steps=steps,
            cfg_scale=cfg_scale,
            return_type='base64'
        )
        
        if not result['success']:
            return result
        
        # 保存文件
        save_result = self.save_audio_to_file(
            audio_data=result['audio_base64'],
            filename=output_path,
            is_base64=True
        )
        
        if save_result['success']:
            return {
                'success': True,
                'filename': save_result['filename'],
                'size_bytes': save_result['size_bytes'],
                'prompt': result['prompt'],
                'parameters': result['parameters'],
                'audio_info': result['audio_info'],
                'request_time': result['request_time']
            }
        else:
            return save_result
    
    def get_models_info(self) -> Dict[str, Any]:
        """
        获取可用模型信息
        
        Returns:
            Dict: 模型信息
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/audio/models",
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Failed to get models info: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# 预定义的环境音提示词模板
ENVIRONMENT_SOUND_TEMPLATES = {
    'nature': {
        'rain': [
            "Heavy rain falling on leaves with distant thunder",
            "Light rain drops on window glass",
            "Rain storm with strong wind"
        ],
        'ocean': [
            "Ocean waves crashing on rocky shore",
            "Gentle waves lapping on sandy beach",
            "Stormy sea with powerful waves"
        ],
        'forest': [
            "Birds chirping in early morning forest",
            "Wind blowing through tall trees",
            "Forest with flowing stream and birds"
        ],
        'wind': [
            "Wind blowing through tall grass in meadow",
            "Strong wind howling through mountains",
            "Gentle breeze rustling leaves"
        ]
    },
    'urban': {
        'traffic': [
            "Busy city street with car traffic and footsteps",
            "Highway traffic with cars passing by",
            "Traffic jam with car horns"
        ],
        'indoor': [
            "Coffee shop ambiance with background chatter",
            "Library with quiet studying atmosphere",
            "Office with keyboard typing sounds"
        ],
        'transport': [
            "Train station with announcements and trains",
            "Airport with boarding announcements",
            "Subway train arriving at station"
        ]
    },
    'mechanical': {
        'machines': [
            "Old clock ticking steadily",
            "Washing machine spinning cycle",
            "Air conditioner humming quietly"
        ],
        'tools': [
            "Construction site with machinery sounds",
            "Workshop with drilling and hammering",
            "Factory assembly line working"
        ]
    },
    'animals': {
        'domestic': [
            "Cat purring contentedly",
            "Dog barking in the distance",
            "Birds singing in garden"
        ],
        'wild': [
            "Crickets chirping on summer night",
            "Owls hooting in dark forest",
            "Wolves howling in moonlight"
        ]
    }
}

def get_environment_sound_template(category: str, subcategory: str = None) -> list:
    """
    获取环境音提示词模板
    
    Args:
        category: 大类 ('nature', 'urban', 'mechanical', 'animals')
        subcategory: 子类
        
    Returns:
        list: 提示词列表
    """
    if category not in ENVIRONMENT_SOUND_TEMPLATES:
        return []
    
    if subcategory:
        return ENVIRONMENT_SOUND_TEMPLATES[category].get(subcategory, [])
    else:
        # 返回该类别下所有提示词
        all_prompts = []
        for sub_dict in ENVIRONMENT_SOUND_TEMPLATES[category].values():
            all_prompts.extend(sub_dict)
        return all_prompts 