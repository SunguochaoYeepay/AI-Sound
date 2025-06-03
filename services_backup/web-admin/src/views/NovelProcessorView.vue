<template>
  <div class="novel-processor">
    <page-header title="小说处理" subtitle="将小说文本转换为有声书" />
    
    <a-row :gutter="16">
      <a-col :span="16">
        <a-card title="上传小说">
          <a-form :model="formState" layout="vertical">
            <a-form-item label="选择小说文件" v-if="!fileInfo.name">
              <a-upload
                name="file"
                :multiple="false"
                :showUploadList="false"
                :customRequest="uploadNovel"
                :beforeUpload="beforeUpload"
                :disabled="processing"
              >
                <a-button :disabled="processing">
                  <upload-outlined /> 点击上传小说文件
                </a-button>
              </a-upload>
            </a-form-item>
            
            <div class="file-info" v-if="fileInfo.name">
              <a-alert
                :message="`当前小说: ${fileInfo.name} (${formatFileSize(fileInfo.size)})`"
                type="info"
                show-icon
                class="mb-16"
              />
              <a-button size="small" type="link" @click="resetForm">选择其他小说</a-button>
            </div>
            
            <a-divider orientation="left">语音设置</a-divider>
            
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="音色选择">
                  <a-select
                    v-model:value="formState.voiceId"
                    placeholder="选择音色"
                    :disabled="processing"
                    :options="availableVoices"
                    show-search
                    optionFilterProp="label"
                  >
                    <template v-if="availableVoices?.length === 0">
                      <a-select-option value="female_young">年轻女声</a-select-option>
                      <a-select-option value="female_mature">成熟女声</a-select-option>
                      <a-select-option value="male_young">年轻男声</a-select-option>
                      <a-select-option value="male_middle">中年男声</a-select-option>
                      <a-select-option value="male_elder">老年男声</a-select-option>
                    </template>
                  </a-select>
                </a-form-item>
              </a-col>
              
              <a-col :span="12">
                <a-form-item label="语音技术">
                  <a-radio-group v-model:value="formState.ttsEngine" :disabled="processing">
                    <a-radio value="standard">标准语音</a-radio>
                    <a-radio value="neural">神经网络语音</a-radio>
                  </a-radio-group>
                </a-form-item>
              </a-col>
            </a-row>
            
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="情感类型">
                  <a-select
                    v-model:value="formState.emotionType"
                    placeholder="选择情感类型"
                    :disabled="processing || !formState.enableEmotionDetection"
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
                    :disabled="processing || !formState.enableEmotionDetection"
                  />
                </a-form-item>
              </a-col>
              
              <a-col :span="8">
                <a-form-item label="情感检测">
                  <a-switch 
                    v-model:checked="formState.enableEmotionDetection"
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
            
            <a-divider orientation="left">高级设置</a-divider>
            
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="分章节处理">
                  <a-switch 
                    v-model:checked="formState.splitByChapter" 
                    :disabled="processing"
                  />
                </a-form-item>
              </a-col>
              
              <a-col :span="8">
                <a-form-item label="自动合并音频">
                  <a-switch 
                    v-model:checked="formState.mergeAudio" 
                    :disabled="processing"
                  />
                </a-form-item>
              </a-col>
              
              <a-col :span="8">
                <a-form-item label="使用角色声音映射">
                  <a-switch 
                    v-model:checked="formState.useCharacterVoiceMapping" 
                    :disabled="processing"
                  />
                  <a-button 
                    type="link" 
                    size="small" 
                    v-if="formState.useCharacterVoiceMapping"
                    @click="showCharacterMappings"
                  >
                    查看映射
                  </a-button>
                </a-form-item>
              </a-col>
            </a-row>
            
            <a-form-item>
              <a-space>
                <a-button 
                  type="primary" 
                  @click="processNovel" 
                  :loading="processing"
                  :disabled="!fileInfo.name"
                >
                  处理小说
                </a-button>
                <a-button @click="resetForm" :disabled="processing">重置</a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>
      
      <a-col :span="8">
        <a-card title="处理进度">
          <div v-if="!taskId" class="empty-status">
            <read-outlined :style="{ fontSize: '64px', color: '#d9d9d9' }" />
            <p>提交任务后将在此处显示进度</p>
          </div>
          
          <div v-else class="task-status">
            <div class="task-header">
              <div class="task-title">任务ID: {{ taskId }}</div>
              <a-tag :color="getStatusColor(taskStatus)">{{ getStatusText(taskStatus) }}</a-tag>
            </div>
            
            <a-progress 
              :percent="taskProgress" 
              :status="taskStatus === 'failed' ? 'exception' : taskStatus === 'completed' ? 'success' : 'active'"
            />
            
            <div class="task-info">
              <p><strong>小说名称:</strong> {{ fileInfo.name }}</p>
              <p><strong>总章节数:</strong> {{ taskDetails.total_chapters || 0 }}</p>
              <p><strong>已处理章节:</strong> {{ taskDetails.processed_chapters || 0 }}</p>
              <p><strong>预计剩余时间:</strong> {{ formatTime(taskDetails.estimated_time_remaining) }}</p>
            </div>
            
            <div class="task-actions" v-if="taskStatus === 'completed'">
              <a-button type="primary" @click="downloadResults">
                <download-outlined /> 下载所有文件
              </a-button>
            </div>
          </div>
        </a-card>
        
        <!-- 角色映射卡片 -->
        <a-card title="角色声音映射" class="mt-16" v-if="formState.useCharacterVoiceMapping">
          <div v-if="characterVoiceMappings?.length === 0" class="empty-mappings">
            <p>暂无角色声音映射</p>
            <a-button type="link" @click="goToCharacterMapper">前往设置角色声音映射</a-button>
          </div>
          
          <div v-else>
            <a-list size="small">
              <a-list-item v-for="character in characterVoiceMappings" :key="character.name">
                <a-list-item-meta :title="character.name">
                  <template #description>
                    <a-tag color="blue">{{ character.voice_name }}</a-tag>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </a-list>
            <a-button type="link" @click="goToCharacterMapper" class="mt-16">
              管理角色声音映射
            </a-button>
          </div>
        </a-card>
      </a-col>
    </a-row>
    
    <!-- 角色映射对话框 -->
    <a-modal
      v-model:visible="mappingModalVisible"
      title="角色声音映射"
      :footer="null"
      width="600px"
    >
      <a-empty v-if="characterVoiceMappings?.length === 0" description="暂无角色声音映射">
        <template #description>
          <div>
            <p>没有找到角色声音映射</p>
            <p>请先在"角色声音映射"页面配置角色与声音的对应关系</p>
          </div>
        </template>
        <a-button type="primary" @click="goToCharacterMapper">
          前往配置
        </a-button>
      </a-empty>
      
      <div v-else>
        <a-table
          :columns="mappingColumns"
          :dataSource="characterVoiceMappings"
          :pagination="false"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'voice'">
              <a-tag color="blue">{{ record.voice_name }}</a-tag>
            </template>
            
            <template v-if="column.key === 'attributes'">
              <a-tag v-for="attr in record.attributes" :key="attr">{{ attr }}</a-tag>
            </template>
          </template>
        </a-table>
        
        <div style="margin-top: 16px; text-align: right;">
          <a-button type="primary" @click="goToCharacterMapper">
            管理映射
          </a-button>
          <a-button @click="mappingModalVisible = false" style="margin-left: 8px">
            关闭
          </a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import { ttsAPI } from '../services/api';
