#!/usr/bin/env node

/**
 * 批量替换硬编码样式值的脚本
 * 将项目中的硬编码样式值替换为CSS变量
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// 替换规则
const replacements = [
  // 间距替换
  { from: /padding:\s*24px/g, to: 'padding: var(--content-padding)' },
  { from: /padding:\s*16px/g, to: 'padding: var(--content-padding-sm)' },
  { from: /padding:\s*32px/g, to: 'padding: var(--content-padding-lg)' },
  { from: /padding:\s*8px/g, to: 'padding: var(--spacing-sm)' },
  { from: /padding:\s*12px/g, to: 'padding: var(--spacing-md)' },
  { from: /padding:\s*48px/g, to: 'padding: var(--spacing-xxxl)' },
  
  // margin替换
  { from: /margin:\s*24px/g, to: 'margin: var(--content-padding)' },
  { from: /margin:\s*16px/g, to: 'margin: var(--content-padding-sm)' },
  { from: /margin:\s*32px/g, to: 'margin: var(--content-padding-lg)' },
  { from: /margin:\s*8px/g, to: 'margin: var(--spacing-sm)' },
  { from: /margin:\s*12px/g, to: 'margin: var(--spacing-md)' },
  { from: /margin:\s*48px/g, to: 'margin: var(--spacing-xxxl)' },
  
  // gap替换
  { from: /gap:\s*24px/g, to: 'gap: var(--content-padding)' },
  { from: /gap:\s*16px/g, to: 'gap: var(--content-padding-sm)' },
  { from: /gap:\s*32px/g, to: 'gap: var(--content-padding-lg)' },
  { from: /gap:\s*8px/g, to: 'gap: var(--spacing-sm)' },
  { from: /gap:\s*12px/g, to: 'gap: var(--spacing-md)' },
  { from: /gap:\s*48px/g, to: 'gap: var(--spacing-xxxl)' },
  
  // 高度计算替换
  { from: /calc\(100vh\s*-\s*60px\)/g, to: 'var(--content-min-height)' },
  { from: /calc\(100vh\s*-\s*200px\)/g, to: 'calc(100vh - var(--spacing-xxxl) - var(--spacing-xxxl))' },
  { from: /calc\(100vh\s*-\s*120px\)/g, to: 'calc(100vh - var(--spacing-xxxl) - var(--spacing-xxxl))' },
  
  // 内联样式替换
  { from: /style="[^"]*padding:\s*24px[^"]*"/g, (match) => {
    return match.replace(/padding:\s*24px/g, 'padding: var(--content-padding)');
  }},
  { from: /style="[^"]*padding:\s*16px[^"]*"/g, (match) => {
    return match.replace(/padding:\s*16px/g, 'padding: var(--content-padding-sm)');
  }},
  { from: /style="[^"]*padding:\s*32px[^"]*"/g, (match) => {
    return match.replace(/padding:\s*32px/g, 'padding: var(--content-padding-lg)');
  }},
];

// 查找Vue文件
const vueFiles = glob.sync('platform/frontend/src/**/*.vue');

console.log(`找到 ${vueFiles.length} 个Vue文件`);

let totalReplacements = 0;

vueFiles.forEach(filePath => {
  try {
    let content = fs.readFileSync(filePath, 'utf8');
    let fileReplacements = 0;
    
    replacements.forEach(replacement => {
      const matches = content.match(replacement.from);
      if (matches) {
        if (typeof replacement.to === 'function') {
          content = content.replace(replacement.from, replacement.to);
        } else {
          content = content.replace(replacement.from, replacement.to);
        }
        fileReplacements += matches.length;
      }
    });
    
    if (fileReplacements > 0) {
      fs.writeFileSync(filePath, content, 'utf8');
      console.log(`✅ ${filePath}: 替换了 ${fileReplacements} 处`);
      totalReplacements += fileReplacements;
    }
  } catch (error) {
    console.error(`❌ 处理文件 ${filePath} 时出错:`, error.message);
  }
});

console.log(`\n🎉 完成！总共替换了 ${totalReplacements} 处硬编码样式值`);
console.log('💡 建议：运行后请检查替换结果，确保样式正确');
