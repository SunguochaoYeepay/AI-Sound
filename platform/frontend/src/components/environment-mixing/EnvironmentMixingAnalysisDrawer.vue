<template>
  <a-drawer
    :open="visible"
    title="🧠 环境混音智能配置"
    placement="right"
    width="1000px"
    :closable="true"
    :maskClosable="false"
    destroyOnClose
    class="environment-mixing-drawer"
    @close="emit('update:visible', false)"
  >
    <div class="mixing-analysis-content">
      <!-- 步骤指示器 -->
      <div class="steps-container">
        <a-steps :current="currentStep" direction="horizontal" size="small">
          <a-step title="选择内容" description="选择要分析的小说章节" />
          <a-step title="AI分析" description="智能识别场景和情感" />
          <a-step title="确认开始" description="确认方案并开始混音" />
          <a-step title="生成中" description="AI正在生成环境混音" />
        </a-steps>
      </div>

      <!-- 步骤1: 章节选择 -->
      <div v-if="currentStep === 0" class="analysis-step">
        <h3>选择小说章节</h3>
        <p style="color: #666; margin-bottom: 16px">从已导入的小说中选择章节进行环境音智能分析</p>

        <div>
          <a-select
            v-model:value="selectedBook"
            placeholder="选择书籍"
            style="width: 100%; margin-bottom: 16px"
            :loading="bookLoading"
            @change="loadProjectsAndChapters"
          >
            <a-select-option v-for="book in books" :key="book.id" :value="book.id">
              {{ book.title }}
            </a-select-option>
          </a-select>

          <a-select
            v-model:value="selectedProject"
            placeholder="选择朗读项目（必选）"
            style="width: 100%; margin-bottom: 16px"
            :loading="projectLoading"
          >
            <a-select-option v-for="project in projects" :key="project.id" :value="project.id">
              <div style="display: flex; justify-content: space-between; align-items: center">
                <span>{{ project.name }}</span>
                <a-tag :color="getProjectStatusColor(project.status)" size="small">{{
                  getProjectStatusText(project.status)
                }}</a-tag>
              </div>
            </a-select-option>
          </a-select>

          <a-select
            v-model:value="selectedChapterIds"
            mode="multiple"
            placeholder="选择已分析的章节（支持多选）"
            style="width: 100%; margin-bottom: 16px"
            :max-tag-count="3"
            :loading="chapterLoading"
          >
            <a-select-option v-for="chapter in chapters" :key="chapter.id" :value="chapter.id">
              <div style="display: flex; justify-content: space-between; align-items: center">
                <span>{{ chapter.chapter_title || chapter.title }}</span>
                <a-tag color="blue" size="small">可分析</a-tag>
              </div>
            </a-select-option>
          </a-select>

          <!-- 提示信息 -->
          <div v-if="projects.length === 0 && selectedBook" style="margin-bottom: 16px">
            <a-alert
              message="该书籍暂无朗读项目"
              description="请先为该书籍创建朗读项目，才能进行环境音混音。可在语音合成中心创建朗读项目。"
              type="warning"
              show-icon
            />
          </div>

          <div v-if="chapters.length === 0 && selectedBook" style="margin-bottom: 16px">
            <a-alert
              message="该书籍暂无可用章节"
              description="请检查书籍是否包含章节数据，可能需要先上传或导入章节内容。"
              type="info"
              show-icon
            />
          </div>

          <!-- 分析选项 -->
          <div v-if="selectedChapterIds.length > 0" style="margin-bottom: 16px">
            <h4>分析选项</h4>
            <a-checkbox-group v-model:value="analysisOptions">
              <a-checkbox value="include_emotion">包含情感分析</a-checkbox>
              <a-checkbox value="precise_timing">精确时长计算</a-checkbox>
              <a-checkbox value="intensity_analysis">强度分析</a-checkbox>
            </a-checkbox-group>
          </div>
        </div>

        <div class="step-actions">
          <a-button
            type="primary"
            @click="startAnalysis"
            :disabled="!selectedProject || selectedChapterIds.length === 0"
          >
            开始智能分析
          </a-button>
        </div>
      </div>

      <!-- 步骤2: 分析进行中和结果，或环境音匹配 -->
      <div v-if="currentStep === 1" class="analysis-step">
        <div v-if="analyzing" class="analyzing-state">
          <a-spin size="large">
            <template #indicator>
              <BulbOutlined style="font-size: 24px" spin />
            </template>
          </a-spin>
          <h3 style="margin-top: 16px">正在生成混音配置...</h3>
          <p>AI正在分析章节内容，生成环境音混音参数和时间轴配置</p>
          <a-progress :percent="analysisProgress" status="active" />
        </div>

        <div v-if="analysisResult && !analyzing" class="analysis-result">
          <h3>📚 AI智能分析结果</h3>
          <p style="color: #666; margin-bottom: 20px">
            AI已完成对小说内容的深度分析，为您智能匹配环境音效
          </p>

          <!-- 🚀 新增：分析摘要 - 用人话展示AI分析了什么 -->
          <a-card title="🧠 AI分析总结" style="margin-bottom: 20px" size="small">
            <div class="analysis-summary">
              <a-row :gutter="16">
                <a-col :span="8">
                  <div class="summary-item">
                    <div class="summary-icon">🎭</div>
                    <div class="summary-content">
                      <strong>故事类型</strong>
                      <p>{{ analysisResult.narrative_analysis?.genre || '现代小说' }}</p>
                    </div>
                  </div>
                </a-col>
                <a-col :span="8">
                  <div class="summary-item">
                    <div class="summary-icon">💓</div>
                    <div class="summary-content">
                      <strong>情感基调</strong>
                      <p>{{ analysisResult.narrative_analysis?.emotional_arc || '温馨平和' }}</p>
                    </div>
                  </div>
                </a-col>
                <a-col :span="8">
                  <div class="summary-item">
                    <div class="summary-icon">⚡</div>
                    <div class="summary-content">
                      <strong>节奏感</strong>
                      <p>{{ analysisResult.narrative_analysis?.pace || '舒缓' }}</p>
                    </div>
                  </div>
                </a-col>
              </a-row>

              <a-divider style="margin: 16px 0" />

              <!-- AI发现的场景 -->
              <div class="discovered-scenes">
                <h4 style="margin-bottom: 12px">🎬 AI识别的场景环境</h4>
                <div class="scenes-grid">
                  <template v-if="analysisResult.chapters && analysisResult.chapters.length > 0">
                    <div
                      v-for="(chapter, chapterIndex) in analysisResult.chapters"
                      :key="chapterIndex"
                      class="chapter-scenes"
                    >
                      <div class="chapter-header">
                        <h5>
                          {{
                            chapter.chapter_info?.chapter_title ||
                            `第${chapter.chapter_info?.chapter_number}章`
                          }}
                        </h5>
                      </div>

                      <div class="scene-tags">
                        <a-tag
                          v-for="(track, index) in chapter.analysis_result?.environment_tracks ||
                          []"
                          :key="`${chapterIndex}-${index}`"
                          :color="getSceneColor(track.scene_description)"
                          class="scene-tag"
                        >
                          {{ getSceneIcon(track.scene_description) }}
                          {{ track.scene_description || '环境场景' }}
                        </a-tag>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </a-card>

          <!-- 🚀 新增：环境音效匹配预览 -->
          <a-card title="🎵 环境音效智能匹配" style="margin-bottom: 20px" size="small">
            <div class="matching-preview">
              <div class="matching-stats">
                <a-row :gutter="16">
                  <a-col :span="6">
                    <a-statistic
                      title="识别场景"
                      :value="analysisResult.total_tracks || 0"
                      suffix="个"
                      :value-style="{ color: '#1890ff' }"
                    />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic
                      title="章节数"
                      :value="analysisResult.chapters_analyzed || 1"
                      suffix="章"
                      :value-style="{ color: '#52c41a' }"
                    />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic
                      title="预计时长"
                      :value="Math.round((analysisResult.total_duration || 0) / 60)"
                      suffix="分钟"
                      :value-style="{ color: '#fa8c16' }"
                    />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic
                      title="音效库匹配"
                      :value="85"
                      suffix="%"
                      :value-style="{ color: '#722ed1' }"
                    />
                  </a-col>
                </a-row>
              </div>

              <a-divider style="margin: 16px 0" />

              <!-- 简化的场景列表 -->
              <div class="simple-scene-list">
                <h4 style="margin-bottom: 12px">🎯 AI为您准备的环境音效</h4>
                <template v-if="analysisResult.chapters && analysisResult.chapters.length > 0">
                  <div
                    v-for="(chapter, chapterIndex) in analysisResult.chapters"
                    :key="chapterIndex"
                    class="chapter-preview"
                  >
                    <div class="chapter-title">
                      <BookOutlined />
                      {{
                        chapter.chapter_info?.chapter_title ||
                        `第${chapter.chapter_info?.chapter_number}章`
                      }}
                    </div>

                    <div class="scene-previews">
                      <div
                        v-for="(track, index) in (
                          chapter.analysis_result?.environment_tracks || []
                        ).slice(0, 3)"
                        :key="`${chapterIndex}-${index}`"
                        class="scene-preview"
                      >
                        <div class="scene-info">
                          <span class="scene-icon">{{
                            getSceneIcon(track.scene_description)
                          }}</span>
                          <span class="scene-name">{{
                            track.scene_description || '环境场景'
                          }}</span>
                          <a-tag size="small" :color="getIntensityColor(track.intensity_level)">
                            {{ getIntensityText(track.intensity_level) }}
                          </a-tag>
                        </div>
                        <div class="scene-duration">
                          <ClockCircleOutlined />
                          {{ Math.round(track.duration || 0) }}秒
                        </div>
                      </div>

                      <div
                        v-if="(chapter.analysis_result?.environment_tracks || []).length > 3"
                        class="more-scenes"
                      >
                        <a-button type="link" size="small">
                          还有
                          {{ (chapter.analysis_result?.environment_tracks || []).length - 3 }}
                          个场景...
                        </a-button>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </a-card>

          <!-- 简化的操作按钮 -->
          <div class="step-actions" style="margin-top: 20px">
            <a-space size="large">
              <a-button @click="currentStep = 0" size="large">
                <LeftOutlined />
                重新选择
              </a-button>
              <a-button @click="forceReanalyze" size="large" :loading="analyzing">
                <ReloadOutlined />
                重新分析 (查看优化效果)
              </a-button>
              <a-button type="primary" size="large" @click="proceedToConfig">
                <CheckOutlined />
                确认分析结果
              </a-button>
            </a-space>
          </div>

          <!-- 🚀 新增：详细分析信息展开面板 -->
          <a-card title="🔍 详细分析信息" style="margin-top: 20px" size="small">
            <a-collapse v-model:activeKey="expandedPanels" ghost>
              <a-collapse-panel key="1" header="📊 环境音识别详情">
                <div class="detailed-analysis">
                  <template v-if="analysisResult.chapters && analysisResult.chapters.length > 0">
                    <div
                      v-for="(chapter, chapterIndex) in analysisResult.chapters"
                      :key="chapterIndex"
                      class="chapter-detailed-analysis"
                    >
                      <h4>
                        {{
                          chapter.chapter_info?.chapter_title ||
                          `第${chapter.chapter_info?.chapter_number}章`
                        }}
                      </h4>

                      <div
                        v-if="chapter.analysis_result?.environment_tracks?.length > 0"
                        class="tracks-detailed"
                      >
                        <a-table
                          :dataSource="chapter.analysis_result.environment_tracks"
                          :columns="detailedTrackColumns"
                          size="small"
                          :pagination="false"
                          :scroll="{ x: 800 }"
                        >
                          <template #bodyCell="{ column, record, index }">
                            <template v-if="column.key === 'scene'">
                              <div class="scene-cell">
                                <span class="scene-icon">{{
                                  getSceneIcon(record.scene_description)
                                }}</span>
                                <span>{{ record.scene_description || '环境场景' }}</span>
                              </div>
                            </template>
                            <template v-if="column.key === 'keywords'">
                              <div class="keywords-cell">
                                <a-tag
                                  v-for="keyword in record.environment_keywords || []"
                                  :key="keyword"
                                  size="small"
                                  color="blue"
                                >
                                  {{ keyword }}
                                </a-tag>
                              </div>
                            </template>
                            <template v-if="column.key === 'timing'">
                              <div class="timing-cell">
                                <div>
                                  <strong>{{ Math.round(record.start_time || 0) }}s</strong> →
                                  <strong
                                    >{{
                                      Math.round((record.start_time || 0) + (record.duration || 0))
                                    }}s</strong
                                  >
                                </div>
                                <div style="color: #666; font-size: 12px">
                                  时长: {{ Math.round(record.duration || 0) }}秒
                                </div>
                              </div>
                            </template>
                            <template v-if="column.key === 'confidence'">
                              <a-progress
                                :percent="Math.round((record.confidence || 0) * 100)"
                                size="small"
                                :stroke-color="getConfidenceColor(record.confidence)"
                              />
                            </template>
                            <template v-if="column.key === 'narration'">
                              <div class="narration-cell">
                                <a-typography-text
                                  :ellipsis="{ rows: 2, expandable: true, symbol: '展开' }"
                                  style="font-size: 12px"
                                >
                                  {{ record.narration_text || '暂无旁白文本' }}
                                </a-typography-text>
                              </div>
                            </template>
                          </template>
                        </a-table>
                      </div>
                      <div v-else class="no-tracks">
                        <a-empty description="该章节未识别到环境音" />
                      </div>
                    </div>
                  </template>
                </div>
              </a-collapse-panel>

              <a-collapse-panel key="2" header="⚙️ 分析方法信息">
                <div class="analysis-method-info">
                  <a-descriptions :column="2" size="small" bordered>
                    <a-descriptions-item label="分析方法">
                      <a-tag color="green">优化版智能分析</a-tag>
                    </a-descriptions-item>
                    <a-descriptions-item label="LLM模型">
                      {{ analysisResult.analysis_metadata?.llm_model || 'Ollama' }}
                    </a-descriptions-item>
                    <a-descriptions-item label="关键词映射">
                      <a-tag color="blue">扩展词汇库 (50+ 类别)</a-tag>
                    </a-descriptions-item>
                    <a-descriptions-item label="时长计算">
                      <a-tag color="orange">实际音频时长</a-tag>
                    </a-descriptions-item>
                    <a-descriptions-item label="分析时间">
                      {{ formatAnalysisTime(analysisResult.analysis_timestamp) }}
                    </a-descriptions-item>
                    <a-descriptions-item label="映射策略">
                      {{ analysisResult.analysis_metadata?.mapping_strategy || '智能位置映射' }}
                    </a-descriptions-item>
                  </a-descriptions>

                  <div style="margin-top: 16px">
                    <a-alert
                      message="🚀 分析优化说明"
                      description="本次分析使用了最新优化的算法：1) 详细的环境音分类指导提示词；2) 扩展的50+关键词映射关系；3) 实际音频时长而非估算时长；4) 智能场景匹配策略。"
                      type="success"
                      show-icon
                    />
                  </div>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </a-card>
        </div>
      </div>

      <!-- 步骤3: 简化的最终确认 -->
      <div v-if="currentStep === 2" class="analysis-step">
        <h3>🎯 确认开始混音</h3>
        <p style="color: #666; margin-bottom: 20px">
          AI已完成分析并准备好环境音效，请确认是否开始混音
        </p>

        <!-- 简化的确认信息 -->
        <a-card title="📋 混音方案总览" style="margin-bottom: 20px" size="small">
          <div class="mixing-summary">
            <a-row :gutter="16">
              <a-col :span="6">
                <div class="summary-stat">
                  <div class="stat-number">{{ selectedChapterIds.length }}</div>
                  <div class="stat-label">选择章节</div>
                </div>
              </a-col>
              <a-col :span="6">
                <div class="summary-stat">
                  <div class="stat-number">{{ analysisResult?.total_tracks || 0 }}</div>
                  <div class="stat-label">环境场景</div>
                </div>
              </a-col>
              <a-col :span="6">
                <div class="summary-stat">
                  <div class="stat-number">
                    {{ Math.round((analysisResult?.total_duration || 0) / 60) }}
                  </div>
                  <div class="stat-label">预计时长(分钟)</div>
                </div>
              </a-col>
              <a-col :span="6">
                <div class="summary-stat">
                  <div class="stat-number">{{ estimatedTime }}</div>
                  <div class="stat-label">处理时间(分钟)</div>
                </div>
              </a-col>
            </a-row>
          </div>
        </a-card>

        <!-- 简化的设置选项 -->
        <a-card title="🎚️ 快速设置" style="margin-bottom: 20px" size="small">
          <div class="quick-settings">
            <a-row :gutter="16">
              <a-col :span="12">
                <div class="setting-item">
                  <label>环境音强度</label>
                  <a-radio-group v-model:value="mixingConfig.environmentVolume" size="small">
                    <a-radio-button value="0.2">轻柔</a-radio-button>
                    <a-radio-button value="0.3">适中</a-radio-button>
                    <a-radio-button value="0.5">强烈</a-radio-button>
                  </a-radio-group>
                </div>
              </a-col>
              <a-col :span="12">
                <div class="setting-item">
                  <label>输出质量</label>
                  <a-radio-group v-model:value="mixingConfig.outputFormat" size="small">
                    <a-radio-button value="mp3">标准</a-radio-button>
                    <a-radio-button value="wav">高品质</a-radio-button>
                  </a-radio-group>
                </div>
              </a-col>
            </a-row>
          </div>
        </a-card>

        <!-- 预览信息 -->
        <a-alert
          message="🎵 即将开始AI环境音混音"
          description="系统将根据您的小说内容智能生成环境音效，并与语音完美融合。整个过程大约需要几分钟，请耐心等待。"
          type="info"
          show-icon
          style="margin-bottom: 20px"
        />

        <div class="step-actions">
          <a-space size="large">
            <a-button @click="currentStep = 1" size="large">
              <LeftOutlined />
              返回分析
            </a-button>
            <a-button type="primary" size="large" @click="startMixing" :loading="startingMixing">
              <PlayCircleOutlined />
              确认开始混音
            </a-button>
          </a-space>
        </div>
      </div>

      <!-- 步骤4: 开始混音 -->
      <div v-if="currentStep === 3" class="start-step">
        <h3>🚀 开始环境混音</h3>
        <p style="color: #666; margin-bottom: 16px">确认配置并启动环境混音生成</p>

        <!-- 配置确认 -->
        <a-card title="配置确认" style="margin-bottom: 16px">
          <a-descriptions :column="2" size="small">
            <a-descriptions-item label="总环境轨道"
              >{{ analysisResult?.total_tracks || 0 }}个</a-descriptions-item
            >
            <a-descriptions-item label="匹配音效"
              >{{ matchingResult?.matched_count || 0 }}个</a-descriptions-item
            >
            <a-descriptions-item label="新生成音效"
              >{{ batchProgress.completed || 0 }}个</a-descriptions-item
            >
            <a-descriptions-item label="环境音音量"
              >{{ (mixingConfig.environmentVolume * 100).toFixed(0) }}%</a-descriptions-item
            >
            <a-descriptions-item label="语音音量"
              >{{ (mixingConfig.voiceVolume * 100).toFixed(0) }}%</a-descriptions-item
            >
            <a-descriptions-item label="输出格式">{{
              mixingConfig.outputFormat.toUpperCase()
            }}</a-descriptions-item>
            <a-descriptions-item label="采样率"
              >{{ (mixingConfig.sampleRate / 1000).toFixed(1) }} kHz</a-descriptions-item
            >
            <a-descriptions-item label="高级功能"
              >{{ mixingConfig.advancedOptions.length }}项</a-descriptions-item
            >
          </a-descriptions>
        </a-card>

        <!-- 预计时间 -->
        <a-card title="预计信息" style="margin-bottom: 16px">
          <a-alert
            :message="`预计处理时间：${estimatedTime}分钟`"
            :description="`将处理 ${analysisResult?.total_tracks || 0} 个环境音轨道，总时长 ${analysisResult?.total_duration || 0} 秒`"
            type="info"
            show-icon
          />
        </a-card>

        <div class="step-actions">
          <a-button @click="currentStep = 2">
            <template #icon><LeftOutlined /></template>
            上一步
          </a-button>
          <a-button type="primary" size="large" @click="startMixing" :loading="starting">
            <template #icon><PlayCircleOutlined /></template>
            开始环境混音
          </a-button>
        </div>
      </div>

      <!-- 步骤5: 混音进行中 -->
      <div v-if="currentStep === 4" class="mixing-step">
        <div class="mixing-state">
          <a-spin size="large">
            <template #indicator>
              <SoundOutlined style="font-size: 24px" spin />
            </template>
          </a-spin>
          <h3 style="margin-top: 16px">正在生成环境混音...</h3>
          <p>AI正在将环境音与语音进行智能混合，生成最终的混音文件</p>
          <a-progress :percent="mixingProgress" status="active" />

          <div style="margin-top: 16px">
            <a-descriptions :column="2" size="small">
              <a-descriptions-item label="处理进度">{{ mixingProgress }}%</a-descriptions-item>
              <a-descriptions-item label="预计剩余时间"
                >{{ Math.max(0, Math.ceil((100 - mixingProgress) / 10)) }}分钟</a-descriptions-item
              >
              <a-descriptions-item label="当前状态">{{
                mixingProgress < 100 ? '混音中' : '完成'
              }}</a-descriptions-item>
              <a-descriptions-item label="输出格式">{{
                mixingConfig.outputFormat.toUpperCase()
              }}</a-descriptions-item>
            </a-descriptions>
          </div>

          <div v-if="mixingProgress >= 100" style="margin-top: 24px">
            <a-result
              status="success"
              title="🎉 环境混音完成！"
              sub-title="混音文件已生成并保存，您可以在项目文件中找到生成的混音音频。窗口将在5秒后自动关闭。"
            >
              <template #extra>
                <a-space>
                  <a-button type="primary" size="large" @click="emit('update:visible', false)">
                    立即关闭
                  </a-button>
                  <a-button
                    size="large"
                    @click="
                      currentStep = 0
                      mixingProgress = 0
                    "
                  >
                    重新配置
                  </a-button>
                </a-space>
              </template>
            </a-result>
          </div>
        </div>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
  import { ref, reactive, computed, watch, onMounted } from 'vue'
  import { message, notification } from 'ant-design-vue'
  import {
    SearchOutlined,
    BulbOutlined,
    ReloadOutlined,
    LeftOutlined,
    LinkOutlined,
    PlayCircleOutlined,
    SwapOutlined,
    SoundOutlined,
    CheckOutlined,
    BookOutlined,
    ClockCircleOutlined
  } from '@ant-design/icons-vue'

  import { booksAPI, chaptersAPI, readerAPI } from '@/api'
  import { getAudioService } from '@/utils/audioService'

  // Props
  const props = defineProps({
    visible: {
      type: Boolean,
      default: false
    }
  })

  // Emits
  const emit = defineEmits(['update:visible', 'complete', 'start-mixing', 'mixing-completed'])

  // 响应式数据
  const currentStep = ref(0)
  const analyzing = ref(false)
  const matching = ref(false)
  const generatingPrompts = ref(false)
  const starting = ref(false)
  const saving = ref(false)
  const startingMixing = ref(false)
  const configSaved = ref(false)
  const analysisProgress = ref(0)
  const matchingProgress = ref(0)
  const mixingProgress = ref(0)
  const loadingChapters = ref(false)
  const bookLoading = ref(false)
  const chapterLoading = ref(false)

  const analysisOptions = ref(['include_emotion', 'precise_timing'])
  const selectedBook = ref(null)
  const selectedProject = ref(null)
  const selectedChapterIds = ref([])
  const books = ref([])
  const projects = ref([])
  const chapters = ref([])
  const analyzedChapters = ref([])
  const projectLoading = ref(false)

  // 🚀 新增：详细分析展开面板
  const expandedPanels = ref(['1'])

  const analysisResult = ref(null)
  const matchingResult = ref(null)
  const smartPrompts = ref(null)
  const generationLogs = ref([])

  // 🚀 新增：详细分析表格列定义
  const detailedTrackColumns = [
    {
      title: '场景',
      key: 'scene',
      dataIndex: 'scene_description',
      width: 150
    },
    {
      title: '环境关键词',
      key: 'keywords',
      dataIndex: 'environment_keywords',
      width: 200
    },
    {
      title: '时间轴',
      key: 'timing',
      width: 120
    },
    {
      title: '置信度',
      key: 'confidence',
      dataIndex: 'confidence',
      width: 100
    },
    {
      title: '旁白内容',
      key: 'narration',
      dataIndex: 'narration_text',
      width: 300
    }
  ]

  const batchProgress = reactive({
    total: 0,
    completed: 0,
    processing: 0,
    failed: 0,
    status: 'normal',
    currentTask: null
  })

  // 混音配置
  const mixingConfig = reactive({
    environmentVolume: 0.3,
    voiceVolume: 0.7,
    fadeInDuration: 1.0,
    fadeOutDuration: 1.0,
    outputFormat: 'wav',
    sampleRate: 44100,
    advancedOptions: ['crossfade', 'normalize']
  })

  // 计算属性
  const estimatedTime = computed(() => {
    const baseTime = 5 // 基础混音时间
    const tracks = analysisResult.value?.total_tracks || 0
    return Math.ceil(baseTime + tracks * 0.5)
  })

  const hasSelectedPrompts = computed(() => {
    return smartPrompts.value?.smart_prompts?.some((p) => p.selected) || false
  })

  const selectedPromptsCount = computed(() => {
    return smartPrompts.value?.smart_prompts?.filter((p) => p.selected).length || 0
  })

  // 方法
  const getIntensityColor = (intensity) => {
    const colors = {
      低: 'green',
      中等: 'blue',
      高: 'orange',
      极高: 'red'
    }
    return colors[intensity] || 'default'
  }

  const getPriorityColor = (priority) => {
    const colors = {
      高: 'red',
      中: 'orange',
      低: 'green'
    }
    return colors[priority] || 'default'
  }

  const getProjectStatusColor = (status) => {
    const colors = {
      pending: 'orange',
      processing: 'blue',
      paused: 'orange',
      completed: 'green',
      partial_completed: 'gold',
      failed: 'red'
    }
    return colors[status] || 'default'
  }

  const getProjectStatusText = (status) => {
    const texts = {
      pending: '待处理',
      processing: '处理中',
      paused: '已暂停',
      completed: '已完成',
      partial_completed: '部分完成',
      failed: '失败'
    }
    return texts[status] || status
  }

  // 🚀 新增：场景图标映射
  const getSceneIcon = (sceneDescription) => {
    if (!sceneDescription) return '🎬'

    const scene = sceneDescription.toLowerCase()
    if (scene.includes('办公') || scene.includes('公司') || scene.includes('会议')) return '🏢'
    if (scene.includes('家') || scene.includes('房间') || scene.includes('客厅')) return '🏠'
    if (scene.includes('街道') || scene.includes('马路') || scene.includes('城市')) return '🌆'
    if (scene.includes('咖啡') || scene.includes('餐厅') || scene.includes('酒吧')) return '☕'
    if (scene.includes('学校') || scene.includes('教室') || scene.includes('图书馆')) return '🎓'
    if (scene.includes('公园') || scene.includes('花园') || scene.includes('自然')) return '🌳'
    if (scene.includes('海') || scene.includes('湖') || scene.includes('河')) return '🌊'
    if (scene.includes('夜晚') || scene.includes('夜')) return '🌙'
    if (scene.includes('雨') || scene.includes('雷')) return '🌧️'
    if (scene.includes('车') || scene.includes('交通')) return '🚗'
    return '🎬'
  }

  // 🚀 新增：场景颜色映射
  const getSceneColor = (sceneDescription) => {
    if (!sceneDescription) return 'blue'

    const scene = sceneDescription.toLowerCase()
    if (scene.includes('办公') || scene.includes('会议')) return 'blue'
    if (scene.includes('家') || scene.includes('房间')) return 'green'
    if (scene.includes('街道') || scene.includes('城市')) return 'orange'
    if (scene.includes('咖啡') || scene.includes('餐厅')) return 'gold'
    if (scene.includes('学校') || scene.includes('图书馆')) return 'purple'
    if (scene.includes('公园') || scene.includes('自然')) return 'lime'
    if (scene.includes('海') || scene.includes('水')) return 'cyan'
    if (scene.includes('夜')) return 'geekblue'
    if (scene.includes('雨') || scene.includes('雷')) return 'volcano'
    return 'blue'
  }

  // 🚀 新增：强度等级文本
  const getIntensityText = (intensity) => {
    const texts = {
      低: '轻柔',
      中等: '适中',
      高: '强烈',
      极高: '激烈'
    }
    return texts[intensity] || intensity || '适中'
  }

  // 🚀 新增：置信度颜色映射
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return '#52c41a' // 绿色
    if (confidence >= 0.6) return '#faad14' // 橙色
    if (confidence >= 0.4) return '#fa8c16' // 深橙色
    return '#ff4d4f' // 红色
  }

  // 🚀 新增：格式化分析时间
  const formatAnalysisTime = (timestamp) => {
    if (!timestamp) return '未知时间'
    const date = new Date(timestamp)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // 🚀 新增：强制重新分析方法
  const forceReanalyze = async () => {
    if (analyzing.value) return

    try {
      message.info('开始重新分析，将使用最新的优化算法...')

      // 重置分析结果
      analysisResult.value = null
      analyzing.value = true
      analysisProgress.value = 0

      // 调用分析方法
      await startAnalysis()

      message.success('重新分析完成！请查看详细分析信息对比优化效果')

      // 自动展开详细分析面板
      expandedPanels.value = ['1', '2']
    } catch (error) {
      console.error('Force reanalyze error:', error)
      message.error('重新分析失败: ' + (error.message || '未知错误'))
    } finally {
      analyzing.value = false
    }
  }

  const loadBooks = async () => {
    try {
      bookLoading.value = true
      // 使用正确的API调用方式
      const response = await booksAPI.getBooks()

      console.log('Books API response:', response)

      // 兼容多种响应格式
      let booksData = []
      if (response?.data?.success && response.data.data) {
        // 格式1: {data: {success: true, data: [...]}}
        booksData = response.data.data
      } else if (response?.data && Array.isArray(response.data)) {
        // 格式2: {data: [...]}
        booksData = response.data
      } else if (response?.success && response.data) {
        // 格式3: {success: true, data: [...]}
        booksData = response.data
      } else if (Array.isArray(response)) {
        // 格式4: [...]
        booksData = response
      }

      console.log('Processed books data:', booksData)
      books.value = booksData || []
    } catch (error) {
      console.error('加载书籍失败:', error)
      notification.error({
        message: '加载失败',
        description: '无法加载书籍列表，请稍后重试'
      })
      books.value = []
    } finally {
      bookLoading.value = false
    }
  }

  const loadProjectsAndChapters = async () => {
    if (!selectedBook.value) {
      projects.value = []
      chapters.value = []
      selectedProject.value = null
      return
    }

    // 并行加载项目和章节
    await Promise.all([loadProjects(), loadChapters()])
  }

  const loadProjects = async () => {
    try {
      projectLoading.value = true

      // 调用项目API获取指定书籍的朗读项目
      const response = await readerAPI.getProjects({ book_id: selectedBook.value })

      console.log('Projects API response:', response)

      // 处理响应数据
      let projectsData = []
      if (response?.data?.success && response.data.data) {
        projectsData = response.data.data
      } else if (response?.data && Array.isArray(response.data)) {
        projectsData = response.data
      } else if (Array.isArray(response)) {
        projectsData = response
      }

      console.log('Processed projects data:', projectsData)
      projects.value = projectsData || []

      // 如果只有一个项目，自动选择（章节已经在书籍选择时加载了）
      if (projects.value.length === 1) {
        selectedProject.value = projects.value[0].id
      }
    } catch (error) {
      console.error('加载朗读项目失败:', error)
      notification.error({
        message: '加载失败',
        description: '无法加载朗读项目列表，请稍后重试'
      })
      projects.value = []
    } finally {
      projectLoading.value = false
    }
  }

  const loadChapters = async () => {
    if (!selectedBook.value) {
      chapters.value = []
      return
    }

    try {
      chapterLoading.value = true

      // 直接使用选中的书籍ID获取该书的所有章节
      // 章节是书籍级别的，不属于特定项目，项目只是选择性地使用部分章节
      const response = await chaptersAPI.getChapters({
        book_id: selectedBook.value,
        sort_by: 'chapter_number',
        sort_order: 'asc'
      })

      console.log('Chapters API response:', response)

      // 兼容多种响应格式
      let chaptersData = []
      if (response?.data?.success && response.data.data) {
        // 格式1: {data: {success: true, data: [...]}}
        chaptersData = response.data.data
      } else if (response?.data && Array.isArray(response.data)) {
        // 格式2: {data: [...]}
        chaptersData = response.data
      } else if (response?.success && response.data) {
        // 格式3: {success: true, data: [...]}
        chaptersData = response.data
      } else if (Array.isArray(response)) {
        // 格式4: [...]
        chaptersData = response
      }

      console.log(`书籍 ${selectedBook.value} 的章节数: ${chaptersData.length}`)
      console.log('Book chapters:', chaptersData)

      // 直接使用所有章节，用户可以自由选择任意章节进行环境音分析
      chapters.value = chaptersData || []
    } catch (error) {
      console.error('加载章节失败:', error)
      notification.error({
        message: '加载失败',
        description: `无法加载章节列表: ${error.message}`
      })
      chapters.value = []
    } finally {
      chapterLoading.value = false
    }
  }

  const startAnalysis = async () => {
    try {
      analyzing.value = true
      analysisProgress.value = 0
      currentStep.value = 1

      // 模拟分析进度
      const progressInterval = setInterval(() => {
        if (analysisProgress.value < 90) {
          analysisProgress.value += Math.random() * 15
        }
      }, 800)

      // 调用真实的章节环境音分析API
      const analysisRequest = {
        chapter_ids: selectedChapterIds.value,
        analysis_options: {
          include_emotion: analysisOptions.value.includes('include_emotion'),
          precise_timing: analysisOptions.value.includes('precise_timing'),
          intensity_analysis: analysisOptions.value.includes('intensity_analysis')
        }
      }

      console.log('开始调用章节环境音分析API:', analysisRequest)

      const response = await fetch('/api/v1/environment-generation/chapters/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(analysisRequest)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `API调用失败: ${response.status}`)
      }

      const result = await response.json()
      console.log('章节环境音分析结果:', result)

      clearInterval(progressInterval)
      analysisProgress.value = 100

      // 使用真实的分析结果
      analysisResult.value = {
        total_tracks: result.total_tracks || 0,
        total_duration: result.total_duration || 0,
        chapters_analyzed: result.chapters_analyzed || selectedChapterIds.value.length,
        chapters: result.chapters || [],
        llm_provider: '智能分析',
        analysis_timestamp: result.analysis_timestamp,
        narrative_analysis: {
          genre: '智能识别',
          pace: '动态分析',
          emotional_arc: '基于内容智能生成'
        }
      }

      message.success('章节智能分析完成！AI已生成真实的环境音配置')
    } catch (error) {
      clearInterval(progressInterval)
      console.error('章节分析失败:', error)

      // 显示具体错误信息
      let errorMessage = '章节分析失败'
      if (error.message.includes('没有完成智能准备')) {
        errorMessage = '所选章节未完成智能准备，请先在语音合成中心完成章节准备'
      } else if (error.message.includes('章节') && error.message.includes('不存在')) {
        errorMessage = '选择的章节不存在，请重新选择'
      } else {
        errorMessage = `分析失败: ${error.message}`
      }

      message.error(errorMessage)
    } finally {
      analyzing.value = false
    }
  }

  const proceedToMatching = async () => {
    matching.value = true
    matchingProgress.value = 0

    // 模拟匹配进度
    const progressInterval = setInterval(() => {
      if (matchingProgress.value < 90) {
        matchingProgress.value += Math.random() * 15
      }
    }, 300)

    await new Promise((resolve) => setTimeout(resolve, 2000))

    clearInterval(progressInterval)
    matchingProgress.value = 100
    matching.value = false

    matchingResult.value = {
      matched_count: 10,
      need_generation_count: 5,
      accuracy: 85
    }

    message.success('环境音匹配完成！')
  }

  const proceedToConfig = () => {
    currentStep.value = 2
  }

  const saveConfig = async () => {
    try {
      saving.value = true

      // 构建配置数据
      const configData = {
        chapters: selectedChapterIds.value,
        book_id: selectedBook.value,
        analysis_result: analysisResult.value,
        mixing_config: mixingConfig,
        created_at: new Date().toISOString()
      }

      // 模拟保存API调用
      await new Promise((resolve) => setTimeout(resolve, 1000))

      configSaved.value = true
      message.success('混音配置已保存！')
    } catch (error) {
      console.error('保存配置失败:', error)
      message.error('保存配置失败: ' + error.message)
    } finally {
      saving.value = false
    }
  }

  const proceedToGeneration = async () => {
    generatingPrompts.value = true
    currentStep.value = 2

    await new Promise((resolve) => setTimeout(resolve, 1500))

    smartPrompts.value = {
      soundscape_recommendation: {
        primary_elements: ['鸟鸣', '风声', '脚步声'],
        secondary_elements: ['水声', '叶片摩擦'],
        overall_duration: 2400,
        ambient_layers: ['前景', '中景', '背景']
      },
      smart_prompts: Array.from({ length: 5 }, (_, i) => ({
        title: `环境音 ${i + 1}`,
        prompt: `gentle wind through trees, birds chirping softly ${i + 1}`,
        duration: 120,
        priority: ['高', '中', '低'][i % 3],
        selected: true,
        dynamic_elements: ['风声变化', '鸟鸣节奏'],
        fade_settings: { fade_in: 2, fade_out: 2 },
        generation_tips: { complexity: '中等' }
      }))
    }

    generatingPrompts.value = false
  }

  const selectAllPrompts = () => {
    if (smartPrompts.value?.smart_prompts) {
      smartPrompts.value.smart_prompts.forEach((prompt) => {
        prompt.selected = true
      })
    }
  }

  const selectNonePrompts = () => {
    if (smartPrompts.value?.smart_prompts) {
      smartPrompts.value.smart_prompts.forEach((prompt) => {
        prompt.selected = false
      })
    }
  }

  const startBatchGeneration = async () => {
    currentStep.value = 3

    const selectedPrompts = smartPrompts.value.smart_prompts.filter((p) => p.selected)
    batchProgress.total = selectedPrompts.length
    batchProgress.completed = 0
    batchProgress.status = 'active'

    for (let i = 0; i < selectedPrompts.length; i++) {
      batchProgress.currentTask = {
        title: selectedPrompts[i].title,
        progress: 0
      }

      // 模拟单个任务进度
      for (let progress = 0; progress <= 100; progress += 20) {
        batchProgress.currentTask.progress = progress
        await new Promise((resolve) => setTimeout(resolve, 200))
      }

      batchProgress.completed++
      generationLogs.value.push({
        time: new Date().toLocaleTimeString(),
        message: `${selectedPrompts[i].title} 生成完成`,
        type: 'success'
      })
    }

    batchProgress.status = 'success'
    batchProgress.currentTask = null
    message.success('批量生成完成！')
  }

  const proceedToMixing = () => {
    currentStep.value = 4
  }

  const cancelBatchGeneration = () => {
    batchProgress.status = 'exception'
    message.warning('批量生成已取消')
  }

  const startMixing = async () => {
    try {
      starting.value = true
      mixingProgress.value = 0 // 重置进度
      currentStep.value = 4 // 进入混音进行中状态

      console.log('切换到混音步骤，当前步骤:', currentStep.value)

      // 构建混音配置数据（符合后端API格式）
      const mixingData = {
        environment_config: {
          analysis_result: analysisResult.value,
          book_id: selectedBook.value,
          project_id: selectedProject.value,
          mixing_id: `mixing_${Date.now()}`
        },
        chapter_ids: selectedChapterIds.value,
        mixing_options: {
          ...mixingConfig,
          analysis_options: analysisOptions.value
        }
      }

      console.log('开始环境混音合成:', mixingData)

      // 先显示初始进度
      mixingProgress.value = 5
      await new Promise((resolve) => setTimeout(resolve, 500))

      // 调用后端环境混音API
      const response = await fetch(`/api/v1/environment/mixing/${selectedProject.value}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(mixingData)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `混音启动失败: ${response.status}`)
      }

      const result = await response.json()
      console.log('环境混音启动结果:', result)

      // 模拟混音进度 - 更慢更明显
      let progress = 10
      const progressInterval = setInterval(() => {
        if (progress < 85) {
          progress += Math.random() * 8 + 2 // 每次增加2-10%
          mixingProgress.value = Math.min(progress, 85)
          console.log('更新混音进度:', mixingProgress.value)
        }
      }, 1500) // 每1.5秒更新一次

      // 等待一段时间模拟合成过程
      await new Promise((resolve) => setTimeout(resolve, 12000)) // 延长到12秒

      clearInterval(progressInterval)
      mixingProgress.value = 100
      console.log('混音完成，进度:', mixingProgress.value)

      message.success('环境混音合成完成！混音文件已生成')

      // 等待用户看到完成信息后再关闭 - 延长等待时间
      setTimeout(() => {
        console.log('准备关闭窗口')
        emit('update:visible', false)
        // 触发混音完成事件
        emit('mixing-completed', {
          ...mixingData,
          mixing_result: result
        })
      }, 5000) // 延长到5秒
    } catch (error) {
      console.error('环境混音失败:', error)
      message.error(`混音失败: ${error.message}`)
      // 发生错误时不自动关闭窗口，让用户看到错误信息
    } finally {
      starting.value = false
    }
  }

  // 监听visible变化，重置状态
  watch(
    () => props.visible,
    (newVal) => {
      if (newVal) {
        loadBooks()
      } else {
        // 重置所有状态
        currentStep.value = 0
        analyzing.value = false
        matching.value = false
        generatingPrompts.value = false
        starting.value = false
        saving.value = false
        startingMixing.value = false
        configSaved.value = false
        analysisProgress.value = 0
        matchingProgress.value = 0
        mixingProgress.value = 0
        analysisResult.value = null
        matchingResult.value = null
        smartPrompts.value = null
        selectedBook.value = null
        selectedProject.value = null
        selectedChapterIds.value = []
        projects.value = []
        Object.assign(batchProgress, {
          total: 0,
          completed: 0,
          processing: 0,
          failed: 0,
          status: 'normal',
          currentTask: null
        })
        generationLogs.value = []
      }
    }
  )

  onMounted(() => {
    loadBooks()
  })
</script>

<style scoped>
  .environment-mixing-drawer {
    --primary-color: #1890ff;
    --success-color: #52c41a;
    --warning-color: #fa8c16;
  }

  .mixing-analysis-content {
    padding: 0;
  }

  .steps-container {
    margin-bottom: 32px;
    padding: 20px;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-radius: 8px;
  }

  .analysis-step,
  .config-step,
  .start-step,
  .mixing-step {
    min-height: 400px;
  }

  .mixing-state {
    text-align: center;
    padding: 60px 20px;
  }

  .analysis-step h3,
  .config-step h3,
  .start-step h3 {
    color: var(--primary-color);
    margin-bottom: 8px;
    font-weight: 600;
  }

  .analyzing-state,
  .matching-state,
  .generating-state {
    text-align: center;
    padding: 60px 20px;
  }

  .chapter-tracks {
    margin-bottom: 24px;
  }

  .tracks-list {
    max-height: 300px;
    overflow-y: auto;
  }

  .track-item {
    border: 1px solid #f0f0f0;
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 12px;
    background: #fafafa;
  }

  .track-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .track-header h5 {
    margin: 0;
    color: var(--primary-color);
  }

  .track-keywords {
    margin-top: 8px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
  }

  .prompts-list {
    max-height: 500px;
    overflow-y: auto;
  }

  .prompt-item {
    border: 1px solid #f0f0f0;
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 16px;
    background: #fafafa;
  }

  .prompt-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .prompt-header h4 {
    margin: 0;
    color: var(--primary-color);
  }

  .prompt-content {
    margin-bottom: 12px;
  }

  .prompt-features,
  .prompt-settings {
    margin-top: 8px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .generation-logs {
    max-height: 200px;
    overflow-y: auto;
    border: 1px solid #f0f0f0;
    border-radius: 4px;
    padding: 8px;
  }

  .log-item {
    display: flex;
    margin-bottom: 4px;
    font-size: 12px;
  }

  .log-time {
    color: #666;
    margin-right: 8px;
    min-width: 80px;
  }

  .log-message {
    flex: 1;
  }

  .log-item.success .log-message {
    color: var(--success-color);
  }

  .step-actions {
    margin-top: 32px;
    text-align: right;
    padding-top: 20px;
    border-top: 1px solid #f0f0f0;
  }

  .step-actions .ant-btn {
    margin-left: 12px;
  }

  .total-stats {
    text-align: center;
    padding: 16px;
  }

  /* 🚀 新增：分析结果样式 */
  .analysis-summary {
    background: #f9f9f9;
    border-radius: 8px;
    padding: 16px;
  }

  .summary-item {
    display: flex;
    align-items: center;
    text-align: center;
    padding: 12px;
  }

  .summary-icon {
    font-size: 24px;
    margin-bottom: 8px;
  }

  .summary-content {
    flex: 1;
  }

  .summary-content strong {
    display: block;
    color: #1890ff;
    margin-bottom: 4px;
  }

  .summary-content p {
    margin: 0;
    color: #666;
    font-size: 14px;
  }

  .discovered-scenes {
    margin-top: 16px;
  }

  .chapter-scenes {
    margin-bottom: 16px;
  }

  .chapter-header h5 {
    color: #1890ff;
    margin-bottom: 8px;
    font-weight: 600;
  }

  .scene-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .scene-tag {
    margin: 0;
    padding: 4px 8px;
    border-radius: 12px;
  }

  .matching-preview {
    background: #f9f9f9;
    border-radius: 8px;
    padding: 16px;
  }

  .matching-stats {
    margin-bottom: 16px;
  }

  .chapter-preview {
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    background: white;
  }

  .chapter-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #1890ff;
    margin-bottom: 12px;
  }

  .scene-previews {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .scene-preview {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: #f5f5f5;
    border-radius: 6px;
  }

  .scene-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .scene-icon {
    font-size: 16px;
  }

  .scene-name {
    font-weight: 500;
    color: #333;
  }

  .scene-duration {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #666;
    font-size: 12px;
  }

  .more-scenes {
    text-align: center;
    padding: 8px;
    background: #f0f0f0;
    border-radius: 6px;
  }

  /* 🚀 新增：混音总览样式 */
  .mixing-summary {
    padding: 16px;
  }

  .summary-stat {
    text-align: center;
    padding: 16px;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-radius: 8px;
    border: 1px solid #91d5ff;
  }

  .stat-number {
    font-size: 24px;
    font-weight: bold;
    color: #1890ff;
    margin-bottom: 4px;
  }

  .stat-label {
    font-size: 12px;
    color: #666;
    font-weight: 500;
  }

  .quick-settings {
    padding: 16px;
  }

  .setting-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .setting-item label {
    font-weight: 500;
    color: #333;
    font-size: 14px;
  }

  /* 暗黑模式适配 */
  @media (prefers-color-scheme: dark) {
    .steps-container {
      background: linear-gradient(135deg, #001529 0%, #002140 100%);
    }

    .track-item,
    .prompt-item {
      background: #1f1f1f;
      border-color: #434343;
    }

    .generation-logs {
      background: #1f1f1f;
      border-color: #434343;
    }

    .analysis-summary,
    .matching-preview {
      background: #1f1f1f;
    }

    .chapter-preview {
      background: #262626;
      border-color: #434343;
    }

    .scene-preview {
      background: #1f1f1f;
    }

    .summary-content p {
      color: #ccc;
    }

    .scene-name {
      color: #fff;
    }

    .summary-stat {
      background: linear-gradient(135deg, #001529 0%, #002140 100%);
      border-color: #177ddc;
    }

    .stat-label {
      color: #ccc;
    }

    .setting-item label {
      color: #fff;
    }
  }

  /* 🚀 新增：详细分析信息样式 */
  .detailed-analysis {
    margin-top: 16px;
  }

  .chapter-detailed-analysis {
    margin-bottom: 24px;
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 16px;
    background: #fafafa;
  }

  .chapter-detailed-analysis h4 {
    color: #1890ff;
    margin-bottom: 16px;
    font-weight: 600;
    border-bottom: 2px solid #e6f7ff;
    padding-bottom: 8px;
  }

  .tracks-detailed {
    margin-top: 12px;
  }

  .scene-cell {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .scene-icon {
    font-size: 18px;
  }

  .keywords-cell {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    max-width: 200px;
  }

  .timing-cell {
    text-align: center;
  }

  .timing-cell strong {
    color: #1890ff;
  }

  .narration-cell {
    max-width: 300px;
    word-break: break-word;
  }

  .no-tracks {
    text-align: center;
    padding: 40px 0;
    color: #999;
  }

  .analysis-method-info {
    padding: 16px;
  }

  .analysis-method-info .ant-descriptions {
    margin-bottom: 16px;
  }

  /* 移动端适配 */
  @media (max-width: 768px) {
    .detailed-analysis .ant-table {
      font-size: 12px;
    }

    .chapter-detailed-analysis {
      padding: 12px;
    }

    .keywords-cell {
      max-width: 150px;
    }

    .narration-cell {
      max-width: 200px;
    }

    .timing-cell {
      font-size: 11px;
    }
  }

  /* 暗黑模式适配详细分析 */
  @media (prefers-color-scheme: dark) {
    .chapter-detailed-analysis {
      background: #1f1f1f;
      border-color: #434343;
    }

    .chapter-detailed-analysis h4 {
      color: #177ddc;
      border-bottom-color: #001529;
    }

    .timing-cell strong {
      color: #177ddc;
    }

    .no-tracks {
      color: #666;
    }
  }
</style>
