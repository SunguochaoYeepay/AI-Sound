/**
 * API连接测试脚本
 * 测试前端是否能正常连接到后端API
 */

// 使用环境配置 - 统一通过nginx
const isDevelopment = true // 测试环境默认为开发环境
const API_BASE_URL = isDevelopment ? 'http://localhost:3000' : 'http://localhost:3000'

console.log('[测试配置] API地址:', API_BASE_URL)

// 使用fetch API测试连接
async function testApiConnection() {
  console.log('🔌 开始测试API连接...');
  
  // 测试1: 基础健康检查
  try {
    console.log(`\n📋 测试1: 基础API连接`);
    console.log(`🔗 URL: ${API_BASE_URL}/`);
    const response = await fetch(`${API_BASE_URL}/`);
    const data = await response.json();
    console.log('✅ 基础API连接成功:', data);
  } catch (error) {
    console.error('❌ 基础API连接失败:', error.message);
  }
  
  // 测试2: Characters API
  try {
    console.log(`\n📋 测试2: Characters API`);
    console.log(`🔗 URL: ${API_BASE_URL}/api/characters/`);
    const response = await fetch(`${API_BASE_URL}/api/characters/`);
    const data = await response.json();
    console.log('✅ Characters API连接成功:', data);
  } catch (error) {
    console.error('❌ Characters API连接失败:', error.message);
  }
  
  // 测试3: Health检查
  try {
    console.log(`\n📋 测试3: Health检查`);
    console.log(`🔗 URL: ${API_BASE_URL}/health`);
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();
    console.log('✅ Health检查成功:', data);
  } catch (error) {
    console.error('❌ Health检查失败:', error.message);
  }
  
  // 测试代理API
  try {
    console.log('\n测试4: 测试通过本地代理访问API');
    const response = await fetch('/api/characters/');
    if (response.ok) {
      const data = await response.json();
      console.log('✅ 代理API连接成功:', data.success ? '成功' : '失败');
    } else {
      console.error('❌ 代理API连接失败:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('❌ 代理API连接错误:', error.message);
  }
  
  console.log('\n测试完成!');
}

// 如果在浏览器中直接运行
if (typeof window !== 'undefined') {
  window.testApiConnection = testApiConnection;
  console.log('请在浏览器控制台中运行 testApiConnection() 函数进行测试');
}

// 如果在Node.js环境中运行
if (typeof module !== 'undefined') {
  module.exports = { testApiConnection };
  
  // 如果直接执行脚本，则自动运行测试
  if (require.main === module) {
    // 在Node环境需要安装node-fetch
    const fetch = require('node-fetch');
    global.fetch = fetch;
    testApiConnection();
  }
} 