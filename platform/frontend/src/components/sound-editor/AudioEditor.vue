<template>
  <div class="audio-editor">
    <a-card title="多轨音频合成（骨架）">
      <a-upload
        multiple
        :before-upload="() => false"
        @change="handleFileChange"
      >
        <a-button>上传音频文件</a-button>
      </a-upload>
      <div style="margin: 16px 0;">
        <a-button type="primary" @click="handleMix">合成音频</a-button>
      </div>
      <div v-if="taskId">
        <a-alert :message="`任务ID: ${taskId}，状态: ${status}`" type="info" show-icon />
      </div>
      <div v-if="outputUrl">
        <audio :src="outputUrl" controls style="width: 100%; margin-top: 16px;" />
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { mixAudio, getTaskStatus } from '../api/audioMix'

const fileList = ref([])
const taskId = ref('')
const status = ref('')
const outputUrl = ref('')
let pollInterval = null

function handleFileChange(info) {
  fileList.value = info.fileList
}

async function handleMix() {
  try {
    // 这里只做接口调用骨架，实际需先上传文件
    const tracks = fileList.value.map((f, i) => ({
      file_path: f.name,
      start_time: i * 2,
      end_time: i * 2 + 5,
      volume: 1.0
    }))
    
    const res = await mixAudio({ tracks, output_format: 'wav' })
    taskId.value = res.task_id
    status.value = res.status
    outputUrl.value = res.output_url || ''
    
    // 开始轮询任务状态
    startPolling()
  } catch (error) {
    console.error('提交任务失败:', error)
  }
}

function startPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
  
  pollInterval = setInterval(async () => {
    try {
      const res = await getTaskStatus(taskId.value)
      status.value = res.status
      
      if (res.status === 'completed') {
        outputUrl.value = res.output_url || ''
        clearInterval(pollInterval)
        pollInterval = null
      } else if (res.status === 'failed') {
        clearInterval(pollInterval)
        pollInterval = null
      }
    } catch (error) {
      console.error('查询任务状态失败:', error)
    }
  }, 2000) // 每2秒查询一次
}

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})
</script>

<style scoped>
.audio-editor {
  max-width: 600px;
  margin: 40px auto;
}
</style>
