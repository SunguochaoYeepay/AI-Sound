# AI-Sound 音视频编辑系统设计文档

## 🎯 系统概述

AI-Sound 音视频编辑系统是一个集成在合成中心的专业级音视频编辑模块，旨在为用户提供类似剪映的编辑体验，支持对话音频与环境音的精确混合，以及未来的视频生成功能。

### 核心目标
- 🎵 **音频编辑**: 专业的多轨音频编辑功能
- 🎬 **视频生成**: 基于书籍内容生成图片和视频（未来）
- 🤖 **智能集成**: 与AI-Sound现有的智能分析无缝对接
- 🎛️ **用户体验**: 类似剪映的直观操作界面

## 🏗️ 系统架构

### 整体架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue3 前端     │    │   FastAPI后端   │    │   MoviePy引擎   │
│  音视频编辑器    │◄──►│   编辑API服务   │◄──►│   音视频处理    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Web Audio API  │    │  PostgreSQL DB  │    │    FFmpeg       │
│   实时预览      │    │   项目数据存储   │    │   底层处理      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📱 前端界面设计

### 1. 菜单结构增强

#### 路由配置更新
```javascript
// platform/frontend/src/router/index.js 新增路由
const routes = [
  // ... 现有路由
  
  // 音视频编辑中心（新增）
  {
    path: '/synthesis/:projectId/editor',
    name: 'AudioVideoEditor', 
    component: () => import('../views/AudioVideoEditor.vue'),
    meta: { 
      title: '音视频编辑器',
      requiresProject: true
    }
  },
  
  // 编辑项目管理（新增）
  {
    path: '/editor-projects',
    name: 'EditorProjects',
    component: () => import('../views/EditorProjects.vue'),
    meta: { 
      title: '编辑项目'
    }
  }
]
```

#### 主导航菜单更新
```vue
<!-- App.vue 或主导航组件 -->
<template>
  <ALayout>
    <ALayoutSider>
      <AMenu mode="inline" :selected-keys="selectedKeys">
        <!-- 现有菜单项... -->
        
        <!-- 新增：编辑中心 -->
        <AMenuItem key="editor-center">
          <FileImageOutlined />
          <span>编辑中心</span>
        </AMenuItem>
        
        <ASubMenu key="editor-submenu">
          <template #title>
            <ScissorOutlined />
            <span>音视频编辑</span>
          </template>
          
          <AMenuItem key="editor-projects">
            <FolderOutlined />
            <span>编辑项目</span>
          </AMenuItem>
          
          <AMenuItem key="audio-mixer">
            <SoundOutlined />
            <span>音频混音台</span>
          </AMenuItem>
        </ASubMenu>
      </AMenu>
    </ALayoutSider>
  </ALayout>
</template>
```

### 2. 编辑器界面布局

#### 编辑器主界面设计
```
┌─────────────────────────────────────────────────────┐
│  📺 预览区域 (Preview Area)                        │
│  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   波形预览      │  │      控制面板               │ │
│  │   🎵           │  │  ⏯️ ⏹️ 🔊 📤              │ │
│  │   🎛️ 时间轴编辑区 (Timeline Area)                     │
│  │   ┌─ 00:00 ────── 01:30 ────── 03:00 ────── 04:30 ─┐ │
│  │   │ 🎤 对话轨  [████████░░░░][░░░░████████]          │ │
│  │   │ 🌊 环境轨  [░░░░░░░░████████████████████]        │ │
│  │   │ 🎵 音效轨  [░░██░░░░░░░░░░░░░░████░░░░░░]          │ │
│  │   │ 🎬 视频轨  [████████████████████████████]（未来）│ │
│  │   └─────────────────────────────────────────────────┘ │
│   └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## 🔧 后端MoviePy集成

### 1. MoviePy简介

**MoviePy** 是一个功能强大的Python视频编辑库，特点包括：

- **编程式编辑**: 使用Python代码进行音视频处理
- **基于FFmpeg**: 支持几乎所有音视频格式
- **功能丰富**: 音频混合、视频合成、特效处理等
- **易于集成**: 与现有Python后端无缝集成

### 2. 音频处理服务

#### MoviePy服务类
```python
# platform/backend/app/services/moviepy_service.py
from moviepy.editor import *
from moviepy.audio.fx import all as afx
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
import time
import logging

logger = logging.getLogger(__name__)

