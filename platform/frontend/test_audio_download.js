/**
 * 音频文件下载测试脚本
 * 用于验证对音频文件的访问是否正常
 */

async function testAudioDownload() {
  console.log('开始测试音频文件下载...');
  
  // 测试1: 直接通过URL获取音频文件
  try {
    console.log('测试1: 直接获取音频文件');
    // 使用一个测试音频文件路径
    const audioUrl = 'http://soundapi.cpolar.top/audio/tts_2fb418d7d49144f7be0fd0e8dd2bc0a0.wav';
    console.log('请求URL:', audioUrl);
    
    const response = await fetch(audioUrl, {
      method: 'GET',
      headers: {
        'Accept': 'audio/wav,audio/*;q=0.8,*/*;q=0.5',
      },
      cache: 'no-cache',
      mode: 'cors'
    });
    
    if (response.ok) {
      const blob = await response.blob();
      console.log('✅ 音频文件下载成功!');
      console.log('文件大小:', (blob.size / 1024).toFixed(2) + ' KB');
      console.log('文件类型:', blob.type);
    } else {
      console.error('❌ 音频文件下载失败:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('❌ 音频文件下载错误:', error.message);
  }
  
  // 测试2: 通过代理获取音频文件
  try {
    console.log('\n测试2: 通过本地代理获取音频文件');
    const audioUrl = '/audio/tts_2fb418d7d49144f7be0fd0e8dd2bc0a0.wav';
    console.log('请求URL:', audioUrl);
    
    const response = await fetch(audioUrl, {
      method: 'GET',
      headers: {
        'Accept': 'audio/wav,audio/*;q=0.8,*/*;q=0.5',
      },
      cache: 'no-cache'
    });
    
    if (response.ok) {
      const blob = await response.blob();
      console.log('✅ 通过代理下载音频文件成功!');
      console.log('文件大小:', (blob.size / 1024).toFixed(2) + ' KB');
      console.log('文件类型:', blob.type);
    } else {
      console.error('❌ 通过代理下载音频文件失败:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('❌ 通过代理下载音频文件错误:', error.message);
  }
  
  // 测试3: 创建一个音频元素并尝试播放
  try {
    console.log('\n测试3: 创建音频元素测试');
    const audioUrl = '/audio/tts_2fb418d7d49144f7be0fd0e8dd2bc0a0.wav';
    console.log('音频元素源:', audioUrl);
    
    if (typeof window !== 'undefined') {
      const audio = new Audio(audioUrl);
      
      audio.onloadeddata = () => {
        console.log('✅ 音频加载成功，准备播放');
        console.log('音频时长:', audio.duration.toFixed(2) + '秒');
      };
      
      audio.onerror = (e) => {
        console.error('❌ 音频加载失败:', e);
      };
      
      // 触发加载
      audio.load();
      console.log('音频元素创建成功，等待加载...');
    } else {
      console.log('⚠️ 非浏览器环境，无法创建音频元素');
    }
  } catch (error) {
    console.error('❌ 音频元素测试错误:', error.message);
  }
  
  console.log('\n测试完成!');
}

// 如果在浏览器中直接运行
if (typeof window !== 'undefined') {
  window.testAudioDownload = testAudioDownload;
  console.log('请在浏览器控制台中运行 testAudioDownload() 函数进行测试');
}

// 如果在Node.js环境中运行
if (typeof module !== 'undefined') {
  module.exports = { testAudioDownload };
  
  // 如果直接执行脚本，则自动运行测试
  if (require.main === module) {
    // 在Node环境需要安装node-fetch
    console.log('请在浏览器中运行此测试以获得更完整的结果');
  }
} 