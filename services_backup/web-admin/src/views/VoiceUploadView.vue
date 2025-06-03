<template>
  <div class="voice-upload-container">
    <a-page-header
      title="声音上传"
      sub-title="为MegaTTS3引擎添加自定义声音"
      @back="goBack"
    />
    
    <a-card title="上传声音文件">
      <a-form :model="uploadForm" layout="vertical" @finish="handleUpload">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item 
              label="声音名称" 
              name="name" 
              :rules="[{ required: true, message: '请输入声音名称' }]"
            >
              <a-input 
                v-model:value="uploadForm.name" 
                placeholder="例如：温柔女声、磁性男声"
                allow-clear
              />
            </a-form-item>
          </a-col>
          
          <a-col :span="12">
            <a-form-item label="目标引擎" name="engine">
              <a-select v-model:value="uploadForm.engine" placeholder="选择TTS引擎">
                <a-select-option value="megatts3">MegaTTS3</a-select-option>
                <a-select-option value="bert-vits2">Bert-VITS2</a-select-option>
                <a-select-option value="espnet">ESPnet</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="24">
          <a-col :span="8">
            <a-form-item label="性别" name="gender">
              <a-select v-model:value="uploadForm.gender" placeholder="选择性别" allow-clear>
                <a-select-option value="male">男性</a-select-option>
                <a-select-option value="female">女性</a-select-option>
                <a-select-option value="other">其他</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          
          <a-col :span="8">
            <a-form-item label="年龄段" name="age_group">
              <a-select v-model:value="uploadForm.age_group" placeholder="选择年龄段" allow-clear>
                <a-select-option value="child">儿童</a-select-option>
                <a-select-option value="young">青年</a-select-option>
                <a-select-option value="middle">中年</a-select-option>
                <a-select-option value="old">老年</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          
          <a-col :span="8">
            <a-form-item label="语言" name="language">
              <a-select v-model:value="uploadForm.language" placeholder="选择语言">
                <a-select-option value="zh-CN">中文</a-select-option>
                <a-select-option value="en-US">英文</a-select-option>
                <a-select-option value="ja-JP">日文</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-form-item label="声音标签" name="tags">
          <a-select 
            v-model:value="uploadForm.tags" 
            mode="tags" 
            placeholder="添加标签，如：清晰、温柔、磁性等"
            :options="tagOptions"
            allow-clear
          />
        </a-form-item>
        
        <a-form-item label="声音描述" name="description">
          <a-textarea 
            v-model:value="uploadForm.description" 
            placeholder="描述这个声音的特点、适用场景等"
            :rows="3"
            allow-clear
          />
        </a-form-item>
        
        <!-- 音频文件上传 -->
        <a-form-item 
          label="参考音频文件"
        >
          <a-upload-dragger
            v-model:file-list="audioFileList"
            name="audio"
            :multiple="false"
            :before-upload="beforeAudioUpload"
            @remove="handleAudioRemove"
            accept=".wav,.mp3,.flac,.m4a"
          >
            <p class="ant-upload-drag-icon">
              <sound-outlined />
            </p>
            <p class="ant-upload-text">点击或拖拽音频文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持 WAV、MP3、FLAC、M4A 格式，建议使用高质量音频文件（时长10-30秒）
            </p>
          </a-upload-dragger>
          <div v-if="!audioFileList?.length" style="color: #ff4d4f; margin-top: 8px;">
            请上传音频文件
          </div>
        </a-form-item>
        
        <!-- 特征文件上传（可选，MegaTTS3专用） -->
        <a-form-item 
          v-if="uploadForm.engine === 'megatts3'"
          label="特征文件（可选）" 
          name="npyFile"
        >
          <a-upload-dragger
            v-model:file-list="npyFileList"
            name="npy"
            :multiple="false"
            :before-upload="beforeNpyUpload"
            @remove="handleNpyRemove"
            accept=".npy"
          >
            <p class="ant-upload-drag-icon">
              <file-outlined />
            </p>
            <p class="ant-upload-text">上传预提取的特征文件（.npy格式）</p>
            <p class="ant-upload-hint">
              如果没有特征文件，系统将自动从音频文件中提取
            </p>
          </a-upload-dragger>
        </a-form-item>
        
        <!-- 音频预览 -->
        <a-form-item v-if="audioPreviewUrl" label="音频预览">
          <div class="audio-preview">
            <div id="waveform" ref="waveformRef"></div>
            <div class="audio-controls">
              <a-button 
                :disabled="!audioLoaded"
                @click="toggleAudio"
                type="primary"
                shape="circle"
                size="large"
              >
                <template #icon>
                  <pause-outlined v-if="isPlaying" />
                  <caret-right-outlined v-else />
                </template>
              </a-button>
              <span class="audio-duration" v-if="audioDuration">
                时长: {{ formatDuration(audioDuration) }}
              </span>
            </div>
          </div>
        </a-form-item>
        
        <a-form-item>
          <a-space>
            <a-button 
              type="primary" 
              html-type="submit"
              :loading="uploading"
              :disabled="!audioFileList?.length"
            >
              <template #icon><upload-outlined /></template>
              上传并处理
            </a-button>
            <a-button @click="resetForm">
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
    
    <!-- 处理进度 -->
    <a-card v-if="processing" title="处理进度" style="margin-top: 24px">
      <a-steps :current="currentStep" :status="stepStatus">
        <a-step title="上传文件" description="上传音频和特征文件" />
        <a-step title="音频处理" description="格式转换和质量检查" />
        <a-step title="特征提取" description="提取声音特征" />
        <a-step title="注册声音" description="保存到声音库" />
      </a-steps>
      
      <div class="progress-details" style="margin-top: 24px">
        <a-progress 
          :percent="progressPercent" 
          :status="progressStatus"
          :show-info="true"
        />
        <p style="margin-top: 8px">{{ progressMessage }}</p>
      </div>
    </a-card>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { voiceAPI } from '../services/api';
