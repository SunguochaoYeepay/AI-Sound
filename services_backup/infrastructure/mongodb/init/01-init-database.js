// AI-Sound 数据库初始化脚本
// 创建应用数据库和用户

// 切换到admin数据库
db = db.getSiblingDB('admin');

// 创建应用用户
db.createUser({
  user: 'ai_sound_user',
  pwd: 'ai_sound_pass_2024',
  roles: [
    {
      role: 'readWrite',
      db: 'ai_sound'
    }
  ]
});

// 切换到应用数据库
db = db.getSiblingDB('ai_sound');

// 创建基础集合
db.createCollection('engines');
db.createCollection('voices');
db.createCollection('characters');
db.createCollection('synthesis_tasks');
db.createCollection('system_logs');

// 创建索引
db.engines.createIndex({ "name": 1 }, { unique: true });
db.engines.createIndex({ "status": 1 });
db.engines.createIndex({ "created_at": 1 });

db.voices.createIndex({ "engine_id": 1, "voice_id": 1 }, { unique: true });
db.voices.createIndex({ "language": 1 });
db.voices.createIndex({ "gender": 1 });

db.characters.createIndex({ "name": 1 }, { unique: true });
db.characters.createIndex({ "voice_engine": 1 });

db.synthesis_tasks.createIndex({ "task_id": 1 }, { unique: true });
db.synthesis_tasks.createIndex({ "status": 1 });
db.synthesis_tasks.createIndex({ "created_at": 1 });

db.system_logs.createIndex({ "timestamp": 1 });
db.system_logs.createIndex({ "level": 1 });

// 插入初始数据
db.engines.insertMany([
  {
    name: "MegaTTS3",
    type: "neural_tts",
    status: "available",
    endpoint: "http://host.docker.internal:7929",
    description: "MegaTTS3 神经网络语音合成引擎",
    supported_languages: ["zh-CN", "en-US"],
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    name: "ESPnet",
    type: "neural_tts",
    status: "available", 
    endpoint: "http://espnet-service:9001",
    description: "ESPnet 端到端语音处理工具包",
    supported_languages: ["zh-CN", "en-US", "ja-JP"],
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    name: "Bert-VITS2",
    type: "neural_tts",
    status: "available",
    endpoint: "http://bert-vits2-service:9932", 
    description: "Bert-VITS2 高质量语音合成引擎",
    supported_languages: ["zh-CN", "ja-JP"],
    created_at: new Date(),
    updated_at: new Date()
  }
]);

print("AI-Sound 数据库初始化完成");
print("- 创建了应用用户: ai_sound_user");
print("- 创建了基础集合和索引");
print("- 插入了初始引擎数据"); 