class AudioEditingService:
    """基于MoviePy的音频编辑服务"""
    
    def __init__(self):
        self.temp_dir = Path("storage/temp/audio_editing")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def mix_dialogue_with_environment(
        self,
        dialogue_path: str,
        environment_path: str,
        environment_volume: float = 0.3,
        fade_duration: float = 1.0
    ) -> str:
        """混合对话音频与环境音"""
        try:
            # 加载音频文件
            dialogue = AudioFileClip(dialogue_path)
            environment = AudioFileClip(environment_path)
            
            # 环境音循环播放，匹配对话长度
            if environment.duration < dialogue.duration:
                environment = environment.loop(duration=dialogue.duration)
            else:
                environment = environment.subclip(0, dialogue.duration)
            
            # 调整环境音音量
            environment = environment.volumex(environment_volume)
            
            # 为环境音添加淡入淡出效果
            if fade_duration > 0:
                environment = environment.fx(afx.audio_fadein, fade_duration)
                environment = environment.fx(afx.audio_fadeout, fade_duration)
            
            # 混合音轨
            mixed_audio = CompositeAudioClip([dialogue, environment])
            
            # 输出文件
            output_path = self.temp_dir / f"mixed_{int(time.time())}.wav"
            mixed_audio.write_audiofile(str(output_path), verbose=False)
            
            # 清理资源
            dialogue.close()
            environment.close() 
            mixed_audio.close()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"音频混合失败: {str(e)}")
            raise AudioProcessingError(f"混合音频时发生错误: {str(e)}")
    
    async def create_chapter_audio(
        self,
        audio_segments: List[Dict],
        crossfade_duration: float = 0.5
    ) -> str:
        """创建完整章节音频"""
        try:
            clips = []
            
            for segment in audio_segments:
                # 加载对话音频
                dialogue = AudioFileClip(segment['dialogue_path'])
                
                # 根据场景类型添加环境音
                if segment.get('environment_path'):
                    env = AudioFileClip(segment['environment_path'])
                    env = env.volumex(segment.get('environment_volume', 0.2))
                    env = env.loop(duration=dialogue.duration)
                    
                    # 混合当前片段
                    mixed_segment = CompositeAudioClip([dialogue, env])
                    clips.append(mixed_segment)
                else:
                    clips.append(dialogue)
            
            # 使用交叉淡化连接所有片段
            if crossfade_duration > 0:
                final_audio = concatenate_audioclips(
                    clips, 
                    method="crossfadein",
                    crossfade=crossfade_duration
                )
            else:
                final_audio = concatenate_audioclips(clips)
            
            # 输出最终音频
            output_path = self.temp_dir / f"chapter_{int(time.time())}.wav"
            final_audio.write_audiofile(str(output_path), verbose=False)
            
            # 清理资源
            for clip in clips:
                clip.close()
            final_audio.close()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"章节音频创建失败: {str(e)}")
            raise AudioProcessingError(f"创建章节音频时发生错误: {str(e)}")

class VideoGenerationService:
    """视频生成服务（未来功能）"""
    
    def __init__(self):
        self.temp_dir = Path("storage/temp/video_generation")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_slideshow_video(
        self,
        images: List[str],
        audio_path: str,
        transition_duration: float = 1.0
    ) -> str:
        """创建图片轮播视频"""
        try:
            # 加载音频
            audio = AudioFileClip(audio_path)
            
            # 计算每张图片的显示时长
            image_duration = audio.duration / len(images)
            
            # 创建图片剪辑
            clips = []
            for i, image_path in enumerate(images):
                img_clip = ImageClip(image_path, duration=image_duration)
                img_clip = img_clip.resize(height=720)  # 标准化高度
                clips.append(img_clip)
            
            # 添加转场效果
            if transition_duration > 0:
                video = concatenate_videoclips(
                    clips, 
                    method="crossfadein",
                    crossfade=transition_duration
                )
            else:
                video = concatenate_videoclips(clips)
            
            # 设置音频
            final_video = video.set_audio(audio)
            
            # 输出视频
            output_path = self.temp_dir / f"slideshow_{int(time.time())}.mp4"
            final_video.write_videofile(
                str(output_path),
                fps=24,
                codec='libx264',
                audio_codec='aac',
                verbose=False
            )
            
            # 清理资源
            audio.close()
            video.close()
            final_video.close()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"视频生成失败: {str(e)}")
            raise VideoProcessingError(f"生成视频时发生错误: {str(e)}")
```

### 3. 编辑API接口

#### 音频编辑API
```python
# platform/backend/app/api/v1/audio_editor.py
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from app.services.moviepy_service import AudioEditingService, VideoGenerationService
from app.schemas.audio_editor import *
from typing import List
from pathlib import Path

router = APIRouter(prefix="/api/v1/audio-editor", tags=["音频编辑"])

audio_service = AudioEditingService()
video_service = VideoGenerationService()

@router.post("/mix-audio", response_model=AudioMixResult)
async def mix_audio(request: AudioMixRequest):
    """混合对话音频与环境音"""
    try:
        output_path = await audio_service.mix_dialogue_with_environment(
            dialogue_path=request.dialogue_path,
            environment_path=request.environment_path,
            environment_volume=request.environment_volume,
            fade_duration=request.fade_duration
        )
        
        return AudioMixResult(
            success=True,
            output_path=output_path,
            message="音频混合成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-chapter", response_model=ChapterAudioResult)
