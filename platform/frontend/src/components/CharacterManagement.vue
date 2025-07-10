<template>
  <a-drawer
    :open="visible"
    title="🎭 段落角色"
    placement="right"
    :width="800"
    @close="handleClose"
  >
    <template #extra>
      <a-space>
        <a-button @click="refreshCharacters" :loading="loadingCharacters">
          🔄 刷新
        </a-button>
        <a-button @click="rebuildCharacterSummary" :loading="rebuildingCharacters">
          🔧 重建汇总
        </a-button>
        <a-button type="primary" @click="goToCharacterManagement">
          🎭 管理角色库
        </a-button>
      </a-space>
    </template>

    <div class="character-management">
      <!-- 角色统计卡片 -->
      <div class="character-stats">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-statistic title="检测到的角色" :value="characterSummary.character_count || 0" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="已创建角色" :value="characterLibraryCount || 0" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="分析章节数" :value="characterSummary.total_chapters_analyzed || 0" />
          </a-col>
          <a-col :span="6">
            <a-statistic 
              title="角色库覆盖率" 
              :value="characterSummary.character_count > 0 ? Math.round((characterLibraryCount / characterSummary.character_count) * 100) : 0" 
              suffix="%" 
            />
          </a-col>
        </a-row>
      </div>

      <!-- 加载状态 -->
      <div v-if="loadingCharacters" class="loading-characters">
        <a-spin size="large" tip="加载角色信息中...">
          <div style="height: 200px;"></div>
        </a-spin>
      </div>

      <!-- 角色列表 -->
      <div v-else-if="characterSummary.characters && characterSummary.characters.length > 0" class="character-list">
        <div class="list-header">
          <h3>角色列表</h3>
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索角色名称..."
            style="width: 200px;"
            allowClear
          />
        </div>

        <div class="characters-grid">
          <div
            v-for="(character, index) in filteredCharacters"
            :key="character.name"
            class="character-card"
          >
            <!-- 角色头像和基本信息 -->
            <div class="character-header">
              <div class="character-avatar">
                <a-avatar 
                  :size="48" 
                  :src="getCharacterAvatar(character.name)"
                  :style="{ backgroundColor: getCharacterColor(character.name) }"
                >
                  {{ getCharacterInitial(character.name) }}
                </a-avatar>
              </div>
              
              <div class="character-info">
                <div class="character-name">
                  <span class="name-text">{{ character.name }}</span>
                  <span class="character-rank">
                    {{ getCharacterRank(character, index) }}
                  </span>
                </div>
                <div class="character-tags">
                  <a-tag v-if="character.gender" size="small" :color="getGenderColor(character.gender)">
                    {{ getGenderText(character.gender) }}
                  </a-tag>
                  <a-tag :color="getCharacterStatusColor(character.name)" size="small">
                    {{ getCharacterStatusText(character.name) }}
                  </a-tag>
                </div>
              </div>
            </div>
            
            <!-- 角色详情 -->
            <div class="character-details">
              <div v-if="character.description" class="character-description">
                {{ character.description }}
              </div>
              <div v-if="character.personality" class="character-personality">
                <strong>性格：</strong>{{ character.personality }}
              </div>
              <div class="character-stats">
                <a-row :gutter="8">
                  <a-col :span="12">
                    <a-statistic 
                      title="出现次数" 
                      :value="character.total_appearances || 1" 
                      :value-style="{ fontSize: '14px' }"
                    />
                  </a-col>
                  <a-col :span="12">
                    <a-statistic 
                      title="涉及章节" 
                      :value="(character.chapters || []).length" 
                      :value-style="{ fontSize: '14px' }"
                    />
                  </a-col>
                </a-row>
              </div>
            </div>
            
            <!-- 角色状态和操作 -->
            <div class="character-actions">
              <div class="status-info">
                <div v-if="getCharacterFromLibrary(character.name)" class="library-info">
                  <div class="voice-info">
                    <span class="voice-label">音频配置：</span>
                    <a-tag v-if="getCharacterFromLibrary(character.name).is_voice_configured" color="green">
                      已配置
                    </a-tag>
                    <a-tag v-else color="orange">
                      需配置
                    </a-tag>
                  </div>
                  <div class="quality-info">
                    <span class="quality-label">质量评分：</span>
                    <a-rate 
                      :value="getCharacterFromLibrary(character.name).quality_score || 3" 
                      :count="5" 
                      disabled 
                      style="font-size: 12px;"
                    />
                    <span class="quality-score">{{ getCharacterFromLibrary(character.name).quality_score || 3 }}/5</span>
                  </div>
                </div>
                <div v-else class="not-in-library">
                  <a-tag color="red">未创建</a-tag>
                  <span class="hint">角色库中不存在此角色</span>
                </div>
              </div>
              
              <div class="action-buttons">
                <a-button 
                  v-if="getCharacterFromLibrary(character.name)"
                  type="primary" 
                  size="small"
                  @click="editCharacterInLibrary(character.name)"
                >
                  ✏️ 编辑
                </a-button>
                <a-button 
                  v-else
                  type="primary" 
                  size="small"
                  @click="createCharacterInLibrary(character.name)"
                >
                  ➕ 创建
                </a-button>
                <a-button 
                  v-if="getCharacterFromLibrary(character.name)?.is_voice_configured"
                  size="small"
                  @click="testCharacterVoice(character.name)"
                  :loading="testingVoice === character.name"
                >
                  🔊 试听
                </a-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="no-characters">
        <a-empty
          description="暂无检测到的角色"
        >
          <p>请先对章节进行智能准备，系统会自动识别角色信息</p>
        </a-empty>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { booksAPI, charactersAPI } from '../api'
