<template>
  <div class="song-structure-helper">
    <!-- 模式切换 -->
    <div class="mode-switcher">
      <a-radio-group v-model:value="currentMode" button-style="solid" size="small">
        <a-radio-button value="text">📝 文本模式</a-radio-button>
        <a-radio-button value="visual">🎨 可视化模式</a-radio-button>
      </a-radio-group>
      
      <a-button 
        size="small" 
        type="text" 
        @click="showHelp = !showHelp"
        :icon="showHelp ? 'up' : 'down'"
      >
        {{ showHelp ? '收起帮助' : '查看帮助' }}
      </a-button>
    </div>

    <!-- 帮助说明 -->
    <div v-if="showHelp" class="help-section">
      <a-collapse v-model:activeKey="activeHelpKeys" ghost>
        <a-collapse-panel key="structure" header="🎵 歌曲结构标记说明">
          <div class="structure-explanation">
            <a-table 
              :columns="structureColumns" 
              :data-source="structureData" 
              :pagination="false"
              size="small"
              bordered
            />
          </div>
        </a-collapse-panel>
        
        <a-collapse-panel key="example" header="📝 完整示例">
          <div class="example-section">
            <a-typography-text code>
              <pre>{{ exampleLyrics }}</pre>
            </a-typography-text>
          </div>
        </a-collapse-panel>
      </a-collapse>
    </div>

    <!-- 文本模式 -->
    <div v-if="currentMode === 'text'" class="text-mode">
      <div class="quick-templates">
        <a-space wrap>
          <span style="font-size: 12px; color: #666;">快速模板：</span>
          <a-button 
            v-for="template in templates" 
            :key="template.name"
            size="small" 
            type="dashed"
            @click="applyTemplate(template)"
          >
            {{ template.name }}
          </a-button>
        </a-space>
      </div>
      
      <a-textarea
        v-model:value="textValue"
        :placeholder="placeholderText"
        :rows="8"
        :maxLength="2000"
        show-count
        @change="handleTextChange"
      />
    </div>

    <!-- 可视化模式 -->
    <div v-if="currentMode === 'visual'" class="visual-mode">
      <div class="visual-builder">
        <!-- 结构元素面板 -->
        <div class="elements-panel">
          <a-space wrap>
            <span style="font-size: 12px; color: #666;">拖拽添加：</span>
            <a-tag 
              v-for="element in availableElements" 
              :key="element.tag"
              :color="element.color"
              style="cursor: pointer; margin: 2px;"
              @click="addElement(element)"
            >
              {{ element.label }}
            </a-tag>
          </a-space>
        </div>
        
        <!-- 歌曲结构构建区 -->
        <div class="song-builder">
          <div 
            v-for="(section, index) in songStructure" 
            :key="index"
            class="song-section"
            :class="{ 'has-lyrics': section.lyrics }"
          >
            <div class="section-header">
              <a-tag :color="getElementColor(section.tag)">
                {{ getElementLabel(section.tag) }}
              </a-tag>
              <a-button 
                size="small" 
                type="text" 
                danger
                @click="removeSection(index)"
                :icon="'delete'"
              >
                删除
              </a-button>
            </div>
            
            <div v-if="section.needsLyrics" class="section-content">
              <a-textarea
                v-model:value="section.lyrics"
                :placeholder="`输入${getElementLabel(section.tag)}歌词...`"
                :rows="3"
                :maxLength="500"
                show-count
                @change="updateVisualText"
              />
            </div>
            
            <!-- 不需要歌词的段落显示提示 -->
            <div v-else class="section-no-lyrics">
              <a-typography-text type="secondary">
                🎵 纯音乐段落，无需输入歌词
              </a-typography-text>
            </div>
          </div>
          
          <!-- 空状态 -->
          <div v-if="songStructure.length === 0" class="empty-builder">
            <a-empty description="点击上方标签添加歌曲段落" />
          </div>
        </div>
        
        <!-- 预览文本 -->
        <div class="text-preview">
          <div class="preview-header">
            <span style="font-size: 12px; color: #666;">生成的歌词格式：</span>
            <a-button size="small" @click="copyToClipboard">复制</a-button>
          </div>
          <a-typography-text code>
            <pre>{{ visualToText }}</pre>
          </a-typography-text>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, defineEmits, defineProps } from 'vue'
import { message } from 'ant-design-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

// 响应式数据
const currentMode = ref('text')
const showHelp = ref(false)
const activeHelpKeys = ref(['structure'])
const textValue = ref(props.modelValue)
const songStructure = reactive([])

// 歌曲结构说明数据
const structureColumns = [
  { title: '标记', dataIndex: 'tag', key: 'tag', width: 120 },
  { title: '中文说明', dataIndex: 'label', key: 'label', width: 100 },
  { title: '作用', dataIndex: 'description', key: 'description' },
  { title: '是否需要歌词', dataIndex: 'needsLyrics', key: 'needsLyrics', width: 100 }
]

