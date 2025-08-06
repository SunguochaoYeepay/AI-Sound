<template>
  <a-drawer
    :open="visible"
    title="智能角色发现"
    width="1000"
    placement="right"
    @close="$emit('close')"
  >
    <div class="smart-discovery-container">
      <!-- 步骤条 -->
      <a-steps :current="currentStep" class="discovery-steps" :items="steps" />

      <!-- 步骤内容 -->
      <div class="step-content">
        <!-- 步骤1: 选择书籍 -->
        <div v-if="currentStep === 0" class="step-panel">
          <div class="step-header">
            <h3>选择书籍项目</h3>
            <p>请选择要分析角色的书籍项目</p>
          </div>

          <div class="book-selection">
            <a-spin :spinning="booksLoading">
              <div v-if="booksData.length === 0" class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="#d1d5db">
                  <path
                    d="M19,3H5C3.9,3 3,3.9 3,5V19C3,20.1 3.9,21 5,21H19C20.1,21 21,20.1 21,19V5C21,3.9 20.1,3 19,3M19,19H5V5H19V19Z"
                  />
                </svg>
                <p>暂无可用的书籍项目</p>
                <a-button type="link" @click="$emit('load-books')">刷新</a-button>
              </div>

              <div v-else class="books-grid">
                <div
                  v-for="book in booksData"
                  :key="book.id"
                  class="book-card"
                  :class="{ selected: selectedBook?.id === book.id }"
                  @click="$emit('select-book', book)"
                >
                  <div class="book-icon">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                      <path
                        d="M19,3H5C3.9,3 3,3.9 3,5V19C3,20.1 3.9,21 5,21H19C20.1,21 21,20.1 21,19V5C21,3.9 20.1,3 19,3M19,19H5V5H19V19Z"
                      />
                    </svg>
                  </div>
                  <div class="book-info">
                    <h4>{{ book.title || '未命名书籍' }}</h4>
                    <p>{{ book.author || '未知作者' }}</p>
                    <div class="book-stats">
                      <span>{{ book.total_chapters || book.chapter_count || book.chapterCount || 0 }} 章节</span>
                      <span>{{ formatNumber(book.word_count || book.wordCount || 0) }} 字</span>
                    </div>
                    <div class="book-meta">
                      <span class="book-status">{{ getBookStatusText(book.status) }}</span>
                      <span class="book-id">ID: {{ book.id }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </a-spin>
          </div>

          <div class="step-actions">
            <a-button @click="$emit('close')">取消</a-button>
            <a-button type="primary" :disabled="!selectedBook" @click="$emit('next-step')">
              下一步：选择章节
            </a-button>
          </div>
        </div>

        <!-- 步骤2: 选择章节 -->
        <div v-if="currentStep === 1" class="step-panel">
          <div class="step-header">
            <h3>选择分析章节</h3>
            <p>从《{{ selectedBook?.title }}》中选择要分析的章节</p>
          </div>

          <div class="chapter-selection">
            <div class="selection-controls">
              <a-checkbox
                :indeterminate="chapterIndeterminate"
                :checked="chapterCheckAll"
                @change="$emit('toggle-all-chapters')"
              >
                全选
              </a-checkbox>
              <span class="selection-info">
                已选择 {{ selectedChapters.length }} / {{ chaptersData.length }} 章节
              </span>
            </div>

            <a-spin :spinning="chaptersLoading">
              <div class="chapters-list">
                <div class="chapters-grid">
                  <div
                    v-for="chapter in chaptersData"
                    :key="chapter.id"
                    class="chapter-item"
                    :class="{ selected: selectedChapters.some((c) => c.id === chapter.id) }"
                    @click="$emit('toggle-chapter', chapter)"
                  >
                    <a-checkbox
                      :checked="selectedChapters.some((c) => c.id === chapter.id)"
                      @click.stop="$emit('toggle-chapter', chapter)"
                    >
                      <div class="chapter-content">
                        <div class="chapter-title">
                          第{{ chapter.chapter_number }}章
                          {{ chapter.title || chapter.chapter_title || '未命名章节' }}
                        </div>
                        <div class="chapter-meta">
                          字数: {{ formatNumber(chapter.word_count || 0) }} | 状态:
                          {{ getChapterStatusText(chapter.analysis_status || chapter.status) }}
                        </div>
                      </div>
                    </a-checkbox>
                  </div>
                </div>
              </div>
            </a-spin>
          </div>

          <div class="step-actions">
            <a-button @click="$emit('prev-step')">上一步</a-button>
            <a-button
              type="primary"
              :disabled="selectedChapters.length === 0"
              @click="$emit('analyze-characters')"
            >
              开始分析角色
            </a-button>
          </div>
        </div>

        <!-- 步骤3: 角色分析 -->
        <div v-if="currentStep === 2" class="step-panel">
          <div class="step-header">
            <h3>角色分析中</h3>
            <p>正在使用编程识别规则分析选定章节中的角色...</p>
          </div>

          <div class="analysis-progress">
            <a-progress
              :percent="analysisProgress"
              :status="analysisStatus"
              :show-info="true"
            />
            <p class="progress-text">{{ analysisText }}</p>
          </div>

          <div v-if="analysisComplete" class="analysis-results">
            <div class="results-summary">
              <div class="statistics-grid">
                <a-statistic title="发现角色" :value="discoveredCharacters.length" />
                <a-statistic title="主要角色" :value="mainCharactersCount" />
                <a-statistic title="分析章节" :value="selectedChapters.length" />
              </div>
            </div>

            <div class="characters-preview">
              <h4>发现的角色预览</h4>
              <div class="characters-list">
                <div
                  v-for="character in discoveredCharacters"
                  :key="character.name"
                  class="character-preview-item"
                >
                  <div
                    class="character-avatar"
                    :style="{
                      background: character.avatarUrl
                        ? 'transparent'
                        : character.recommended_config.color
                    }"
                  >
                    <img
                      v-if="character.avatarUrl"
                      :src="character.avatarUrl"
                      :alt="character.name"
                      class="avatar-image"
                    />
                    <span v-else>{{ character.name.charAt(0) }}</span>
                  </div>
                  <div class="character-info">
                    <div class="character-name">
                      {{ character.name }}
                      <a-tooltip
                        v-if="character.exists_in_library"
                        title="此角色已存在于角色库中"
                      >
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="#1890ff"
                          style="margin-left: 4px"
                        >
                          <path
                            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
                          />
                        </svg>
                      </a-tooltip>
                    </div>
                    <div class="character-meta">
                      {{ character.recommended_config.gender === 'male' ? '男性' : '女性' }} |
                      {{ character.recommended_config.personality_description }} | 出现
                      {{ character.frequency }} 次
                      <span v-if="character.exists_in_library && character.existing_config">
                        | 质量评分: {{ character.existing_config.quality || 'N/A' }} | 使用:
                        {{ character.existing_config.usageCount || 0 }}次
                      </span>
                    </div>
                  </div>
                  <div class="character-status">
                    <a-tag v-if="character.is_main_character" color="blue">主要角色</a-tag>
                    <a-tag v-if="character.exists_in_library" color="green">已配置</a-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="step-actions">
            <a-button @click="$emit('prev-step')" :disabled="!analysisComplete">重新选择</a-button>
            <a-button type="primary" :disabled="!analysisComplete" @click="$emit('next-step')">
              配置角色信息
            </a-button>
          </div>
        </div>

        <!-- 步骤4: 批量配置 -->
        <div v-if="currentStep === 3" class="step-panel">
          <div class="step-header">
            <h3>批量配置角色</h3>
            <p>为发现的角色配置详细信息，已存在的角色会显示当前配置（无法选择创建）</p>
          </div>

          <div class="batch-config">
            <div class="config-controls">
              <a-checkbox
                :indeterminate="configIndeterminate"
                :checked="configCheckAll"
                @change="$emit('check-all-configs')"
              >
                全选
              </a-checkbox>
              <span class="selection-info"> 将创建 {{ selectedConfigs.length }} 个新角色 </span>
            </div>

            <div class="config-list">
              <a-checkbox-group :value="selectedConfigs" class="config-grid" @change="$emit('update:selectedConfigs', $event)">
                <div
                  v-for="character in newCharacters"
                  :key="character.name"
                  class="config-item"
                  :class="{ 'existing-character': character.exists_in_library }"
                >
                  <a-checkbox :value="character.name" :disabled="character.exists_in_library">
                    <div class="config-card">
                      <div class="config-header">
                        <div
                          class="character-avatar"
                          :style="{
                            background: character.avatarUrl
                              ? 'transparent'
                              : character.recommended_config.color
                          }"
                        >
                          <img
                            v-if="character.avatarUrl"
                            :src="character.avatarUrl"
                            :alt="character.name"
                            class="avatar-image"
                          />
                          <span v-else>{{ character.name.charAt(0) }}</span>
                        </div>
                        <div class="character-basic">
                          <h4>
                            {{ character.name }}
                            <a-tag v-if="character.exists_in_library" color="green" size="small">已配置</a-tag>
                          </h4>
                          <p>
                            {{
                              character.existing_config?.description ||
                              character.recommended_config.description
                            }}
                          </p>
                        </div>
                      </div>

                      <div class="config-details">
                        <div v-if="character.exists_in_library" class="existing-character-info">
                          <a-alert
                            message="角色已存在于角色库中，无需重复创建"
                            type="info"
                            show-icon
                            :closable="false"
                            style="margin-bottom: 16px"
                          />
                          <div class="existing-config-display">
                            <a-descriptions :column="2" size="small">
                              <a-descriptions-item label="性别">
                                {{
                                  character.existing_config?.type === 'male'
                                    ? '男性'
                                    : character.existing_config?.type === 'female'
                                      ? '女性'
                                      : '未设置'
                                }}
                              </a-descriptions-item>
                              <a-descriptions-item label="状态">
                                <a-tag
                                  :color="
                                    character.existing_config?.status === 'active'
                                      ? 'green'
                                      : 'orange'
                                  "
                                >
                                  {{
                                    character.existing_config?.status === 'active'
                                      ? '可用'
                                      : '需配置'
                                  }}
                                </a-tag>
                              </a-descriptions-item>
                              <a-descriptions-item label="质量评分">
                                <a-rate
                                  :value="character.existing_config?.quality || 0"
                                  disabled
                                  allow-half
                                  size="small"
                                />
                                <span style="margin-left: 8px">{{ character.existing_config?.quality || 0 }} 星</span>
                              </a-descriptions-item>
                              <a-descriptions-item label="使用次数">
                                {{ character.existing_config?.usageCount || 0 }} 次
                              </a-descriptions-item>
                              <a-descriptions-item label="描述" :span="2">
                                {{ character.existing_config?.description || '暂无描述' }}
                              </a-descriptions-item>
                            </a-descriptions>
                          </div>
                        </div>
                        <a-form v-else layout="vertical" size="small">
                          <a-row :gutter="16">
                            <a-col :span="8">
                              <a-form-item label="性别">
                                <a-select v-model:value="character.config.gender" size="small">
                                  <a-select-option value="male">男性</a-select-option>
                                  <a-select-option value="female">女性</a-select-option>
                                </a-select>
                              </a-form-item>
                            </a-col>
                            <a-col :span="8">
                              <a-form-item label="性格">
                                <a-select v-model:value="character.config.personality" size="small">
                                  <a-select-option value="gentle">温柔</a-select-option>
                                  <a-select-option value="fierce">刚烈</a-select-option>
                                  <a-select-option value="calm">沉稳</a-select-option>
                                  <a-select-option value="lively">活泼</a-select-option>
                                </a-select>
                              </a-form-item>
                            </a-col>
                            <a-col :span="8">
                              <a-form-item label="颜色">
                                <a-select v-model:value="character.config.color" size="small">
                                  <a-select-option
                                    v-for="color in colorOptions"
                                    :key="color"
                                    :value="color"
                                  >
                                    <div style="display: flex; align-items: center; gap: 8px">
                                      <div
                                        style="width: 16px; height: 16px; border-radius: 4px"
                                        :style="{ background: color }"
                                      ></div>
                                      {{ color }}
                                    </div>
                                  </a-select-option>
                                </a-select>
                              </a-form-item>
                            </a-col>
                          </a-row>

                          <a-form-item label="描述">
                            <a-textarea
                              v-model:value="character.config.description"
                              :rows="2"
                              size="small"
                              placeholder="角色描述..."
                            />
                          </a-form-item>

                          <a-form-item label="音频配置">
                            <a-alert
                              message="角色创建后，请在角色管理页面配置音频文件"
                              type="info"
                              show-icon
                              :closable="false"
                              style="margin-bottom: 0"
                            />
                            <p style="margin-top: 8px; color: #666; font-size: 12px">
                              音频文件配置包括：参考音频文件(.wav/.mp3/.m4a/.flac)和对应的Latent特征文件(.npy)
                            </p>
                          </a-form-item>
                        </a-form>
                      </div>
                    </div>
                  </a-checkbox>
                </div>
              </a-checkbox-group>
            </div>
          </div>

          <div class="step-actions">
            <a-button @click="$emit('prev-step')">重新分析</a-button>
            <a-button
              type="primary"
              :loading="creatingCharacters"
              :disabled="selectedConfigs.length === 0"
              @click="$emit('create-characters')"
            >
              创建 {{ selectedConfigs.length }} 个角色
            </a-button>
          </div>
        </div>

        <!-- 步骤5: 创建完成 -->
        <div v-if="currentStep === 4" class="step-panel">
          <div class="step-header">
            <div class="success-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="#10b981">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
              </svg>
            </div>
            <h3>创建完成</h3>
            <p>成功创建了 {{ createdCharacters.length }} 个角色</p>
          </div>

          <div class="creation-results">
            <div class="results-summary">
              <a-alert
                message="角色创建成功"
                :description="creationSummary"
                type="success"
                show-icon
              />
            </div>

            <div class="created-characters">
              <h4>已创建的角色</h4>
              <div class="characters-list">
                <div
                  v-for="character in createdCharacters"
                  :key="character.id"
                  class="created-character-item"
                >
                  <div class="character-avatar" :style="{ background: character.color }">
                    {{ character.name.charAt(0) }}
                  </div>
                  <div class="character-info">
                    <div class="character-name">{{ character.name }}</div>
                    <div class="character-meta">
                      {{ character.type === 'male' ? '男性' : '女性' }} |
                      {{ character.description }}
                    </div>
                    <div class="character-files">
                      <a-tag v-if="character.hasAudio" color="green" size="small">
                        <template #icon>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                            <path
                              d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
                            />
                          </svg>
                        </template>
                        音频已上传
                      </a-tag>
                      <a-tag v-if="character.hasLatent" color="blue" size="small">
                        <template #icon>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                            <path
                              d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"
                            />
                          </svg>
                        </template>
                        Latent已上传
                      </a-tag>
                      <a-tag v-if="character.status === 'active'" color="success" size="small">
                        可用
                      </a-tag>
                      <a-tag v-else color="warning" size="small"> 需要音频 </a-tag>
                    </div>
                  </div>
                  <div class="character-actions">
                    <a-button
                      v-if="character.status !== 'active'"
                      size="small"
                      @click="$emit('edit-character', character)"
                    >
                      上传音频
                    </a-button>
                    <a-button
                      v-else
                      size="small"
                      type="primary"
                      @click="$emit('edit-character', character)"
                    >
                      编辑配置
                    </a-button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="step-actions">
            <a-button @click="$emit('close')">关闭</a-button>
            <a-button type="primary" @click="$emit('start-new-discovery')"> 发现更多角色 </a-button>
          </div>
        </div>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  currentStep: {
    type: Number,
    default: 0
  },
  steps: {
    type: Array,
    default: () => []
  },
  booksData: {
    type: Array,
    default: () => []
  },
  booksLoading: {
    type: Boolean,
    default: false
  },
  selectedBook: {
    type: Object,
    default: null
  },
  chaptersData: {
    type: Array,
    default: () => []
  },
  chaptersLoading: {
    type: Boolean,
    default: false
  },
  selectedChapters: {
    type: Array,
    default: () => []
  },
  chapterIndeterminate: {
    type: Boolean,
    default: false
  },
  chapterCheckAll: {
    type: Boolean,
    default: false
  },
  analysisProgress: {
    type: Number,
    default: 0
  },
  analysisStatus: {
    type: String,
    default: 'active'
  },
  analysisText: {
    type: String,
    default: ''
  },
  analysisComplete: {
    type: Boolean,
    default: false
  },
  discoveredCharacters: {
    type: Array,
    default: () => []
  },
  mainCharactersCount: {
    type: Number,
    default: 0
  },
  newCharacters: {
    type: Array,
    default: () => []
  },
  selectedConfigs: {
    type: Array,
    default: () => []
  },
  configIndeterminate: {
    type: Boolean,
    default: false
  },
  configCheckAll: {
    type: Boolean,
    default: false
  },
  creatingCharacters: {
    type: Boolean,
    default: false
  },
  createdCharacters: {
    type: Array,
    default: () => []
  },
  creationSummary: {
    type: String,
    default: ''
  },
  colorOptions: {
    type: Array,
    default: () => [
      '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444',
      '#ec4899', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'
    ]
  }
})

