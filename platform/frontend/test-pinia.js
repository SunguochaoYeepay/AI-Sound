// 测试pinia模块导入
console.log('🧪 测试Pinia模块导入...')

try {
  // 测试pinia主模块
  const pinia = require('./node_modules/pinia/index.js')
  console.log('✅ Pinia CommonJS 导入成功:', typeof pinia)
  
  // 测试ESM导入路径
  const fs = require('fs')
  const path = require('path')
  
  const esModulePath = path.join(__dirname, 'node_modules/pinia/dist/pinia.mjs')
  if (fs.existsSync(esModulePath)) {
    console.log('✅ Pinia ESM 文件存在:', esModulePath)
  } else {
    console.log('❌ Pinia ESM 文件缺失:', esModulePath)
  }
  
  // 检查package.json导出
  const pkgPath = path.join(__dirname, 'node_modules/pinia/package.json')
  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'))
  console.log('📦 Pinia 版本:', pkg.version)
  console.log('📤 Pinia 导出配置:', pkg.exports)
  
} catch (error) {
  console.error('❌ Pinia 导入失败:', error.message)
}

console.log('🏁 测试完成') 