const structureData = [
  { tag: '[intro-short]', label: '短前奏', description: '3-5秒纯音乐开场', needsLyrics: '否' },
  { tag: '[intro-medium]', label: '中前奏', description: '8-12秒音乐开场', needsLyrics: '否' },
  { tag: '[intro-long]', label: '长前奏', description: '15-20秒音乐开场', needsLyrics: '否' },
  { tag: '[verse]', label: '主歌', description: '叙述性歌词，推进故事', needsLyrics: '是' },
  { tag: '[chorus]', label: '副歌', description: '最抓耳的旋律部分', needsLyrics: '是' },
  { tag: '[bridge]', label: '桥段', description: '转换段落，增加层次', needsLyrics: '是' },
  { tag: '[inst-short]', label: '短间奏', description: '3-5秒纯音乐', needsLyrics: '否' },
  { tag: '[inst-medium]', label: '中间奏', description: '8-12秒纯音乐', needsLyrics: '否' },
  { tag: '[inst-long]', label: '长间奏', description: '15-20秒纯音乐', needsLyrics: '否' },
  { tag: '[outro-short]', label: '短尾奏', description: '3-5秒音乐结尾', needsLyrics: '否' },
  { tag: '[outro-medium]', label: '中尾奏', description: '8-12秒音乐结尾', needsLyrics: '否' },
  { tag: '[outro-long]', label: '长尾奏', description: '15-20秒音乐结尾', needsLyrics: '否' },
  { tag: '[silence]', label: '静音', description: '静音段落', needsLyrics: '否' }
]

// 可用元素 - 与SongGeneration引擎完全兼容
const availableElements = [
  { tag: '[intro-short]', label: '短前奏', color: 'blue', needsLyrics: false },
  { tag: '[intro-medium]', label: '中前奏', color: 'blue', needsLyrics: false },
  { tag: '[intro-long]', label: '长前奏', color: 'blue', needsLyrics: false },
  { tag: '[verse]', label: '主歌', color: 'green', needsLyrics: true },
  { tag: '[chorus]', label: '副歌', color: 'red', needsLyrics: true },
  { tag: '[bridge]', label: '桥段', color: 'purple', needsLyrics: true },
  { tag: '[inst-short]', label: '短间奏', color: 'cyan', needsLyrics: false },
  { tag: '[inst-medium]', label: '中间奏', color: 'cyan', needsLyrics: false },
  { tag: '[inst-long]', label: '长间奏', color: 'cyan', needsLyrics: false },
  { tag: '[outro-short]', label: '短尾奏', color: 'blue', needsLyrics: false },
  { tag: '[outro-medium]', label: '中尾奏', color: 'blue', needsLyrics: false },
  { tag: '[outro-long]', label: '长尾奏', color: 'blue', needsLyrics: false },
  { tag: '[silence]', label: '静音', color: 'gray', needsLyrics: false }
]

// 快速模板 - 使用SongGeneration引擎支持的标记
const templates = [
  {
    name: '流行歌曲',
    content: `[intro-short]

[verse]
在这里写主歌歌词
叙述故事情节

[chorus]
在这里写副歌歌词
最抓耳的部分

[verse]
第二段主歌
继续故事发展

[chorus]
重复副歌部分

[outro-short]`
  },
  {
    name: '简短版',
    content: `[intro-short]

[verse]
简短的歌词内容

[chorus]
核心旋律部分

[outro-short]`
  },
  {
    name: '完整版',
    content: `[intro-medium]

[verse]
第一段主歌歌词

[chorus]
副歌部分

[verse]
第二段主歌

[chorus]
重复副歌

[bridge]
桥段转换

[chorus]
最终副歌

[inst-short]

[chorus]
最后一遍副歌

[outro-medium]`
  }
]

// 示例歌词 - 使用SongGeneration引擎支持的标记
const exampleLyrics = `[intro-short]

[verse]
夜晚的街灯闪烁
我漫步在熟悉的角落
回忆像潮水般涌来

[chorus]
音乐的节奏奏响
我的心却在流浪
没有你的日子很难过

[inst-short]

[chorus]
音乐的节奏奏响
我的心却在流浪
没有你的日子很难过

[outro-short]`

// 占位符文本 - 使用SongGeneration引擎支持的标记
const placeholderText = `请输入歌词，支持以下格式：

[intro-short]

[verse]
夜晚的街灯闪烁
我漫步在熟悉的角落
回忆像潮水般涌来

[chorus]
音乐的节奏奏响
我的心却在流浪
没有你的日子很难过

[inst-short]

[outro-short]

💡 提示：
- 前奏、间奏、尾奏段落为纯音乐，无需输入歌词
- 只有主歌、副歌、桥段需要输入歌词内容`

// 计算属性 - 严格验证歌词格式
const visualToText = computed(() => {
  return songStructure.map(section => {
    let result = section.tag
    
    // 🚨 关键修复：严格检查是否应该包含歌词
    if (section.needsLyrics && section.lyrics && section.lyrics.trim()) {
      result += '\n' + section.lyrics.trim()
    }
    // 对于不需要歌词的段落（前奏、间奏、尾奏），即使用户输入了也不输出
    
    return result
  }).join('\n\n')
})