// Emits
const emit = defineEmits([
  'close',
  'load-books',
  'select-book',
  'next-step',
  'prev-step',
  'toggle-all-chapters',
  'toggle-chapter',
  'analyze-characters',
  'check-all-configs',
  'create-characters',
  'edit-character',
  'start-new-discovery',
  'update:selectedConfigs'
])

// Methods
const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

const getBookStatusText = (status) => {
  const statusMap = {
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
    'pending': '待处理'
  }
  return statusMap[status] || status
}

const getChapterStatusText = (status) => {
  const statusMap = {
    'analyzed': '已分析',
    'processing': '分析中',
    'pending': '待分析',
    'failed': '分析失败'
  }
  return statusMap[status] || status
}
</script>

<style scoped>
.smart-discovery-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.discovery-steps {
  margin-bottom: 24px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.step-content {
  flex: 1;
  overflow-y: auto;
}

.step-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.step-header {
  text-align: center;
  margin-bottom: 24px;
}

.step-header h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.step-header p {
  margin: 0;
  color: #6b7280;
}

.success-icon {
  text-align: center;
  margin-bottom: 16px;
}

/* 书籍选择 */
.book-selection {
  flex: 1;
  margin-bottom: 24px;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: #6b7280;
}

.empty-state p {
  margin: 16px 0;
  font-size: 16px;
}

.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.book-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  gap: 12px;
}