import { useAudioPlayerStore } from '@/stores/audioPlayer'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  bookId: {
    type: [String, Number],
    default: null
  }
})

const emit = defineEmits(['update:visible'])

const router = useRouter()
const audioStore = useAudioPlayerStore()

// 响应式数据
const loadingCharacters = ref(false)
const rebuildingCharacters = ref(false)
const testingVoice = ref(null)
const searchKeyword = ref('')

const characterSummary = ref({
  characters: [],
  voice_mappings: {},
  character_count: 0,
  configured_count: 0,
  total_chapters_analyzed: 0
})

const characterLibrary = ref([])
const characterLibraryCount = ref(0)

// 过滤后的角色列表
const filteredCharacters = computed(() => {
  if (!searchKeyword.value) return characterSummary.value.characters || []
  
  const keyword = searchKeyword.value.toLowerCase()
  return (characterSummary.value.characters || []).filter(character => 
    character.name.toLowerCase().includes(keyword) ||
    (character.description && character.description.toLowerCase().includes(keyword))
  )
})

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (newVal && props.bookId) {
    loadCharacters()
  }
})

// 监听bookId变化
watch(() => props.bookId, (newVal) => {
  if (newVal && props.visible) {
    loadCharacters()
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const loadCharacters = async () => {
  if (!props.bookId) return
  
  loadingCharacters.value = true
  try {
    // 加载书籍角色汇总
    const bookCharactersResponse = await booksAPI.getBookCharacters(props.bookId)
    if (bookCharactersResponse.data && bookCharactersResponse.data.success) {
      characterSummary.value = bookCharactersResponse.data.data
    } else {
      characterSummary.value = {
        characters: [],
        voice_mappings: {},
        character_count: 0,
        configured_count: 0,
        total_chapters_analyzed: 0
      }
    }
    
    // 加载角色库中的角色（按书籍过滤）
    const libraryResponse = await charactersAPI.getCharacters({ 
      book_id: props.bookId,
      management_type: 'library'
    })
    if (libraryResponse.data && libraryResponse.data.success) {
      characterLibrary.value = libraryResponse.data.data || []
      characterLibraryCount.value = characterLibrary.value.length
    } else {
      characterLibrary.value = []
      characterLibraryCount.value = 0
    }
    
    console.log('角色数据加载成功:', {
      bookId: props.bookId,
      characterSummary: characterSummary.value,
      characterLibrary: characterLibrary.value
    })
  } catch (error) {
    console.error('加载角色数据失败:', error)
    message.error('加载角色数据失败')
    // 重置为空数据
    characterSummary.value = {
      characters: [],
      voice_mappings: {},
      character_count: 0,
      configured_count: 0,
      total_chapters_analyzed: 0
    }
    characterLibrary.value = []
    characterLibraryCount.value = 0
  } finally {
    loadingCharacters.value = false
  }
}

const refreshCharacters = async () => {
  await loadCharacters()
}

const rebuildCharacterSummary = async () => {
  if (!props.bookId) return
  
  rebuildingCharacters.value = true
  try {
    const response = await booksAPI.rebuildCharacterSummary(props.bookId)
    if (response.data && response.data.success) {
      message.success('角色汇总重建成功')
      await loadCharacters()
    } else {
      message.error(response.data?.message || '重建角色汇总失败')
    }
  } catch (error) {
    console.error('重建角色汇总失败:', error)
    message.error('重建角色汇总失败')
  } finally {
    rebuildingCharacters.value = false
  }
}

const goToCharacterManagement = () => {
  router.push('/characters')
}

const getCharacterAvatar = (name) => {
  // 从角色配音库获取头像URL
  const libraryChar = getCharacterFromLibrary(name)
  if (libraryChar && libraryChar.avatar_path) {
    // 生成头像URL
    const filename = libraryChar.avatar_path.split('/').pop()
    return `/api/v1/avatars/${filename}`
  }
  return null
}

const getCharacterColor = (name) => {
  const colors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']
  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[hash % colors.length]
}

const getCharacterInitial = (name) => {
  return name.charAt(0)
}

const getCharacterRank = (character, index) => {
  const ranks = ['👑', '⭐', '✨', '📖']
  if (index === 0) return ranks[0] + '主角'
  if (index === 1) return ranks[1] + '重要配角'
  if (index <= 3) return ranks[2] + '一般配角'
  return ranks[3] + '其他'
}

const getGenderColor = (gender) => {
  const colors = {
    '男': 'blue',
    'male': 'blue',
    '女': 'pink', 
    'female': 'pink',
    '未知': 'default',
    'unknown': 'default',
    'neutral': 'purple'
  }
  return colors[gender] || 'default'
}

const getGenderText = (gender) => {
  const genderMap = {
    'male': '男',
    'female': '女',
    'neutral': '中性',
    'unknown': '未知',
    '男': '男',
    '女': '女',
    '中性': '中性',
    '未知': '未知'
  }
  return genderMap[gender] || gender || '未知'
}

const getCharacterStatusColor = (name) => {
  const libraryChar = getCharacterFromLibrary(name)
  if (!libraryChar) return 'red'
  return libraryChar.is_voice_configured ? 'green' : 'orange'
}

const getCharacterStatusText = (name) => {
  const libraryChar = getCharacterFromLibrary(name)
  if (!libraryChar) return '未创建'
  return libraryChar.is_voice_configured ? '已配置' : '需配置'
}

const getCharacterFromLibrary = (name) => {
  return characterLibrary.value.find(char => char.name === name)
}

const editCharacterInLibrary = (name) => {
  const libraryChar = getCharacterFromLibrary(name)
  if (libraryChar) {
    router.push(`/characters/edit/${libraryChar.id}`)
  }
}

const createCharacterInLibrary = async (name) => {
  try {
    const characterData = characterSummary.value.characters.find(char => char.name === name)
    if (!characterData) {
      message.error('未找到角色信息')
      return
    }
    
    const response = await charactersAPI.createCharacterRecord({
      name: characterData.name,
      description: characterData.description || '',
      book_id: props.bookId,
      voice_profile: characterData.gender || '',
      voice_config: JSON.stringify({
        gender: characterData.gender,
        personality: characterData.personality
      })
    })
    
    if (response.data && response.data.success) {
      message.success(`角色 "${name}" 创建成功`)
      await loadCharacters() // 重新加载数据
    } else {
      message.error(response.data?.message || '创建角色失败')
    }
  } catch (error) {
    console.error('创建角色失败:', error)
    message.error('创建角色失败')
  }
}

const testCharacterVoice = async (name) => {
  testingVoice.value = name
  try {
    const libraryChar = getCharacterFromLibrary(name)
    if (!libraryChar) {
      // 如果角色不在库中，使用浏览器TTS进行简单试听
      await playSimpleVoiceTest(name)
      return
    }
    
    const response = await charactersAPI.testVoiceSynthesis(libraryChar.id, {
      text: '这是一个声音测试，用于验证角色的声音效果。'
    })
    
    if (response.data && response.data.success && response.data.audioUrl) {
      // 使用音频播放器播放
      const audioInfo = {
        id: `character_test_${name}_${Date.now()}`,
        title: `${name} - 声音试听`,
        url: response.data.audioUrl,
        type: 'character_test',
        metadata: {
          characterName: name,
          voiceId: libraryChar.id
        }
      }
      
      await audioStore.playAudio(audioInfo)
      message.success(`正在播放角色"${name}"的声音`)
    } else {
      message.error(response.data?.message || '生成试听音频失败')
    }
  } catch (error) {
    console.error('声音测试失败:', error)
    message.error('声音测试失败')
  } finally {
    testingVoice.value = null
  }
}

// 简单的声音测试（使用浏览器TTS）
const playSimpleVoiceTest = async (characterName) => {
  try {
    if ('speechSynthesis' in window) {
      // 停止当前播放
      window.speechSynthesis.cancel()
      
      const text = `你好，我是${characterName}。这是一段声音测试。`
      const utterance = new SpeechSynthesisUtterance(text)
      
      // 根据角色名称选择合适的声音
      const voices = window.speechSynthesis.getVoices()
      if (voices.length > 0) {
        // 尝试为不同角色选择不同的声音
        if (characterName.includes('女') || characterName.includes('小') || characterName.includes('妹')) {
          const femaleVoice = voices.find(voice => voice.name.includes('Female') || voice.name.includes('女'))
          if (femaleVoice) utterance.voice = femaleVoice
        } else if (characterName.includes('男') || characterName.includes('先生')) {
          const maleVoice = voices.find(voice => voice.name.includes('Male') || voice.name.includes('男'))
          if (maleVoice) utterance.voice = maleVoice
        }
      }
      
      utterance.rate = 0.9
      utterance.pitch = 1.0
      utterance.volume = 0.8
      
      utterance.onstart = () => {
        console.log(`[CharacterManagement] 开始播放: ${characterName}`)
      }
      
      utterance.onend = () => {
        console.log(`[CharacterManagement] 播放完成: ${characterName}`)
      }
      
      utterance.onerror = (error) => {
        console.error('[CharacterManagement] 播放错误:', error)
        message.error('声音播放失败')
      }
      
      window.speechSynthesis.speak(utterance)
      message.info(`正在播放角色"${characterName}"的声音（浏览器TTS）`)
    } else {
      message.warning('您的浏览器不支持语音合成功能')
    }
  } catch (error) {
    console.error('[CharacterManagement] 简单声音测试失败:', error)
    message.error('声音测试失败')
  }
}
</script>

<style scoped>
.character-management {
  padding: 16px 0;
}

.character-stats {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.loading-characters {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.character-list {
  margin-top: 16px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.list-header h3 {
  margin: 0;
  color: #1f2937;
}

.characters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.character-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.character-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.character-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.character-avatar {
  flex-shrink: 0;
}

.character-info {
  flex: 1;
}

.character-name {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.name-text {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.character-rank {
  font-size: 12px;
  color: #6b7280;
}

.character-tags {
  display: flex;
  gap: 4px;
}

.character-details {
  margin-bottom: 12px;
}

.character-description {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
  line-height: 1.4;
}

.character-personality {
  font-size: 13px;
  color: #4b5563;
  margin-bottom: 8px;
}

.character-stats {
  margin-bottom: 12px;
}

.character-actions {
  border-top: 1px solid #f3f4f6;
  padding-top: 12px;
}

.status-info {
  margin-bottom: 12px;
}

.library-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.voice-info,
.quality-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.voice-label,
.quality-label {
  color: #6b7280;
  min-width: 60px;
}

.quality-score {
  font-size: 11px;
  color: #6b7280;
}

.not-in-library {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hint {
  font-size: 12px;
  color: #9ca3af;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.no-characters {
  text-align: center;
  padding: 40px 20px;
}

.no-characters p {
  color: #6b7280;
  margin: 8px 0 0 0;
}
</style> 