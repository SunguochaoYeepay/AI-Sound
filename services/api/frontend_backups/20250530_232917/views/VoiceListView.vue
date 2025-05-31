<template>
  <div class="voice-list-container">
    <a-page-header
      title="声音库"
      sub-title="管理所有声纹特征和音色"
    >
      <template #extra>
        <a-button type="primary" @click="goToVoiceFeature">
          <template #icon><plus-outlined /></template>
          添加声音
        </a-button>
      </template>
    </a-page-header>
    
    <a-row :gutter="16" class="filter-row">
      <a-col :span="8">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索声音名称或标签"
          @search="onSearch"
          allow-clear
          enter-button
        />
      </a-col>
      <a-col :span="6">
        <a-select
          v-model:value="genderFilter"
          placeholder="性别筛选"
          style="width: 100%"
          allow-clear
          @change="onFilterChange"
        >
          <a-select-option value="male">男性</a-select-option>
          <a-select-option value="female">女性</a-select-option>
          <a-select-option value="other">其他</a-select-option>
        </a-select>
      </a-col>
      <a-col :span="6">
        <a-select
          v-model:value="ageFilter"
          placeholder="年龄段筛选"
          style="width: 100%"
          allow-clear
          @change="onFilterChange"
        >
          <a-select-option value="child">儿童</a-select-option>
          <a-select-option value="young">青年</a-select-option>
          <a-select-option value="middle">中年</a-select-option>
          <a-select-option value="old">老年</a-select-option>
        </a-select>
      </a-col>
      <a-col :span="4">
        <a-select
          v-model:value="tagFilter"
          placeholder="标签筛选"
          style="width: 100%"
          allow-clear
          @change="onFilterChange"
        >
          <a-select-option v-for="tag in tagOptions" :key="tag.value" :value="tag.value">
            {{ tag.label }}
          </a-select-option>
        </a-select>
      </a-col>
    </a-row>
    
    <a-row>
      <a-col :span="24">
        <a-spin :spinning="loading">
          <a-empty v-if="filteredVoiceList.length === 0 && !loading" description="暂无声音数据" />
          
          <a-row :gutter="[16, 16]" v-else>
            <a-col :xs="24" :sm="12" :md="8" :lg="6" v-for="voice in filteredVoiceList" :key="voice.id">
              <a-card hoverable class="voice-card">
                <template #cover>
                  <div class="voice-card-cover">
                    <sound-outlined class="voice-icon" />
                  </div>
                </template>
                <template #title>
                  <div class="voice-card-title">
                    {{ voice.name }}
                    <a-tag color="blue" v-if="voice.gender === 'male'">男性</a-tag>
                    <a-tag color="magenta" v-else-if="voice.gender === 'female'">女性</a-tag>
                  </div>
                </template>
                <template #extra>
                  <a-dropdown>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item key="edit" @click="editVoice(voice)">
                          <edit-outlined /> 编辑
                        </a-menu-item>
                        <a-menu-item key="preview" @click="previewVoice(voice)">
                          <sound-outlined /> 试听
                        </a-menu-item>
                        <a-menu-item key="delete" @click="confirmDeleteVoice(voice)">
                          <delete-outlined /> 删除
                        </a-menu-item>
                      </a-menu>
                    </template>
                    <a-button type="text">
                      <more-outlined />
                    </a-button>
                  </a-dropdown>
                </template>
                
                <div class="voice-tags">
                  <a-tag v-for="tag in voice.tags" :key="tag">{{ tag }}</a-tag>
                </div>
                
                <div class="voice-description">
                  {{ voice.description || '暂无描述' }}
                </div>
                
                <div class="voice-controls">
                  <a-button type="primary" size="small" @click="previewVoice(voice)">
                    <template #icon><sound-outlined /></template>
                    试听
                  </a-button>
                  <a-button size="small" @click="useVoice(voice)">
                    <template #icon><select-outlined /></template>
                    使用
                  </a-button>
                </div>
              </a-card>
            </a-col>
          </a-row>
        </a-spin>
      </a-col>
    </a-row>
    
    <!-- 预览声音对话框 -->
    <a-modal
      v-model:open="previewModalVisible"
      title="声音预览"
      :footer="null"
      @cancel="stopPreviewAudio"
    >
      <div v-if="selectedVoice">
        <h3>{{ selectedVoice.name }}</h3>
        <p>{{ selectedVoice.description || '暂无描述' }}</p>
        
        <div class="preview-audio-player">
          <div id="waveform" ref="waveformRef"></div>
          <div class="audio-controls">
            <a-button 
              :disabled="!previewAudioLoaded"
              @click="togglePreviewAudio"
              type="primary"
              shape="circle"
            >
              <template #icon>
                <pause-outlined v-if="isPlaying" />
                <caret-right-outlined v-else />
              </template>
            </a-button>
          </div>
        </div>
        
        <a-divider />
        
        <div class="preview-text-input">
          <a-textarea
            v-model:value="previewText"
            placeholder="输入文本进行试听"
            :rows="3"
          />
          <a-button 
            type="primary" 
            :loading="generatingPreview" 
            @click="generatePreview"
            style="margin-top: 16px"
          >
            生成预览
          </a-button>
        </div>
      </div>
    </a-modal>
    
    <!-- 编辑声音对话框 -->
    <a-modal
      v-model:open="editModalVisible"
      title="编辑声音信息"
      @ok="updateVoice"
      :confirm-loading="updating"
      okText="保存"
      cancelText="取消"
    >
      <a-form :model="editForm" layout="vertical">
        <a-form-item label="声音名称" name="name" :rules="[{ required: true, message: '请输入声音名称' }]">
          <a-input v-model:value="editForm.name" placeholder="声音名称" allow-clear />
        </a-form-item>
        
        <a-form-item label="性别" name="gender">
          <a-select v-model:value="editForm.gender" placeholder="选择性别" allow-clear>
            <a-select-option value="male">男性</a-select-option>
            <a-select-option value="female">女性</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="年龄段" name="age_group">
          <a-select v-model:value="editForm.age_group" placeholder="选择年龄段" allow-clear>
            <a-select-option value="child">儿童</a-select-option>
            <a-select-option value="young">青年</a-select-option>
            <a-select-option value="middle">中年</a-select-option>
            <a-select-option value="old">老年</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="标签" name="tags">
          <a-select v-model:value="editForm.tags" mode="tags" placeholder="添加标签" :options="tagOptions" allow-clear />
        </a-form-item>
        
        <a-form-item label="声音描述" name="description">
          <a-textarea v-model:value="editForm.description" placeholder="描述这个声音的特点" :rows="4" allow-clear />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import { voiceAPI, ttsAPI } from '../services/api';
