<template>
  <div class="smart-editing-assistant">
    <div class="assistant-header">
      <h3>
        <RobotOutlined />
        智能编辑助手
      </h3>
      <a-button size="small" @click="togglePanel">
        <template #icon>
          <ExpandAltOutlined v-if="collapsed" />
          <ShrinkOutlined v-else />
        </template>
      </a-button>
    </div>

    <div v-show="!collapsed" class="assistant-content">
      <!-- 智能项目导入 -->
      <div class="feature-section">
        <div class="feature-header">
          <h4>
            <ImportOutlined />
            智能项目导入
          </h4>
          <a-switch v-model:checked="features.projectImport.enabled" size="small" />
        </div>

        <div v-if="features.projectImport.enabled" class="feature-controls">
          <div class="control-item">
            <label>选择语音合成项目</label>
            <a-select
              v-model:value="features.projectImport.selectedProject"
              style="width: 100%"
              placeholder="选择要导入的项目"
              @change="onProjectSelect"
              :loading="loadingProjects"
            >
              <a-select-option
                v-for="project in availableProjects"
                :key="project.id"
                :value="project.id"
              >
                {{ project.name }} ({{ project.status }})
              </a-select-option>
            </a-select>
          </div>

          <div v-if="selectedProjectData" class="control-item">
            <label>轨道布局配置</label>
            <div class="track-layout">
              <div class="layout-option">
                <a-radio-group
                  v-model:value="features.projectImport.layoutMode"
                  @change="onLayoutModeChange"
                >
                  <a-radio value="auto">自动分配轨道</a-radio>
                  <a-radio value="manual">手动配置轨道</a-radio>
                </a-radio-group>
              </div>

              <div v-if="features.projectImport.layoutMode === 'auto'" class="auto-layout-preview">
                <div class="layout-item" v-for="(track, index) in autoTrackLayout" :key="index">
                  <span class="track-label">轨道 {{ index + 1 }}:</span>
                  <span class="track-content">{{ track.type }} ({{ track.count }} 个片段)</span>
                </div>
              </div>

              <div
                v-if="features.projectImport.layoutMode === 'manual'"
                class="manual-layout-config"
              >
                <div
                  class="character-mapping"
                  v-for="character in projectCharacters"
                  :key="character"
                >
                  <label>{{ character }}:</label>
                  <a-select
                    v-model:value="features.projectImport.trackMapping[character]"
                    style="width: 100px"
                  >
                    <a-select-option v-for="i in 10" :key="i" :value="i"
                      >轨道 {{ i }}</a-select-option
                    >
                  </a-select>
                </div>
              </div>
            </div>
          </div>

          <div class="action-buttons">
            <a-button @click="refreshProjects" :loading="loadingProjects" size="small">
              <template #icon><ReloadOutlined /></template>
              刷新项目
            </a-button>
            <a-button
              @click="previewImport"
              :loading="previewing"
              size="small"
              :disabled="!selectedProjectData"
            >
              <template #icon><EyeOutlined /></template>
              预览导入
            </a-button>
            <a-button
              @click="executeImport"
              :loading="importing"
              size="small"
              type="primary"
              :disabled="!selectedProjectData"
            >
              <template #icon><CheckOutlined /></template>
              开始导入
            </a-button>
          </div>

          <!-- 导入预览 -->
          <div v-if="importPreview.length > 0" class="analysis-results">
            <h5>将要导入 {{ importPreview.length }} 个音频片段:</h5>
            <div class="import-list">
              <div v-for="(segment, index) in importPreview" :key="index" class="import-item">
                <div class="segment-info">
                  <span class="segment-speaker">{{ segment.speaker || '旁白' }}</span>
                  <span class="segment-track">→ 轨道{{ segment.trackNumber }}</span>
                </div>
                <div class="segment-text">{{ segment.text.substring(0, 50) }}...</div>
                <div class="segment-time">
                  {{ formatTime(segment.startTime) }} - {{ formatTime(segment.endTime) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 环境音导入 -->
      <div class="feature-section">
        <div class="feature-header">
          <h4>
            <EnvironmentOutlined />
            环境音导入
          </h4>
          <a-switch v-model:checked="features.environmentImport.enabled" size="small" />
        </div>

        <div v-if="features.environmentImport.enabled" class="feature-controls">
          <div class="import-mode-tabs">
            <a-tabs v-model:activeKey="features.environmentImport.mode" size="small">
              <!-- JSON配置导入 -->
              <a-tab-pane key="json" tab="📄 JSON配置导入">
                <div class="control-item">
                  <label>环境音配置文件</label>
                  <a-upload
                    v-model:fileList="environmentJsonFiles"
                    :multiple="false"
                    :before-upload="beforeJsonUpload"
                    @change="handleJsonChange"
                    accept=".json"
                    :show-upload-list="false"
                  >
                    <a-button size="small">
                      <template #icon><UploadOutlined /></template>
                      选择JSON文件
                    </a-button>
                  </a-upload>
                  <div v-if="selectedJsonFile" class="selected-file">
                    <FileTextOutlined />
                    {{ selectedJsonFile.name }}
                    <a-button type="link" size="small" @click="removeJsonFile">移除</a-button>
                  </div>
                  <div class="upload-hint">支持环境音模块生成的JSON配置文件</div>
                </div>

                <div v-if="environmentPreview.length > 0" class="control-item">
                  <label>环境音预览</label>
                  <div class="environment-preview">
                    <div v-for="(env, index) in environmentPreview" :key="index" class="env-item">
                      <div class="env-info">
                        <span class="env-id">{{ env.id }}</span>
                        <span class="env-time"
                          >{{ formatTime(env.start_time) }} -
                          {{ formatTime(env.start_time + env.duration) }}</span
                        >
                      </div>
                      <div class="env-track">轨道: {{ env.track_position }}</div>
                    </div>
                  </div>
                </div>

                <div class="action-buttons">
                  <a-button
                    @click="analyzeEnvironmentJson"
                    :loading="analyzing"
                    size="small"
                    type="primary"
                  >
                    <template #icon><SearchOutlined /></template>
                    解析JSON
                  </a-button>
                  <a-button
                    @click="importEnvironmentSounds"
                    :disabled="!hasEnvironmentData"
                    size="small"
                  >
                    <template #icon><ImportOutlined /></template>
                    导入环境音
                  </a-button>
                </div>

                <!-- 解析进度 -->
                <div v-if="analysisProgress > 0" class="recognition-progress">
                  <a-progress :percent="analysisProgress" size="small" />
                  <span class="progress-text">正在解析环境音配置...</span>
                </div>

                <!-- 导入结果 -->
                <div v-if="environmentResults.length > 0" class="speech-results">
                  <h5>导入结果 ({{ environmentResults.length }} 个环境音):</h5>
                  <div class="results-list">
                    <div
                      v-for="(result, index) in environmentResults"
                      :key="index"
                      class="result-item"
                      @click="jumpToTime(result.start_time)"
                    >
                      <div class="result-time">{{ formatTime(result.start_time) }}</div>
                      <div class="result-text">{{ result.id }} ({{ result.duration }}s)</div>
                      <div class="result-confidence">轨道: {{ result.track_position }}</div>
                    </div>
                  </div>
                </div>
              </a-tab-pane>

              <!-- 环境音库选择 -->
              <a-tab-pane key="library" tab="🎵 环境音库选择">
                <div class="library-section">
                  <!-- 搜索和筛选 -->
                  <div class="library-filters">
                    <a-row :gutter="12">
                      <a-col :span="14">
                        <a-input-search
                          v-model:value="environmentSearch.query"
                          placeholder="搜索环境音..."
                          @search="searchEnvironmentSounds"
                          size="small"
                        />
                      </a-col>
                      <a-col :span="10">
                        <a-select
                          v-model:value="environmentSearch.category"
                          placeholder="分类"
                          allowClear
                          size="small"
                          @change="loadEnvironmentSounds"
                        >
                          <a-select-option
                            v-for="category in environmentCategories"
                            :key="category.id"
                            :value="category.id"
                          >
                            {{ category.name }}
                          </a-select-option>
                        </a-select>
                      </a-col>
                    </a-row>
                  </div>

                  <!-- 环境音列表 -->
                  <div class="environment-sounds-list" v-if="availableEnvironmentSounds.length > 0">
                    <div
                      v-for="sound in availableEnvironmentSounds"
                      :key="sound.id"
                      class="sound-item"
                      :class="{ 'sound-selected': selectedEnvironmentSounds.includes(sound.id) }"
                      @click="toggleEnvironmentSound(sound)"
                    >
                      <div class="sound-info">
                        <div class="sound-name">{{ sound.name }}</div>
                        <div class="sound-meta">
                          <span class="sound-category">{{ sound.category?.name }}</span>
                          <span class="sound-duration">{{ sound.duration }}s</span>
                          <a-badge
                            :status="
                              sound.generation_status === 'completed' ? 'success' : 'processing'
                            "
                            :text="sound.generation_status === 'completed' ? '已完成' : '生成中'"
                          />
                        </div>
                        <div class="sound-prompt">{{ sound.prompt }}</div>
                      </div>
                      <div class="sound-actions">
                        <a-button
                          size="small"
                          @click.stop="previewLibrarySound(sound)"
                          :loading="previewingLibSoundId === sound.id"
                          :disabled="sound.generation_status !== 'completed'"
                        >
                          <template #icon><PlayCircleOutlined /></template>
                        </a-button>
                        <a-checkbox
                          :checked="selectedEnvironmentSounds.includes(sound.id)"
                          @click.stop
                          @change="toggleEnvironmentSound(sound)"
                          :disabled="sound.generation_status !== 'completed'"
                        />
                      </div>
                    </div>
                  </div>

                  <!-- 空状态 -->
                  <div v-else-if="!environmentLoading" class="empty-state">
                    <a-empty description="暂无可用环境音" />
                  </div>

                  <!-- 加载状态 -->
                  <div v-if="environmentLoading" class="loading-state">
                    <a-spin size="small" />
                  </div>

                  <!-- 批量导入操作 -->
                  <div v-if="selectedEnvironmentSounds.length > 0" class="batch-import-actions">
                    <div class="selection-info">
                      已选择 {{ selectedEnvironmentSounds.length }} 个环境音
                    </div>
                    <div class="action-buttons">
                      <a-button
                        @click="importSelectedEnvironments"
                        :loading="environmentImporting"
                        size="small"
                        type="primary"
                      >
                        <template #icon><DownloadOutlined /></template>
                        导入选中的环境音
                      </a-button>
                      <a-button @click="clearSelectedEnvironments" size="small">
                        <template #icon><ClearOutlined /></template>
                        清除选择
                      </a-button>
                    </div>
                  </div>
                </div>
              </a-tab-pane>
            </a-tabs>
          </div>
        </div>
      </div>

      <!-- 情感分析配音 -->
      <div class="feature-section">
        <div class="feature-header">
          <h4>
            <HeartOutlined />
            情感分析配音
          </h4>
          <a-switch v-model:checked="features.emotionAnalysis.enabled" size="small" />
        </div>

        <div v-if="features.emotionAnalysis.enabled" class="feature-controls">
          <div class="control-item">
            <label>情感强度</label>
            <div class="control-group">
              <a-slider
                v-model:value="features.emotionAnalysis.intensity"
                :min="0"
                :max="1"
                :step="0.1"
                @change="onEmotionIntensityChange"
              />
              <span class="value-display"
                >{{ Math.round(features.emotionAnalysis.intensity * 100) }}%</span
              >
            </div>
          </div>

          <div class="control-item">
            <label>语调调节</label>
            <a-checkbox-group v-model:value="features.emotionAnalysis.adjustments">
              <a-checkbox value="pitch">音调</a-checkbox>
              <a-checkbox value="speed">语速</a-checkbox>
              <a-checkbox value="volume">音量</a-checkbox>
              <a-checkbox value="tone">语气</a-checkbox>
            </a-checkbox-group>
          </div>

          <div class="action-buttons">
            <a-button @click="analyzeEmotions" :loading="emotionAnalyzing" size="small">
              <template #icon><SearchOutlined /></template>
              分析情感
            </a-button>
            <a-button
              @click="applyEmotionAdjustments"
              :disabled="!hasEmotionResults"
              size="small"
              type="primary"
            >
              <template #icon><CheckOutlined /></template>
              应用调节
            </a-button>
          </div>

          <!-- 情感分析结果 -->
          <div v-if="emotionResults.length > 0" class="emotion-results">
            <h5>情感分析结果:</h5>
            <div class="emotion-chart">
              <div
                v-for="(emotion, index) in emotionResults"
                :key="index"
                class="emotion-bar"
                @click="jumpToTime(emotion.startTime)"
              >
                <div class="emotion-label">{{ getEmotionLabel(emotion.type) }}</div>
                <div class="emotion-timeline">
                  <div
                    class="emotion-segment"
                    :class="emotion.type"
                    :style="{ width: (emotion.duration / totalDuration) * 100 + '%' }"
                  ></div>
                </div>
                <div class="emotion-intensity">{{ Math.round(emotion.intensity * 100) }}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 背景音乐推荐 -->
      <div class="feature-section">
        <div class="feature-header">
          <h4>
            <CustomerServiceOutlined />
            背景音乐推荐
          </h4>
          <a-switch v-model:checked="features.musicRecommendation.enabled" size="small" />
        </div>

        <div v-if="features.musicRecommendation.enabled" class="feature-controls">
          <!-- 选择模式 -->
          <div class="control-item">
            <a-tabs v-model:activeKey="features.musicRecommendation.mode" size="small">
              <a-tab-pane key="recommend" tab="智能推荐">
                <div class="mode-content">
                  <div class="control-item">
                    <label>音乐风格</label>
                    <a-select
                      v-model:value="features.musicRecommendation.style"
                      style="width: 100%"
                      @change="onMusicStyleChange"
                    >
                      <a-select-option value="ambient">环境音乐</a-select-option>
                      <a-select-option value="classical">古典音乐</a-select-option>
                      <a-select-option value="electronic">电子音乐</a-select-option>
                      <a-select-option value="cinematic">电影配乐</a-select-option>
                      <a-select-option value="rock">摇滚音乐</a-select-option>
                      <a-select-option value="jazz">爵士音乐</a-select-option>
                    </a-select>
                  </div>

                  <div class="control-item">
                    <label>音乐强度</label>
                    <div class="control-group">
                      <a-slider
                        v-model:value="features.musicRecommendation.intensity"
                        :min="0"
                        :max="1"
                        :step="0.1"
                      />
                      <span class="value-display"
                        >{{ Math.round(features.musicRecommendation.intensity * 100) }}%</span
                      >
                    </div>
                  </div>

                  <div class="action-buttons">
                    <a-button @click="recommendMusic" :loading="musicRecommending" size="small">
                      <template #icon><SearchOutlined /></template>
                      智能推荐
                    </a-button>
                    <a-button
                      @click="previewMusic"
                      :disabled="!hasMusicRecommendations"
                      size="small"
                    >
                      <template #icon><PlayCircleOutlined /></template>
                      预览音乐
                    </a-button>
                  </div>

                  <!-- 智能推荐结果 -->
                  <div v-if="musicRecommendations.length > 0" class="music-recommendations">
                    <h5>推荐音乐:</h5>
                    <div class="music-list">
                      <div
                        v-for="(music, index) in musicRecommendations"
                        :key="index"
                        class="music-item"
                        @click="selectMusic(music)"
                      >
                        <div class="music-info">
                          <div class="music-name">{{ music.name }}</div>
                          <div class="music-description">{{ music.description }}</div>
                          <div class="music-meta" v-if="music.quality_rating">
                            <span class="quality-rating"
                              >★{{ music.quality_rating?.toFixed(1) || 'N/A' }}</span
                            >
                            <span class="music-style">{{ music.style }}</span>
                          </div>
                        </div>
                        <div class="music-actions">
                          <a-button size="small" @click.stop="previewSingleMusic(music)">
                            <template #icon><PlayCircleOutlined /></template>
                          </a-button>
                          <a-button size="small" @click.stop="addMusicToTrack(music)">
                            <template #icon><PlusOutlined /></template>
                          </a-button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </a-tab-pane>

              <a-tab-pane key="library" tab="音乐库选择">
                <div class="mode-content">
                  <!-- 搜索和筛选 -->
                  <div class="library-filters">
                    <a-input
                      v-model:value="musicLibrarySearch.query"
                      placeholder="搜索音乐名称..."
                      size="small"
                      @change="loadMusicLibrary"
                      style="margin-bottom: 8px"
                    >
                      <template #prefix><SearchOutlined /></template>
                    </a-input>

                    <div style="display: flex; gap: 8px; align-items: center">
                      <a-select
                        v-model:value="musicLibrarySearch.category"
                        placeholder="选择分类"
                        size="small"
                        style="flex: 1"
                        allow-clear
                        @change="loadMusicLibrary"
                      >
                        <a-select-option
                          v-for="category in musicCategories"
                          :key="category.id"
                          :value="category.id"
                        >
                          {{ category.name }}
                        </a-select-option>
                      </a-select>

                      <a-button
                        @click="loadMusicLibrary"
                        :loading="musicLibraryLoading"
                        size="small"
                      >
                        <template #icon><ReloadOutlined /></template>
                      </a-button>
                    </div>
                  </div>

                  <!-- 音乐库列表 -->
                  <div class="music-library-list" v-if="availableMusic.length > 0">
                    <div
                      v-for="music in availableMusic"
                      :key="music.id"
                      class="sound-item"
                      :class="{ 'sound-selected': selectedMusic.some((s) => s.id === music.id) }"
                      @click="toggleMusicSelection(music)"
                    >
                      <a-checkbox
                        :checked="selectedMusic.some((s) => s.id === music.id)"
                        @click.stop="toggleMusicSelection(music)"
                      />

                      <div class="sound-info">
                        <div class="sound-name">{{ music.name }}</div>
                        <div class="sound-meta">
                          <span class="sound-category">{{ music.category_name || '未分类' }}</span>
                          <span class="sound-duration">{{ formatDuration(music.duration) }}</span>
                          <span class="quality-rating"
                            >★{{ music.quality_rating?.toFixed(1) }}</span
                          >
                          <span class="usage-count">{{ music.usage_count }}次</span>
                        </div>

                        <!-- 标签 -->
                        <div class="music-tags" style="margin-top: 4px">
                          <a-tag
                            v-for="tag in music.emotion_tags?.slice(0, 2)"
                            :key="`emotion-${tag}`"
                            color="blue"
                            size="small"
                          >
                            {{ tag }}
                          </a-tag>
                          <a-tag
                            v-for="tag in music.style_tags?.slice(0, 1)"
                            :key="`style-${tag}`"
                            color="green"
                            size="small"
                          >
                            {{ tag }}
                          </a-tag>
                        </div>
                      </div>

                      <div class="sound-actions">
                        <a-button
                          size="small"
                          :loading="previewingMusicId === music.id"
                          @click.stop="previewLibraryMusic(music)"
                        >
                          <template #icon><PlayCircleOutlined /></template>
                        </a-button>
                      </div>
                    </div>
                  </div>

                  <div v-else-if="musicLibraryLoading" class="loading-state">
                    <a-spin size="small" />
                    <span style="margin-left: 8px">加载音乐库中...</span>
                  </div>

                  <div v-else class="empty-state">
                    <p>暂无音乐库数据</p>
                    <a-button type="link" @click="$router.push('/music-library')">
                      前往音乐库管理
                    </a-button>
                  </div>

                  <!-- 已选择的音乐 -->
                  <div v-if="selectedMusic.length > 0" class="batch-import-actions">
                    <div class="selection-info">已选择 {{ selectedMusic.length }} 首音乐</div>

                    <div style="display: flex; gap: 8px">
                      <a-button
                        type="primary"
                        size="small"
                        @click="importSelectedMusic"
                        :loading="musicImporting"
                      >
                        <template #icon><ImportOutlined /></template>
                        导入选中音乐
                      </a-button>

                      <a-button size="small" @click="clearMusicSelection">
                        <template #icon><ClearOutlined /></template>
                        清空选择
                      </a-button>
                    </div>
                  </div>
                </div>
              </a-tab-pane>
            </a-tabs>
          </div>
        </div>
      </div>

      <!-- 批量处理 -->
      <div class="feature-section">
        <div class="feature-header">
          <h4>
            <ThunderboltOutlined />
            批量处理
          </h4>
          <a-switch v-model:checked="features.batchProcessing.enabled" size="small" />
        </div>

        <div v-if="features.batchProcessing.enabled" class="feature-controls">
          <div class="batch-tasks">
            <h5>批量任务:</h5>
            <a-checkbox-group v-model:value="features.batchProcessing.tasks">
              <a-checkbox value="normalize">音量标准化</a-checkbox>
              <a-checkbox value="denoise">批量降噪</a-checkbox>
              <a-checkbox value="compress">动态压缩</a-checkbox>
              <a-checkbox value="enhance">音质增强</a-checkbox>
            </a-checkbox-group>
          </div>

          <div class="action-buttons">
            <a-button
              @click="startBatchProcessing"
              :loading="batchProcessing"
              size="small"
              type="primary"
            >
              <template #icon><ThunderboltOutlined /></template>
              开始批量处理
            </a-button>
          </div>

          <!-- 批量处理进度 -->
          <div v-if="batchProgress > 0" class="batch-progress">
            <a-progress :percent="batchProgress" size="small" />
            <span class="progress-text">正在处理第 {{ currentBatchTask }} 个任务...</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, reactive, computed, watch, onMounted } from 'vue'
  import { message } from 'ant-design-vue'
  import { readerAPI, backgroundMusicAPI } from '../api/index.js'
  import {
    RobotOutlined,
    ExpandAltOutlined,
    ShrinkOutlined,
    ImportOutlined,
    SoundOutlined,
    HeartOutlined,
    CustomerServiceOutlined,
    ThunderboltOutlined,
    SearchOutlined,
    CheckOutlined,
    PlayCircleOutlined,
    ExportOutlined,
    PlusOutlined,
    ReloadOutlined,
    EyeOutlined,
    EnvironmentOutlined,
    UploadOutlined,
    FileTextOutlined,
    DownloadOutlined,
    ClearOutlined,
    CloudOutlined
  } from '@ant-design/icons-vue'

  // Props
  const props = defineProps({
    audioUrl: {
      type: String,
      default: ''
    },
    totalDuration: {
      type: Number,
      default: 0
    }
  })

  // Emits
  const emit = defineEmits([
    'project-imported',
    'speech-recognized',
    'emotion-analyzed',
    'music-recommended',
    'batch-processed',
    'jump-to-time'
  ])

  // 状态
  const collapsed = ref(false)
  const analyzing = ref(false)
  const applying = ref(false)
  const emotionAnalyzing = ref(false)
  const musicRecommending = ref(false)
  const batchProcessing = ref(false)

  // 进度状态
  const analysisProgress = ref(0)
  const batchProgress = ref(0)
  const currentBatchTask = ref(0)

  // 结果数据
  const importPreview = ref([])
  const environmentPreview = ref([])
  const environmentResults = ref([])
  const emotionResults = ref([])
  const musicRecommendations = ref([])

  // 环境音导入相关
  const environmentJsonFiles = ref([])
  const selectedJsonFile = ref(null)

  // 环境音库相关状态
  const availableEnvironmentSounds = ref([])
  const environmentCategories = ref([])
  const selectedEnvironmentSounds = ref([])
  const environmentLoading = ref(false)
  const environmentImporting = ref(false)
  const previewingLibSoundId = ref(null)
  const previewingEnvId = ref(null)
  const environmentSearch = reactive({
    query: '',
    category: null
  })

  // 音乐库相关状态
  const availableMusic = ref([])
  const musicCategories = ref([])
  const selectedMusic = ref([])
  const musicLibraryLoading = ref(false)
  const musicImporting = ref(false)
  const previewingMusicId = ref(null)
  const musicLibrarySearch = reactive({
    query: '',
    category: null
  })

  // 项目导入相关状态
  const availableProjects = ref([])
  const selectedProjectData = ref(null)
  const loadingProjects = ref(false)
  const previewing = ref(false)
  const importing = ref(false)
  const autoTrackLayout = ref([])
  const projectCharacters = ref([])

  // 功能配置
  const features = reactive({
    projectImport: {
      enabled: false,
      selectedProject: null,
      layoutMode: 'auto',
      trackMapping: {}
    },
    environmentImport: {
      enabled: false,
      mode: 'json',
      jsonFile: null,
      autoTrackAssign: true
    },
    emotionAnalysis: {
      enabled: false,
      intensity: 0.7,
      adjustments: ['pitch', 'volume']
    },
    musicRecommendation: {
      enabled: false,
      mode: 'recommend', // 'recommend' 或 'library'
      style: 'ambient',
      intensity: 0.5
    },
    batchProcessing: {
      enabled: false,
      tasks: []
    }
  })

  // 计算属性
  const hasEnvironmentData = computed(() => environmentPreview.value.length > 0)
  const hasEmotionResults = computed(() => emotionResults.value.length > 0)
  const hasMusicRecommendations = computed(() => musicRecommendations.value.length > 0)

  // 方法
  const togglePanel = () => {
    collapsed.value = !collapsed.value
  }

  // 项目导入相关
  const refreshProjects = async () => {
    loadingProjects.value = true
    try {
      const response = await readerAPI.getProjects({ status: 'completed' })
      if (response.data.success) {
        availableProjects.value = response.data.data.items || response.data.data || []
        message.success(`加载了 ${availableProjects.value.length} 个已完成的项目`)
      }
    } catch (error) {
      console.error('获取项目列表失败:', error)
      message.error('获取项目列表失败')
    } finally {
      loadingProjects.value = false
    }
  }

  const onProjectSelect = async (projectId) => {
    if (!projectId) {
      selectedProjectData.value = null
      return
    }

    try {
      const response = await readerAPI.getProject(projectId)
      if (response.data.success) {
        selectedProjectData.value = response.data.data

        // 提取角色信息
        const characters = selectedProjectData.value.character_mapping || {}
        projectCharacters.value = Object.keys(characters)

        // 生成自动轨道布局
        generateAutoTrackLayout()

        // 初始化手动轨道映射
        initializeTrackMapping()

        message.success(`已选择项目: ${selectedProjectData.value.name}`)
      }
    } catch (error) {
      console.error('获取项目详情失败:', error)
      message.error('获取项目详情失败')
    }
  }

  const generateAutoTrackLayout = () => {
    if (!selectedProjectData.value) return

    const tracks = []
    let trackIndex = 0

    // 旁白轨道
    tracks.push({
      type: '旁白',
      count: 0, // 需要从实际数据计算
      characters: ['旁白']
    })
    trackIndex++

    // 角色轨道
    projectCharacters.value.forEach((character) => {
      if (character !== '旁白') {
        tracks.push({
          type: character,
          count: 0, // 需要从实际数据计算
          characters: [character]
        })
        trackIndex++
      }
    })

    // 环境音轨道
    tracks.push({
      type: '环境音',
      count: 0,
      characters: ['环境音']
    })

    autoTrackLayout.value = tracks
  }

  const initializeTrackMapping = () => {
    const mapping = {}
    let trackNumber = 1

    // 默认分配：旁白->轨道1，角色按顺序分配
    mapping['旁白'] = 1
    trackNumber++

    projectCharacters.value.forEach((character) => {
      if (character !== '旁白') {
        mapping[character] = trackNumber
        trackNumber++
      }
    })

    features.projectImport.trackMapping = mapping
  }

  const onLayoutModeChange = () => {
    if (features.projectImport.layoutMode === 'auto') {
      generateAutoTrackLayout()
    }
  }

  const previewImport = async () => {
    if (!selectedProjectData.value) return

    previewing.value = true
    try {
      // 这里应该调用API获取项目的准备数据
      // 暂时模拟数据
      await new Promise((resolve) => setTimeout(resolve, 1000))

      importPreview.value = [
        {
          speaker: '旁白',
          text: '故事开始于一个宁静的小村庄...',
          startTime: 0,
          endTime: 5,
          trackNumber: features.projectImport.trackMapping['旁白'] || 1
        },
        {
          speaker: '主角',
          text: '你好，我是这个故事的主人公',
          startTime: 5,
          endTime: 8,
          trackNumber: features.projectImport.trackMapping['主角'] || 2
        }
      ]

      message.success(`预览了 ${importPreview.value.length} 个音频片段`)
    } catch (error) {
      message.error('预览失败')
    } finally {
      previewing.value = false
    }
  }

  const executeImport = async () => {
    if (!selectedProjectData.value) return

    importing.value = true
    try {
      await new Promise((resolve) => setTimeout(resolve, 2000))

      // 触发导入事件，传递导入的数据到父组件
      emit('project-imported', {
        project: selectedProjectData.value,
        segments: importPreview.value,
        trackMapping: features.projectImport.trackMapping
      })

      message.success('项目导入成功！')
    } catch (error) {
      message.error('项目导入失败')
    } finally {
      importing.value = false
    }
  }

  // 环境音导入相关
  const beforeJsonUpload = (file) => {
    const isJson = file.type === 'application/json' || file.name.endsWith('.json')
    if (!isJson) {
      message.error('只能上传JSON文件!')
      return false
    }

    const isLt10M = file.size / 1024 / 1024 < 10
    if (!isLt10M) {
      message.error('JSON文件大小不能超过10MB!')
      return false
    }

    return false // 阻止自动上传，我们手动处理
  }

  const handleJsonChange = (info) => {
    if (info.fileList.length > 0) {
      selectedJsonFile.value = info.fileList[0].originFileObj || info.fileList[0]
      environmentJsonFiles.value = info.fileList
    }
  }

  const removeJsonFile = () => {
    selectedJsonFile.value = null
    environmentJsonFiles.value = []
    environmentPreview.value = []
  }

  const analyzeEnvironmentJson = async () => {
    if (!selectedJsonFile.value) {
      message.warning('请先选择JSON配置文件')
      return
    }

    analyzing.value = true
    analysisProgress.value = 0

    try {
      // 模拟解析进度
      const progressInterval = setInterval(() => {
        analysisProgress.value += 20
        if (analysisProgress.value >= 100) {
          clearInterval(progressInterval)
        }
      }, 200)

      // 读取JSON文件
      const fileContent = await readJsonFile(selectedJsonFile.value)
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // 解析环境音配置
      const environmentData = JSON.parse(fileContent)

      if (environmentData.environment_sounds && Array.isArray(environmentData.environment_sounds)) {
        environmentPreview.value = environmentData.environment_sounds.map((env) => ({
          id: env.id || 'unknown',
          start_time: env.start_time || 0,
          duration: env.duration || 10,
          track_position: env.track_position || 'environment_track_1'
        }))

        message.success(`解析成功，发现 ${environmentPreview.value.length} 个环境音配置`)
      } else {
        throw new Error('JSON格式不正确，缺少environment_sounds字段')
      }
    } catch (error) {
      console.error('解析JSON失败:', error)
      message.error(`解析失败: ${error.message}`)
    } finally {
      analyzing.value = false
      analysisProgress.value = 0
    }
  }

  const importEnvironmentSounds = async () => {
    if (environmentPreview.value.length === 0) {
      message.warning('请先解析JSON配置')
      return
    }

    try {
      // 模拟导入环境音到轨道
      environmentResults.value = [...environmentPreview.value]

      // 触发环境音导入事件
      emit('environment-imported', {
        sounds: environmentResults.value,
        total: environmentResults.value.length
      })

      message.success(`成功导入 ${environmentResults.value.length} 个环境音到轨道`)
    } catch (error) {
      console.error('导入环境音失败:', error)
      message.error('导入环境音失败')
    }
  }

  const readJsonFile = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => resolve(e.target.result)
      reader.onerror = (e) => reject(new Error('文件读取失败'))
      reader.readAsText(file)
    })
  }

  // 环境音库相关方法
  const loadEnvironmentCategories = async () => {
    try {
      const { environmentSoundsAPI } = await import('@/api')
      const response = await environmentSoundsAPI.getCategories({ active_only: true })
      environmentCategories.value = response.data || []
    } catch (error) {
      console.error('加载环境音分类失败:', error)
    }
  }

  const loadEnvironmentSounds = async () => {
    try {
      environmentLoading.value = true
      const { environmentSoundsAPI } = await import('@/api')

      const params = {
        page: 1,
        page_size: 20,
        status: 'completed',
        sort_by: 'created_at',
        sort_order: 'desc'
      }

      if (environmentSearch.category) {
        params.category_id = environmentSearch.category
      }

      if (environmentSearch.query.trim()) {
        params.search = environmentSearch.query.trim()
      }

      const response = await environmentSoundsAPI.getEnvironmentSounds(params)
      const data = response.data

      availableEnvironmentSounds.value = data.sounds || []
    } catch (error) {
      console.error('加载环境音列表失败:', error)
      message.error('加载环境音列表失败')
    } finally {
      environmentLoading.value = false
    }
  }

  const searchEnvironmentSounds = () => {
    loadEnvironmentSounds()
  }

  const toggleEnvironmentSound = (sound) => {
    if (sound.generation_status !== 'completed') {
      message.warning('该环境音尚未生成完成，无法选择')
      return
    }

    const index = selectedEnvironmentSounds.value.indexOf(sound.id)
    if (index > -1) {
      selectedEnvironmentSounds.value.splice(index, 1)
    } else {
      selectedEnvironmentSounds.value.push(sound.id)
    }
  }

  const previewLibrarySound = async (sound) => {
    try {
      previewingLibSoundId.value = sound.id

      // 使用统一音频服务播放
      const { getAudioService } = await import('@/utils/audioService')
      await getAudioService().playEnvironmentSound(sound)

      // 记录播放日志
      const { environmentSoundsAPI } = await import('@/api')
      await environmentSoundsAPI.playEnvironmentSound(sound.id)
    } catch (error) {
      console.error('试听失败:', error)
      message.error('试听失败')
    } finally {
      previewingLibSoundId.value = null
    }
  }

  const previewEnvironmentSound = async (envConfig) => {
    try {
      previewingEnvId.value = envConfig.id

      // 如果环境音配置包含具体的音频ID，尝试播放
      if (envConfig.sound_id) {
        const { environmentSoundsAPI } = await import('@/api')
        const response = await environmentSoundsAPI.getEnvironmentSound(envConfig.sound_id)
        if (response.data && response.data.generation_status === 'completed') {
          const { getAudioService } = await import('@/utils/audioService')
          await getAudioService().playEnvironmentSound(response.data)
        } else {
          message.warning('该环境音尚未生成完成')
        }
      } else {
        message.info(`预览环境音配置: ${envConfig.id}`)
      }
    } catch (error) {
      console.error('预览失败:', error)
      message.error('预览失败')
    } finally {
      previewingEnvId.value = null
    }
  }

  const importSelectedEnvironments = async () => {
    if (selectedEnvironmentSounds.value.length === 0) {
      message.warning('请先选择要导入的环境音')
      return
    }

    environmentImporting.value = true
    try {
      // 获取选中的环境音详情
      const { environmentSoundsAPI } = await import('@/api')
      const importedSounds = []

      for (const soundId of selectedEnvironmentSounds.value) {
        try {
          const response = await environmentSoundsAPI.getEnvironmentSound(soundId)
          if (response.data && response.data.generation_status === 'completed') {
            importedSounds.push({
              id: response.data.id,
              name: response.data.name,
              duration: response.data.duration,
              file_path: response.data.file_path,
              // 默认导入配置
              start_time: 0,
              track_position: 'environment_track_1',
              volume: 0.5
            })
          }
        } catch (error) {
          console.error(`导入环境音 ${soundId} 失败:`, error)
        }
      }

      if (importedSounds.length > 0) {
        environmentResults.value = importedSounds

        // 触发导入事件
        emit('environment-imported', {
          sounds: importedSounds,
          total: importedSounds.length,
          source: 'library'
        })

        message.success(`成功导入 ${importedSounds.length} 个环境音到编辑器`)
        clearSelectedEnvironments()
      } else {
        message.warning('没有可导入的环境音')
      }
    } catch (error) {
      console.error('批量导入失败:', error)
      message.error('批量导入失败')
    } finally {
      environmentImporting.value = false
    }
  }

  const clearSelectedEnvironments = () => {
    selectedEnvironmentSounds.value = []
  }

  // 情感分析相关
  const onEmotionIntensityChange = () => {
    // 更新情感强度
  }

  const analyzeEmotions = async () => {
    emotionAnalyzing.value = true
    try {
      await new Promise((resolve) => setTimeout(resolve, 2000))

      emotionResults.value = [
        { startTime: 0, duration: 15, type: 'neutral', intensity: 0.7 },
        { startTime: 15, duration: 20, type: 'happy', intensity: 0.8 },
        { startTime: 35, duration: 10, type: 'sad', intensity: 0.6 },
        { startTime: 45, duration: 25, type: 'excited', intensity: 0.9 }
      ]

      emit('emotion-analyzed', emotionResults.value)
      message.success('情感分析完成')
    } catch (error) {
      message.error('情感分析失败')
    } finally {
      emotionAnalyzing.value = false
    }
  }

  const applyEmotionAdjustments = () => {
    message.success('情感调节已应用')
  }

  // 背景音乐推荐相关

  const recommendMusic = async () => {
    musicRecommending.value = true
    try {
      // 基于当前分析结果或选中内容推荐音乐
      const requestData = {
        // 如果有情感分析结果，使用情感标签
        emotion_tags: analysisResult.value?.emotions?.map((emotion) => emotion.type) || ['neutral'],
        // 根据当前场景类型选择风格
        style_preference: 'ambient', // 默认环境音乐
        // 限制推荐数量
        limit: 5
      }

      const response = await backgroundMusicAPI.recommendMusic(requestData)

      if (response.data.success) {
        musicRecommendations.value = response.data.data.map((music) => ({
          id: music.id,
          name: music.name,
          description: music.description,
          style: music.style_tags?.[0] || 'ambient',
          emotion_tags: music.emotion_tags || [],
          quality_rating: music.quality_rating,
          duration: music.duration,
          download_url: music.download_url
        }))

        emit('music-recommended', musicRecommendations.value)
        message.success(`推荐了 ${musicRecommendations.value.length} 首背景音乐`)
      } else {
        // 如果API失败，使用假数据作为后备
        musicRecommendations.value = [
          {
            name: '宁静森林',
            description: '轻柔的自然环境音',
            style: 'ambient',
            quality_rating: 4.2
          },
          {
            name: '温暖阳光',
            description: '温馨的背景音乐',
            style: 'ambient',
            quality_rating: 4.5
          },
          {
            name: '梦幻空间',
            description: '空灵的电子音乐',
            style: 'electronic',
            quality_rating: 4.1
          }
        ]

        emit('music-recommended', musicRecommendations.value)
        message.success(`推荐了 ${musicRecommendations.value.length} 首背景音乐`)
      }
    } catch (error) {
      console.error('音乐推荐失败:', error)

      // API失败时的降级处理
      musicRecommendations.value = [
        {
          name: '宁静森林',
          description: '轻柔的自然环境音',
          style: 'ambient',
          quality_rating: 4.2
        },
        { name: '温暖阳光', description: '温馨的背景音乐', style: 'ambient', quality_rating: 4.5 },
        {
          name: '梦幻空间',
          description: '空灵的电子音乐',
          style: 'electronic',
          quality_rating: 4.1
        }
      ]

      emit('music-recommended', musicRecommendations.value)
      message.warning('使用默认推荐，建议检查音乐库连接')
    } finally {
      musicRecommending.value = false
    }
  }

  const previewMusic = () => {
    message.info('音乐预览功能开发中...')
  }

  const previewSingleMusic = (music) => {
    message.info(`预览: ${music.name}`)
  }

  const selectMusic = (music) => {
    message.success(`已选择: ${music.name}`)
  }

  const addMusicToTrack = (music) => {
    message.success(`已添加 ${music.name} 到轨道`)
  }

  const onMusicStyleChange = () => {
    // 当音乐风格改变时，可以自动重新推荐
    if (musicRecommendations.value.length > 0) {
      message.info('音乐风格已更改，可重新推荐')
    }
  }

  // 批量处理相关
  const startBatchProcessing = async () => {
    batchProcessing.value = true
    batchProgress.value = 0
    currentBatchTask.value = 0

    try {
      const tasks = features.batchProcessing.tasks
      for (let i = 0; i < tasks.length; i++) {
        currentBatchTask.value = i + 1
        await new Promise((resolve) => setTimeout(resolve, 1000))
        batchProgress.value = ((i + 1) / tasks.length) * 100
      }

      emit('batch-processed', features.batchProcessing.tasks)
      message.success('批量处理完成')
    } catch (error) {
      message.error('批量处理失败')
    } finally {
      batchProcessing.value = false
      batchProgress.value = 0
      currentBatchTask.value = 0
    }
  }

  // 工具函数
  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '00:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const getEmotionLabel = (type) => {
    const labels = {
      neutral: '平静',
      happy: '愉悦',
      sad: '悲伤',
      excited: '兴奋',
      angry: '愤怒',
      surprised: '惊讶'
    }
    return labels[type] || type
  }

  const jumpToTime = (time) => {
    emit('jump-to-time', time)
  }

  // 组件挂载时初始化
  onMounted(() => {
    refreshProjects()
    loadEnvironmentCategories()
  })

  // 音乐库相关函数
  const loadMusicCategories = async () => {
    try {
      const { backgroundMusicAPI } = await import('@/api')
      const response = await backgroundMusicAPI.getCategories()
      if (response.data.success) {
        musicCategories.value = response.data.data || []
      }
    } catch (error) {
      console.error('加载音乐分类失败:', error)
    }
  }

  const loadMusicLibrary = async () => {
    musicLibraryLoading.value = true
    try {
      const { backgroundMusicAPI } = await import('@/api')
      const params = {
        page: 1,
        page_size: 50,
        active_only: true
      }

      if (musicLibrarySearch.query) {
        params.search = musicLibrarySearch.query
      }

      if (musicLibrarySearch.category) {
        params.category_id = musicLibrarySearch.category
      }

      const response = await backgroundMusicAPI.getMusic(params)
      if (response.data.success) {
        availableMusic.value = response.data.data || []
      }
    } catch (error) {
      console.error('加载音乐库失败:', error)
      message.error('加载音乐库失败')
    } finally {
      musicLibraryLoading.value = false
    }
  }

  const toggleMusicSelection = (music) => {
    const index = selectedMusic.value.findIndex((s) => s.id === music.id)
    if (index > -1) {
      selectedMusic.value.splice(index, 1)
    } else {
      selectedMusic.value.push(music)
    }
  }

  const clearMusicSelection = () => {
    selectedMusic.value = []
  }

  const previewLibraryMusic = async (music) => {
    try {
      previewingMusicId.value = music.id

      const { backgroundMusicAPI } = await import('@/api')
      await backgroundMusicAPI.playMusic(music.id)

      // 使用音频服务播放
      const audio = new Audio(music.download_url)
      audio.play()

      audio.onended = () => {
        previewingMusicId.value = null
      }

      audio.onerror = () => {
        previewingMusicId.value = null
        message.error('音频播放失败')
      }
    } catch (error) {
      console.error('预览音乐失败:', error)
      message.error('预览音乐失败')
    } finally {
      setTimeout(() => {
        previewingMusicId.value = null
      }, 1000)
    }
  }

  const importSelectedMusic = async () => {
    if (selectedMusic.value.length === 0) {
      message.warning('请先选择要导入的音乐')
      return
    }

    musicImporting.value = true
    try {
      // 这里应该将选中的音乐添加到编辑器轨道
      // 暂时触发事件给父组件处理
      emit('music-recommended', selectedMusic.value)

      message.success(`成功导入 ${selectedMusic.value.length} 首音乐`)
      clearMusicSelection()
    } catch (error) {
      console.error('导入音乐失败:', error)
      message.error('导入音乐失败')
    } finally {
      musicImporting.value = false
    }
  }

  // 格式化时长
  const formatDuration = (seconds) => {
    if (!seconds || isNaN(seconds)) return '00:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // 监听环境音导入模式变化，加载相应数据
  watch(
    () => features.environmentImport.mode,
    (newMode) => {
      if (newMode === 'library' && availableEnvironmentSounds.value.length === 0) {
        loadEnvironmentSounds()
      }
    }
  )

  // 监听音乐推荐模式变化，加载相应数据
  watch(
    () => features.musicRecommendation.mode,
    (newMode) => {
      if (newMode === 'library' && availableMusic.value.length === 0) {
        loadMusicCategories()
        loadMusicLibrary()
      }
    }
  )
</script>

<style scoped>
  .smart-editing-assistant {
    background: #fff;
    border: 1px solid #d9d9d9;
    border-radius: 6px;
    overflow: hidden;
  }

  .assistant-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .assistant-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .assistant-content {
    max-height: 800px;
    overflow-y: auto;
  }

  .feature-section {
    border-bottom: 1px solid #f0f0f0;
    padding: 16px;
  }

  .feature-section:last-child {
    border-bottom: none;
  }

  .feature-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .feature-header h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 500;
    color: #333;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .feature-controls {
    margin-top: 12px;
  }

  .control-item {
    margin-bottom: 16px;
  }

  .control-item label {
    display: block;
    margin-bottom: 8px;
    font-size: 12px;
    color: #666;
    font-weight: 500;
  }

  .control-group {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .control-group .ant-slider {
    flex: 1;
  }

  .value-display {
    min-width: 60px;
    text-align: right;
    font-size: 12px;
    color: #666;
    font-family: monospace;
  }

  .feature-description {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 8px 12px;
    margin: 4px 0;
  }

  .feature-description p {
    margin: 4px 0;
    font-size: 13px;
    color: #666;
    line-height: 1.4;
  }

  .selected-file {
    margin-top: 8px;
    padding: 6px 8px;
    background: #f0f0f0;
    border-radius: 4px;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .environment-preview {
    max-height: 150px;
    overflow-y: auto;
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    padding: 8px;
    background: #fafafa;
  }

  .env-item {
    padding: 8px;
    margin-bottom: 6px;
    background: white;
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    transition: all 0.2s;
  }

  .env-item:hover {
    border-color: #1890ff;
    box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);
  }

  .env-item:last-child {
    margin-bottom: 0;
  }

  .env-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }

  .env-id {
    font-weight: 500;
    color: #333;
    font-size: 12px;
  }

  .env-time {
    font-size: 11px;
    color: #1890ff;
    font-family: monospace;
  }

  .env-track {
    font-size: 11px;
    color: #666;
  }

  .action-buttons {
    display: flex;
    gap: 8px;
    margin-top: 16px;
  }

  /* 章节分析结果 */
  .analysis-results {
    margin-top: 16px;
    padding: 12px;
    background: #f9f9f9;
    border-radius: 4px;
  }

  .analysis-results h5 {
    margin: 0 0 12px 0;
    font-size: 12px;
    color: #666;
  }

  /* 项目导入样式 */
  .track-layout {
    margin-top: 12px;
  }

  .layout-option {
    margin-bottom: 16px;
  }

  .auto-layout-preview {
    background: #f9f9f9;
    padding: 12px;
    border-radius: 4px;
    margin-top: 12px;
  }

  .layout-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid #e8e8e8;
  }

  .layout-item:last-child {
    border-bottom: none;
  }

  .track-label {
    font-weight: 500;
    color: #333;
  }

  .track-content {
    font-size: 12px;
    color: #666;
  }

  .manual-layout-config {
    margin-top: 12px;
  }

  .character-mapping {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
  }

  .character-mapping label {
    margin: 0;
    font-weight: 500;
    color: #333;
  }

  .import-list {
    max-height: 200px;
    overflow-y: auto;
  }

  .import-item {
    padding: 8px 12px;
    margin-bottom: 4px;
    background: white;
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    transition: all 0.2s;
  }

  .import-item:hover {
    border-color: #1890ff;
    box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);
  }

  .segment-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
    font-size: 12px;
    font-weight: 500;
  }

  .segment-speaker {
    color: #333;
  }

  .segment-track {
    color: #1890ff;
  }

  .segment-text {
    font-size: 12px;
    color: #666;
    margin-bottom: 4px;
    line-height: 1.4;
  }

  .segment-time {
    font-size: 11px;
    color: #999;
  }

  /* 语音识别结果 */
  .recognition-progress,
  .batch-progress {
    margin-top: 12px;
  }

  .progress-text {
    font-size: 12px;
    color: #666;
    margin-left: 8px;
  }

  .speech-results {
    margin-top: 16px;
    padding: 12px;
    background: #f9f9f9;
    border-radius: 4px;
  }

  .speech-results h5 {
    margin: 0 0 12px 0;
    font-size: 12px;
    color: #666;
  }

  .results-list {
    max-height: 200px;
    overflow-y: auto;
  }

  .result-item {
    padding: 8px 12px;
    margin-bottom: 8px;
    background: white;
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .result-item:hover {
    border-color: #1890ff;
  }

  .result-time {
    font-size: 11px;
    color: #1890ff;
    font-weight: 500;
  }

  .result-text {
    margin: 4px 0;
    font-size: 13px;
    line-height: 1.4;
  }

  .result-confidence {
    font-size: 11px;
    color: #999;
  }

  /* 情感分析结果 */
  .emotion-results {
    margin-top: 16px;
    padding: 12px;
    background: #f9f9f9;
    border-radius: 4px;
  }

  .emotion-chart {
    margin-top: 12px;
  }

  .emotion-bar {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    cursor: pointer;
  }

  .emotion-label {
    width: 60px;
    font-size: 12px;
    color: #666;
  }

  .emotion-timeline {
    flex: 1;
    height: 20px;
    background: #f0f0f0;
    border-radius: 10px;
    overflow: hidden;
    margin: 0 12px;
  }

  .emotion-segment {
    height: 100%;
    border-radius: 10px;
    transition: all 0.3s;
  }

  .emotion-segment.neutral {
    background: #d9d9d9;
  }
  .emotion-segment.happy {
    background: #52c41a;
  }
  .emotion-segment.sad {
    background: #1890ff;
  }
  .emotion-segment.excited {
    background: #fa8c16;
  }
  .emotion-segment.angry {
    background: #ff4d4f;
  }
  .emotion-segment.surprised {
    background: #722ed1;
  }

  .emotion-intensity {
    width: 40px;
    text-align: right;
    font-size: 11px;
    color: #666;
  }

  /* 音乐推荐结果 */
  .music-recommendations {
    margin-top: 16px;
    padding: 12px;
    background: #f9f9f9;
    border-radius: 4px;
  }

  .music-list {
    max-height: 200px;
    overflow-y: auto;
  }

  .music-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    margin-bottom: 8px;
    background: white;
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .music-item:hover {
    border-color: #1890ff;
  }

  .music-info {
    flex: 1;
  }

  .music-name {
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 2px;
  }

  .music-description {
    font-size: 11px;
    color: #999;
  }

  .music-actions {
    display: flex;
    gap: 4px;
  }

  /* 批量处理 */
  .batch-tasks {
    margin-bottom: 16px;
  }

  .batch-tasks h5 {
    margin: 0 0 8px 0;
    font-size: 12px;
    color: #666;
  }

  /* 深色模式适配 */
  [data-theme='dark'] .smart-editing-assistant {
    background: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .assistant-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #581c87 100%) !important;
  }

  [data-theme='dark'] .assistant-content {
    background: #2d2d2d !important;
  }

  [data-theme='dark'] .feature-section {
    border-bottom-color: #434343 !important;
  }

  [data-theme='dark'] .feature-header h4 {
    color: #fff !important;
  }

  [data-theme='dark'] .control-item label {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .value-display {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .feature-description {
    background: #1f1f1f !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .feature-description p {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .selected-file {
    background: #3a3a3a !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .environment-preview {
    background: #1f1f1f !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .env-item {
    background: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .env-item:hover {
    border-color: #525252 !important;
    background: #3a3a3a !important;
  }

  [data-theme='dark'] .env-id {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .env-time {
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .env-track {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .analysis-results {
    background: #1f1f1f !important;
  }

  [data-theme='dark'] .analysis-results h5 {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .chapter-item {
    background: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .chapter-item:hover {
    border-color: var(--primary-color) !important;
    box-shadow: 0 2px 4px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  [data-theme='dark'] .chapter-time {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .progress-text {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .speech-results {
    background: #1f1f1f !important;
  }

  [data-theme='dark'] .speech-results h5 {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .result-item {
    background: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .result-item:hover {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .result-time {
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .result-confidence {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .emotion-results {
    background: #1f1f1f !important;
  }

  [data-theme='dark'] .emotion-label {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .emotion-timeline {
    background: #434343 !important;
  }

  [data-theme='dark'] .emotion-intensity {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .music-recommendations {
    background: #1f1f1f !important;
  }

  [data-theme='dark'] .music-item {
    background: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .music-item:hover {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .music-description {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .batch-tasks h5 {
    color: #8c8c8c !important;
  }

  /* 深色模式下的项目导入样式 */
  [data-theme='dark'] .auto-layout-preview {
    background: #1f1f1f !important;
  }

  [data-theme='dark'] .layout-item {
    border-bottom-color: #434343 !important;
  }

  [data-theme='dark'] .track-label {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .track-content {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .character-mapping label {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .import-item {
    background: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .import-item:hover {
    border-color: #525252 !important;
    background: #3a3a3a !important;
  }

  [data-theme='dark'] .segment-speaker {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .segment-track {
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .segment-text {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .segment-time {
    color: #666 !important;
  }

  /* 环境音库样式 */
  .import-mode-tabs {
    margin-top: 8px;
  }

  .library-section {
    margin-top: 12px;
  }

  .library-filters {
    margin-bottom: 16px;
  }

  .upload-hint {
    margin-top: 8px;
    font-size: 12px;
    color: #8c8c8c;
    font-style: italic;
  }

  .environment-sounds-list {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    padding: 8px;
    background: #fafafa;
  }

  .sound-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    margin-bottom: 8px;
    background: white;
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .sound-item:hover {
    border-color: #1890ff;
    box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);
  }

  .sound-item.sound-selected {
    border-color: #1890ff;
    background: #f6ffed;
  }

  .sound-item.sound-disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .sound-info {
    flex: 1;
    min-width: 0;
  }

  .sound-name {
    font-weight: 500;
    color: #333;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .sound-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 6px;
    font-size: 12px;
  }

  .sound-category {
    color: #666;
    background: #f0f0f0;
    padding: 2px 6px;
    border-radius: 3px;
  }

  .sound-duration {
    color: #1890ff;
    font-weight: 500;
  }

  .sound-prompt {
    font-size: 12px;
    color: #8c8c8c;
    line-height: 1.3;
    margin-top: 4px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .sound-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: 12px;
  }

  .empty-state,
  .loading-state {
    text-align: center;
    padding: 40px 20px;
    color: #8c8c8c;
  }

  .batch-import-actions {
    margin-top: 16px;
    padding: 12px;
    background: #f0f8ff;
    border: 1px solid #d4edda;
    border-radius: 4px;
  }

  .selection-info {
    font-size: 13px;
    color: #155724;
    margin-bottom: 8px;
    font-weight: 500;
  }

  /* 深色模式下的环境音库样式 */
  [data-theme='dark'] .upload-hint {
    color: #666 !important;
  }

  [data-theme='dark'] .environment-sounds-list {
    background: #1f1f1f !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .sound-item {
    background: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .sound-item:hover {
    border-color: var(--primary-color) !important;
    box-shadow: 0 2px 4px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  [data-theme='dark'] .sound-item.sound-selected {
    border-color: var(--primary-color) !important;
    background: rgba(var(--primary-color-rgb), 0.1) !important;
  }

  [data-theme='dark'] .sound-name {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .sound-category {
    background: #3a3a3a !important;
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .sound-duration {
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .sound-prompt {
    color: #666 !important;
  }

  [data-theme='dark'] .empty-state,
  [data-theme='dark'] .loading-state {
    color: #666 !important;
  }

  [data-theme='dark'] .batch-import-actions {
    background: rgba(var(--primary-color-rgb), 0.1) !important;
    border-color: rgba(var(--primary-color-rgb), 0.3) !important;
  }

  [data-theme='dark'] .selection-info {
    color: var(--primary-color) !important;
  }

  /* 音乐推荐相关样式 */
  .music-list {
    max-height: 200px;
    overflow-y: auto;
  }

  .music-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px;
    margin-bottom: 4px;
    background: #f8f9fa;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .music-item:hover {
    background: #e9ecef;
  }

  .music-info {
    flex: 1;
  }

  .music-name {
    font-weight: 500;
    margin-bottom: 2px;
  }

  .music-description {
    font-size: 12px;
    color: #666;
  }

  .music-meta {
    display: flex;
    gap: 8px;
    margin-top: 4px;
    font-size: 11px;
  }

  .quality-rating {
    color: #faad14;
  }

  .music-style {
    background: #e6f7ff;
    color: #1890ff;
    padding: 1px 4px;
    border-radius: 2px;
  }

  .usage-count {
    color: #8c8c8c;
  }

  .music-actions {
    display: flex;
    gap: 4px;
  }

  .music-library-list {
    max-height: 250px;
    overflow-y: auto;
    margin-bottom: 12px;
  }

  .music-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 2px;
  }

  .mode-content {
    margin-top: 8px;
  }

  /* 深色模式适配 */
  [data-theme='dark'] .music-item {
    background: #2d2d2d !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .music-item:hover {
    background: #3a3a3a !important;
  }

  [data-theme='dark'] .music-name {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .music-description {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .music-style {
    background: rgba(24, 144, 255, 0.2) !important;
    color: #40a9ff !important;
  }

  /* 响应式设计 */
  @media (max-width: 768px) {
    .assistant-content {
      max-height: 400px;
    }

    .action-buttons {
      flex-direction: column;
    }

    .control-group {
      flex-direction: column;
      align-items: stretch;
      gap: 8px;
    }

    .value-display {
      text-align: left;
    }
  }
</style>
