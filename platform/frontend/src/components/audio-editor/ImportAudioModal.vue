<template>
  <a-modal
    v-model:open="modalVisible"
    title="导入音频文件"
    width="600px"
    :confirm-loading="uploadLoading"
    @ok="handleImportConfirm"
    @cancel="handleCancel"
  >
    <div class="import-modal-content">
      <a-upload-dragger
        v-model:fileList="uploadFileList"
        name="file"
        multiple
        accept="audio/*"
        :before-upload="beforeUpload"
        @change="handleFileChange"
        @drop="handleFileDrop"
      >
        <p class="ant-upload-drag-icon">
          <SoundOutlined style="font-size: 48px; color: #1890ff;" />
        </p>
        <p class="ant-upload-text">点击或拖拽音频文件到此区域上传</p>
        <p class="ant-upload-hint">
          支持的格式: MP3, WAV, FLAC, AAC, OGG
        </p>
      </a-upload-dragger>
      
      <div v-if="uploadFileList.length > 0" style="margin-top: 16px;">
        <h4>即将导入的文件:</h4>
        <a-list
          :dataSource="uploadFileList"
          size="small"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta>
                <template #title>{{ item.name }}</template>
                <template #description>
                  大小: {{ formatFileSize(item.size) }}
                  <a-tag v-if="item.status === 'uploading'" color="processing">上传中</a-tag>
                  <a-tag v-else-if="item.status === 'done'" color="success">就绪</a-tag>
                  <a-tag v-else-if="item.status === 'error'" color="error">错误</a-tag>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </template>
        </a-list>
      </div>
    </div>
  </a-modal>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { SoundOutlined } from '@ant-design/icons-vue'
import api from '@/api'

export default {
  name: 'ImportAudioModal',
  components: {
    SoundOutlined
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:visible', 'import-success'],
  setup(props, { emit }) {
    // 响应式数据
    const modalVisible = computed({
      get: () => props.visible,
      set: (value) => emit('update:visible', value)
    })
    
    const uploadFileList = ref([])
    const uploadLoading = ref(false)
    
    // 文件上传前验证
    const beforeUpload = (file) => {
      const isAudio = file.type.startsWith('audio/')
      if (!isAudio) {
        message.error('只能上传音频文件!')
        return false
      }
      
      const isLt100M = file.size / 1024 / 1024 < 100
      if (!isLt100M) {
        message.error('音频文件大小不能超过100MB!')
        return false
      }
      
      return false
    }

    // 文件变化处理
    const handleFileChange = (info) => {
      // 文件变化处理逻辑
      console.log('文件变化:', info)
    }

    // 文件拖拽处理
    const handleFileDrop = (e) => {
      // 文件拖拽处理逻辑
      console.log('文件拖拽:', e)
    }

    // 确认导入
    const handleImportConfirm = async () => {
      if (uploadFileList.value.length === 0) {
        message.warning('请先选择要导入的音频文件')
        return
      }
      
      uploadLoading.value = true
      try {
        const importedFiles = []
        
        for (const file of uploadFileList.value) {
          if (file.originFileObj) {
            const audioFileItem = await importAudioFile(file.originFileObj)
            importedFiles.push(audioFileItem)
          }
        }
        
        message.success(`成功导入 ${uploadFileList.value.length} 个音频文件到素材库`)
        
        // 通知父组件导入成功
        emit('import-success', importedFiles)
        
        // 关闭模态框并清空文件列表
        modalVisible.value = false
        uploadFileList.value = []
      } catch (error) {
        console.error('导入音频文件失败:', error)
        message.error('导入失败: ' + error.message)
      } finally {
        uploadLoading.value = false
      }
    }

    // 核心导入逻辑
    const importAudioFile = async (file) => {
      // 创建FormData
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        // 上传文件到服务器
        const uploadResponse = await api.audioEditor.uploadFile(formData)
        
        // 修复：axios响应数据在data字段中
        const responseData = uploadResponse.data || uploadResponse
        
        if (responseData.success || responseData.filename) {
          // 根据实际API响应结构处理数据
          const fileName = responseData.filename
          const filePath = responseData.file_path
          const fileSize = responseData.file_size
          
          // 构建文件访问URL - 将本地路径转换为API访问路径
          const fileUrl = `/api/v1/audio-editor/files/${fileName}`
          
          // 构建音频文件对象
          const audioFileItem = {
            id: Date.now() + Math.random(), // 确保唯一性
            name: file.name.replace(/\.[^/.]+$/, ''), // 移除文件扩展名
            originalName: file.name,
            type: 'audio',
            audioUrl: fileUrl,
            filePath: filePath,
            fileSize: fileSize,
            duration: 30, // 默认30秒，后续可以通过音频元数据获取实际时长
            uploadTime: new Date().toISOString()
          }
          
          return audioFileItem
        } else {
          throw new Error(responseData.message || '上传失败')
        }
      } catch (error) {
        console.error('上传文件详细错误:', error)
        throw new Error(`上传文件 ${file.name} 失败: ${error.message}`)
      }
    }

    // 取消操作
    const handleCancel = () => {
      modalVisible.value = false
      uploadFileList.value = []
    }

    // 工具函数
    const formatFileSize = (size) => {
      if (size < 1024) return size + ' B'
      if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
      return (size / 1024 / 1024).toFixed(1) + ' MB'
    }

    // 监听模态框关闭，重置文件列表
    watch(() => props.visible, (newValue) => {
      if (!newValue) {
        uploadFileList.value = []
      }
    })

    return {
      modalVisible,
      uploadFileList,
      uploadLoading,
      beforeUpload,
      handleFileChange,
      handleFileDrop,
      handleImportConfirm,
      handleCancel,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.import-modal-content {
  max-height: 400px;
  overflow-y: auto;
}

.ant-upload-drag-icon {
  margin-bottom: 16px;
}

.ant-upload-text {
  font-size: 16px;
  color: #666;
  margin-bottom: 8px;
}

.ant-upload-hint {
  font-size: 14px;
  color: #999;
}

/* 暗色主题支持 */
.dark .import-modal-content {
  background-color: #141414;
}

.dark .ant-upload-text {
  color: #d9d9d9;
}

.dark .ant-upload-hint {
  color: #8c8c8c;
}
</style>