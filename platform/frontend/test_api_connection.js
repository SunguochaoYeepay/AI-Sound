/**
 * API连接测试脚本
 * 用于验证前端是否能够正确连接到API服务器
 */

// 使用fetch API测试连接
async function testAPIConnection() {
  console.log('开始测试API连接...');
  
  // 测试API基础连接
  try {
    console.log('测试1: 连接到API根路径');
    const response = await fetch('http://soundapi.cpolar.top/');
    if (response.ok) {
      const data = await response.json();
      console.log('✅ API根路径连接成功:', data);
    } else {
      console.error('❌ API根路径连接失败:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('❌ API根路径连接错误:', error.message);
  }
  
  // 测试角色API连接
  try {
    console.log('\n测试2: 连接到角色API');
    const response = await fetch('http://soundapi.cpolar.top/api/characters/');
    if (response.ok) {
      const data = await response.json();
      console.log('✅ 角色API连接成功:', data.success ? '成功' : '失败');
      console.log(`获取到 ${data.data?.length || 0} 个声音档案`);
    } else {
      console.error('❌ 角色API连接失败:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('❌ 角色API连接错误:', error.message);
  }
  
  // 测试健康检查API
  try {
    console.log('\n测试3: 连接到健康检查API');
    const response = await fetch('http://soundapi.cpolar.top/health');
    if (response.ok) {
      const data = await response.json();
      console.log('✅ 健康检查API连接成功:', data.status);
      console.log('服务状态:', data);
    } else {
      console.error('❌ 健康检查API连接失败:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('❌ 健康检查API连接错误:', error.message);
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
  window.testAPIConnection = testAPIConnection;
  console.log('请在浏览器控制台中运行 testAPIConnection() 函数进行测试');
}

// 如果在Node.js环境中运行
if (typeof module !== 'undefined') {
  module.exports = { testAPIConnection };
  
  // 如果直接执行脚本，则自动运行测试
  if (require.main === module) {
    // 在Node环境需要安装node-fetch
    const fetch = require('node-fetch');
    global.fetch = fetch;
    testAPIConnection();
  }
} 