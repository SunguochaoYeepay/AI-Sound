<template>
  <div class="audio-file-manager">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <a-space>
        <a-upload
          :multiple="true"
          :show-upload-list="false"
          :before-upload="handleBeforeUpload"
          accept="audio/*"
        >
          <a-button type="primary">
            <template #icon><UploadOutlined /></template>
            上传音频文件
          </a-button>
        </a-upload>

        <a-button @click="refreshFileList">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>

        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索文件名..."
          style="width: 200px"
          @search="handleSearch"
        />
      </a-space>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploadingFiles.length > 0" class="upload-progress">
      <a-card size="small" title="上传进度">
        <div v-for="file in uploadingFiles" :key="file.name" class="upload-item">
          <div class="upload-info">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">({{ formatFileSize(file.size) }})</span>
          </div>
          <a-progress :percent="file.progress" :status="file.status" size="small" />
        </div>
      </a-card>
    </div>

    <!-- 文件列表 -->
    <div class="file-list">
      <a-spin :spinning="loading">
        <a-list :data-source="filteredFiles" :pagination="pagination" item-layout="vertical">
          <template #renderItem="{ item }">
            <a-list-item>
              <template #actions>
                <a-space>
                  <a-button size="small" @click="playAudio(item)">
                    <template #icon>
                      <PlayCircleOutlined v-if="!isPlaying(item.file_id)" />
                      <PauseCircleOutlined v-else />
                    </template>
                  </a-button>

                  <a-button size="small" @click="downloadFile(item)">
                    <template #icon><DownloadOutlined /></template>
                  </a-button>

                  <a-button size="small" @click="showFileInfo(item)">
                    <template #icon><InfoCircleOutlined /></template>
                  </a-button>

                  <a-popconfirm title="确定要删除这个文件吗？" @confirm="deleteFile(item)">
                    <a-button size="small" danger>
                      <template #icon><DeleteOutlined /></template>
                    </a-button>
                  </a-popconfirm>
                </a-space>
              </template>

              <template #extra>
                <!-- 波形显示缩略图 -->
                <div v-if="item.waveform_data" class="waveform-thumbnail">
                  <WaveformDisplay
                    :waveform-data="item.waveform_data"
                    :width="200"
                    :height="40"
                    :interactive="false"
                    :show-time-markers="false"
                    :show-progress="false"
                  />
                </div>
              </template>

              <a-list-item-meta>
                <template #title>
                  <span class="file-title">{{ item.original_name || item.filename }}</span>
                  <a-tag v-if="item.format" color="blue" size="small">{{
                    item.format.toUpperCase()
                  }}</a-tag>
                </template>

                <template #description>
                  <a-space split>
                    <span>时长: {{ formatDuration(item.duration) }}</span>
                    <span>大小: {{ formatFileSize(item.file_size) }}</span>
                    <span v-if="item.sample_rate">采样率: {{ item.sample_rate }}Hz</span>
                    <span v-if="item.channels">声道: {{ item.channels }}</span>
                    <span v-if="item.upload_time">
                      上传时间: {{ formatUploadTime(item.upload_time) }}
                    </span>
                  </a-space>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </template>
        </a-list>
      </a-spin>
    </div>

    <!-- 文件信息对话框 -->
    <a-modal v-model:open="fileInfoVisible" title="音频文件信息" width="600px" :footer="null">
      <div v-if="selectedFileInfo" class="file-info-detail">
        <!-- 波形显示 -->
        <div v-if="selectedFileInfo.waveform_data" class="waveform-section">
          <h4>波形图</h4>
          <WaveformDisplay
            :waveform-data="selectedFileInfo.waveform_data"
            :width="500"
            :height="100"
            :duration="selectedFileInfo.duration"
            :interactive="true"
            @seek="handleWaveformSeek"
          />
        </div>

        <!-- 基本信息 -->
        <a-descriptions title="基本信息" bordered size="small">
          <a-descriptions-item label="文件名">
            {{ selectedFileInfo.original_name || selectedFileInfo.filename }}
          </a-descriptions-item>
          <a-descriptions-item label="文件大小">
            {{ formatFileSize(selectedFileInfo.file_size) }}
          </a-descriptions-item>
          <a-descriptions-item label="时长">
            {{ formatDuration(selectedFileInfo.duration) }}
          </a-descriptions-item>
          <a-descriptions-item label="格式">
            {{ selectedFileInfo.format }}
          </a-descriptions-item>
          <a-descriptions-item label="编码">
            {{ selectedFileInfo.codec }}
          </a-descriptions-item>
          <a-descriptions-item label="比特率">
            {{
              selectedFileInfo.bitrate
                ? `${Math.round(selectedFileInfo.bitrate / 1000)}kbps`
                : 'N/A'
            }}
          </a-descriptions-item>
          <a-descriptions-item label="采样率">
            {{ selectedFileInfo.sample_rate }}Hz
          </a-descriptions-item>
          <a-descriptions-item label="声道数">
            {{ selectedFileInfo.channels }}
          </a-descriptions-item>
          <a-descriptions-item label="文件路径" :span="2">
            {{ selectedFileInfo.file_path }}
          </a-descriptions-item>
        </a-descriptions>

        <!-- 操作按钮 -->
        <div class="file-actions" style="margin-top: 16px">
          <a-space>
            <a-button @click="downloadFile(selectedFileInfo)">
              <template #icon><DownloadOutlined /></template>
              下载文件
            </a-button>
            <a-button @click="convertFile(selectedFileInfo)">
              <template #icon><SwapOutlined /></template>
              格式转换
            </a-button>
            <a-button @click="addToProject(selectedFileInfo)" type="primary">
              <template #icon><PlusOutlined /></template>
              添加到项目
            </a-button>
          </a-space>
        </div>
      </div>
    </a-modal>

    <!-- 格式转换对话框 -->
    <a-modal
      v-model:open="convertModalVisible"
      title="音频格式转换"
      @ok="performConvert"
      @cancel="convertModalVisible = false"
    >
      <a-form :model="convertForm" layout="vertical">
        <a-form-item label="输出格式">
          <a-select v-model:value="convertForm.format">
            <a-select-option value="wav">WAV</a-select-option>
            <a-select-option value="mp3">MP3</a-select-option>
            <a-select-option value="flac">FLAC</a-select-option>
            <a-select-option value="aac">AAC</a-select-option>
            <a-select-option value="ogg">OGG</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="采样率">
          <a-select v-model:value="convertForm.sampleRate">
            <a-select-option :value="44100">44.1 kHz</a-select-option>
            <a-select-option :value="48000">48 kHz</a-select-option>
            <a-select-option :value="96000">96 kHz</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
  import { ref, reactive, onMounted, computed } from 'vue'
  import { message } from 'ant-design-vue'
  import {
    UploadOutlined,
    ReloadOutlined,
    PlayCircleOutlined,
    PauseCircleOutlined,
    DownloadOutlined,
    InfoCircleOutlined,
    DeleteOutlined,
    SwapOutlined,
    PlusOutlined
  } from '@ant-design/icons-vue'

  import {
    uploadMultipleAudioFiles,
    listAudioFiles,
    getAudioFileInfo,
    getAudioWaveform,
    deleteAudioFile,
    downloadAudioFile,
    convertAudioFile,
    formatFileSize,
    formatDuration,
    isValidAudioFile
  } from '../../../api/sound-editor/audioFiles'

  import WaveformDisplay from './WaveformDisplay.vue'

  const emit = defineEmits(['add-to-project'])

  // 数据状态
  const loading = ref(false)
  const fileList = ref([])
  const searchKeyword = ref('')
  const uploadingFiles = ref([])

  // 播放状态
  const currentPlayingId = ref(null)
  const audioElement = ref(null)

  // 对话框状态
  const fileInfoVisible = ref(false)
  const selectedFileInfo = ref(null)
  const convertModalVisible = ref(false)
  const convertForm = reactive({
    format: 'wav',
    sampleRate: 44100
  })

  // 分页配置
  const pagination = reactive({
    current: 1,
    pageSize: 10,
    total: 0,
    showSizeChanger: true,
    showQuickJumper: true
  })

  // 计算属性
  const filteredFiles = computed(() => {
    if (!searchKeyword.value) return fileList.value

    return fileList.value.filter((file) => {
      const name = file.original_name || file.filename || ''
      return name.toLowerCase().includes(searchKeyword.value.toLowerCase())
    })
  })

  // 方法
  async function refreshFileList() {
    loading.value = true
    try {
      const result = await listAudioFiles()
      if (result.success) {
        // 为每个文件获取详细信息和波形数据
        fileList.value = await Promise.all(
          result.data.map(async (file) => {
            try {
              const info = await getAudioFileInfo(file.file_id)
              if (info.success) {
                // 尝试获取波形数据
                try {
                  const waveform = await getAudioWaveform(file.file_id, 200, 40)
                  if (waveform.success) {
                    return { ...info.data, waveform_data: waveform.data.waveform }
                  }
                } catch (e) {
                  console.warn('获取波形失败:', e)
                }
                return info.data
              }
              return file
            } catch (e) {
              console.warn('获取文件信息失败:', e)
              return file
            }
          })
        )
        pagination.total = fileList.value.length
      }
    } catch (error) {
      console.error('获取文件列表失败:', error)
      message.error('获取文件列表失败')
    } finally {
      loading.value = false
    }
  }

  function handleBeforeUpload(file, fileList) {
    // 验证文件类型
    if (!isValidAudioFile(file)) {
      message.error(`不支持的文件格式: ${file.name}`)
      return false
    }

    // 添加到上传队列
    const uploadFile = {
      name: file.name,
      size: file.size,
      progress: 0,
      status: 'active'
    }
    uploadingFiles.value.push(uploadFile)

    // 开始上传
    performUpload(file, uploadFile)

    return false // 阻止默认上传
  }

  async function performUpload(file, uploadFile) {
    try {
      // 模拟上传进度
      const progressInterval = setInterval(() => {
        if (uploadFile.progress < 90) {
          uploadFile.progress += Math.random() * 20
        }
      }, 100)

      const result = await uploadMultipleAudioFiles([file])

      clearInterval(progressInterval)
      uploadFile.progress = 100
      uploadFile.status = 'success'

      if (result.success && result.data[0].upload_success) {
        message.success(`${file.name} 上传成功`)
        // 刷新文件列表
        await refreshFileList()
      } else {
        uploadFile.status = 'exception'
        message.error(`${file.name} 上传失败: ${result.data[0].error}`)
      }
    } catch (error) {
      uploadFile.status = 'exception'
      message.error(`${file.name} 上传失败`)
    } finally {
      // 移除上传项
      setTimeout(() => {
        const index = uploadingFiles.value.indexOf(uploadFile)
        if (index > -1) {
          uploadingFiles.value.splice(index, 1)
        }
      }, 2000)
    }
  }

  function handleSearch() {
    // 搜索逻辑在计算属性中处理
  }

  function isPlaying(fileId) {
    return currentPlayingId.value === fileId
  }

  function playAudio(file) {
    if (isPlaying(file.file_id)) {
      // 暂停播放
      if (audioElement.value) {
        audioElement.value.pause()
      }
      currentPlayingId.value = null
    } else {
      // 开始播放
      if (audioElement.value) {
        audioElement.value.pause()
      }

      audioElement.value = new Audio()
      audioElement.value.src = `http://localhost:8000/api/v1/audio-files/download/${file.file_id}`
      audioElement.value.crossOrigin = 'anonymous'

      audioElement.value.addEventListener('ended', () => {
        currentPlayingId.value = null
      })

      audioElement.value.addEventListener('error', () => {
        message.error('音频播放失败')
        currentPlayingId.value = null
      })

      audioElement.value.play()
      currentPlayingId.value = file.file_id
    }
  }

  async function downloadFile(file) {
    try {
      await downloadAudioFile(file.file_id)
    } catch (error) {
      console.error('下载失败:', error)
      message.error('下载失败')
    }
  }

  async function showFileInfo(file) {
    try {
      const result = await getAudioFileInfo(file.file_id)
      if (result.success) {
        selectedFileInfo.value = result.data

        // 获取详细波形数据
        try {
          const waveform = await getAudioWaveform(file.file_id, 500, 100)
          if (waveform.success) {
            selectedFileInfo.value.waveform_data = waveform.data.waveform
          }
        } catch (e) {
          console.warn('获取波形失败:', e)
        }

        fileInfoVisible.value = true
      }
    } catch (error) {
      console.error('获取文件信息失败:', error)
      message.error('获取文件信息失败')
    }
  }

  async function deleteFile(file) {
    try {
      const result = await deleteAudioFile(file.file_id)
      if (result.success) {
        message.success('文件删除成功')
        await refreshFileList()
      }
    } catch (error) {
      console.error('删除失败:', error)
      message.error('删除失败')
    }
  }

  function convertFile(file) {
    selectedFileInfo.value = file
    convertModalVisible.value = true
  }

  async function performConvert() {
    try {
      const result = await convertAudioFile(
        selectedFileInfo.value.file_id,
        convertForm.format,
        convertForm.sampleRate
      )

      if (result.success) {
        message.success('转换成功')
        convertModalVisible.value = false
        await refreshFileList()
      }
    } catch (error) {
      console.error('转换失败:', error)
      message.error('转换失败')
    }
  }

  function addToProject(file) {
    emit('add-to-project', file)
    fileInfoVisible.value = false
  }

  function handleWaveformSeek(time) {
    if (audioElement.value) {
      audioElement.value.currentTime = time
    }
  }

  function formatUploadTime(timestamp) {
    return new Date(timestamp * 1000).toLocaleString()
  }

  // 生命周期
  onMounted(() => {
    refreshFileList()
  })
</script>

<style scoped>
  .audio-file-manager {
    background: white;
    border-radius: 6px;
    overflow: hidden;
  }

  .toolbar {
    padding: 16px;
    background: #fafafa;
    border-bottom: 1px solid #e8e8e8;
  }

  .upload-progress {
    padding: 16px;
    background: #f0f8ff;
    border-bottom: 1px solid #e8e8e8;
  }

  .upload-item {
    margin-bottom: 8px;
  }

  .upload-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }

  .file-name {
    font-weight: 500;
  }

  .file-size {
    color: #666;
    font-size: 12px;
  }

  .file-list {
    padding: 16px;
  }

  .file-title {
    font-weight: 500;
    margin-right: 8px;
  }

  .waveform-thumbnail {
    width: 200px;
    height: 40px;
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    overflow: hidden;
  }

  .file-info-detail {
    max-height: 70vh;
    overflow-y: auto;
  }

  .waveform-section {
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e8e8e8;
  }

  .waveform-section h4 {
    margin-bottom: 8px;
  }

  .file-actions {
    text-align: center;
  }
</style>