.book-card:hover {
  border-color: #8b5cf6;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
}

.book-card.selected {
  border-color: #8b5cf6;
  background: #f8f7ff;
}

.book-icon {
  flex-shrink: 0;
  color: #8b5cf6;
}

.book-info {
  flex: 1;
}

.book-info h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.book-info p {
  margin: 0 0 8px 0;
  color: #6b7280;
  font-size: 14px;
}

.book-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #6b7280;
}

.book-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.book-status {
  color: #10b981;
  font-weight: 500;
}

.book-id {
  color: #9ca3af;
}

/* 章节选择 */
.chapter-selection {
  flex: 1;
  margin-bottom: 24px;
}

.selection-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.selection-info {
  font-size: 14px;
  color: #6b7280;
}

.chapters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.chapter-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.chapter-item:hover {
  border-color: #8b5cf6;
  background: #f8f7ff;
}

.chapter-item.selected {
  border-color: #8b5cf6;
  background: #f8f7ff;
}

.chapter-content {
  margin-left: 8px;
}

.chapter-title {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.chapter-meta {
  font-size: 12px;
  color: #6b7280;
}

/* 分析进度 */
.analysis-progress {
  text-align: center;
  margin-bottom: 32px;
}

.progress-text {
  margin-top: 16px;
  color: #6b7280;
}

/* 分析结果 */
.analysis-results {
  flex: 1;
  margin-bottom: 24px;
}

.results-summary {
  margin-bottom: 24px;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.characters-preview {
  margin-bottom: 24px;
}

.characters-preview h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.characters-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.character-preview-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.character-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 16px;
  flex-shrink: 0;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.character-info {
  flex: 1;
}

.character-name {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
}

.character-meta {
  font-size: 12px;
  color: #6b7280;
}

.character-status {
  display: flex;
  gap: 8px;
}

/* 批量配置 */
.batch-config {
  flex: 1;
  margin-bottom: 24px;
}

.config-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.config-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.config-item:hover {
  border-color: #8b5cf6;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1);
}

.config-item.existing-character {
  background: #f0fdf4;
  border-color: #10b981;
}

.config-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-header {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.character-basic h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.character-basic p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.config-details {
  border-top: 1px solid #f3f4f6;
  padding-top: 16px;
}

.existing-character-info {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  padding: 16px;
}

/* 创建结果 */
.creation-results {
  flex: 1;
  margin-bottom: 24px;
}

.created-characters {
  margin-top: 24px;
}

.created-characters h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.created-character-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  margin-bottom: 8px;
}

.character-files {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.character-actions {
  flex-shrink: 0;
}

/* 步骤操作 */
.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
  margin-top: auto;
}

/* 暗黑模式适配 */
[data-theme='dark'] .smart-discovery-container {
  color: #d1d5db;
}

[data-theme='dark'] .discovery-steps {
  border-bottom-color: #434343;
}

[data-theme='dark'] .step-header h3 {
  color: #f9fafb;
}

[data-theme='dark'] .step-header p {
  color: #9ca3af;
}

[data-theme='dark'] .empty-state {
  color: #9ca3af;
}

[data-theme='dark'] .book-card {
  border-color: #434343;
  background: #1f1f1f;
}

[data-theme='dark'] .book-card:hover {
  border-color: #8b5cf6;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

[data-theme='dark'] .book-card.selected {
  background: #2d1b69;
  border-color: #8b5cf6;
}

[data-theme='dark'] .book-info h4 {
  color: #f9fafb;
}

[data-theme='dark'] .book-info p {
  color: #9ca3af;
}

[data-theme='dark'] .book-stats {
  color: #9ca3af;
}

[data-theme='dark'] .book-id {
  color: #6b7280;
}

[data-theme='dark'] .selection-controls {
  background: #1f1f1f;
}

[data-theme='dark'] .selection-info {
  color: #9ca3af;
}

[data-theme='dark'] .chapter-item {
  border-color: #434343;
  background: #1f1f1f;
}

[data-theme='dark'] .chapter-item:hover {
  border-color: #8b5cf6;
  background: #2d1b69;
}

[data-theme='dark'] .chapter-item.selected {
  background: #2d1b69;
  border-color: #8b5cf6;
}

[data-theme='dark'] .chapter-title {
  color: #f9fafb;
}

[data-theme='dark'] .chapter-meta {
  color: #9ca3af;
}

[data-theme='dark'] .progress-text {
  color: #9ca3af;
}

[data-theme='dark'] .characters-preview h4 {
  color: #f9fafb;
}

[data-theme='dark'] .character-preview-item {
  border-color: #434343;
  background: #1f1f1f;
}

[data-theme='dark'] .character-name {
  color: #f9fafb;
}

[data-theme='dark'] .character-meta {
  color: #9ca3af;
}

[data-theme='dark'] .config-controls {
  background: #1f1f1f;
}

[data-theme='dark'] .config-item {
  border-color: #434343;
  background: #1f1f1f;
}

[data-theme='dark'] .config-item:hover {
  border-color: #8b5cf6;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.2);
}

[data-theme='dark'] .config-item.existing-character {
  background: #064e3b;
  border-color: #10b981;
}

[data-theme='dark'] .character-basic h4 {
  color: #f9fafb;
}

[data-theme='dark'] .character-basic p {
  color: #9ca3af;
}

[data-theme='dark'] .config-details {
  border-top-color: #374151;
}

[data-theme='dark'] .existing-character-info {
  background: #064e3b;
  border-color: #10b981;
}

[data-theme='dark'] .created-characters h4 {
  color: #f9fafb;
}

[data-theme='dark'] .created-character-item {
  border-color: #434343;
  background: #1f1f1f;
}

[data-theme='dark'] .step-actions {
  border-top-color: #434343;
}
</style>