import { useRoute, useRouter } from 'vue-router';
import PageHeader from '@/components/common/PageHeader.vue';
import { 
  UploadOutlined,
  FileTextOutlined,
  ReadOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue';

export default defineComponent({
  name: 'NovelProcessorView',
  components: {
    PageHeader,
    UploadOutlined,
    FileTextOutlined,
    ReadOutlined,
    DownloadOutlined
  },
  setup() {
    // 移除 apiStore 引用
    const route = useRoute();
    const router = useRouter();
    
    // 表单状态
    const formState = reactive({
      voiceId: 'female_young',
      ttsEngine: 'neural',
      emotionType: 'neutral',
      emotionIntensity: 0.5,
      speedScale: 1.0,
      pitchScale: 1.0,
      splitByChapter: true,
      mergeAudio: true,
      useCharacterVoiceMapping: true,
      enableEmotionDetection: true
    });
    
    // 上传文件信息
    const fileInfo = reactive({
      id: '',
      name: '',
      size: 0,
      path: ''
    });
    
    // 角色声音映射
    const characterVoiceMappings = ref([]);
    const availableVoices = ref([]);
    const mappingModalVisible = ref(false);
    
    // 映射表格列定义
    const mappingColumns = [
      {
        title: '角色名称',
        dataIndex: 'name',
        key: 'name',
      },
      {
        title: '声音',
        dataIndex: 'voice_name',
        key: 'voice',
      },
      {
        title: '属性',
        dataIndex: 'attributes',
        key: 'attributes',
      }
    ];
    
    // 任务状态
    const processing = ref(false);
    const taskId = ref('');
    const taskStatus = ref('pending');
    const taskProgress = ref(0);
    const taskDetails = reactive({
      total_chapters: 0,
      processed_chapters: 0,
      estimated_time_remaining: 0
    });
    
    // 初始化时从URL加载小说ID
    onMounted(async () => {
      // 获取可用的声音列表
      loadAvailableVoices();
      
      // 检查URL中是否包含小说ID
      const novelId = route.query.id;
      if (novelId) {
        await loadNovelInfo(novelId);
      }
    });
    
    // 监听路由变化
    watch(() => route.query.id, async (newId, oldId) => {
      if (newId && newId !== oldId) {
        await loadNovelInfo(newId);
      }
    });
    
    // 加载可用的声音列表
    const loadAvailableVoices = async () => {
      try {
        const voices = await apiStore.getNovels();
        if (voices && Array.isArray(voices)) {
          availableVoices.value = voices?.map(voice => ({
            value: voice.id,
            label: voice.name,
            gender: voice.attributes?.gender,
            age: voice.attributes?.age_group
          }));
        }
      } catch (error) {
        console.error('获取声音列表失败', error);
      }
    };
    
    // 加载小说信息
    const loadNovelInfo = async (novelId) => {
      try {
        const novelInfo = await apiStore.getNovelDetails(novelId);
        if (novelInfo) {
          // 填充文件信息
          fileInfo.id = novelId;
          fileInfo.name = novelInfo.name;
          fileInfo.size = novelInfo.size;
          fileInfo.path = novelInfo.path;
          
          // 如果有配置信息，应用配置
          if (novelInfo.config) {
            formState.voiceId = novelInfo.config.defaultVoice || 'female_young';
            formState.splitByChapter = novelInfo.config.splitByChapter !== false;
            formState.useCharacterVoiceMapping = novelInfo.config.useVoiceMapping !== false;
            formState.enableEmotionDetection = novelInfo.config.detectEmotion !== false;
          }
          
          // 加载角色声音映射
          loadCharacterMappings();
          
          message.success(`已加载小说: ${novelInfo.name}`);
        }
      } catch (error) {
        message.error(`加载小说信息失败: ${error.message || '未知错误'}`);
      }
    };
    
    // 加载角色声音映射
    const loadCharacterMappings = async () => {
      try {
        const response = await apiStore.getCharacterMappings();
        if (response && Array.isArray(response)) {
          characterVoiceMappings.value = response;
        }
      } catch (error) {
        console.error('获取角色声音映射失败', error);
      }
    };
    
    // 显示角色映射对话框
    const showCharacterMappings = () => {
      mappingModalVisible.value = true;
    };
    
    // 跳转到角色映射页面
    const goToCharacterMapper = () => {
      router.push('/character-mapper');
    };
    
    // 上传前检查
    const beforeUpload = (file) => {
      const isText = file.type === 'text/plain' || 
                     file.name.endsWith('.txt') || 
                     file.name.endsWith('.md');
      
      if (!isText) {
        message.error('只能上传TXT或MD文件!');
        return false;
      }
      
      if (file.size / 1024 / 1024 > 10) {
        message.error('文件大小不能超过10MB!');
        return false;
      }
      
      return true;
    };
    
    // 上传小说
    const uploadNovel = async ({ file }) => {
      processing.value = true;
      try {
        const result = await apiStore.uploadNovel(file);
        if (result && result.success) {
          message.success('文件上传成功');
          fileInfo.id = result.id || '';
          fileInfo.name = file.name;
          fileInfo.size = file.size;
          fileInfo.path = result.file_path;
        } else {
          message.error(result?.message || '文件上传失败');
        }
      } catch (error) {
        message.error('文件上传失败: ' + (error.message || '未知错误'));
        console.error('上传错误', error);
      } finally {
        processing.value = false;
      }
    };
    
    // 处理小说
    const processNovel = async () => {
      if (!fileInfo.path && !fileInfo.id) {
        message.warning('请先上传小说文件或从列表选择小说');
        return;
      }
      
      processing.value = true;
      try {
        // 准备处理参数
        const params = {
          novel_id: fileInfo.id,
          novel_path: fileInfo.path,
          voice_id: formState.voiceId,
          tts_engine: formState.ttsEngine,
          emotion_type: formState.emotionType,
          emotion_intensity: formState.emotionIntensity,
          speed_scale: formState.speedScale,
          pitch_scale: formState.pitchScale,
          split_by_chapter: formState.splitByChapter,
          merge_audio: formState.mergeAudio,
          use_character_mapping: formState.useCharacterVoiceMapping,
          enable_emotion_detection: formState.enableEmotionDetection
        };
        
        const result = await apiStore.processNovel(fileInfo.path || fileInfo.id, params);
        
        if (result && result.task_id) {
          message.success('任务提交成功');
          taskId.value = result.task_id;
          taskStatus.value = 'pending';
          taskProgress.value = 0;
          
          // 启动任务状态轮询
          pollTaskStatus();
        } else {
          message.error(result?.message || '任务提交失败');
        }
      } catch (error) {
        message.error('任务提交失败: ' + (error.message || '未知错误'));
        console.error('处理错误', error);
      } finally {
        processing.value = false;
      }
    };
    
    // 轮询任务状态
    const pollTaskStatus = async () => {
      if (!taskId.value) return;
      
      try {
        const result = await apiStore.getTaskDetails(taskId.value);
        if (result) {
          taskStatus.value = result.status;
          taskProgress.value = result.progress || 0;
          
          if (result.details) {
            taskDetails.total_chapters = result.details.total_chapters || 0;
            taskDetails.processed_chapters = result.details.processed_chapters || 0;
            taskDetails.estimated_time_remaining = result.details.estimated_time_remaining || 0;
          }
          
          if (taskStatus.value === 'processing' || taskStatus.value === 'pending') {
            setTimeout(pollTaskStatus, 3000);
          } else if (taskStatus.value === 'completed') {
            message.success('小说处理完成');
          } else if (taskStatus.value === 'failed') {
            message.error(result.message || '小说处理失败');
          }
        }
      } catch (error) {
        console.error('获取任务状态失败', error);
        setTimeout(pollTaskStatus, 5000);
      }
    };
    
    // 下载结果
    const downloadResults = () => {
      if (!taskId.value) return;
      
      // 下载生成的音频文件
      window.open(`${apiStore.baseUrl}/api/download/${taskId.value}`, '_blank');
    };
    
    // 重置表单
    const resetForm = () => {
      formState.voiceId = 'female_young';
      formState.ttsEngine = 'neural';
      formState.emotionType = 'neutral';
      formState.emotionIntensity = 0.5;
      formState.speedScale = 1.0;
      formState.pitchScale = 1.0;
      formState.splitByChapter = true;
      formState.mergeAudio = true;
      formState.useCharacterVoiceMapping = true;
      formState.enableEmotionDetection = true;
      
      fileInfo.id = '';
      fileInfo.name = '';
      fileInfo.size = 0;
      fileInfo.path = '';
      
      taskId.value = '';
      taskStatus.value = 'pending';
      taskProgress.value = 0;
    };
    
    // 格式化文件大小
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 B';
      
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    // 格式化时间
    const formatTime = (seconds) => {
      if (!seconds || seconds <= 0) return '0秒';
      
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const remainingSeconds = Math.floor(seconds % 60);
      
      let result = '';
      if (hours > 0) result += `${hours}小时`;
      if (minutes > 0) result += `${minutes}分钟`;
      if (remainingSeconds > 0) result += `${remainingSeconds}秒`;
      
      return result;
    };
    
    // 获取状态颜色
    const getStatusColor = (status) => {
      const colors = {
        'pending': 'blue',
        'processing': 'orange',
        'completed': 'green',
        'failed': 'red'
      };
      return colors[status] || 'default';
    };
    
    // 获取状态文本
    const getStatusText = (status) => {
      const texts = {
        'pending': '等待中',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败'
      };
      return texts[status] || status;
    };
    
    return {
      formState,
      fileInfo,
      processing,
      taskId,
      taskStatus,
      taskProgress,
      taskDetails,
      availableVoices,
      characterVoiceMappings,
      mappingModalVisible,
      mappingColumns,
      uploadNovel,
      processNovel,
      resetForm,
      beforeUpload,
      downloadResults,
      formatFileSize,
      formatTime,
      getStatusColor,
      getStatusText,
      showCharacterMappings,
      goToCharacterMapper
    };
  }
});
</script>

<style scoped>
.novel-processor {
  padding: 0 24px 24px;
}

.file-info {
  margin-top: 8px;
}

.empty-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  background-color: #fafafa;
}

.task-status {
  padding: 16px 0;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.task-title {
  font-weight: 500;
}

.task-info {
  margin-top: 24px;
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
}

.task-info p {
  margin-bottom: 8px;
}

.task-actions {
  margin-top: 24px;
  text-align: center;
}

.empty-mappings {
  text-align: center;
  padding: 20px 0;
}

.mb-16 {
  margin-bottom: 16px;
}

.mt-16 {
  margin-top: 16px;
}
</style> 