"""
ComfyUI客户端
用于与ComfyUI服务通信生成图片
"""

import logging
import aiohttp
import asyncio
import json
import uuid
import websockets
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import random

logger = logging.getLogger(__name__)


class ComfyUIClient:
    """ComfyUI客户端"""
    
    def __init__(self, 
                 server_address: str = "127.0.0.1:8188",
                 client_id: str = None):
        self.server_address = server_address
        self.client_id = client_id or str(uuid.uuid4())
        self.http_url = f"http://{server_address}"
        self.ws_url = f"ws://{server_address}/ws?clientId={self.client_id}"
        
        # 默认工作流模板（FluxKontext - 完整功能，支持参考图像和纯文本生成）
        self.default_workflow = {
            "6": {
                "inputs": {
                    "text": "A beautiful landscape with mountains and rivers",
                    "clip": ["38", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP文本编码器"}
            },
            "8": {
                "inputs": {
                    "samples": ["31", 0],
                    "vae": ["39", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE解码"}
            },
            "31": {
                "inputs": {
                    "seed": 784381637916598,
                    "steps": 20,
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "model": ["37", 0],
                    "positive": ["35", 0],
                    "negative": ["135", 0],
                    "latent_image": ["124", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "K采样器"}
            },
            "35": {
                "inputs": {
                    "guidance": 2.5,
                    "conditioning": ["177", 0]
                },
                "class_type": "FluxGuidance",
                "_meta": {"title": "Flux引导"}
            },
            "37": {
                "inputs": {
                    "unet_name": "flux1-dev-kontext_fp8_scaled.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "UNET加载器"}
            },
            "38": {
                "inputs": {
                    "clip_name1": "clip_l.safetensors",
                    "clip_name2": "t5xxl_fp8_e4m3fn_scaled.safetensors",
                    "type": "flux",
                    "device": "default"
                },
                "class_type": "DualCLIPLoader",
                "_meta": {"title": "双CLIP加载器"}
            },
            "39": {
                "inputs": {
                    "vae_name": "ae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {"title": "VAE加载器"}
            },
            "42": {
                "inputs": {
                    "image": ["146", 0]
                },
                "class_type": "FluxKontextImageScale",
                "_meta": {"title": "FluxKontextImageScale"}
            },
            "124": {
                "inputs": {
                    "pixels": ["42", 0],
                    "vae": ["39", 0]
                },
                "class_type": "VAEEncode",
                "_meta": {"title": "VAE编码"}
            },
            "135": {
                "inputs": {
                    "conditioning": ["6", 0]
                },
                "class_type": "ConditioningZeroOut",
                "_meta": {"title": "条件零化"}
            },
            "136": {
                "inputs": {
                    "filename_prefix": "FluxKontext",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "保存图像"}
            },
            "142": {
                "inputs": {
                    "image": "placeholder_image.png",  # 使用占位图像
                    "refresh": "refresh"
                },
                "class_type": "LoadImageOutput",
                "_meta": {"title": "加载图像（来自输出）"}
            },
            "146": {
                "inputs": {
                    "direction": "right",
                    "match_image_size": True,
                    "spacing_width": 0,
                    "spacing_color": "white",
                    "image1": ["142", 0]
                },
                "class_type": "ImageStitch",
                "_meta": {"title": "Image Stitch"}
            },
            "173": {
                "inputs": {
                    "images": ["42", 0]
                },
                "class_type": "PreviewImage",
                "_meta": {"title": "预览图像"}
            },
            "177": {
                "inputs": {
                    "conditioning": ["6", 0],
                    "latent": ["124", 0]
                },
                "class_type": "ReferenceLatent",
                "_meta": {"title": "ReferenceLatent"}
            }
        }
    
    async def generate_image(self, 
                           prompt: str, 
                           negative_prompt: str = "",
                           width: int = 1024, 
                           height: int = 1024,
                           steps: int = 20,
                           cfg: float = 1.0,
                           seed: int = None,
                           filename_prefix: str = "ai_sound_generated",
                           reference_image: str = None) -> str:
        """
        生成图片
        
        Args:
            prompt: 正面提示词
            negative_prompt: 负面提示词
            width: 图片宽度 
            height: 图片高度
            steps: 采样步数
            cfg: CFG值 (Flux建议使用1.0)
            seed: 随机种子
            filename_prefix: 文件名前缀
            reference_image: 参考图像路径（可选，用于角色一致性）
            
        Returns:
            生成图片的本地路径
        """
        
        try:
            # 1. 准备工作流
            workflow = self.default_workflow.copy()
            
            # 2. 设置随机种子
            if seed is None:
                seed = random.randint(0, 2**32 - 1)
            
            # 3. 根据是否有参考图像选择工作流模式
            if not reference_image:
                # 纯文本模式：移除参考图像相关节点，使用EmptyLatentImage
                logger.info("使用纯文本模式生成图片")
                
                # 修改工作流为纯文本模式
                workflow["124"] = {
                    "inputs": {
                        "width": width,
                        "height": height,
                        "batch_size": 1
                    },
                    "class_type": "EmptyLatentImage",
                    "_meta": {"title": "空Latent图像"}
                }
                
                # 移除参考图像相关节点
                nodes_to_remove = ["42", "142", "146", "173", "177"]
                for node_id in nodes_to_remove:
                    if node_id in workflow:
                        del workflow[node_id]
                
                # 修改Flux引导直接使用文本编码
                workflow["35"]["inputs"]["conditioning"] = ["6", 0]
                
            else:
                # 参考图像模式：保留完整工作流
                logger.info(f"使用参考图像模式生成图片: {reference_image}")
                workflow["142"]["inputs"]["image"] = reference_image
            
            # 4. 更新基本参数
            workflow["6"]["inputs"]["text"] = prompt
            workflow["31"]["inputs"]["seed"] = seed
            workflow["31"]["inputs"]["steps"] = steps
            workflow["31"]["inputs"]["cfg"] = cfg
            workflow["35"]["inputs"]["guidance"] = 2.5
            
            # 5. 设置保存文件名前缀
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{filename_prefix}_{timestamp}_{seed}"
            workflow["136"]["inputs"]["filename_prefix"] = unique_filename
            
            logger.info(f"FluxKontext生成参数: prompt='{prompt[:50]}...', steps={steps}, cfg={cfg}, seed={seed}, 参考图像={bool(reference_image)}")
            
            # 6. 发送生成请求
            prompt_id = await self._queue_prompt(workflow)
            logger.info(f"FluxKontext任务已提交，prompt_id: {prompt_id}")
            
            # 7. 等待生成完成并获取结果
            image_path = await self._wait_for_completion(prompt_id, unique_filename)
            
            logger.info(f"FluxKontext图片生成成功: {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"FluxKontext图片生成失败: {str(e)}")
            raise Exception(f"FluxKontext图片生成失败: {str(e)}")
    
    async def _queue_prompt(self, workflow: Dict) -> str:
        """提交提示词到ComfyUI队列"""
        
        prompt_data = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.http_url}/prompt",
                json=prompt_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    prompt_id = result.get("prompt_id")
                    logger.info(f"ComfyUI任务已提交，prompt_id: {prompt_id}")
                    return prompt_id
                else:
                    error_text = await response.text()
                    raise Exception(f"提交ComfyUI任务失败: {response.status} - {error_text}")
    
    async def _wait_for_completion(self, prompt_id: str, filename_prefix: str, timeout: int = 300) -> str:
        """等待任务完成并返回图片路径"""
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # 使用WebSocket监听任务状态
            async with websockets.connect(self.ws_url) as websocket:
                while True:
                    current_time = asyncio.get_event_loop().time()
                    if current_time - start_time > timeout:
                        raise Exception(f"任务超时: {timeout}秒")
                    
                    try:
                        # 等待消息，超时时间5秒
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        
                        # 安全处理消息编码
                        if isinstance(message, bytes):
                            try:
                                message = message.decode('utf-8')
                            except UnicodeDecodeError:
                                # 跳过无法解码的消息
                                logger.warning(f"跳过无法解码的WebSocket消息")
                                continue
                        
                        # 解析JSON
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError as e:
                            logger.warning(f"跳过无效的JSON消息: {e}")
                            continue
                        
                        if data.get('type') == 'executing' and data.get('data'):
                            node_id = data['data'].get('node')
                            prompt_id_received = data['data'].get('prompt_id')
                            
                            if prompt_id_received == prompt_id and node_id is None:
                                # 任务完成
                                logger.info(f"FluxKontext任务完成，prompt_id: {prompt_id}")
                                
                                # 获取生成的图片
                                image_path = await self._get_generated_image_path(prompt_id, filename_prefix)
                                return image_path
                        
                    except asyncio.TimeoutError:
                        # 超时继续等待
                        continue
                    except UnicodeDecodeError as e:
                        # 编码错误，跳过这条消息
                        logger.warning(f"WebSocket消息编码错误: {e}")
                        continue
                    except Exception as e:
                        # 其他错误，记录但继续等待
                        logger.warning(f"WebSocket消息处理错误: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"等待FluxKontext任务完成失败: {str(e)}")
            
            # 备用方案：使用HTTP轮询检查任务状态
            logger.info("WebSocket监听失败，尝试HTTP轮询方式...")
            try:
                return await self._wait_for_completion_polling(prompt_id, filename_prefix, timeout)
            except Exception as polling_error:
                logger.error(f"HTTP轮询也失败: {str(polling_error)}")
                raise Exception(f"等待FluxKontext任务完成失败: {str(e)}")
    
    async def _wait_for_completion_polling(self, prompt_id: str, filename_prefix: str, timeout: int = 300) -> str:
        """使用HTTP轮询方式等待任务完成"""
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > timeout:
                raise Exception(f"HTTP轮询超时: {timeout}秒")
            
            try:
                # 检查任务队列状态
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.http_url}/queue") as response:
                        if response.status == 200:
                            queue_data = await response.json()
                            
                            # 检查running队列
                            running_tasks = queue_data.get('queue_running', [])
                            pending_tasks = queue_data.get('queue_pending', [])
                            
                            # 检查我们的任务是否还在队列中
                            task_found = False
                            for task_info in running_tasks + pending_tasks:
                                if len(task_info) > 1 and task_info[1] == prompt_id:
                                    task_found = True
                                    break
                            
                            if not task_found:
                                # 任务不在队列中，说明已完成或失败
                                logger.info(f"任务 {prompt_id} 已从队列中移除，检查历史记录...")
                                
                                # 检查历史记录确认任务完成
                                image_path = await self._get_generated_image_path(prompt_id, filename_prefix)
                                return image_path
                
                # 等待3秒后再次检查
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.warning(f"HTTP轮询检查失败: {e}, 3秒后重试...")
                await asyncio.sleep(3)
    
    async def _get_generated_image_path(self, prompt_id: str, filename_prefix: str) -> str:
        """获取生成图片的本地路径"""
        
        try:
            # 获取任务历史记录
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.http_url}/history/{prompt_id}") as response:
                    if response.status == 200:
                        history_data = await response.json()
                        
                        if prompt_id in history_data:
                            outputs = history_data[prompt_id].get('outputs', {})
                            
                            # FluxKontext工作流的输出在节点136 (SaveImage)
                            save_image_output = outputs.get('136', {})
                            images = save_image_output.get('images', [])
                            
                            if images:
                                # 获取第一张图片
                                image_info = images[0]
                                filename = image_info['filename']
                                subfolder = image_info.get('subfolder', '')
                                
                                # 下载图片到本地
                                download_url = f"{self.http_url}/view"
                                params = {
                                    'filename': filename,
                                    'subfolder': subfolder,
                                    'type': 'output'
                                }
                                
                                # 下载并保存图片
                                local_path = await self._download_image(download_url, params, filename)
                                return local_path
                            else:
                                raise Exception("没有找到生成的图片")
                    else:
                        raise Exception(f"获取任务历史失败: {response.status}")
                        
        except Exception as e:
            logger.error(f"获取生成图片失败: {str(e)}")
            raise Exception(f"获取生成图片失败: {str(e)}")
    
    async def _download_image(self, url: str, params: Dict, filename: str) -> str:
        """下载图片到本地"""
        
        try:
            # 创建保存目录
            save_dir = "storage/audio_editor/exports/image_generation"
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(filename)[1] or ".png"
            local_filename = f"generated_{timestamp}_{uuid.uuid4().hex[:8]}{file_extension}"
            local_path = os.path.join(save_dir, local_filename)
            
            # 下载图片
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        with open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        logger.info(f"图片已保存到: {local_path}")
                        return local_path
                    else:
                        raise Exception(f"下载图片失败: {response.status}")
                        
        except Exception as e:
            logger.error(f"下载图片失败: {str(e)}")
            raise Exception(f"下载图片失败: {str(e)}")
    
    def _build_query_string(self, params: Dict) -> str:
        """构建查询字符串"""
        return "&".join([f"{k}={v}" for k, v in params.items()])
    
    async def get_models(self) -> List[Dict]:
        """获取可用的模型列表"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.http_url}/object_info") as response:
                    if response.status == 200:
                        object_info = await response.json()
                        
                        # 提取检查点模型
                        checkpoints = []
                        if "CheckpointLoaderSimple" in object_info:
                            ckpt_info = object_info["CheckpointLoaderSimple"]
                            if "input" in ckpt_info and "required" in ckpt_info["input"]:
                                ckpt_names = ckpt_info["input"]["required"].get("ckpt_name", [])
                                if isinstance(ckpt_names, list) and ckpt_names:
                                    checkpoints = [{"name": name, "type": "checkpoint"} for name in ckpt_names[0]]
                        
                        return checkpoints
                    else:
                        logger.error(f"获取模型列表失败: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"获取模型列表失败: {str(e)}")
            return []
    
    async def test_connection(self) -> bool:
        """测试与ComfyUI的连接"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.http_url}/history", timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"ComfyUI连接测试失败: {str(e)}")
            return False 
    
    def load_workflow_from_file(self, workflow_path: str) -> Dict:
        """从文件加载工作流"""
        
        try:
            import json
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            logger.info(f"工作流已从文件加载: {workflow_path}")
            return workflow
            
        except Exception as e:
            logger.error(f"加载工作流文件失败: {str(e)}")
            return self.default_workflow.copy()
    
    def validate_workflow(self, workflow: Dict) -> bool:
        """验证工作流是否有效"""
        
        required_nodes = ["3", "4", "5", "6", "7", "8", "9"]  # 基本节点
        
        for node_id in required_nodes:
            if node_id not in workflow:
                logger.warning(f"工作流缺少必需节点: {node_id}")
                return False
        
        # 检查关键节点的class_type
        expected_types = {
            "3": "KSampler",
            "4": "CheckpointLoaderSimple", 
            "5": "EmptyLatentImage",
            "6": "CLIPTextEncode",
            "7": "CLIPTextEncode",
            "8": "VAEDecode",
            "9": "SaveImage"
        }
        
        for node_id, expected_type in expected_types.items():
            if workflow.get(node_id, {}).get("class_type") != expected_type:
                logger.warning(f"节点 {node_id} 类型不匹配，期望: {expected_type}")
                return False
        
        logger.info("工作流验证通过")
        return True 