// 方法
const handleTextChange = () => {
  emit('update:modelValue', textValue.value)
}

const updateVisualText = () => {
  const text = visualToText.value
  textValue.value = text
  emit('update:modelValue', text)
}

const applyTemplate = (template) => {
  textValue.value = template.content
  emit('update:modelValue', template.content)
  message.success(`已应用模板：${template.name}`)
}

const addElement = (element) => {
  songStructure.push({
    tag: element.tag,
    label: element.label,
    needsLyrics: element.needsLyrics,
    lyrics: ''
  })
  updateVisualText()
}

const removeSection = (index) => {
  songStructure.splice(index, 1)
  updateVisualText()
}

const getElementColor = (tag) => {
  const element = availableElements.find(el => el.tag === tag)
  return element ? element.color : 'default'
}

const getElementLabel = (tag) => {
  const element = availableElements.find(el => el.tag === tag)
  return element ? element.label : tag
}

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(visualToText.value)
    message.success('已复制到剪贴板')
  } catch (err) {
    message.error('复制失败')
  }
}

// 监听模式切换
watch(currentMode, (newMode) => {
  if (newMode === 'visual' && songStructure.length === 0) {
    // 如果切换到可视化模式且没有内容，尝试解析文本内容
    parseTextToStructure()
  }
})

// 解析文本内容到结构 - 智能过滤不需要歌词的段落
const parseTextToStructure = () => {
  if (!textValue.value.trim()) return
  
  // 清空现有结构
  songStructure.length = 0
  
  // 按双换行分割段落，确保与后端验证逻辑一致
  const paragraphs = textValue.value.trim().split('\n\n').filter(p => p.trim())
  
  for (let paragraph of paragraphs) {
    const lines = paragraph.trim().split('\n')
    if (lines.length === 0) continue
    
    // 第一行应该是标记
    const tagLine = lines[0].trim()
    const tagMatch = tagLine.match(/^\[([^\]]+)\]$/)
    
    if (tagMatch) {
      const tag = tagLine.toLowerCase() // 转为小写匹配
      const element = availableElements.find(el => el.tag === tag)
      
      if (element) {
        const section = {
          tag: element.tag,
          label: element.label,
          needsLyrics: element.needsLyrics,
          lyrics: ''
        }
        
        // 🚨 关键修复：只有需要歌词的段落才提取歌词内容
        if (element.needsLyrics && lines.length > 1) {
          section.lyrics = lines.slice(1).join('\n').trim()
        }
        // 对于不需要歌词的段落（前奏、间奏、尾奏），即使原文有内容也忽略
        
        songStructure.push(section)
      } else {
        // 未知标记，尝试转换为支持的标记
        const legacyMappings = {
          '[intro]': '[intro-medium]',
          '[outro]': '[outro-medium]',
          '[instrumental]': '[inst-medium]',
          '[inst]': '[inst-medium]'
        }
        
        const mappedTag = legacyMappings[tag]
        if (mappedTag) {
          const mappedElement = availableElements.find(el => el.tag === mappedTag)
          if (mappedElement) {
            songStructure.push({
              tag: mappedElement.tag,
              label: mappedElement.label,
              needsLyrics: mappedElement.needsLyrics,
              lyrics: ''
            })
          }
        }
      }
    }
  }
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  textValue.value = newValue
})

// 初始化
if (props.modelValue) {
  textValue.value = props.modelValue
}
</script>

<style scoped>
.song-structure-helper {
  background: #fafafa;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
}

.mode-switcher {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.help-section {
  margin-bottom: 16px;
  background: white;
  border-radius: 4px;
  padding: 12px;
}

.structure-explanation .ant-table {
  font-size: 12px;
}

.example-section pre {
  background: #f6f8fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
}

.text-mode .quick-templates {
  margin-bottom: 8px;
  padding: 8px;
  background: white;
  border-radius: 4px;
}

.visual-mode .visual-builder {
  background: white;
  border-radius: 4px;
  padding: 16px;
}

.elements-panel {
  margin-bottom: 16px;
  padding: 12px;
  background: #f6f8fa;
  border-radius: 4px;
}

.song-builder {
  min-height: 200px;
  margin-bottom: 16px;
}

.song-section {
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 8px;
  background: #fafafa;
}

.song-section.has-lyrics {
  background: white;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-content {
  margin-top: 8px;
}

.empty-builder {
  text-align: center;
  padding: 40px;
  color: #999;
}

.text-preview {
  background: #f6f8fa;
  border-radius: 4px;
  padding: 12px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.text-preview pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  max-height: 200px;
  overflow-y: auto;
}

.section-no-lyrics {
  margin-top: 8px;
  padding: 12px;
  background: #f6f8fa;
  border-radius: 4px;
  text-align: center;
  border: 1px dashed #d9d9d9;
}
</style> 