import WaveSurfer from 'wavesurfer.js';
import { 
  PlusOutlined,
  SoundOutlined,
  EditOutlined,
  DeleteOutlined,
  MoreOutlined,
  CaretRightOutlined,
  PauseOutlined,
  SelectOutlined
} from '@ant-design/icons-vue';

export default defineComponent({
  name: 'VoiceListView',
  components: {
    PlusOutlined,
    SoundOutlined,
    EditOutlined,
    DeleteOutlined,
    MoreOutlined,
    CaretRightOutlined,
    PauseOutlined,
    SelectOutlined
  },
  setup() {
    const router = useRouter();
    const loading = ref(true);
    const voiceList = ref([]);
    
    // 筛选参数
    const searchKeyword = ref('');
    const genderFilter = ref(undefined);
    const ageFilter = ref(undefined);
    const tagFilter = ref(undefined);
    
    // 预览相关
    const previewModalVisible = ref(false);
    const selectedVoice = ref(null);
    const previewText = ref('这是一段用于测试声音的文本，可以听听效果如何？');
    const waveformRef = ref(null);
    const waveSurfer = ref(null);
    const isPlaying = ref(false);
    const previewAudioLoaded = ref(false);
    const generatingPreview = ref(false);
    
    // 编辑相关
    const editModalVisible = ref(false);
    const updating = ref(false);
    const editForm = reactive({
      id: '',
      name: '',
      gender: undefined,
      age_group: undefined,
      tags: [],
      description: ''
    });
    
    // Base64转Blob工具函数
    const base64ToBlob = (base64, mimeType) => {
      const byteCharacters = atob(base64);
      const byteArrays = [];
      
      for (let offset = 0; offset < byteCharacters.length; offset += 512) {
        const slice = byteCharacters.slice(offset, offset + 512);
        
        const byteNumbers = new Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
          byteNumbers[i] = slice.charCodeAt(i);
        }
        
        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
      }
      
      return new Blob(byteArrays, { type: mimeType });
    };
    
    // 标签选项
    const tagOptions = [
      { value: 'male', label: '男性' },
      { value: 'female', label: '女性' },
      { value: 'young', label: '年轻' },
      { value: 'mature', label: '成熟' },
      { value: 'clear', label: '清晰' },
      { value: 'deep', label: '低沉' },
      { value: 'soft', label: '柔和' },
      { value: 'energetic', label: '有活力' }
    ];
    
    // 筛选后的声音列表
    const filteredVoiceList = computed(() => {
      return voiceList.value.filter(voice => {
        // 关键词筛选
        if (searchKeyword.value && !voice.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) && 
            !voice.tags.some(tag => tag.toLowerCase().includes(searchKeyword.value.toLowerCase()))) {
          return false;
        }
        
        // 性别筛选
        if (genderFilter.value && voice.gender !== genderFilter.value) {
          return false;
        }
        
        // 年龄段筛选
        if (ageFilter.value && voice.age_group !== ageFilter.value) {
          return false;
        }
        
        // 标签筛选
        if (tagFilter.value && !voice.tags.includes(tagFilter.value)) {
          return false;
        }
        
        return true;
      });
    });
    
    // 加载声音列表
    const fetchVoiceList = async () => {
      loading.value = true;
      try {
        const response = await voiceAPI.getVoices();
        // axios拦截器已经处理了API响应格式，response.data已经是{ voices: [...] }
        const voices = response.voices || [];
        
        // 为每个voice对象添加缺失字段的默认值
        voiceList.value = voices.map(voice => ({
          ...voice,
          tags: voice.tags || [],
          age_group: voice.age_group || 'unknown'
        }));
      } catch (error) {
        console.error('获取声音列表失败:', error);
        message.error('获取声音列表失败: ' + (error.response?.data?.message || error.message));
      } finally {
        loading.value = false;
      }
    };
    
    // 搜索处理
    const onSearch = (value) => {
      searchKeyword.value = value;
    };
    
    // 筛选变化处理
    const onFilterChange = () => {
      // 筛选条件变化时自动应用筛选
    };
    
    // 预览声音
    const previewVoice = async (voice) => {
      selectedVoice.value = voice;
      previewModalVisible.value = true;
      previewAudioLoaded.value = false;
      
      // 在下一个 tick 中初始化 WaveSurfer
      await nextTick();
      
      // 创建波形图
      if (waveSurfer.value) {
        waveSurfer.value.destroy();
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
        previewAudioLoaded.value = true;
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
      
      try {
        // 加载预览音频
        const response = await voiceAPI.previewVoice(voice.id, '这是一段用于测试声音的文本');
        if (response && response.audio_url) {
          waveSurfer.value.load(response.audio_url);
        } else if (response && response.audio_base64) {
          const blob = base64ToBlob(response.audio_base64, 'audio/wav');
          const audioUrl = URL.createObjectURL(blob);
          waveSurfer.value.load(audioUrl);
        } else {
          message.warning('没有可用的预览音频');
        }
      } catch (error) {
        console.error('获取预览音频失败:', error);
        message.error('获取预览音频失败: ' + (error.response?.data?.message || error.message));
      }
    };
    
    // 播放/暂停预览音频
    const togglePreviewAudio = () => {
      if (waveSurfer.value) {
        waveSurfer.value.playPause();
      }
    };
    
    // 停止预览音频
    const stopPreviewAudio = () => {
      if (waveSurfer.value && isPlaying.value) {
        waveSurfer.value.pause();
      }
    };
    
    // 生成预览音频
    const generatePreview = async () => {
      if (!selectedVoice.value || !previewText.value.trim()) {
        message.warning('请输入要试听的文本');
        return;
      }
      
      generatingPreview.value = true;
      
      try {
        // 调用API生成预览音频
        const response = await ttsAPI.synthesize({
          text: previewText.value,
          voice_id: selectedVoice.value.id,
          format: 'wav',
          return_base64: true
        });
        
        if (response && response.audio_base64) {
          const blob = base64ToBlob(response.audio_base64, 'audio/wav');
          const audioUrl = URL.createObjectURL(blob);
          
          // 重置并加载新音频
          if (waveSurfer.value) {
            waveSurfer.value.pause();
            waveSurfer.value.load(audioUrl);
            waveSurfer.value.on('ready', () => {
              waveSurfer.value.play();
            });
          }
        } else {
          message.warning('生成的音频无法播放');
        }
      } catch (error) {
        console.error('生成预览音频失败:', error);
        message.error('生成预览音频失败: ' + (error.response?.data?.message || error.message));
      } finally {
        generatingPreview.value = false;
      }
    };
    
    // 编辑声音
    const editVoice = (voice) => {
      editForm.id = voice.id;
      editForm.name = voice.name;
      editForm.gender = voice.gender;
      editForm.age_group = voice.age_group;
      editForm.tags = [...voice.tags];
      editForm.description = voice.description;
      
      editModalVisible.value = true;
    };
    
    // 更新声音信息
    const updateVoice = async () => {
      if (!editForm.name.trim()) {
        message.warning('声音名称不能为空');
        return;
      }
      
      updating.value = true;
      
      try {
        // 调用API更新声音信息
        const response = await voiceAPI.updateVoice(editForm.id, {
          name: editForm.name,
          gender: editForm.gender,
          age_group: editForm.age_group,
          tags: editForm.tags,
          description: editForm.description
        });
        
        message.success('声音信息更新成功');
        editModalVisible.value = false;
        
        // 更新本地列表
        const index = voiceList.value.findIndex(voice => voice.id === editForm.id);
        if (index !== -1) {
          voiceList.value[index] = {
            ...voiceList.value[index],
            name: editForm.name,
            gender: editForm.gender,
            age_group: editForm.age_group,
            tags: [...editForm.tags],
            description: editForm.description
          };
        }
      } catch (error) {
        console.error('更新声音信息失败:', error);
        message.error('更新声音信息失败: ' + (error.response?.data?.message || error.message));
      } finally {
        updating.value = false;
      }
    };
    
    // 确认删除声音
    const confirmDeleteVoice = (voice) => {
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除声音"${voice.name}"吗？此操作不可恢复。`,
        okText: '删除',
        okType: 'danger',
        cancelText: '取消',
        async onOk() {
          try {
            // 调用API删除声音
            await voiceAPI.deleteVoice(voice.id);
            message.success('声音已删除');
            
            // 从列表中移除
            voiceList.value = voiceList.value.filter(item => item.id !== voice.id);
          } catch (error) {
            console.error('删除声音失败:', error);
            message.error('删除声音失败: ' + (error.response?.data?.message || error.message));
          }
        }
      });
    };
    
    // 使用声音
    const useVoice = (voice) => {
      // 导航到文本转语音页面并传递声音ID
      router.push({
        path: '/tts',
        query: { voice_id: voice.id }
      });
    };
    
    // 前往声音上传页面
    const goToVoiceFeature = () => {
      router.push('/voice-upload');
    };
    
    // 页面加载时获取声音列表
    onMounted(() => {
      fetchVoiceList();
    });
    
    // 组件卸载时清理资源
    onUnmounted(() => {
      if (waveSurfer.value) {
        waveSurfer.value.destroy();
      }
    });
    
    return {
      loading,
      voiceList,
      filteredVoiceList,
      searchKeyword,
      genderFilter,
      ageFilter,
      tagFilter,
      tagOptions,
      onSearch,
      onFilterChange,
      previewVoice,
      editVoice,
      confirmDeleteVoice,
      useVoice,
      goToVoiceFeature,
      
      // 预览相关
      previewModalVisible,
      selectedVoice,
      previewText,
      waveformRef,
      isPlaying,
      previewAudioLoaded,
      generatingPreview,
      togglePreviewAudio,
      stopPreviewAudio,
      generatePreview,
      
      // 编辑相关
      editModalVisible,
      editForm,
      updating,
      updateVoice
    };
  }
});
</script>

<style scoped>
.voice-list-container {
  max-width: 100%;
}

.filter-row {
  margin-bottom: 24px;
}

.voice-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.voice-card-cover {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
}

.voice-icon {
  font-size: 48px;
  color: white;
}

.voice-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.voice-tags {
  margin: 8px 0;
  min-height: 22px;
}

.voice-description {
  margin-bottom: 16px;
  flex-grow: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  color: rgba(0, 0, 0, 0.45);
  font-size: 14px;
}

.voice-controls {
  display: flex;
  gap: 8px;
  justify-content: flex-start;
}

.preview-audio-player {
  margin: 16px 0;
}

.audio-controls {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.preview-text-input {
  margin-top: 16px;
}
</style> 