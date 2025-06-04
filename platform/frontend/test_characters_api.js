#!/usr/bin/env node

/**
 * Characters API 连接测试脚本
 */

const axios = require('axios')

const API_BASE_URL = 'http://soundapi.cpolar.top'

async function testCharactersAPI() {
    console.log('🧪 开始测试 Characters API...')
    
    const tests = [
        {
            name: '健康检查',
            url: `${API_BASE_URL}/health`,
            method: 'GET'
        },
        {
            name: '获取角色列表 (无参数)',
            url: `${API_BASE_URL}/api/characters/`,
            method: 'GET'
        },
        {
            name: '获取角色列表 (带参数)',
            url: `${API_BASE_URL}/api/characters/?page=1&page_size=5`,
            method: 'GET'
        },
        {
            name: '测试不带末尾斜杠',
            url: `${API_BASE_URL}/api/characters`,
            method: 'GET'
        }
    ]
    
    for (const test of tests) {
        console.log(`\n📋 测试: ${test.name}`)
        console.log(`🔗 URL: ${test.url}`)
        
        try {
            const response = await axios({
                method: test.method,
                url: test.url,
                timeout: 10000,
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            })
            
            console.log(`✅ 成功 - 状态码: ${response.status}`)
            if (response.data) {
                if (typeof response.data === 'object') {
                    if (response.data.success !== undefined) {
                        console.log(`📊 Success: ${response.data.success}`)
                        if (response.data.data && Array.isArray(response.data.data)) {
                            console.log(`📝 数据条数: ${response.data.data.length}`)
                        }
                    } else {
                        console.log(`📊 响应类型: ${typeof response.data}`)
                        if (response.data.status) {
                            console.log(`📊 状态: ${response.data.status}`)
                        }
                    }
                } else {
                    console.log(`📊 响应: ${response.data}`)
                }
            }
            
        } catch (error) {
            console.log(`❌ 失败`)
            
            if (error.response) {
                console.log(`📊 HTTP 状态码: ${error.response.status}`)
                console.log(`📊 错误信息: ${JSON.stringify(error.response.data)}`)
            } else if (error.request) {
                console.log(`📊 网络错误: 无法连接到服务器`)
                console.log(`📊 错误详情: ${error.message}`)
            } else {
                console.log(`📊 未知错误: ${error.message}`)
            }
        }
    }
    
    console.log('\n🎯 测试完成!')
}

testCharactersAPI().catch(console.error) 