async def create_chapter_audio(request: ChapterAudioRequest):
    """创建完整章节音频"""
    try:
        output_path = await audio_service.create_chapter_audio(
            audio_segments=request.segments,
            crossfade_duration=request.crossfade_duration
        )
        
        return ChapterAudioResult(
            success=True,
            output_path=output_path,
            duration=0,  # 可以计算实际时长
            message="章节音频创建成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_audio(filename: str):
    """下载处理后的音频文件"""
    file_path = Path(f"storage/temp/audio_editing/{filename}")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='audio/wav'
    )
```

## 🗄️ 数据库设计

### 编辑项目表结构
```sql
-- 音视频编辑项目表
CREATE TABLE IF NOT EXISTS audio_video_projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_project_id INTEGER REFERENCES novel_projects(id),
    project_type VARCHAR(50) DEFAULT 'audio_editing',
    project_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 编辑轨道表
CREATE TABLE IF NOT EXISTS editor_tracks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES audio_video_projects(id) ON DELETE CASCADE,
    track_name VARCHAR(255) NOT NULL,
    track_type VARCHAR(50) NOT NULL, -- 'dialogue', 'environment', 'sfx', 'video'
    track_order INTEGER DEFAULT 0,
    is_muted BOOLEAN DEFAULT FALSE,
    volume FLOAT DEFAULT 1.0,
    track_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 音频片段表
CREATE TABLE IF NOT EXISTS audio_clips (
    id SERIAL PRIMARY KEY,
    track_id INTEGER REFERENCES editor_tracks(id) ON DELETE CASCADE,
    clip_name VARCHAR(255),
    file_path VARCHAR(500) NOT NULL,
    start_time FLOAT NOT NULL,
    duration FLOAT NOT NULL,
    volume FLOAT DEFAULT 1.0,
    effects JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 📋 实施计划

### Phase 1: MoviePy集成 (1周)
- ✅ 安装MoviePy依赖
- ✅ 创建音频处理服务类
- ✅ 实现基础混音功能
- ✅ 测试音频处理能力

### Phase 2: 前端编辑界面 (3周)
- ✅ 创建编辑器页面组件
- ✅ 实现时间轴界面
- ✅ 音频轨道可视化
- ✅ 拖拽编辑功能

### Phase 3: 系统集成 (2周)
- ✅ API接口开发
- ✅ 数据库表创建
- ✅ 与合成中心集成
- ✅ 测试完整流程

### Phase 4: 高级功能 (2周)
- ✅ 波形可视化
- ✅ 音频效果处理
- ✅ 批量导出功能
- ✅ 用户体验优化

## 🎯 集成方案

### 与AI-Sound现有系统集成

#### 1. 合成中心集成
```vue
<!-- SynthesisCenter.vue 增强版 -->
<template>
  <div class="synthesis-center">
    <!-- 原有内容 -->
    <ProjectHeader />
    <ChapterSelector />
    <ContentPreview />
    
    <!-- 新增：编辑器入口 -->
    <div class="editor-actions">
      <AButton 
        type="primary" 
        @click="openAudioEditor"
        :disabled="!hasGeneratedAudio"
      >
        🎛️ 进入音频编辑器
      </AButton>
    </div>
  </div>
</template>

<script setup>
const openAudioEditor = () => {
  // 跳转到编辑器页面
  router.push(`/synthesis/${projectId}/editor`)
}
</script>
```

#### 2. 菜单结构更新
```vue
<!-- 主导航增加编辑中心 -->
<AMenuItem key="editor-center" @click="goToEditorProjects">
  <ScissorOutlined />
  <span>编辑中心</span>
</AMenuItem>
```

## 💡 技术优势

### MoviePy的优势
1. **功能强大**: 支持复杂的音视频处理
2. **Python原生**: 与AI-Sound后端完美集成
3. **社区成熟**: 丰富的文档和示例
4. **扩展性好**: 可轻松扩展到视频处理

### 自研界面的优势
1. **定制化**: 完全适配AI-Sound的业务需求
2. **用户体验**: 类似剪映的专业界面
3. **集成性**: 与现有系统无缝对接
4. **扩展性**: 为未来功能预留空间

## 📈 预期效果

1. **功能完整性**: 从智能分析到专业编辑的完整闭环
2. **用户体验**: 专业级音频编辑能力
3. **扩展潜力**: 为视频生成功能奠定基础
4. **竞争优势**: 在语音合成基础上增加编辑能力

---

## 📝 总结

通过引入MoviePy作为音频处理引擎，结合自研的Vue3编辑界面，AI-Sound将从单纯的语音合成平台升级为具备专业编辑能力的综合性内容创作工具。

这个混合方案既保证了处理能力的专业性，又维持了系统的一致性和扩展性，为AI-Sound的长远发展奠定了坚实基础。 