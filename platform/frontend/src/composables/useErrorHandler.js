import { message } from 'ant-design-vue'

/**
 * 统一错误处理 Composable
 */
export const useErrorHandler = () => {
  /**
   * 处理错误
   * @param {Error} error - 错误对象
   * @param {string} context - 错误上下文
   * @param {Object} options - 处理选项
   */
  const handleError = (error, context = '操作失败', options = {}) => {
    const {
      showMessage = true,
      logError = true,
      fallbackMessage = context
    } = options

    // 记录错误日志
    if (logError) {
      console.error(`${context}:`, error)
    }

    // 显示错误消息
    if (showMessage) {
      let errorMessage = fallbackMessage
      
      // 尝试从错误对象中提取更具体的错误信息
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message
      } else if (error.message) {
        errorMessage = error.message
      }

      message.error(errorMessage)
    }
  }

  /**
   * 处理 API 错误
   * @param {Error} error - API 错误对象
   * @param {string} operation - 操作名称
   */
  const handleApiError = (error, operation = '请求') => {
    handleError(error, `${operation}失败`, {
      fallbackMessage: `${operation}失败，请稍后重试`
    })
  }

  /**
   * 处理网络错误
   * @param {Error} error - 网络错误对象
   */
  const handleNetworkError = (error) => {
    handleError(error, '网络连接失败', {
      fallbackMessage: '网络连接失败，请检查网络设置'
    })
  }

  /**
   * 处理验证错误
   * @param {Error} error - 验证错误对象
   */
  const handleValidationError = (error) => {
    handleError(error, '数据验证失败', {
      fallbackMessage: '输入数据有误，请检查后重试'
    })
  }

  return {
    handleError,
    handleApiError,
    handleNetworkError,
    handleValidationError
  }
}
