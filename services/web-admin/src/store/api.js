import { defineStore } from 'pinia'
import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:9930',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

export const useApiStore = defineStore({
  id: 'api',
  state: () => ({
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:9930',
    apiStatus: false,
    apiVersion: '',
    errorMessage: '',
    isLoading: false
  }),
  actions: {
    /**
     * 检查API健康状态
     */
    async checkHealth() {
      this.isLoading = true;
      try {
        const response = await apiClient.get('/health');
        this.apiStatus = true;
        this.errorMessage = '';
        return { 
          status: 'ok', 
          info: {
            version: response.data.version || '1.0.0',
            uptime: response.data.uptime || 0
          }
        };
      } catch (error) {
        this.apiStatus = false;
        this.errorMessage = '无法连接到API服务';
        console.error('API健康检查失败', error);
        return { status: 'error' };
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 获取系统信息
     */
    async getSystemInfo() {
      this.isLoading = true;
      try {
        const response = await apiClient.get('/api/system/info');
        return response.data;
      } catch (error) {
        console.error('获取系统信息失败', error);
        return {
          gpu_available: false,
          gpu_info: '未知',
          storage_used: '未知',
          storage_available: '未知'
        };
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 获取统计数据
     */
    async getStats() {
      this.isLoading = true;
      try {
        const response = await apiClient.get('/api/stats');
        return response.data;
      } catch (error) {
        console.error('获取统计数据失败', error);
        return {
          tts_count: 0,
          novel_count: 0,
          pending_tasks: 0,
          audio_count: 0
        };
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 获取最近任务
     * @param {Number} limit - 限制数量
     */
    async getRecentTasks(limit = 5) {
      this.isLoading = true;
      try {
        const response = await apiClient.get(`/api/tasks?limit=${limit}`);
        return response.data.tasks || [];
      } catch (error) {
        console.error('获取最近任务失败', error);
        return [];
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 获取任务详情
     * @param {String} taskId - 任务ID
     */
    async getTaskDetails(taskId) {
      this.isLoading = true;
      try {
        const response = await apiClient.get(`/api/tasks/${taskId}`);
        return response.data;
      } catch (error) {
        console.error(`获取任务详情失败: ${taskId}`, error);
        return null;
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 上传小说文件
     * @param {File} file - 小说文件
     * @param {Object} options - 处理选项
     */
    async uploadNovel(file, options = {}) {
      this.isLoading = true;
      const formData = new FormData();
      formData.append('file', file);
      
      Object.keys(options).forEach(key => {
        formData.append(key, options[key]);
      });
      
      try {
        const response = await apiClient.post('/api/novels/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        return response.data;
      } catch (error) {
        console.error('上传小说失败', error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 处理小说
     * @param {String} novelPath - 小说路径
     * @param {Object} options - 处理选项
     */
    async processNovel(novelPath, options = {}) {
      this.isLoading = true;
      try {
        const response = await apiClient.post('/api/tts/novel', {
          novel_path: novelPath,
          ...options
        });
        return response.data;
      } catch (error) {
        console.error('小说处理请求失败', error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 文本转语音
     * @param {String} text - 文本内容
     * @param {Object} options - 合成选项
     */
    async textToSpeech(text, options = {}) {
      this.isLoading = true;
      try {
        const response = await apiClient.post('/api/tts', {
          text: text,
          ...options
        });
        return response.data;
      } catch (error) {
        console.error('文本转语音失败', error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 使用FormData格式进行文本转语音请求（支持上传声音文件）
     * @param {FormData} formData - 包含文本和配置的表单数据
     */
    async textToSpeechMultipart(formData) {
      this.isLoading = true;
      try {
        const response = await apiClient.post('/api/tts/text_multipart', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        return response.data;
      } catch (error) {
        console.error('文本转语音失败', error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 获取所有小说列表
     */
    async getNovels() {
      this.isLoading = true;
      try {
        const response = await apiClient.get('/api/novels');
        return response.data.novels || [];
      } catch (error) {
        console.error('获取小说列表失败', error);
        return [];
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 获取小说详情
     * @param {String} novelId - 小说ID
     */
    async getNovelDetails(novelId) {
      this.isLoading = true;
      try {
        const response = await apiClient.get(`/api/novels/${novelId}`);
        return response.data;
      } catch (error) {
        console.error(`获取小说详情失败: ${novelId}`, error);
        return null;
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 删除小说
     * @param {String} novelId - 小说ID
     */
    async deleteNovel(novelId) {
      this.isLoading = true;
      try {
        const response = await apiClient.delete(`/api/novels/${novelId}`);
        return response.data;
      } catch (error) {
        console.error(`删除小说失败: ${novelId}`, error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 获取小说章节列表
     * @param {String} novelId - 小说ID
     */
    async getNovelChapters(novelId) {
      this.isLoading = true;
      try {
        const response = await apiClient.get(`/api/novels/${novelId}/chapters`);
        return response.data.chapters || [];
      } catch (error) {
        console.error(`获取小说章节失败: ${novelId}`, error);
        return [];
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 获取章节内容
     * @param {String} novelId - 小说ID
     * @param {String} chapterId - 章节ID
     */
    async getChapterContent(novelId, chapterId) {
      this.isLoading = true;
      try {
        const response = await apiClient.get(`/api/novels/${novelId}/chapters/${chapterId}`);
        return response.data;
      } catch (error) {
        console.error(`获取章节内容失败: ${novelId}/${chapterId}`, error);
        return null;
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 更新小说配置
     * @param {String} novelId - 小说ID
     * @param {Object} config - 配置信息
     */
    async updateNovelConfig(novelId, config) {
      this.isLoading = true;
      try {
        const response = await apiClient.put(`/api/novels/${novelId}/config`, config);
        return response.data;
      } catch (error) {
        console.error(`更新小说配置失败: ${novelId}`, error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 获取所有任务
     */
    async getAllTasks() {
      this.isLoading = true;
      try {
        const response = await apiClient.get('/api/tasks');
        return response.data;
      } catch (error) {
        console.error('获取所有任务失败', error);
        return { tasks: [] };
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 从URL导入小说
     * @param {String} url - 小说URL
     * @param {Object} options - 导入选项
     */
    async importNovelFromUrl(url, options = {}) {
      this.isLoading = true;
      try {
        const response = await apiClient.post('/api/novels/import', {
          url,
          ...options
        });
        return response.data;
      } catch (error) {
        console.error('导入小说失败', error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 获取角色声音映射
     */
    async getCharacterMappings() {
      this.isLoading = true;
      try {
        const response = await apiClient.get('/api/characters');
        return response.data.characters || [];
      } catch (error) {
        console.error('获取角色声音映射失败', error);
        return [];
      } finally {
        this.isLoading = false;
      }
    }
  }
})