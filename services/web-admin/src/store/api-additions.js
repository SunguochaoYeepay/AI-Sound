/**
 * 获取所有TTS引擎健康状态
 */
async getAllEnginesHealth() {
  this.isLoading = true;
  try {
    const response = await apiClient.get('/api/engines/health');
    return response.data;
  } catch (error) {
    console.error('获取引擎健康状态失败', error);
    return {
      megatts3: { healthy: false, message: '无法获取状态', last_check: Date.now() / 1000 },
      espnet: { healthy: false, message: '无法获取状态', last_check: Date.now() / 1000 }
    };
  } finally {
    this.isLoading = false;
  }
},

/**
 * 获取指定引擎的健康状态
 * @param {String} engineType - 引擎类型 (megatts3, espnet等)
 */
async getEngineHealth(engineType) {
  this.isLoading = true;
  try {
    const response = await apiClient.get(`/api/engines/${engineType}/health`);
    return response.data;
  } catch (error) {
    console.error(`获取引擎健康状态失败: ${engineType}`, error);
    return { healthy: false, message: '无法获取状态', last_check: Date.now() / 1000 };
  } finally {
    this.isLoading = false;
  }
},

/**
 * 获取所有TTS引擎列表及其信息
 */
async getAllEngines() {
  this.isLoading = true;
  try {
    const response = await apiClient.get('/api/engines');
    return response.data.engines || [];
  } catch (error) {
    console.error('获取引擎列表失败', error);
    return [];
  } finally {
    this.isLoading = false;
  }
}