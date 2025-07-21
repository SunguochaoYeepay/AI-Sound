/**
 * Stagewise工具栏配置文件
 * 用于配置Stagewise开发工具栏的行为
 */

export default {
  // 插件配置
  plugins: [],
  
  // 实验性功能
  experimental: {
    // 禁用MCP服务器功能
    enableStagewiseMCP: false,
    // 禁用工具调用功能
    enableToolCalls: false
  },
  
  // 网络配置（如果支持的话）
  network: {
    // 尝试限制扫描的端口范围
    // 注意：这些配置可能不被当前版本支持，但作为未来配置的占位符
    scanPorts: [8001], // 只扫描我们的后端端口
    excludePorts: [5747, 5749], // 排除这些端口
    timeout: 1000 // 连接超时时间（毫秒）
  },
  
  // 调试配置
  debug: {
    // 启用详细日志
    verbose: false,
    // 禁用自动端口扫描
    disableAutoScan: true
  }
}