import WaveSurfer from 'wavesurfer.js';
import {
  SoundOutlined,
  FileOutlined,
  UploadOutlined,
  CaretRightOutlined,
  PauseOutlined
} from '@ant-design/icons-vue';

export default defineComponent({
  name: 'VoiceUploadView',
  components: {
    SoundOutlined,
    FileOutlined,
    UploadOutlined,
    CaretRightOutlined,
    PauseOutlined
  },
  setup() {
    const router = useRouter();
    
    // 表单数据
    const uploadForm = reactive({
      name: '',
      engine: 'megatts3',
      gender: undefined,
      age_group: undefined,
      language: 'zh-CN',
      tags: [],
      description: ''
    });
    
    // 文件列表
    const audioFileList = ref([]);
    const npyFileList = ref([]);
    
    // 音频预览
    const waveformRef = ref(null);
    const waveSurfer = ref(null);
    const audioPreviewUrl = ref('');
    const audioLoaded = ref(false);
    const isPlaying = ref(false);
    const audioDuration = ref(0);
    
    // 上传状态
    const uploading = ref(false);
    const processing = ref(false);
    const currentStep = ref(0);
    const stepStatus = ref('process');
    const progressPercent = ref(0);
    const progressStatus = ref('active');
    const progressMessage = ref('');
    
    // 标签选项
    const tagOptions = [
      { value: 'clear', label: '清晰' },
      { value: 'soft', label: '柔和' },
      { value: 'deep', label: '低沉' },
      { value: 'bright', label: '明亮' },
      { value: 'warm', label: '温暖' },
      { value: 'energetic', label: '有活力' },
      { value: 'calm', label: '平静' },
      { value: 'professional', label: '专业' },
      { value: 'friendly', label: '友好' },
      { value: 'authoritative', label: '权威' }
    ];
    
    // 音频文件上传前检查
    const beforeAudioUpload = (file) => {
      const isAudio = file.type.startsWith('audio/') || 
                     ['.wav', '.mp3', '.flac', '.m4a'].some(ext => file.name.toLowerCase().endsWith(ext));
      
      if (!isAudio) {
        message.error('只能上传音频文件！');
        return false;
      }
      
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('音频文件大小不能超过50MB！');
        return false;
      }
      
      // 创建预览URL
      audioPreviewUrl.value = URL.createObjectURL(file);
      
      // 初始化波形图
      nextTick(() => {
        initWaveform();
      });
      
      return false; // 阻止自动上传
    };
    
    // NPY文件上传前检查
    const beforeNpyUpload = (file) => {
      const isNpy = file.name.toLowerCase().endsWith('.npy');
      
      if (!isNpy) {
        message.error('只能上传.npy格式的特征文件！');
        return false;
      }
      
      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('特征文件大小不能超过10MB！');
        return false;
      }
      
      return false; // 阻止自动上传
    };
    
    // 移除音频文件
    const handleAudioRemove = () => {
      if (audioPreviewUrl.value) {
        URL.revokeObjectURL(audioPreviewUrl.value);
        audioPreviewUrl.value = '';
      }
      
      if (waveSurfer.value) {
        waveSurfer.value.destroy();
        waveSurfer.value = null;
      }
      
      audioLoaded.value = false;
      isPlaying.value = false;
      audioDuration.value = 0;
    };
    
    // 移除NPY文件
    const handleNpyRemove = () => {
      // NPY文件移除处理
    };
    
    // 初始化波形图
    const initWaveform = () => {
      if (waveSurfer.value) {
        waveSurfer.value.destroy();
      }
      
      if (!waveformRef.value || !audioPreviewUrl.value) {
        return;
      }
      
      waveSurfer.value = WaveSurfer.create({
        container: waveformRef.value,
        waveColor: '#4096ff',
        progressColor: '#1677ff',
        cursorColor: '#999',
        height: 80,
        responsive: true,
        normalize: true
      });
      
      // 监听事件
      waveSurfer.value.on('ready', () => {
        audioLoaded.value = true;
        audioDuration.value = waveSurfer.value.getDuration();
      });
      
      waveSurfer.value.on('play', () => {
        isPlaying.value = true;
      });
      
      waveSurfer.value.on('pause', () => {
        isPlaying.value = false;
      });
      
      waveSurfer.value.on('finish', () => {
        isPlaying.value = false;
      });
      
      // 加载音频
      waveSurfer.value.load(audioPreviewUrl.value);
    };
    
    // 播放/暂停音频
    const toggleAudio = () => {
      if (waveSurfer.value) {
        waveSurfer.value.playPause();
      }
    };
    
    // 格式化时长
    const formatDuration = (seconds) => {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    };
    
    // 处理上传
    const handleUpload = async () => {
      if (!audioFileList.value?.length) {
        message.error('请先上传音频文件');
        return;
      }
      
      uploading.value = true;
      processing.value = true;
      currentStep.value = 0;
      stepStatus.value = 'process';
      progressPercent.value = 0;
      progressStatus.value = 'active';
      
      try {
        // 步骤1: 上传文件
        progressMessage.value = '正在上传文件...';
        progressPercent.value = 10;
        
        const formData = new FormData();
        formData.append('audio', audioFileList.value[0].originFileObj);
        
        if (npyFileList.value.length > 0) {
          formData.append('npy', npyFileList.value[0].originFileObj);
        }
        
        // 添加元数据
        formData.append('metadata', JSON.stringify({
          name: uploadForm.name,
          engine: uploadForm.engine,
          gender: uploadForm.gender,
          age_group: uploadForm.age_group,
          language: uploadForm.language,
          tags: uploadForm.tags,
          description: uploadForm.description
        }));
        
        currentStep.value = 1;
        progressMessage.value = '正在处理音频文件...';
        progressPercent.value = 30;
        
        // 调用API上传
        const response = await voiceAPI.uploadVoice(formData, {
          onUploadProgress: (progressEvent) => {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            progressPercent.value = 30 + (percent * 0.4); // 30-70%
          }
        });
        
        currentStep.value = 2;
        progressMessage.value = '正在提取声音特征...';
        progressPercent.value = 70;
        
        // 等待特征提取完成
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        currentStep.value = 3;
        progressMessage.value = '正在注册声音到库...';
        progressPercent.value = 90;
        
        // 等待注册完成
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        progressPercent.value = 100;
        progressStatus.value = 'success';
        progressMessage.value = '声音上传成功！';
        stepStatus.value = 'finish';
        
        message.success('声音上传并处理成功！');
        
        // 延迟后跳转到声音列表
        setTimeout(() => {
          router.push('/voices');
        }, 2000);
        
      } catch (error) {
        console.error('上传失败:', error);
        stepStatus.value = 'error';
        progressStatus.value = 'exception';
        progressMessage.value = '上传失败: ' + (error.response?.data?.message || error.message);
        message.error('上传失败: ' + (error.response?.data?.message || error.message));
      } finally {
        uploading.value = false;
      }
    };
    
    // 重置表单
    const resetForm = () => {
      Object.assign(uploadForm, {
        name: '',
        engine: 'megatts3',
        gender: undefined,
        age_group: undefined,
        language: 'zh-CN',
        tags: [],
        description: ''
      });
      
      audioFileList.value = [];
      npyFileList.value = [];
      
      handleAudioRemove();
      
      processing.value = false;
      currentStep.value = 0;
      progressPercent.value = 0;
    };
    
    // 返回上一页
    const goBack = () => {
      router.go(-1);
    };
    
    // 组件卸载时清理资源
    onUnmounted(() => {
      if (waveSurfer.value) {
        waveSurfer.value.destroy();
      }
      
      if (audioPreviewUrl.value) {
        URL.revokeObjectURL(audioPreviewUrl.value);
      }
    });
    
    return {
      uploadForm,
      audioFileList,
      npyFileList,
      tagOptions,
      
      // 音频预览
      waveformRef,
      audioPreviewUrl,
      audioLoaded,
      isPlaying,
      audioDuration,
      toggleAudio,
      formatDuration,
      
      // 文件处理
      beforeAudioUpload,
      beforeNpyUpload,
      handleAudioRemove,
      handleNpyRemove,
      
      // 上传处理
      uploading,
      processing,
      currentStep,
      stepStatus,
      progressPercent,
      progressStatus,
      progressMessage,
      handleUpload,
      resetForm,
      goBack
    };
  }
});
</script>

<style scoped>
.voice-upload-container {
  max-width: 1000px;
  margin: 0 auto;
}

.audio-preview {
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 16px;
  background: #fafafa;
}

.audio-controls {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: center;
}

.audio-duration {
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
}

.progress-details {
  text-align: center;
}

:deep(.ant-upload-drag) {
  background: #fafafa;
}

:deep(.ant-upload-drag:hover) {
  border-color: #4096ff;
}

:deep(.ant-upload-drag-icon) {
  font-size: 48px;
  color: #4096ff;
}

:deep(.ant-upload-text) {
  font-size: 16px;
  color: rgba(0, 0, 0, 0.85);
}

:deep(.ant-upload-hint) {
  color: rgba(0, 0, 0, 0.45);
}
</style>