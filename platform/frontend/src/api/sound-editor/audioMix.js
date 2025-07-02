import axios from 'axios'

export async function mixAudio(data) {
  const res = await axios.post('/api/v1/audio-editor/mix', data)
  return res.data
}

export async function getTaskStatus(taskId) {
  const res = await axios.get(`/api/v1/audio-editor/task/${taskId}`)
  return res.data
}

export async function deletePreviewFile(filename) {
  const res = await axios.delete(`/api/v1/audio-editor/preview/${filename}`)
  return res.data
}
