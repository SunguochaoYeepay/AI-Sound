// 简单的前端调试脚本，用于测试WebSocket连接和API
console.log('🧪 开始调试WebSocket进度连接...')

// 1. 测试基本API连接
async function testAPI() {
    console.log('1️⃣ 测试API连接...')
    try {
        const response = await fetch('http://localhost:8000/health')
        if (response.ok) {
            const data = await response.json()
            console.log('✅ API连接成功:', data)
            return true
        } else {
            console.log('❌ API连接失败:', response.status)
            return false
        }
    } catch (error) {
        console.log('❌ API连接异常:', error)
        return false
    }
}

// 2. 测试WebSocket连接
function testWebSocket() {
    console.log('2️⃣ 测试WebSocket连接...')
    
    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onopen = function(event) {
        console.log('✅ WebSocket连接成功')
        
        // 订阅测试主题
        const subscribeMessage = {
            type: 'subscribe',
            topic: 'synthesis_24'  // 使用项目ID 24作为测试
        }
        
        ws.send(JSON.stringify(subscribeMessage))
        console.log('📝 已发送订阅消息:', subscribeMessage)
    }
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data)
        console.log('📨 收到WebSocket消息:', data)
        
        if (data.type === 'topic_message' && data.topic === 'synthesis_24') {
            console.log('🎯 收到合成进度消息:', data.data)
        }
    }
    
    ws.onclose = function(event) {
        console.log('🔌 WebSocket连接关闭:', event.code, event.reason)
    }
    
    ws.onerror = function(error) {
        console.log('❌ WebSocket连接错误:', error)
    }
    
    // 10秒后关闭连接
    setTimeout(() => {
        ws.close()
        console.log('⏰ 测试超时，关闭WebSocket连接')
    }, 10000)
}

// 3. 测试项目进度API
async function testProjectProgress() {
    console.log('3️⃣ 测试项目进度API...')
    try {
        const response = await fetch('http://localhost:8000/api/v1/novel-reader/projects/24/progress')
        if (response.ok) {
            const data = await response.json()
            console.log('✅ 项目进度API成功:', data)
            return true
        } else {
            const text = await response.text()
            console.log('❌ 项目进度API失败:', response.status, text)
            return false
        }
    } catch (error) {
        console.log('❌ 项目进度API异常:', error)
        return false
    }
}

// 主测试函数
async function runDebugTests() {
    console.log('=' * 50)
    
    const apiOk = await testAPI()
    await new Promise(resolve => setTimeout(resolve, 1000)) // 等待1秒
    
    const progressOk = await testProjectProgress()
    await new Promise(resolve => setTimeout(resolve, 1000)) // 等待1秒
    
    testWebSocket()
    
    console.log('=' * 50)
    console.log('🎯 测试结果总结:')
    console.log(`API连接: ${apiOk ? '✅ 通过' : '❌ 失败'}`)
    console.log(`项目进度API: ${progressOk ? '✅ 通过' : '❌ 失败'}`)
    console.log('WebSocket测试: 请查看上方日志')
}

// 运行测试
runDebugTests() 