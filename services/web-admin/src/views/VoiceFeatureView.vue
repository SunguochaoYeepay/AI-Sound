<template>
  <div class="voice-feature-container">
    <a-page-header
      title="声纹特征提取"
      sub-title="上传音频提取声纹特征，用于自定义音色合成"
    />
    
    <a-row :gutter="24">
      <a-col :span="16">
        <a-card title="声纹特征提取" class="extract-card">
          <a-upload-dragger
            name="voice_file"
            :multiple="false"
            action="/api/voices/extract"
            :headers="uploadHeaders"
            :before-upload="beforeUpload"
            :custom-request="customUploadRequest"
            @change="handleUploadChange"
            accept=".wav,.mp3,.flac"
          >
            <p class="ant-upload-drag-icon">
              <inbox-outlined />
            </p>
            <p class="ant-upload-text">点击或拖拽音频文件到此区域</p>
            <p class="ant-upload-hint">
              支持WAV、MP3、FLAC格式，建议5-10秒高质量录音<br>
              上传的音频将用于提取声纹特征，以便生成相似的语音
            </p>
          </a-upload-dragger>
          
          <a-divider />
          
          <a-form
            :model="formState"
            name="voiceFeatureForm"
            layout="vertical"
            :disabled="uploadStatus === 'uploading'"
          >
            <a-form-item
              label="声音名称"
              name="name"
              :rules="[{ required: true, message: '请输入声音名称' }]"
            >
              <a-input 
                v-model:value="formState.name" 
                placeholder="给这个声音起个名字"
                allow-clear
              />
            </a-form-item>
            
            <a-form-item
              label="声音标签"
              name="tags"
            >
              <a-select
                v-model:value="formState.tags"
                mode="tags"
                placeholder="添加标签"
                :options="tagOptions"
                allow-clear
              />
            </a-form-item>
            
            <a-form-item
              label="性别"
              name="gender"
            >
              <a-select
                v-model:value="formState.gender"
                placeholder="选择性别"
                allow-clear
              >
                <a-select-option value="male">男性</a-select-option>
                <a-select-option value="female">女性</a-select-option>
                <a-select-option value="other">其他</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item
              label="年龄段"
              name="age_group"
            >
              <a-select
                v-model:value="formState.age_group"
                placeholder="选择年龄段"
                allow-clear
              >
                <a-select-option value="child">儿童</a-select-option>
                <a-select-option value="young">青年</a-select-option>
                <a-select-option value="middle">中年</a-select-option>
                <a-select-option value="old">老年</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item
              label="声音描述"
              name="description"
            >
              <a-textarea
                v-model:value="formState.description"
                placeholder="描述这个声音的特点"
                :rows="4"
                allow-clear
              />
            </a-form-item>
            
            <a-form-item>
              <a-button
                type="primary"
                :loading="uploadStatus === 'uploading'"
                :disabled="!audioFile"
                @click="submitForm"
                block
              >
                <template #icon><cloud-upload-outlined /></template>
                提取声纹特征
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>
      
      <a-col :span="8">
        <a-card title="提取说明" class="help-card">
          <p><strong>什么是声纹特征？</strong></p>
          <p>声纹特征是从音频中提取的用于表示说话者独特声音特点的数据。AI-Sound可以使用这些特征生成与原始声音相似的语音。</p>
          
          <a-divider />
          
          <p><strong>如何获得好的声纹特征？</strong></p>
          <ul>
            <li>选择5-10秒的高质量录音，避免背景噪音</li>
            <li>使用清晰的语音，避免太多情感起伏</li>
            <li>尽量使用标准普通话，避免方言</li>
            <li>确保音频采样率至少为16kHz</li>
          </ul>
          
          <a-divider />
          
          <p><strong>提取后如何使用？</strong></p>
          <p>提取完成后，您可以在"声音库"中找到这个声音，并将其分配给小说角色，或直接在文本转语音中使用。</p>
        </a-card>
        
        <a-card title="提取进度" class="progress-card" v-if="uploadStatus !== 'idle'">
          <div v-if="uploadStatus === 'uploading'">
            <a-progress :percent="uploadProgress" status="active" />
            <p>正在上传音频文件...</p>
          </div>
          
          <div v-else-if="uploadStatus === 'extracting'">
            <a-progress :percent="100" status="active" />
            <p>正在提取声纹特征，这可能需要几秒钟...</p>
          </div>
          
          <div v-else-if="uploadStatus === 'success'">
            <a-result
              status="success"
              title="声纹特征提取成功！"
              sub-title="您的声音已添加到声音库"
            >
              <template #extra>
                <a-button type="primary" @click="goToVoiceList">
                  查看声音库
                </a-button>
                <a-button @click="resetForm">
                  继续添加
                </a-button>
              </template>
            </a-result>
          </div>
          
          <div v-else-if="uploadStatus === 'error'">
            <a-result
              status="error"
              title="提取失败"
              :sub-title="errorMessage"
            >
              <template #extra>
                <a-button type="primary" @click="resetForm">
                  重试
                </a-button>
              </template>
            </a-result>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script>
