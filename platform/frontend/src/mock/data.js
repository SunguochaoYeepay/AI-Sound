// Mock数据模拟

// 可用语音列表
export const mockVoices = [
  { id: 'female_calm', name: '女声-温柔', description: '适合温柔的女性角色' },
  { id: 'female_energetic', name: '女声-活泼', description: '适合活泼的女性角色' },
  { id: 'male_deep', name: '男声-深沉', description: '适合成熟的男性角色' },
  { id: 'male_young', name: '男声-年轻', description: '适合年轻的男性角色' },
  { id: 'child_cute', name: '童声-可爱', description: '适合儿童角色' },
  { id: 'elder_wise', name: '老者-睿智', description: '适合长者角色' }
]

// 已创建的角色列表
export const mockCharacters = [
  {
    id: 1,
    name: '林清雅',
    voiceId: 'female_calm',
    voiceName: '女声-温柔',
    description: '小说女主角，温柔善良',
    testText: '你好，我是林清雅。',
    createdAt: '2024-01-15 10:30:00'
  },
  {
    id: 2,
    name: '张浩然',
    voiceId: 'male_deep',
    voiceName: '男声-深沉',
    description: '小说男主角，成熟稳重',
    testText: '我是张浩然，很高兴认识你。',
    createdAt: '2024-01-15 11:15:00'
  },
  {
    id: 3,
    name: '小灵儿',
    voiceId: 'child_cute',
    voiceName: '童声-可爱',
    description: '灵兽角色，天真可爱',
    testText: '主人，小灵儿想要吃糖果！',
    createdAt: '2024-01-15 14:20:00'
  }
]

// 小说项目列表
export const mockNovelProjects = [
  {
    id: 1,
    name: '修仙传奇第一章',
    fileName: '修仙传奇.txt',
    status: 'completed',
    characterCount: 3,
    audioCount: 15,
    createdAt: '2024-01-15 09:00:00',
    characters: ['林清雅', '张浩然', '小灵儿'],
    chapters: [
      {
        id: 1,
        title: '第一章 初入仙门',
        audioUrl: '/mock/audio/chapter1.wav',
        duration: '15:30',
        status: 'completed'
      }
    ]
  },
  {
    id: 2,
    name: '都市修真第二章',
    fileName: '都市修真.txt',
    status: 'processing',
    characterCount: 2,
    audioCount: 0,
    createdAt: '2024-01-16 10:30:00',
    characters: ['林清雅', '张浩然'],
    chapters: []
  }
]

// TTS历史记录
export const mockTTSHistory = [
  {
    id: 1,
    text: '欢迎使用AI-Sound语音合成平台！',
    voiceId: 'female_calm',
    voiceName: '女声-温柔',
    audioUrl: '/mock/audio/tts1.wav',
    duration: '3.5s',
    createdAt: '2024-01-16 15:30:00'
  },
  {
    id: 2,
    text: '这是一段测试文本，用来验证语音合成效果。',
    voiceId: 'male_deep',
    voiceName: '男声-深沉',
    audioUrl: '/mock/audio/tts2.wav',
    duration: '5.2s',
    createdAt: '2024-01-16 14:15:00'
  }
]

// API模拟函数
export const mockAPI = {
  // TTS合成
  async synthesize(text, voiceId, speed = 1.0, pitch = 1.0) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockAudioUrl = `/mock/audio/generated_${Date.now()}.wav`
        resolve({
          success: true,
          audioUrl: mockAudioUrl,
          duration: `${(text.length * 0.1).toFixed(1)}s`,
          message: '语音合成成功'
        })
      }, 2000) // 模拟2秒生成时间
    })
  },

  // 获取角色列表
  async getCharacters() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          data: mockCharacters
        })
      }, 500)
    })
  },

  // 创建角色
  async createCharacter(character) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const newCharacter = {
          ...character,
          id: Date.now(),
          createdAt: new Date().toLocaleString('zh-CN')
        }
        mockCharacters.push(newCharacter)
        resolve({
          success: true,
          data: newCharacter,
          message: '角色创建成功'
        })
      }, 1000)
    })
  },

  // 删除角色
  async deleteCharacter(id) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const index = mockCharacters.findIndex((c) => c.id === id)
        if (index > -1) {
          mockCharacters.splice(index, 1)
          resolve({
            success: true,
            message: '角色删除成功'
          })
        } else {
          resolve({
            success: false,
            message: '角色不存在'
          })
        }
      }, 500)
    })
  },

  // 解析小说文本
  async parseNovelText(text) {
    return new Promise((resolve) => {
      setTimeout(() => {
        // 模拟解析出的对话和角色
        const dialogues = [
          { speaker: '林清雅', text: '师兄，这里就是传说中的仙门吗？' },
          { speaker: '张浩然', text: '是的，师妹。从今天开始，我们就是仙门弟子了。' },
          { speaker: '小灵儿', text: '主人，这里的灵气好浓郁呀！' },
          { speaker: '林清雅', text: '小灵儿说得对，我感觉整个人都轻松了许多。' }
        ]

        const characters = ['林清雅', '张浩然', '小灵儿']

        resolve({
          success: true,
          data: {
            dialogues,
            characters,
            totalDialogues: dialogues.length
          }
        })
      }, 3000) // 模拟3秒解析时间
    })
  },

  // 生成小说音频
  async generateNovelAudio(projectId, characterMapping) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          data: {
            audioFiles: [
              {
                id: 1,
                title: '第一章 初入仙门',
                audioUrl: '/mock/audio/chapter1.wav',
                duration: '15:30'
              }
            ]
          },
          message: '音频生成成功'
        })
      }, 5000) // 模拟5秒生成时间
    })
  }
}
