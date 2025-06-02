/* global use, db */
// MongoDB索引修复脚本
// 解决 engine_id_1_voice_id_1 索引与模型字段不匹配的问题

// 连接到ai_sound数据库
use('ai_sound');

// 第1步：查看voices集合当前的索引
console.log('=== 当前索引列表 ===');
db.voices.getIndexes().forEach(index => {
    console.log('索引名:', index.name);
    console.log('索引字段:', index.key);
    console.log('是否唯一:', index.unique || false);
    console.log('---');
});

// 第2步：删除有问题的索引（如果存在）
try {
    const result = db.voices.dropIndex("engine_id_1_voice_id_1");
    console.log('✅ 成功删除有问题的索引:', result);
} catch (error) {
    console.log('ℹ️ 索引不存在或删除失败:', error.message);
}

// 第3步：创建正确的索引
try {
    const newIndex = db.voices.createIndex(
        {
            engine_id: 1,
            engine_voice_id: 1
        },
        {
            unique: true,
            name: "engine_id_1_engine_voice_id_1"
        }
    );
    console.log('✅ 成功创建正确的索引:', newIndex);
} catch (error) {
    console.log('❌ 创建索引失败:', error.message);
}

// 第4步：验证修复结果
console.log('\n=== 修复后的索引列表 ===');
db.voices.getIndexes().forEach(index => {
    console.log('索引名:', index.name);
    console.log('索引字段:', index.key);
    console.log('是否唯一:', index.unique || false);
    console.log('---');
});

// 第5步：检查并清理可能的脏数据
const nullRecords = db.voices.countDocuments({
    $or: [
        {engine_voice_id: null},
        {engine_voice_id: {$exists: false}}
    ]
});

if (nullRecords > 0) {
    console.log(`\n⚠️ 发现 ${nullRecords} 条engine_voice_id为空的记录`);
    
    // 修复这些记录
    const updateResult = db.voices.updateMany(
        {
            $or: [
                {engine_voice_id: null},
                {engine_voice_id: {$exists: false}}
            ]
        },
        {
            $set: {engine_voice_id: "default_voice"}
        }
    );
    console.log('✅ 已修复空记录数量:', updateResult.modifiedCount);
} else {
    console.log('\n✅ 没有发现engine_voice_id为空的记录');
}

console.log('\n🎉 数据库索引修复完成！');