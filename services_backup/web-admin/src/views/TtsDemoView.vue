<template>
  <div class="tts-demo">
    <page-header title="语音试听" subtitle="测试不同音色和参数效果" />
    
    <a-row :gutter="16">
      <a-col :span="16">
        <a-card title="文本输入">
          <a-form :model="formState" layout="vertical">
            <a-form-item label="输入文本">
              <a-textarea 
                v-model:value="formState.text" 
                placeholder="请输入要转换的文本内容，如：你好，世界！" 
                :rows="6"
                :disabled="processing"
              />
            </a-form-item>
            
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="TTS引擎选择">
                  <a-select
                    v-model:value="formState.engine"
                    placeholder="选择TTS引擎"
                    :disabled="processing"
                    :loading="loadingEngines"
                    @change="onEngineChange"
                  >
                    <a-select-option value="auto">
                      🤖 智能选择 (推荐)
                    </a-select-option>
                    <a-select-option 
                      v-for="engine in availableEngines" 
                      :key="engine.id" 
                      :value="engine.id"
                      :disabled="engine.status !== 'healthy'"
                    >
                      {{ getEngineDisplayName(engine) }}
                      <a-tag 
                        :color="engine.status === 'healthy' ? 'green' : 'red'"
                        size="small"
                        style="margin-left: 8px;"
                      >
                        {{ engine.status === 'healthy' ? '正常' : '离线' }}
                      </a-tag>
                    </a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              
              <a-col :span="8">
                <a-form-item label="音色选择">
                  <a-select
                    v-model:value="formState.voiceId"
                    placeholder="选择音色"
                    :disabled="processing"
                    :loading="loadingVoices"
                  >
                    <a-select-option 
                      v-for="voice in availableVoices" 
                      :key="voice.id" 
                      :value="voice.id"
                    >
                      {{ voice.name }} ({{ voice.language || '中文' }})
                    </a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              
              <a-col :span="8">
                <a-form-item label="情感类型">
                  <a-select
                    v-model:value="formState.emotionType"
                    placeholder="选择情感类型"
                    :disabled="processing"
                  >
                    <a-select-option value="neutral">中性</a-select-option>
                    <a-select-option value="happy">开心</a-select-option>
                    <a-select-option value="sad">悲伤</a-select-option>
                    <a-select-option value="angry">愤怒</a-select-option>
                    <a-select-option value="surprised">惊讶</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              
              <a-col :span="8">
                <a-form-item label="情感强度">
                  <a-slider
                    v-model:value="formState.emotionIntensity"
                    :min="0"
                    :max="1"
                    :step="0.1"
                    :disabled="processing"
                  />
                </a-form-item>
              </a-col>
            </a-row>
            
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="语速调节">
                  <a-slider
                    v-model:value="formState.speedScale"
                    :min="0.5"
                    :max="2.0"
                    :step="0.1"
                    :disabled="processing"
                  />
                </a-form-item>
              </a-col>
              
              <a-col :span="12">
                <a-form-item label="音调调节">
                  <a-slider
                    v-model:value="formState.pitchScale"
                    :min="0.5"
                    :max="2.0"
                    :step="0.1"
                    :disabled="processing"
                  />
                </a-form-item>
              </a-col>
            </a-row>
            
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="声音参考文件(可选)">
                  <div class="upload-box">
                    <input 
                      type="file" 
                      accept="audio/*" 
                      @change="onVoiceFileChange" 
                      ref="voiceFileRef" 
                      style="display: none;"
                      :disabled="processing"
                    />
                    <a-button 
                      type="dashed" 
                      @click="triggerFileUpload"
                      style="width: 100%;"
                      :disabled="processing"
                    >
                      <upload-outlined /> 上传声音文件
                    </a-button>
                    <span v-if="voiceFileName" class="file-name">{{ voiceFileName }}</span>
                  </div>
                </a-form-item>
              </a-col>
            </a-row>
            
            <a-form-item>
              <a-space>
                <a-button 
                  type="primary" 
                  @click="generateSpeech" 
                  :loading="processing"
                >
                  生成语音
                </a-button>
                <a-button @click="resetForm" :disabled="processing">重置</a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>
      
      <a-col :span="8">
        <a-card title="语音试听">
          <div v-if="!audioUrl" class="empty-player">
            <sound-outlined :style="{ fontSize: '64px', color: '#d9d9d9' }" />
            <p>生成语音后将在此处播放</p>
          </div>
          
          <div v-else class="audio-player">
            <div ref="waveformRef" class="waveform"></div>
            
            <div class="audio-controls">
              <a-button
                type="primary"
                shape="circle"
                :icon="isPlaying ? h(PauseOutlined) : h(PlayCircleOutlined)"
                @click="togglePlay"
              />
              
              <a-button
                type="link"
                @click="downloadAudio"
              >
                <download-outlined /> 下载音频
              </a-button>
            </div>
            
            <div class="audio-info">
              <p><strong>时长:</strong> {{ audioDuration.toFixed(2) }}秒</p>
              <p><strong>音色:</strong> {{ getVoiceName(formState.voiceId) }}</p>
              <p><strong>情感:</strong> {{ getEmotionName(formState.emotionType) }}</p>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted, onBeforeUnmount, h } from 'vue';
