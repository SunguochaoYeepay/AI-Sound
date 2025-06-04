/**
 * 静态文件服务器检查脚本
 * 检查音频静态文件服务器是否正常工作
 */

const API_BASE_URL = 'http://soundapi.cpolar.top';

async function checkStaticServer() {
  console.log('开始检查静态文件服务器...');
  console.log(`基础URL: ${API_BASE_URL}`);
  
  // 检查服务器状态
  try {
    console.log('\n1. 检查API服务器基本状态');
    const healthResponse = await fetch(`${API_BASE_URL}/health`);
    
    if (healthResponse.ok) {
      const healthData = await healthResponse.json();
      console.log('✅ API服务器健康状态:', healthData.status);
    } else {
      console.error('❌ API服务器健康检查失败:', healthResponse.status);
    }
  } catch (error) {
    console.error('❌ API服务器连接错误:', error.message);
  }
  
  // 发送OPTIONS请求到静态文件路径
  try {
    console.log('\n2. 发送OPTIONS请求到静态文件路径');
    const optionsResponse = await fetch(`${API_BASE_URL}/audio/test.wav`, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET'
      }
    });
    
    console.log('状态码:', optionsResponse.status);
    console.log('CORS响应头:');
    
    for (const [key, value] of optionsResponse.headers.entries()) {
      if (key.toLowerCase().includes('access-control')) {
        console.log(`  ${key}: ${value}`);
      }
    }
    
    if (optionsResponse.ok) {
      console.log('✅ OPTIONS请求成功');
    } else {
      console.error('❌ OPTIONS请求失败');
    }
  } catch (error) {
    console.error('❌ OPTIONS请求错误:', error.message);
  }
  
  // 检查音频目录结构
  try {
    console.log('\n3. 检查服务器上的目录结构 (如果API支持)');
    
    try {
      const audioListResponse = await fetch(`${API_BASE_URL}/api/monitor/files?dir=audio`);
      
      if (audioListResponse.ok) {
        const filesData = await audioListResponse.json();
        console.log('✅ 音频目录列表:', filesData.files ? filesData.files.length + '个文件' : '不可用');
      } else {
        console.log('⚠️ 无法获取音频文件列表 (可能API不支持)');
      }
    } catch (e) {
      console.log('⚠️ 无法获取音频文件列表 (API可能不支持)');
    }
  } catch (error) {
    console.error('❌ 目录检查错误:', error.message);
  }
  
  // 检查跨域资源共享配置
  try {
    console.log('\n4. 检查跨域资源共享(CORS)配置');
    
    // 从两个不同来源发送请求
    const origins = ['http://localhost:3000', 'http://aisound.cpolar.top'];
    
    for (const origin of origins) {
      console.log(`\n检查来源: ${origin}`);
      
      try {
        const corsResponse = await fetch(`${API_BASE_URL}/audio/test.wav`, {
          method: 'HEAD',
          headers: {
            'Origin': origin
          }
        });
        
        const allowOrigin = corsResponse.headers.get('Access-Control-Allow-Origin');
        
        console.log('状态码:', corsResponse.status);
        console.log('Access-Control-Allow-Origin:', allowOrigin || '无');
        
        if (allowOrigin === '*' || allowOrigin === origin) {
          console.log(`✅ CORS配置正确`);
        } else {
          console.log(`❌ CORS配置错误`);
        }
      } catch (e) {
        console.error(`❌ 从 ${origin} 检查CORS失败:`, e.message);
      }
    }
  } catch (error) {
    console.error('❌ CORS检查错误:', error.message);
  }
  
  console.log('\n检查完成!');
}

// 如果在浏览器中直接运行
if (typeof window !== 'undefined') {
  window.checkStaticServer = checkStaticServer;
  console.log('请在浏览器控制台中运行 checkStaticServer() 函数进行测试');
}

// 如果在Node.js环境中运行
if (typeof module !== 'undefined') {
  module.exports = { checkStaticServer };
  
  // 如果直接执行脚本，则自动运行测试
  if (require.main === module) {
    // 在Node环境需要安装node-fetch
    const fetch = require('node-fetch');
    global.fetch = fetch;
    checkStaticServer();
  }
} 