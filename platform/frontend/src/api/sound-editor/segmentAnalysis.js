import apiClient from '@/api/config'

export function smartPrepareAPI(rawText) {
  return apiClient.post('/segment_analysis/smart_prepare', { raw_text: rawText })
}

export function deepAnalyzeAPI(segments) {
  return apiClient.post('/segment_analysis/deep_analyze', { segments })
}