import { message } from 'ant-design-vue';
import { ttsAPI, voiceAPI, engineAPI } from '../services/api';
import { 
  SoundOutlined, 
  PlayCircleOutlined, 
  PauseOutlined, 
  DownloadOutlined,
  UploadOutlined
} from '@ant-design/icons-vue';
import WaveSurfer from 'wavesurfer.js';
import PageHeader from '@/components/common/PageHeader.vue';

export default defineComponent({
  name: 'TtsDemoView',
  components: {
    PageHeader,
    SoundOutlined,
    PlayCircleOutlined,
    PauseOutlined,
    DownloadOutlined,
    UploadOutlined
  },
  setup() {
    // 移除旧的API store
    const waveformRef = ref(null);
    const wavesurfer = ref(null);
    const voiceFileRef = ref(null);
    
    // 表单状态
    const formState = reactive({
      text: '老爹，这是AI-Sound语音合成系统的演示！',
      voiceId: 'voice_1748615762_2f4146ac',
      engine: 'auto', // 默认智能选择
      emotionType: 'neutral',
      emotionIntensity: 0.5,
      speedScale: 1.0,
      pitchScale: 1.0,
      p_w: 1.0,
      t_w: 1.0
    });
    
    // 音频状态
    const audioUrl = ref('');
    const audioBase64 = ref('');
    const audioDuration = ref(0);
    const isPlaying = ref(false);
    const processing = ref(false);
    
    // 声音列表状态
    const availableVoices = ref([]);
    const loadingVoices = ref(false);
    
    // 引擎列表状态
    const availableEngines = ref([]);
    const loadingEngines = ref(false);
    
    // 新增：声纹文件状态
    const voiceFile = ref(null);
    const voiceFileName = ref('');
    const onVoiceFileChange = (e) => {
      const file = e.target.files[0];
      if (file) {
        voiceFile.value = file;
        voiceFileName.value = file.name;
      } else {
        voiceFile.value = null;
        voiceFileName.value = '';
      }
    };
    
    // 触发文件上传
    const triggerFileUpload = () => {
      if (voiceFileRef.value) {
        voiceFileRef.value.click();
      }
    };
    
    // 初始化波形图
    const initWaveSurfer = () => {
      if (wavesurfer.value) {
        wavesurfer.value.destroy();
      }
      
      wavesurfer.value = WaveSurfer.create({
        container: waveformRef.value,
        waveColor: '#409EFF',
        progressColor: '#1890ff',
        cursorColor: '#f5222d',
        barWidth: 2,
        barRadius: 3,
        cursorWidth: 1,
        height: 80,
        barGap: 2
      });
      
      wavesurfer.value.on('play', () => {
        isPlaying.value = true;
      });
      
      wavesurfer.value.on('pause', () => {
        isPlaying.value = false;
      });
      
      wavesurfer.value.on('finish', () => {
        isPlaying.value = false;
      });
    };
    
    // 生成语音
    const generateSpeech = async () => {
      if (!formState.text.trim()) {
        message.warning('请输入要转换的文本');
        return;
      }
      processing.value = true;
      try {
        // 准备合成参数
        const synthesisParams = {
          text: formState.text,
          voice_id: formState.voiceId,
          speed: formState.speedScale,
          pitch: formState.pitchScale,
          format: 'wav'
        };
        
        // 如果选择了特定引擎，添加到参数中
        if (formState.engine && formState.engine !== 'auto') {
          synthesisParams.engine = formState.engine;
        }
        
        // 使用统一的API代理调用
        const response = await ttsAPI.synthesize(synthesisParams);
        
        if (response && response.data && response.data.audio_url) {
          // 下载音频文件
          const audioResponse = await fetch(response.data.audio_url);
          const blob = await audioResponse.blob();
          
          if (audioUrl.value) {
            URL.revokeObjectURL(audioUrl.value);
          }
          audioUrl.value = URL.createObjectURL(blob);
          audioDuration.value = response.data.duration || 1.0;
          
          setTimeout(() => {
            initWaveSurfer();
            wavesurfer.value.load(audioUrl.value);
          }, 100);
          
          message.success(`语音生成成功！`);
        } else {
          message.error(response?.message || '语音生成失败');
        }
      } catch (error) {
        message.error('语音生成请求失败: ' + (error.message || '未知错误'));
        console.error('语音生成错误', error);
      } finally {
        processing.value = false;
      }
    };
    
    // Base64转Blob
    const base64ToBlob = (base64, mimeType) => {
      const byteCharacters = atob(base64);
      const byteArrays = [];
      
      for (let offset = 0; offset < byteCharacters?.length; offset += 512) {
        const slice = byteCharacters.slice(offset, offset + 512);
        
        const byteNumbers = new Array(slice?.length);
        for (let i = 0; i < slice?.length; i++) {
          byteNumbers[i] = slice.charCodeAt(i);
        }
        
        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
      }
      
      return new Blob(byteArrays, { type: mimeType });
    };
    
    // 播放/暂停
    const togglePlay = () => {
      if (wavesurfer.value) {
        wavesurfer.value.playPause();
      }
    };
    
    // 下载音频
    const downloadAudio = () => {
      if (audioUrl.value) {
        const a = document.createElement('a');
        a.href = audioUrl.value;
        a.download = `tts_demo_${new Date().getTime()}.wav`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    };
    
    // 获取引擎显示名称
    const getEngineDisplayName = (engine) => {
      const engineMap = {
        'megatts3': '🚀 MegaTTS3',
        'megatts3_001': '🚀 MegaTTS3-001',
        'espnet': '🎵 ESPnet', 
        'bert_vits2': '🎭 Bert-VITS2'
      };
      
      // 如果有映射，使用映射名称；否则使用引擎名称，如果是UNKNOWN则使用ID
      const mappedName = engineMap[engine.id];
      if (mappedName) {
        return mappedName;
      }
      
      // 如果name是UNKNOWN，使用ID
      if (engine.name === 'UNKNOWN' || !engine.name) {
        return `🔧 ${engine.id.toUpperCase()}`;
      }
      
      return engine.name || engine.id;
    };
    
    // 引擎切换处理
    const onEngineChange = async (engineId) => {
      if (engineId === 'auto') {
        message.info('已启用智能引擎选择，系统将根据文本特征自动选择最佳引擎');
      } else {
        const engine = availableEngines.value.find(e => e.id === engineId);
        if (engine) {
          message.info(`已选择 ${getEngineDisplayName(engine)} 引擎`);
        }
      }
      
      // 重新加载该引擎的声音列表
      await loadAvailableVoices();
    };
    
    // 加载可用引擎列表
    const loadAvailableEngines = async () => {
      loadingEngines.value = true;
      try {
        const response = await engineAPI.getEngines();
        // 兼容不同的API响应格式
        availableEngines.value = response.engines || response.data?.engines || [];
        
        // 显示引擎状态统计
        const healthyEngines = availableEngines.value.filter(e => e.status === 'healthy');
        console.log(`已加载 ${availableEngines.value.length} 个引擎，其中 ${healthyEngines.length} 个正常运行`);
        
      } catch (error) {
        console.error('加载引擎列表失败:', error);
        // 静默失败，使用默认配置
        availableEngines.value = [];
      } finally {
        loadingEngines.value = false;
      }
    };
    
    // 重置表单
    const resetForm = () => {
      formState.text = '老爹，这是AI-Sound语音合成系统的演示！';
      formState.voiceId = 'voice_1748615762_2f4146ac';
      formState.engine = 'auto';
      formState.emotionType = 'neutral';
      formState.emotionIntensity = 0.5;
      formState.speedScale = 1.0;
      formState.pitchScale = 1.0;
      formState.p_w = 1.0;
      formState.t_w = 1.0;
    };
    
    // 获取音色名称
    const getVoiceName = (voiceId) => {
      const voiceMap = {
        'female_young': '年轻女声',
        'female_mature': '成熟女声',
        'male_young': '年轻男声',
        'male_middle': '中年男声',
        'male_elder': '老年男声'
      };
      return voiceMap[voiceId] || voiceId;
    };
    
    // 获取情感名称
    const getEmotionName = (emotionType) => {
      const emotionMap = {
        'neutral': '中性',
        'happy': '开心',
        'sad': '悲伤',
        'angry': '愤怒',
        'surprised': '惊讶'
      };
      return emotionMap[emotionType] || emotionType;
    };
    
    // 加载可用声音列表
    const loadAvailableVoices = async () => {
      loadingVoices.value = true;
      try {
        const response = await voiceAPI.getVoices();
        // axios拦截器已经处理了API响应格式，response.voices已经是数组
        availableVoices.value = response.voices || [];
        
        // 如果有声音且当前选中的声音不在列表中，选择第一个
        if (availableVoices.value.length > 0) {
          const currentVoiceExists = availableVoices.value.some(v => v.id === formState.voiceId);
          if (!currentVoiceExists) {
            formState.voiceId = availableVoices.value[0].id;
          }
        }
      } catch (error) {
        console.error('加载声音列表失败:', error);
        message.error('加载声音列表失败');
      } finally {
        loadingVoices.value = false;
      }
    };
    
    onMounted(async () => {
      // 先加载引擎列表
      await loadAvailableEngines();
      
      // 再加载声音列表
      await loadAvailableVoices();
      
      // 初始化波形图（如果有默认音频）
      if (audioUrl.value) {
        initWaveSurfer();
        wavesurfer.value.load(audioUrl.value);
      }
    });
    
    onBeforeUnmount(() => {
      // 清理资源
      if (wavesurfer.value) {
        wavesurfer.value.destroy();
      }
      
      if (audioUrl.value) {
        URL.revokeObjectURL(audioUrl.value);
      }
    });
    
    return {
      waveformRef,
      formState,
      audioUrl,
      audioDuration,
      isPlaying,
      processing,
      availableVoices,
      loadingVoices,
      availableEngines,
      loadingEngines,
      generateSpeech,
      togglePlay,
      downloadAudio,
      resetForm,
      getVoiceName,
      getEmotionName,
      h,
      PlayCircleOutlined,
      PauseOutlined,
      voiceFile,
      voiceFileName,
      onVoiceFileChange,
      voiceFileRef,
      triggerFileUpload,
      getEngineDisplayName,
      onEngineChange,
      loadAvailableEngines
    };
  }
});
</script>

<style scoped>
.tts-demo {
  padding: 0 24px 24px;
}

.empty-player {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  background-color: #fafafa;
}

.audio-player {
  padding: 16px 0;
}

.waveform {
  margin-bottom: 16px;
  border-radius: 4px;
  overflow: hidden;
}

.audio-controls {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.audio-controls button:first-child {
  margin-right: 16px;
}

.audio-info {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
}

.audio-info p {
  margin-bottom: 8px;
}

.audio-info p:last-child {
  margin-bottom: 0;
}

.upload-box {
  display: flex;
  flex-direction: column;
}

.file-name {
  margin-top: 8px;
  font-size: 12px;
  color: #1890ff;
}
</style> 