import { defineComponent, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import axios from '../plugins/axios';
import { 
  InboxOutlined,
  CloudUploadOutlined
} from '@ant-design/icons-vue';

export default defineComponent({
  name: 'VoiceFeatureView',
  components: {
    InboxOutlined,
    CloudUploadOutlined
  },
  setup() {
    const router = useRouter();
    const formState = reactive({
      name: '',
      tags: [],
      gender: undefined,
      age_group: undefined,
      description: ''
    });
    
    const audioFile = ref(null);
    const uploadStatus = ref('idle'); // idle, uploading, extracting, success, error
    const uploadProgress = ref(0);
    const errorMessage = ref('');
    
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
    
    const uploadHeaders = {
      'Accept': 'application/json'
    };
    
    const beforeUpload = (file) => {
      // 验证文件类型
      const isAudio = file.type === 'audio/wav' || 
                     file.type === 'audio/mp3' || 
                     file.type === 'audio/mpeg' ||
                     file.type === 'audio/flac' ||
                     /\.(wav|mp3|flac)$/i.test(file.name);
                     
      if (!isAudio) {
        message.error('只能上传WAV、MP3或FLAC音频文件！');
        return false;
      }
      
      // 验证文件大小，限制为20MB
      const isLt20M = file.size / 1024 / 1024 < 20;
      if (!isLt20M) {
        message.error('音频文件大小不能超过20MB！');
        return false;
      }
      
      // 设置要上传的文件
      audioFile.value = file;
      
      // 阻止默认上传行为
      return false;
    };
    
    const customUploadRequest = async ({ file, onProgress, onSuccess, onError }) => {
      // 自定义上传，不在这里实际上传，在submitForm中上传
      // 这个函数只是为了防止默认上传行为
    };
    
    const handleUploadChange = (info) => {
      // 处理上传状态变化
      if (info.file.status === 'uploading') {
        uploadStatus.value = 'uploading';
      }
    };
    
    const submitForm = async () => {
      if (!audioFile.value) {
        message.warning('请先上传音频文件');
        return;
      }
      
      // 创建FormData对象
      const formData = new FormData();
      formData.append('voice_file', audioFile.value);
      
      // 添加表单数据
      if (formState.name) {
        formData.append('name', formState.name);
      }
      
      if (formState.tags && formState.tags.length > 0) {
        formData.append('tags', formState.tags.join(','));
      }
      
      if (formState.gender) {
        formData.append('gender', formState.gender);
      }
      
      if (formState.age_group) {
        formData.append('age_group', formState.age_group);
      }
      
      if (formState.description) {
        formData.append('description', formState.description);
      }
      
      // 开始上传
      uploadStatus.value = 'uploading';
      uploadProgress.value = 0;
      
      try {
        // 上传文件并提取声纹特征
        const response = await axios.post('/api/voices/extract', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            // 计算上传进度
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            uploadProgress.value = percentCompleted;
          }
        });
        
        // 上传完成后，服务器开始提取特征
        uploadStatus.value = 'extracting';
        
        // 检查响应
        if (response.data && response.data.success) {
          // 提取成功
          uploadStatus.value = 'success';
          message.success('声纹特征提取成功！');
        } else {
          // 提取失败
          uploadStatus.value = 'error';
          errorMessage.value = response.data.message || '未知错误';
          message.error('声纹特征提取失败: ' + errorMessage.value);
        }
      } catch (error) {
        // 处理错误
        uploadStatus.value = 'error';
        errorMessage.value = error.response?.data?.message || error.message || '未知错误';
        message.error('声纹特征提取失败: ' + errorMessage.value);
      }
    };
    
    const resetForm = () => {
      // 重置表单和上传状态
      formState.name = '';
      formState.tags = [];
      formState.gender = undefined;
      formState.age_group = undefined;
      formState.description = '';
      
      audioFile.value = null;
      uploadStatus.value = 'idle';
      uploadProgress.value = 0;
      errorMessage.value = '';
    };
    
    const goToVoiceList = () => {
      // 导航到声音库页面
      router.push('/voice-list');
    };
    
    return {
      formState,
      tagOptions,
      audioFile,
      uploadStatus,
      uploadProgress,
      errorMessage,
      uploadHeaders,
      beforeUpload,
      customUploadRequest,
      handleUploadChange,
      submitForm,
      resetForm,
      goToVoiceList
    };
  }
});
</script>

<style scoped>
.voice-feature-container {
  max-width: 100%;
}

.extract-card, .help-card, .progress-card {
  margin-bottom: 24px;
}

.help-card ul {
  padding-left: 20px;
}
</style> 