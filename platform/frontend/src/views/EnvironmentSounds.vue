<template>
  <div class="environment-sounds-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-with-back">
            
            <h1 class="page-title">
              <SoundOutlined class="title-icon" />
              环境音管理
            </h1>
          </div>
          <p class="page-description">
            通过书籍智能分析，快速生成定制化环境音效，丰富音效库资源<br/>
            <small style="color: rgba(255,255,255,0.7);">📚 书籍内容分析 + 🎵 AI音效生成 → 🔄 快速扩充音效库 | 🔧 手工创建：单个定制化生成</small>
          </p>
        </div>
        <div class="action-section">
          <a-space size="large">
            <a-button 
              type="primary" 
              size="large"
              @click="showSmartAnalysisModal = true"
              :loading="analyzing"
            >
              <BulbOutlined />
              智能分析生成环境音
            </a-button>
            <a-button 
              type="default" 
              size="large"
              @click="showGenerateModal = true"
              :loading="generating"
            >
              <PlusOutlined />
              手工创建
            </a-button>
          </a-space>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总环境音"
              :value="stats.total_sounds"
              :value-style="{ color: '#1890ff' }"
            >
              <template #prefix>
                <SoundOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="已完成"
              :value="stats.completed_sounds"
              :value-style="{ color: '#52c41a' }"
            >
              <template #prefix>
                <CheckCircleOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="生成中"
              :value="stats.processing_sounds"
              :value-style="{ color: '#fa8c16' }"
            >
              <template #prefix>
                <LoadingOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总播放"
              :value="stats.total_plays"
              :value-style="{ color: '#722ed1' }"
            >
              <template #prefix>
                <PlayCircleOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <a-card>
        <a-form layout="inline" :model="searchForm">
          <a-form-item label="搜索">
            <a-input
              v-model:value="searchForm.search"
              placeholder="搜索环境音名称、描述或提示词"
              style="width: 300px"
              @pressEnter="loadSounds"
            >
              <template #prefix>
                <SearchOutlined />
              </template>
            </a-input>
          </a-form-item>
          
          <a-form-item label="分类">
            <a-select
              v-model:value="searchForm.category_id"
              placeholder="选择分类"
              style="width: 150px"
              allowClear
              @change="loadSounds"
            >
              <a-select-option
                v-for="category in categories"
                :key="category.id"
                :value="category.id"
              >
                {{ category.name }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="标签">
            <a-select
              v-model:value="searchForm.tag_ids"
              mode="multiple"
              placeholder="选择标签"
              style="width: 200px"
              allowClear
              @change="loadSounds"
            >
              <a-select-option
                v-for="tag in tags"
                :key="tag.id"
                :value="tag.id"
              >
                <a-tag :color="tag.color" style="margin: 0;">
                  {{ tag.name }}
                </a-tag>
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="状态">
            <a-select
              v-model:value="searchForm.status"
              placeholder="生成状态"
              style="width: 120px"
              allowClear
              @change="loadSounds"
            >
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="processing">生成中</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item>
            <a-button type="primary" @click="loadSounds">
              <SearchOutlined />
              搜索
            </a-button>
          </a-form-item>

          <a-form-item>
            <a-button @click="resetSearch">
              重置
            </a-button>
          </a-form-item>

          <a-form-item>
            <a-button @click="loadSounds" :loading="loading">
              <ReloadOutlined />
              刷新
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </div>

    <!-- 环境音列表 -->
    <div class="sounds-section">
      <a-card>
        <template #title>
          <div class="list-header">
            <span>环境音列表</span>
            <div class="list-actions">
              <a-switch
                v-model:checked="showFeaturedOnly"
                checkedChildren="精选"
                unCheckedChildren="全部"
                @change="loadSounds"
              />
              <a-select
                v-model:value="sortBy"
                style="width: 120px; margin-left: 8px"
                @change="loadSounds"
              >
                <a-select-option value="created_at">创建时间</a-select-option>
                <a-select-option value="play_count">播放次数</a-select-option>
                <a-select-option value="download_count">下载次数</a-select-option>
                <a-select-option value="favorite_count">收藏数</a-select-option>
                <a-select-option value="duration">时长</a-select-option>
              </a-select>
            </div>
          </div>
        </template>

        <div class="sounds-grid">
          <div
            v-for="sound in sounds"
            :key="sound.id"
            class="sound-card"
            :class="{ 'featured': sound.is_featured }"
          >
            <!-- 状态标识 -->
            <div class="status-badge">
              <a-badge
                :status="getStatusType(sound.generation_status)"
                :text="getStatusText(sound.generation_status)"
              />
            </div>

            <!-- 精选标识 -->
            <div v-if="sound.is_featured" class="featured-badge">
              <StarFilled />
            </div>

            <!-- 音频信息 -->
            <div class="sound-info">
              <h3 class="sound-name">{{ sound.name }}</h3>
              <p class="sound-prompt">{{ sound.prompt }}</p>
              <div class="sound-meta">
                <a-tag v-if="sound.category" :color="'blue'">
                  {{ sound.category.name }}
                </a-tag>
                <a-tag
                  v-for="tag in sound.tags"
                  :key="tag.id"
                  :color="tag.color"
                  style="margin: 2px;"
                >
                  {{ tag.name }}
                </a-tag>
              </div>
              <div class="sound-params">
                <span class="param">{{ sound.duration }}s</span>
                <span class="param">{{ sound.steps }} steps</span>
                <span class="param">CFG {{ sound.cfg_scale }}</span>
              </div>
            </div>

            <!-- 统计信息 -->
            <div class="sound-stats">
              <div class="stat-item">
                <PlayCircleOutlined />
                {{ sound.play_count }}
              </div>
              <div class="stat-item">
                <DownloadOutlined />
                {{ sound.download_count }}
              </div>
              <div class="stat-item">
                <HeartOutlined />
                {{ sound.favorite_count }}
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="sound-actions">
              <a-button-group size="small">
                <a-button
                  v-if="sound.generation_status === 'completed'"
                  type="primary"
                  @click="playSound(sound)"
                  :loading="playingId === sound.id"
                >
                  <PlayCircleOutlined />
                </a-button>
                
                <a-button
                  v-if="sound.generation_status === 'completed'"
                  @click="downloadSound(sound)"
                >
                  <DownloadOutlined />
                </a-button>

                <a-button
                  @click="toggleFavorite(sound)"
                  :type="sound.is_favorited ? 'primary' : 'default'"
                >
                  <HeartOutlined />
                </a-button>

                <a-dropdown>
                  <a-button>
                    <MoreOutlined />
                  </a-button>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item
                        v-if="sound.generation_status === 'failed'"
                        @click="regenerateSound(sound)"
                      >
                        <RedoOutlined />
                        重新生成
                      </a-menu-item>
                      <a-menu-item @click="editSound(sound)">
                        <EditOutlined />
                        编辑
                      </a-menu-item>
                      <a-menu-item @click="copyPrompt(sound.prompt)">
                        <CopyOutlined />
                        复制提示词
                      </a-menu-item>
                      <a-menu-divider />
                      <a-menu-item danger @click="deleteSound(sound)">
                        <DeleteOutlined />
                        删除
                      </a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </a-button-group>
            </div>

            <!-- 错误信息 -->
            <div v-if="sound.generation_status === 'failed'" class="error-message">
              <a-alert
                type="error"
                :message="sound.error_message || '生成失败'"
                banner
              />
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <a-empty
          v-if="!loading && sounds && sounds.length === 0"
          description="暂无环境音"
        >
          <a-button type="primary" @click="showGenerateModal = true">
            立即生成
          </a-button>
        </a-empty>

        <!-- 分页 -->
        <div v-if="pagination.total > 0" class="pagination-section">
          <a-pagination
            v-model:current="pagination.current"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            show-size-changer
            show-quick-jumper
            :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
            @change="loadSounds"
            @showSizeChange="loadSounds"
          />
        </div>
      </a-card>
    </div>

    <!-- 生成环境音抽屉 -->
    <GenerateDrawer
      v-model:visible="showGenerateModal"
      :categories="categories"
      :tags="tags"
      :presets="presets"
      @generated="onSoundGenerated"
    />

    <!-- 编辑环境音弹窗 -->
    <EditModal
      v-model:visible="showEditModal"
      :sound="editingSound"
      :categories="categories"
      :tags="tags"
      @updated="onSoundUpdated"
    />

    <!-- 智能分析抽屉 -->
    <a-drawer
      v-model:open="showSmartAnalysisModal"
              title="🧠 智能分析生成"
      placement="right"
      width="1000px"
      :closable="true"
      :maskClosable="false"
      destroyOnClose
      class="smart-analysis-drawer"
    >
      <div class="smart-analysis-content">
        <!-- 步骤指示器 -->
        <div class="steps-container">
          <a-steps :current="analysisStep" direction="horizontal" size="small">
            <a-step title="选择章节" description="选择小说章节进行分析" />
                            <a-step title="智能分析" description="AI分析场景识别环境音需求" />
                <a-step title="确认配置" description="确认环境音生成配置" />
                <a-step title="批量生成" description="批量生成环境音到音效库" />
          </a-steps>
        </div>

        <!-- 步骤1: 章节选择 -->
        <div v-if="analysisStep === 0" class="analysis-step">
          <h3>选择小说章节</h3>
          <p style="color: #666; margin-bottom: 16px;">从已导入的小说中选择章节进行环境音智能分析</p>

          <div>
            <a-select
              v-model:value="selectedBook"
              placeholder="选择书籍"
              style="width: 100%; margin-bottom: 16px;"
              @change="loadBookChapters"
            >
              <a-select-option
                v-for="book in books"
                :key="book.id"
                :value="book.id"
              >
                {{ book.title }}
              </a-select-option>
            </a-select>

            <a-select
              v-model:value="selectedChapterIds"
              mode="multiple"
              placeholder="选择已分析的章节（支持多选）"
              style="width: 100%; margin-bottom: 16px;"
              :max-tag-count="3"
              :loading="loadingChapters"
            >
              <a-select-option
                v-for="chapter in analyzedChapters"
                :key="chapter.id"
                :value="chapter.id"
              >
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>{{ chapter.chapter_title || chapter.title }}</span>
                  <a-tag color="green" size="small">已分析</a-tag>
                </div>
              </a-select-option>
            </a-select>

            <!-- 提示信息 -->
            <div v-if="analyzedChapters.length === 0" style="margin-bottom: 16px;">
              <a-alert
                message="暂无已分析的章节"
                description="请先在「书籍管理」中对章节进行智能分析，然后再回来使用环境音优化功能。"
                type="info"
                show-icon
              />
            </div>

            <!-- 分析选项 -->
            <div v-if="selectedChapterIds.length > 0" style="margin-bottom: 16px;">
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
              :disabled="selectedChapterIds.length === 0"
            >
              {{ selectedChapterIds.length > 0 ? '开始4步优化分析' : '开始分析' }}
            </a-button>
          </div>
        </div>

        <!-- 步骤2: 分析进行中和结果，或环境音匹配 -->
        <div v-if="analysisStep === 1" class="analysis-step">
          <div v-if="analyzing" class="analyzing-state">
            <a-spin size="large">
              <template #indicator>
                <BulbOutlined style="font-size: 24px" spin />
              </template>
            </a-spin>
            <h3 style="margin-top: 16px;">正在分析场景...</h3>
            <p>AI正在深度理解文本内容，识别场景、氛围和情感变化</p>
            <a-progress :percent="analysisProgress" status="active" />
          </div>

          <div v-if="analysisResult && !analyzing" class="analysis-result">
            <h3>分析结果</h3>
            
            <!-- 分析摘要 -->
            <a-card title="分析摘要" style="margin-bottom: 16px;">
              <a-descriptions :column="2" size="small">
                <a-descriptions-item label="总轨道数">{{ analysisResult.total_tracks || analysisResult.total_scenes || 0 }}</a-descriptions-item>
                <a-descriptions-item label="分析模式">{{ analysisResult.llm_provider || '章节分析' }}</a-descriptions-item>
                <a-descriptions-item label="总时长">{{ analysisResult.total_duration || 0 }}秒</a-descriptions-item>
                <a-descriptions-item label="章节数">{{ analysisResult.chapters_analyzed || 1 }}</a-descriptions-item>
              </a-descriptions>
              
              <div v-if="analysisResult.narrative_analysis" style="margin-top: 16px;">
                <a-tag color="blue">{{ analysisResult.narrative_analysis.genre || '未知体裁' }}</a-tag>
                <a-tag color="green">{{ analysisResult.narrative_analysis.pace || '中等节奏' }}</a-tag>
                <span style="margin-left: 8px; color: #666;">
                  {{ analysisResult.narrative_analysis.emotional_arc }}
                </span>
              </div>
            </a-card>

            <!-- 环境音轨道列表 -->
            <a-card title="环境音轨道">
              <template v-if="analysisResult.chapters && analysisResult.chapters.length > 0">
                <!-- 新的章节级分析结果格式 -->
                <div v-for="(chapter, chapterIndex) in analysisResult.chapters" :key="chapterIndex" class="chapter-tracks">
                  <a-divider v-if="chapterIndex > 0" />
                  <h4 style="margin-bottom: 16px;">
                    {{ chapter.chapter_info?.chapter_title || `第${chapter.chapter_info?.chapter_number}章` }}
                    <a-tag color="blue" style="margin-left: 8px;">
                      {{ (chapter.analysis_result?.environment_tracks || []).length }} 个轨道
                    </a-tag>
                  </h4>
                  
                  <div class="tracks-list">
                    <div
                      v-for="(track, index) in chapter.analysis_result?.environment_tracks || []"
                      :key="`${chapterIndex}-${index}`"
                      class="track-item"
                    >
                      <div class="track-header">
                        <h5>轨道 {{ index + 1 }}</h5>
                        <a-tag :color="getIntensityColor(track.intensity_level)">{{ track.intensity_level || '中等' }}</a-tag>
                      </div>
                      <div class="track-details">
                        <a-space>
                          <a-tag>🕐 {{ track.start_time }}s - {{ (track.end_time || (track.start_time + track.duration)) }}s</a-tag>
                          <a-tag>⏱️ {{ track.duration }}s</a-tag>
                          <a-tag>📝 {{ track.scene_description || '环境音轨道' }}</a-tag>
                        </a-space>
                      </div>
                      <div v-if="track.environment_keywords && track.environment_keywords.length > 0" class="track-keywords">
                        <strong style="margin-right: 8px;">关键词:</strong>
                        <a-tag
                          v-for="keyword in track.environment_keywords"
                          :key="keyword"
                          size="small"
                          color="blue"
                        >
                          {{ keyword }}
                        </a-tag>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 总计统计 -->
                <a-divider />
                <div class="total-stats">
                  <a-space>
                    <a-statistic title="总章节数" :value="analysisResult.chapters_analyzed || analysisResult.chapters.length" />
                    <a-statistic title="总轨道数" :value="analysisResult.total_tracks" />
                    <a-statistic title="总时长" :value="analysisResult.total_duration" suffix="秒" />
                  </a-space>
                </div>
              </template>
              
              <template v-else-if="analysisResult.environment_tracks && analysisResult.environment_tracks.length > 0">
                <!-- 直接包含environment_tracks的格式（增强分析结果） -->
                <div class="tracks-list">
                  <div
                    v-for="(track, index) in analysisResult.environment_tracks"
                    :key="index"
                    class="track-item"
                  >
                    <div class="track-header">
                      <h5>轨道 {{ index + 1 }}</h5>
                      <a-space>
                        <a-tag :color="getIntensityColor(track.intensity_level)">{{ track.intensity_level || '中等' }}</a-tag>
                        <a-tag v-if="track.has_match" color="green">✅ 已匹配</a-tag>
                        <a-tag v-else color="orange">🔄 需要生成</a-tag>
                      </a-space>
                    </div>
                    <div class="track-details">
                      <a-space>
                        <a-tag>🕐 {{ track.start_time }}s - {{ (track.end_time || (track.start_time + track.duration)) }}s</a-tag>
                        <a-tag>⏱️ {{ track.duration }}s</a-tag>
                        <a-tag>📝 {{ track.scene_description || '环境音轨道' }}</a-tag>
                      </a-space>
                    </div>
                    <div v-if="track.environment_keywords && track.environment_keywords.length > 0" class="track-keywords">
                      <strong style="margin-right: 8px;">关键词:</strong>
                      <a-tag
                        v-for="keyword in track.environment_keywords"
                        :key="keyword"
                        size="small"
                        color="blue"
                      >
                        {{ keyword }}
                      </a-tag>
                    </div>
                    <!-- 显示匹配结果 -->
                    <div v-if="track.has_match && track.best_match" class="track-match-info" style="margin-top: 8px;">
                      <a-alert type="success" show-icon style="border-radius: 4px;">
                        <template #message>
                          <strong>最佳匹配:</strong> {{ track.best_match.sound_name }} 
                          <a-tag color="green" size="small" style="margin-left: 8px;">
                            置信度: {{ (track.best_match.confidence * 100).toFixed(1) }}%
                          </a-tag>
                        </template>
                        <template #description>
                          {{ track.best_match.reason }}
                        </template>
                      </a-alert>
                    </div>
                  </div>
                </div>
                
                <!-- 匹配汇总 -->
                <a-divider />
                <div v-if="analysisResult.matching_summary" class="matching-summary">
                  <h4>🎵 匹配汇总</h4>
                  <a-row :gutter="16">
                    <a-col :span="6">
                      <a-statistic title="总轨道数" :value="analysisResult.matching_summary.total_tracks" />
                    </a-col>
                    <a-col :span="6">
                      <a-statistic title="已匹配" :value="analysisResult.matching_summary.matched_tracks" />
                    </a-col>
                    <a-col :span="6">
                      <a-statistic title="需要生成" :value="analysisResult.matching_summary.need_generation_tracks" />
                    </a-col>
                    <a-col :span="6">
                      <a-statistic title="匹配率" :value="analysisResult.matching_summary.match_rate" suffix="%" />
                    </a-col>
                  </a-row>
                </div>
              </template>
              
              <template v-else>
                <!-- 兼容旧的单章节分析结果格式 -->
                <div class="tracks-list">
                  <div
                    v-for="(track, index) in analysisResult.environment_tracks || []"
                    :key="index"
                    class="track-item"
                  >
                    <div class="track-header">
                      <h4>轨道 {{ index + 1 }}</h4>
                      <a-tag :color="getIntensityColor(track.intensity_level)">{{ track.intensity_level || '中等' }}</a-tag>
                    </div>
                    <div class="track-details">
                      <a-space>
                        <a-tag>🕐 {{ track.start_time }}s - {{ track.end_time }}s</a-tag>
                        <a-tag>⏱️ {{ track.duration }}s</a-tag>
                        <a-tag>📝 {{ track.scene_description || '环境音轨道' }}</a-tag>
                      </a-space>
                    </div>
                    <div v-if="track.environment_keywords && track.environment_keywords.length > 0" class="track-keywords">
                      <strong style="margin-right: 8px;">关键词:</strong>
                      <a-tag
                        v-for="keyword in track.environment_keywords"
                        :key="keyword"
                        size="small"
                        color="blue"
                      >
                        {{ keyword }}
                      </a-tag>
                    </div>
                  </div>
                </div>
              </template>
              
              <div class="step-actions" style="margin-top: 16px;">
                <a-space>
                  <a-button @click="analysisStep = 0">重新分析</a-button>
                </a-space>
              </div>
            </a-card>
          </div>

          <!-- 新的4步流程：环境音匹配进度 -->
          <div v-if="matching" class="matching-progress">
            <div class="progress-header">
              <a-spin size="large">
                <template #indicator>
                  <SoundOutlined style="font-size: 32px" spin />
                </template>
              </a-spin>
              <h2>正在智能匹配环境音...</h2>
              <p>匹配已有环境音和制定生成计划</p>
            </div>
            <a-progress :percent="matchingProgress" status="active" />
          </div>

          <!-- 新的4步流程：环境音匹配结果 -->
          <div v-if="matchingResult && !matching" class="matching-result">
            <h3>🎵 环境音匹配结果</h3>
            <EnvironmentMatchingPanel
              :matching-result="matchingResult"
              :analysis-result="analysisResult"
              @generate-sounds="handleGenerateSounds"
              @update-matching="handleUpdateMatching"
            />
            
            <div class="step-actions" style="margin-top: 16px;">
              <a-space>
                <a-button @click="analysisStep = 0">重新分析</a-button>
                <a-button type="primary" @click="proceedToGeneration">
                  开始批量生成到音效库
                </a-button>
              </a-space>
            </div>
          </div>
        </div>

        <!-- 步骤3: 智能提示词和生成计划 -->
        <div v-if="analysisStep === 2" class="analysis-step">
          <div v-if="generatingPrompts" class="generating-state">
            <a-spin size="large" />
            <h3 style="margin-top: 16px;">正在生成智能提示词...</h3>
          </div>

          <div v-if="smartPrompts && !generatingPrompts" class="smart-prompts-result">
            <h3>智能提示词方案</h3>
            
            <!-- 音景推荐 -->
            <a-card v-if="smartPrompts.soundscape_recommendation" title="整体音景设计" style="margin-bottom: 16px;">
              <a-descriptions :column="2" size="small">
                <a-descriptions-item label="主要元素">
                  <a-tag v-for="element in smartPrompts.soundscape_recommendation.primary_elements" :key="element" color="blue">
                    {{ element }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="次要元素">
                  <a-tag v-for="element in smartPrompts.soundscape_recommendation.secondary_elements" :key="element" color="green">
                    {{ element }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="建议总时长">{{ smartPrompts.soundscape_recommendation.overall_duration }}秒</a-descriptions-item>
                <a-descriptions-item label="环境层次">{{ smartPrompts.soundscape_recommendation.ambient_layers?.join(', ') }}</a-descriptions-item>
              </a-descriptions>
            </a-card>

            <!-- 提示词列表 -->
            <a-card title="生成提示词">
              <div class="prompts-list">
                <div
                  v-for="(prompt, index) in smartPrompts.smart_prompts"
                  :key="index"
                  class="prompt-item"
                >
                  <div class="prompt-header">
                    <h4>{{ prompt.title }}</h4>
                    <a-space>
                      <a-tag color="orange">{{ prompt.duration }}s</a-tag>
                      <a-tag :color="getPriorityColor(prompt.priority)">优先级 {{ prompt.priority }}</a-tag>
                      <a-checkbox v-model:checked="prompt.selected">生成</a-checkbox>
                    </a-space>
                  </div>
                  
                  <div class="prompt-content">
                    <a-typography-paragraph :copyable="{ text: prompt.prompt }">
                      <code>{{ prompt.prompt }}</code>
                    </a-typography-paragraph>
                  </div>

                  <div v-if="prompt.dynamic_elements && prompt.dynamic_elements.length > 0" class="prompt-features">
                    <strong>动态元素:</strong>
                    <a-tag
                      v-for="element in prompt.dynamic_elements"
                      :key="element"
                      size="small"
                      color="purple"
                    >
                      {{ element }}
                    </a-tag>
                  </div>

                  <div class="prompt-settings">
                    <a-space>
                      <span>淡入: {{ prompt.fade_settings.fade_in }}s</span>
                      <span>淡出: {{ prompt.fade_settings.fade_out }}s</span>
                      <span>复杂度: {{ prompt.generation_tips.complexity }}</span>
                    </a-space>
                  </div>
                </div>
              </div>

              <div class="step-actions" style="margin-top: 16px;">
                <a-space>
                  <a-button @click="analysisStep = 1">返回分析</a-button>
                  <a-button @click="selectAllPrompts">全选</a-button>
                  <a-button @click="selectNonePrompts">全不选</a-button>
                  <a-button type="primary" @click="startBatchGeneration" :disabled="!hasSelectedPrompts">
                    开始批量生成 ({{ selectedPromptsCount }})
                  </a-button>
                </a-space>
              </div>
            </a-card>
          </div>
        </div>

        <!-- 步骤4: 批量生成进度 -->
        <div v-if="analysisStep === 3" class="analysis-step">
          <h3>批量生成进行中</h3>
          
          <a-card>
            <div class="generation-progress">
              <a-progress 
                :percent="Math.round((batchProgress.completed / batchProgress.total) * 100)"
                :status="batchProgress.status"
                style="margin-bottom: 16px;"
              />
              
              <a-descriptions :column="2" size="small">
                <a-descriptions-item label="总任务">{{ batchProgress.total }}</a-descriptions-item>
                <a-descriptions-item label="已完成">{{ batchProgress.completed }}</a-descriptions-item>
                <a-descriptions-item label="进行中">{{ batchProgress.processing }}</a-descriptions-item>
                <a-descriptions-item label="失败">{{ batchProgress.failed }}</a-descriptions-item>
              </a-descriptions>

              <div v-if="batchProgress.currentTask" style="margin-top: 16px;">
                <h4>当前任务</h4>
                <p>{{ batchProgress.currentTask.title }}</p>
                <a-progress :percent="batchProgress.currentTask.progress" size="small" />
              </div>
            </div>

            <!-- 生成日志 -->
            <div v-if="generationLogs.length > 0" class="generation-logs" style="margin-top: 16px;">
              <h4>生成日志</h4>
              <div class="logs-container">
                <div
                  v-for="(log, index) in generationLogs"
                  :key="index"
                  class="log-item"
                  :class="log.type"
                >
                  <span class="log-time">{{ log.time }}</span>
                  <span class="log-message">{{ log.message }}</span>
                </div>
              </div>
            </div>

            <div class="step-actions" style="margin-top: 16px;">
              <a-space>
                <a-button v-if="batchProgress.status !== 'active'" @click="showSmartAnalysisModal = false">
                  关闭
                </a-button>
                <a-button v-if="batchProgress.status === 'active'" @click="cancelBatchGeneration" danger>
                  取消生成
                </a-button>
              </a-space>
            </div>
          </a-card>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  SoundOutlined, PlusOutlined, SearchOutlined, PlayCircleOutlined,
  DownloadOutlined, HeartOutlined, MoreOutlined, EditOutlined,
  DeleteOutlined, CopyOutlined, RedoOutlined, CheckCircleOutlined,
  LoadingOutlined, StarFilled, ArrowLeftOutlined, BulbOutlined,
  ReloadOutlined, ThunderboltOutlined
} from '@ant-design/icons-vue'

import GenerateDrawer from '@/components/environment-sounds/GenerateDrawer.vue'
import EditModal from '@/components/environment-sounds/EditModal.vue'
import EnvironmentMatchingPanel from '@/components/environment-sounds/EnvironmentMatchingPanel.vue'
import { getAudioService } from '@/utils/audioService'
import { environmentSoundsAPI, booksAPI, chaptersAPI, environmentGenerationAPI } from '@/api'
import apiClient, { llmAnalysisClient } from '@/api/config'

// 路由
const router = useRouter()

// 响应式数据
const loading = ref(false)
const generating = ref(false) // 用于环境音生成
const playingId = ref(null)
const sounds = ref([])
const categories = ref([])
const tags = ref([])
const presets = ref([])

// 统计数据
const stats = reactive({
  total_sounds: 0,
  completed_sounds: 0,
  processing_sounds: 0,
  failed_sounds: 0,
  total_plays: 0
})

// 搜索表单
const searchForm = reactive({
  search: '',
  category_id: null,
  tag_ids: [],
  status: null
})

// 排序和筛选
const showFeaturedOnly = ref(false)
const sortBy = ref('created_at')

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

// 弹窗控制
const showGenerateModal = ref(false)
const showEditModal = ref(false)
const editingSound = ref(null)

// 智能分析相关
const showSmartAnalysisModal = ref(false)
const analyzing = ref(false)
const analysisStep = ref(0)
const analysisProgress = ref(0)
const textSource = ref('chapter')
const analysisText = ref('')
const analysisResult = ref(null)
const smartPrompts = ref(null)
const generatingPrompts = ref(false)

// 新的4步优化流程相关
const selectedChapterIds = ref([])
const analysisOptions = ref(['precise_timing', 'intensity_analysis'])
const matchingResult = ref(null)
const matching = ref(false)
const matchingProgress = ref(0)
const generationResult = ref(null)
const batchGenerating = ref(false) // 重命名避免冲突
const generationProgress = ref(0)

// 书籍和章节数据
const books = ref([])
const chapters = ref([])
const analyzedChapters = ref([])
const loadingChapters = ref(false)
const selectedBook = ref(null)
const selectedChapter = ref(null)

// 批量生成相关
const batchProgress = reactive({
  total: 0,
  completed: 0,
  processing: 0,
  failed: 0,
  status: 'idle', // idle, active, completed, error
  currentTask: null
})
const generationLogs = ref([])

// 生命周期
onMounted(() => {
  loadInitialData()
})

// 方法
const loadInitialData = async () => {
  await Promise.all([
    loadCategories(),
    loadTags(),
    loadPresets(),
    loadStats(),
    loadSounds()
  ])
}

const loadCategories = async () => {
  try {
    const response = await environmentSoundsAPI.getCategories()
    categories.value = response.data
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const loadTags = async () => {
  try {
    const response = await environmentSoundsAPI.getTags()
    tags.value = response.data
  } catch (error) {
    console.error('加载标签失败:', error)
  }
}

const loadPresets = async () => {
  try {
    const response = await environmentSoundsAPI.getPresets()
    presets.value = response.data
  } catch (error) {
    console.error('加载预设失败:', error)
  }
}

const loadStats = async () => {
  try {
    const response = await environmentSoundsAPI.getStats()
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadSounds = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...searchForm,
      featured_only: showFeaturedOnly.value,
      sort_by: sortBy.value,
      sort_order: 'desc'
    }

    // 处理数组参数
    if (params.tag_ids && params.tag_ids.length > 0) {
      params.tag_ids = params.tag_ids.join(',')
    } else {
      delete params.tag_ids
    }

    const response = await environmentSoundsAPI.getEnvironmentSounds(params)
    const responseData = response.data
    
    // 根据后端返回的实际格式处理数据
    if (responseData.success && responseData.data) {
      const data = responseData.data
      sounds.value = data.sounds || []
      pagination.total = data.total || 0
      pagination.current = data.page || 1
      pagination.pageSize = data.page_size || 20
    } else {
      // 如果是直接返回数据格式
      sounds.value = responseData.sounds || []
      pagination.total = responseData.total || 0
      pagination.current = responseData.page || 1
      pagination.pageSize = responseData.page_size || 20
    }

  } catch (error) {
    console.error('加载环境音列表失败:', error)
    message.error('加载环境音列表失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  Object.assign(searchForm, {
    search: '',
    category_id: null,
    tag_ids: [],
    status: null
  })
  showFeaturedOnly.value = false
  sortBy.value = 'created_at'
  pagination.current = 1
  loadSounds()
}

const playSound = async (sound) => {
  try {
    playingId.value = sound.id
    
    // 记录播放日志
    await environmentSoundsAPI.playEnvironmentSound(sound.id)
    
    // 使用统一音频服务播放
    await getAudioService().playEnvironmentSound(sound)
    
    // 更新播放计数
    sound.play_count += 1
    
  } catch (error) {
    console.error('播放失败:', error)
    message.error('播放失败')
  } finally {
    playingId.value = null
  }
}

const downloadSound = async (sound) => {
  try {
    const response = await environmentSoundsAPI.downloadEnvironmentSound(sound.id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${sound.name}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    // 更新下载计数
    sound.download_count += 1
    message.success('下载成功')
    
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

const toggleFavorite = async (sound) => {
  try {
    const response = await environmentSoundsAPI.toggleFavorite(sound.id)
    const result = response.data
    
    sound.is_favorited = result.is_favorited
    sound.favorite_count = result.favorite_count
    
    message.success(result.is_favorited ? '已收藏' : '已取消收藏')
    
  } catch (error) {
    console.error('收藏操作失败:', error)
    message.error('收藏操作失败')
  }
}

const regenerateSound = async (sound) => {
  try {
    await environmentSoundsAPI.regenerateEnvironmentSound(sound.id)
    sound.generation_status = 'processing'
    sound.error_message = null
    message.success('重新生成任务已启动')
    
    // 定期检查生成状态
    checkGenerationStatus(sound.id)
    
  } catch (error) {
    console.error('重新生成失败:', error)
    message.error('重新生成失败')
  }
}

const editSound = (sound) => {
  editingSound.value = { ...sound }
  showEditModal.value = true
}

const deleteSound = (sound) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除环境音"${sound.name}"吗？此操作不可恢复。`,
    onOk: async () => {
      try {
        await environmentSoundsAPI.deleteEnvironmentSound(sound.id)
        message.success('删除成功')
        loadSounds()
        loadStats()
      } catch (error) {
        console.error('删除失败:', error)
        message.error('删除失败')
      }
    }
  })
}

const copyPrompt = (prompt) => {
  navigator.clipboard.writeText(prompt).then(() => {
    message.success('提示词已复制到剪贴板')
  }).catch(() => {
    message.error('复制失败')
  })
}

const onSoundGenerated = (soundId) => {
  showGenerateModal.value = false
  loadSounds()
  loadStats()
  
  // 开始检查生成状态
  checkGenerationStatus(soundId)
}

const onSoundUpdated = () => {
  showEditModal.value = false
  editingSound.value = null
  loadSounds()
}

const checkGenerationStatus = (soundId) => {
  const interval = setInterval(async () => {
    try {
      const response = await environmentSoundsAPI.getEnvironmentSound(soundId)
      const sound = response.data
      
      // 更新列表中的对应项
      const index = sounds.value.findIndex(s => s.id === soundId)
      if (index !== -1) {
        sounds.value[index] = sound
      } else {
        // 如果在当前列表中找不到，重新加载列表
        await loadSounds()
      }
      
      // 如果生成完成或失败，停止检查
      if (sound.generation_status === 'completed' || sound.generation_status === 'failed') {
        clearInterval(interval)
        
        // 强制刷新统计数据和列表
        await Promise.all([loadStats(), loadSounds()])
        
        if (sound.generation_status === 'completed') {
          message.success(`环境音"${sound.name}"生成完成`)
        } else {
          message.error(`环境音"${sound.name}"生成失败: ${sound.error_message || '未知错误'}`)
        }
      }
      
    } catch (error) {
      clearInterval(interval)
      console.error('检查生成状态失败:', error)
      // 如果检查失败，也尝试刷新列表
      await loadSounds()
    }
  }, 2000) // 改为每2秒检查一次，更及时
}

// 智能分析方法
const loadBooks = async () => {
  try {
    const response = await booksAPI.getBooks()
    books.value = (response.data.success && response.data.data) ? response.data.data : (response.data.data || [])
  } catch (error) {
    console.error('加载书籍失败:', error)
    message.error('加载书籍失败')
  }
}

const loadBookChapters = async () => {
  if (!selectedBook.value) return
  
  try {
    loadingChapters.value = true
    const response = await booksAPI.getBookChapters(selectedBook.value)
    const allChapters = (response.data.success && response.data.data) ? response.data.data : (response.data.data || response.data || [])
    
    // 过滤出已完成智能分析的章节
    analyzedChapters.value = allChapters.filter(chapter => 
      chapter.analysis_status === 'completed' || 
      chapter.intelligent_analysis_completed || 
      chapter.analysis_result
    )
    
    chapters.value = allChapters // 保留原有逻辑兼容性
    
  } catch (error) {
    console.error('加载章节失败:', error)
    message.error('加载章节失败')
  } finally {
    loadingChapters.value = false
  }
}

const loadChapterContent = async () => {
  if (!selectedChapter.value) return
  
  try {
    const response = await chaptersAPI.getChapter(selectedChapter.value)
    analysisText.value = (response.data.success && response.data.data) ? 
      (response.data.data?.content || '') : 
      (response.data.data?.content || response.data.content || '')
  } catch (error) {
    console.error('加载章节内容失败:', error)
    message.error('加载章节内容失败')
  }
}

const startAnalysis = async () => {
  // 检查是否选择了章节
  if (selectedChapterIds.value.length === 0) {
    message.error('请选择要分析的章节')
    return
  }
  
  return startNewAnalysisFlow()
}

// 新的4步优化流程分析方法
const startNewAnalysisFlow = async () => {
  analyzing.value = true
  analysisStep.value = 1
  analysisProgress.value = 0

  try {
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (analysisProgress.value < 90) {
        analysisProgress.value += Math.random() * 10
      }
    }, 500)

    // 调用新的章节级环境音智能分析API
    const response = await environmentGenerationAPI.analyzeChaptersEnvironment(
      selectedChapterIds.value,
      {
        include_emotion: analysisOptions.value.includes('include_emotion'),
        precise_timing: analysisOptions.value.includes('precise_timing'),
        intensity_analysis: analysisOptions.value.includes('intensity_analysis')
      }
    )

    clearInterval(progressInterval)
    analysisProgress.value = 100

    // 检查响应格式并正确提取分析结果
    if (response.data.enhanced_analysis_result) {
      // 新的增强分析结果格式（来自匹配API）
      analysisResult.value = response.data.enhanced_analysis_result
      console.log('使用增强分析结果格式')
    } else if (response.data.chapters) {
      // 章节级分析结果格式
      analysisResult.value = response.data
      console.log('使用章节级分析结果格式')
    } else {
      // 默认格式
      analysisResult.value = response.data
      console.log('使用默认分析结果格式')
    }
    
    message.success('章节环境音分析完成！')

    // 检查是否已包含匹配结果
    if (analysisResult.value.matching_summary) {
      // 分析结果已包含匹配信息，直接进入匹配结果展示
      console.log('分析结果已包含匹配信息，跳过匹配步骤')
      matchingResult.value = {
        enhanced_analysis_result: analysisResult.value,
        matching_summary: analysisResult.value.matching_summary,
        generation_plan: response.data.generation_plan // 从原始响应中获取
      }
      analysisStep.value = 2 // 跳转到匹配结果展示
    } else {
      // 自动进入下一步：环境音匹配
      setTimeout(() => {
        startMatching()
      }, 1000)
    }

  } catch (error) {
    console.error('章节分析失败:', error)
    message.error('章节分析失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    analyzing.value = false
  }
}

// 环境音匹配方法
const startMatching = async () => {
  if (!analysisResult.value) {
    message.error('没有分析结果')
    return
  }

  matching.value = true
  matchingProgress.value = 0
  analysisStep.value = 2

  try {
    // 模拟匹配进度
    const progressInterval = setInterval(() => {
      if (matchingProgress.value < 90) {
        matchingProgress.value += Math.random() * 15
      }
    }, 300)

    // 从章节分析结果中提取环境轨道数据
    let combinedEnvironmentTracks = []
    
    if (analysisResult.value.chapters && analysisResult.value.chapters.length > 0) {
      // 新的章节级分析结果格式
      for (const chapter of analysisResult.value.chapters) {
        if (chapter.analysis_result && chapter.analysis_result.environment_tracks) {
          // 为每个轨道添加章节信息
          const chapterTracks = chapter.analysis_result.environment_tracks.map(track => ({
            ...track,
            chapter_info: chapter.chapter_info || {}
          }))
          combinedEnvironmentTracks.push(...chapterTracks)
        }
      }
      console.log(`从${analysisResult.value.chapters.length}个章节中提取到${combinedEnvironmentTracks.length}个环境轨道`)
    } else if (analysisResult.value.environment_tracks) {
      // 旧的单章节分析结果格式（向下兼容）
      combinedEnvironmentTracks = analysisResult.value.environment_tracks
      console.log(`使用兼容格式，发现${combinedEnvironmentTracks.length}个环境轨道`)
    } else {
      console.error('分析结果中未找到有效的环境轨道数据:', analysisResult.value)
      message.error('分析结果格式不正确，未找到环境轨道数据')
      return
    }

    if (combinedEnvironmentTracks.length === 0) {
      message.warning('分析结果中没有环境轨道需要匹配')
      clearInterval(progressInterval)
      matchingProgress.value = 100
      matching.value = false
      return
    }

    // 构建匹配API期望的数据格式
    const matchingData = {
      environment_tracks: combinedEnvironmentTracks,
      analysis_metadata: {
        total_tracks: combinedEnvironmentTracks.length,
        source: 'chapter_analysis',
        analysis_timestamp: analysisResult.value.analysis_timestamp || new Date().toISOString()
      }
    }

    console.log(`准备匹配数据:`, matchingData)

    // 调用环境音智能匹配API
    const response = await environmentGenerationAPI.matchEnvironmentSounds(
      matchingData,
      { confidence_threshold: 0.4 }
    )

    clearInterval(progressInterval)
    matchingProgress.value = 100
    
    // 正确处理匹配API响应
    if (response.data.enhanced_analysis_result) {
      // 更新分析结果为增强版本（包含匹配信息）
      analysisResult.value = response.data.enhanced_analysis_result
      
      // 设置匹配结果
      matchingResult.value = {
        enhanced_analysis_result: response.data.enhanced_analysis_result,
        matching_summary: response.data.matching_summary || response.data.enhanced_analysis_result.matching_summary,
        generation_plan: response.data.generation_plan,
        ready_for_generation: response.data.ready_for_generation
      }
      
      console.log('匹配结果已更新:', matchingResult.value)
    } else {
      // 兼容旧格式
      matchingResult.value = response.data
    }

    message.success('环境音匹配完成！')
    
    // 添加调试信息
    console.log('匹配完成状态检查:')
    console.log('- matching.value:', matching.value)
    console.log('- matchingResult.value:', matchingResult.value)
    console.log('- analysisResult.value:', analysisResult.value)

  } catch (error) {
    console.error('匹配失败:', error)
    message.error('匹配失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    matching.value = false
    console.log('匹配状态已重置为 false')
  }
}

const generateSmartPrompts = async () => {
  if (!analysisResult.value) return

  generatingPrompts.value = true
  analysisStep.value = 2

  try {
    const response = await apiClient.post('/scene-analysis/generate-smart-prompts', {
      text: analysisText.value,
      llm_provider: 'auto'
    })

    smartPrompts.value = response.data
    
    // 为每个提示词添加选中状态
    smartPrompts.value.smart_prompts.forEach(prompt => {
      prompt.selected = true // 默认全选
    })

    message.success('智能提示词生成完成！')

  } catch (error) {
    console.error('生成提示词失败:', error)
    message.error('生成提示词失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    generatingPrompts.value = false
  }
}

const startBatchGeneration = async () => {
  const selectedPrompts = smartPrompts.value.smart_prompts.filter(p => p.selected)
  
  if (selectedPrompts.length === 0) {
    message.error('请至少选择一个提示词')
    return
  }

  analysisStep.value = 3
  batchProgress.total = selectedPrompts.length
  batchProgress.completed = 0
  batchProgress.processing = 0
  batchProgress.failed = 0
  batchProgress.status = 'active'
  generationLogs.value = []

  // 添加开始日志
  addGenerationLog('info', '开始批量生成环境音...')

  try {
    // 逐个生成环境音
    for (let i = 0; i < selectedPrompts.length; i++) {
      const prompt = selectedPrompts[i]
      
      batchProgress.currentTask = {
        title: prompt.title,
        progress: 0
      }
      
      try {
        addGenerationLog('info', `开始生成: ${prompt.title}`)
        
        // 模拟进度更新
        const taskProgressInterval = setInterval(() => {
          if (batchProgress.currentTask && batchProgress.currentTask.progress < 90) {
            batchProgress.currentTask.progress += Math.random() * 15
          }
        }, 1000)

        // 调用生成API
        const response = await environmentSoundsAPI.generateEnvironmentSound({
          name: prompt.title,
          prompt: prompt.prompt,
          duration: prompt.duration,
          category_id: null,
          tag_ids: [],
          metadata: {
            generated_from_analysis: true,
            source_text: analysisText.value.substring(0, 200) + '...',
            scene_details: prompt.scene_details,
            generation_method: 'smart_analysis'
          }
        })

        clearInterval(taskProgressInterval)
        batchProgress.currentTask.progress = 100
        
        batchProgress.completed++
        addGenerationLog('success', `✅ ${prompt.title} 生成任务已启动 (ID: ${response.data.sound_id})`)

        // 开始检查生成状态
        if (response.data.sound_id) {
          addGenerationLog('info', `🔍 开始监控生成状态: ${prompt.title}`)
          checkGenerationStatus(response.data.sound_id)
        }

      } catch (error) {
        batchProgress.failed++
        addGenerationLog('error', `❌ ${prompt.title} 生成失败: ${error.message}`)
        console.error(`生成 ${prompt.title} 失败:`, error)
      }
    }

    batchProgress.status = 'completed'
    batchProgress.currentTask = null
    addGenerationLog('info', '批量生成完成！')
    
    message.success('批量生成任务完成！')
    
    // 刷新环境音列表
    await loadSounds()
    await loadStats()
    
    // 为所有生成的环境音启动状态检查
    const generatedIds = selectedPrompts
      .map((_, index) => sounds.value.length + index + 1)
      .filter(id => id > 0)
    
    generatedIds.forEach(id => {
      checkGenerationStatus(id)
    })

  } catch (error) {
    batchProgress.status = 'error'
    addGenerationLog('error', `批量生成失败: ${error.message}`)
    message.error('批量生成失败')
  }
}

const cancelBatchGeneration = () => {
  batchProgress.status = 'cancelled'
  batchProgress.currentTask = null
  addGenerationLog('warning', '批量生成已取消')
  message.info('批量生成已取消')
}

const addGenerationLog = (type, message) => {
  generationLogs.value.push({
    type,
    message,
    time: new Date().toLocaleTimeString()
  })
}

const selectAllPrompts = () => {
  if (smartPrompts.value && smartPrompts.value.smart_prompts) {
    smartPrompts.value.smart_prompts.forEach(prompt => {
      prompt.selected = true
    })
  }
}

const selectNonePrompts = () => {
  if (smartPrompts.value && smartPrompts.value.smart_prompts) {
    smartPrompts.value.smart_prompts.forEach(prompt => {
      prompt.selected = false
    })
  }
}

// 计算属性
const hasSelectedPrompts = computed(() => {
  return smartPrompts.value && smartPrompts.value.smart_prompts 
    ? smartPrompts.value.smart_prompts.some(p => p.selected)
    : false
})

const selectedPromptsCount = computed(() => {
  return smartPrompts.value && smartPrompts.value.smart_prompts 
    ? smartPrompts.value.smart_prompts.filter(p => p.selected).length
    : 0
})

// 样式相关方法
const getSceneColor = (atmosphere) => {
  const colorMap = {
    'calm': 'blue',
    'tense': 'red', 
    'romantic': 'pink',
    'action': 'orange',
    'mysterious': 'purple',
    'scary': 'volcano',
    'joyful': 'green',
    'sad': 'grey'
  }
  return colorMap[atmosphere] || 'default'
}

const getIntensityColor = (intensity) => {
  const colorMap = {
    'low': 'green',
    'medium': 'blue',
    'high': 'orange',
    'very_high': 'red'
  }
  return colorMap[intensity] || 'blue'
}

const getPriorityColor = (priority) => {
  if (priority >= 4) return 'red'
  if (priority >= 3) return 'orange'
  if (priority >= 2) return 'blue'
  return 'default'
}

// 加载所有已分析的章节
const loadAllAnalyzedChapters = async () => {
  try {
    loadingChapters.value = true
    analyzedChapters.value = []
    
    // 获取所有书籍
    const booksResponse = await booksAPI.getBooks()
    const allBooks = (booksResponse.data.success && booksResponse.data.data) ? booksResponse.data.data : (booksResponse.data.data || booksResponse.data || [])
    
    // 遍历每本书，获取已分析的章节
    for (const book of allBooks) {
      try {
        const chaptersResponse = await booksAPI.getBookChapters(book.id)
        const bookChapters = (chaptersResponse.data.success && chaptersResponse.data.data) ? chaptersResponse.data.data : (chaptersResponse.data.data || chaptersResponse.data || [])
        
        // 过滤已分析的章节并添加书籍信息
        const bookAnalyzedChapters = bookChapters
          .filter(chapter => 
            chapter.analysis_status === 'completed' || 
            chapter.intelligent_analysis_completed || 
            chapter.analysis_result
          )
          .map(chapter => ({
            ...chapter,
            book_title: book.title,
            chapter_title: `${book.title} - ${chapter.title || chapter.chapter_title || `第${chapter.chapter_number}章`}`
          }))
        
        analyzedChapters.value.push(...bookAnalyzedChapters)
      } catch (error) {
        console.error(`加载书籍 ${book.title} 章节失败:`, error)
      }
    }
    
    console.log(`发现 ${analyzedChapters.value.length} 个已分析的章节`)
    
  } catch (error) {
    console.error('加载已分析章节失败:', error)
    message.error('加载已分析章节失败')
  } finally {
    loadingChapters.value = false
  }
}

// 监听智能分析模态框打开
watch(showSmartAnalysisModal, (newValue) => {
  if (newValue) {
    // 重置状态
    analysisStep.value = 0
    analysisText.value = ''
    analysisResult.value = null
    smartPrompts.value = null
    selectedBook.value = null
    selectedChapterIds.value = []
    matchingResult.value = null
    generationResult.value = null
    
    // 加载书籍数据和已分析的章节
    loadBooks()
    loadAllAnalyzedChapters()
  }
})

// 辅助方法
const getStatusType = (status) => {
  const statusMap = {
    'completed': 'success',
    'processing': 'processing',
    'failed': 'error',
    'pending': 'default'
  }
  return statusMap[status] || 'default'
}

const getStatusText = (status) => {
  const statusMap = {
    'completed': '已完成',
    'processing': '生成中',
    'failed': '失败',
    'pending': '等待中'
  }
  return statusMap[status] || '未知'
}



// 环境音生成处理
const handleGenerateSounds = async (generationPlan) => {
  console.log('开始生成环境音:', generationPlan)
  // 可以在这里显示生成进度或调用生成API
}

// 匹配结果更新处理
const handleUpdateMatching = (updatedData) => {
  console.log('更新匹配结果:', updatedData)
  // 更新匹配结果
  if (updatedData) {
    matchingResult.value = { ...matchingResult.value, ...updatedData }
  }
}

// 进入生成阶段
const proceedToGeneration = async () => {
  if (!matchingResult.value?.generation_plan) {
    message.error('没有生成计划')
    return
  }

  try {
    batchGenerating.value = true
    generationProgress.value = 0
    analysisStep.value = 3

    // 调用生成API
    const response = await environmentGenerationAPI.generateEnvironmentSounds(
      matchingResult.value.generation_plan,
      { quality: 'high', batch_size: 3 }
    )

    generationResult.value = response.data
    message.success('环境音生成完成！')

  } catch (error) {
    console.error('生成失败:', error)
    message.error('生成失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    batchGenerating.value = false
  }
}

const goBack = () => {
  router.go(-1) // 返回上一页
}
</script>

<style scoped>


.page-header {
  margin-bottom: 24px;
  padding: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.title-with-back {
  display: flex;
  align-items: center;
  gap: 8px;
}

.back-btn {
  font-size: 16px;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  color: rgba(255, 255, 255, 0.8);
  transition: all 0.2s;
}

.back-btn:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

.title-section .page-title {
  display: flex;
  align-items: center;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: white;
}

.title-icon {
  margin-right: 12px;
  color: #ffffff;
}

.page-description {
  margin: 0;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  line-height: 1.5;
}

.stats-section {
  margin-bottom: 24px;
}

.filter-section {
  margin-bottom: 24px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-actions {
  display: flex;
  align-items: center;
}

.sounds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.sound-card {
  position: relative;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: all 0.3s ease;
}

.sound-card:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.sound-card.featured {
  border-color: #faad14;
  background: linear-gradient(135deg, #fff9e6 0%, #fff 100%);
}

.status-badge {
  position: absolute;
  top: 12px;
  right: 12px;
}

.featured-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  color: #faad14;
  font-size: 16px;
}

.sound-info {
  margin-bottom: 12px;
}

.sound-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

.sound-prompt {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sound-meta {
  margin-bottom: 8px;
}

.sound-params {
  display: flex;
  gap: 8px;
}

.param {
  padding: 2px 6px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.sound-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  padding: 8px 0;
  border-top: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  font-size: 12px;
}

.sound-actions {
  display: flex;
  justify-content: flex-end;
}

.error-message {
  margin-top: 12px;
}

.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 暗黑模式适配 */
[data-theme="dark"] .environment-sounds-page {
  background: #141414 !important;
  min-height: 100vh;
}

[data-theme="dark"] .page-header {
  background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}

[data-theme="dark"] .sound-card {
  background: #1f1f1f !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .sound-card:hover {
  border-color: #4a9eff !important;
  box-shadow: 0 4px 12px rgba(74, 158, 255, 0.25) !important;
}

[data-theme="dark"] .sound-card.featured {
  border-color: #faad14 !important;
  background: linear-gradient(135deg, #2d2419 0%, #1f1f1f 100%) !important;
}

[data-theme="dark"] .sound-name {
  color: #fff !important;
}

[data-theme="dark"] .sound-prompt {
  color: #d1d5db !important;
}

[data-theme="dark"] .stat-item {
  color: #8c8c8c !important;
}

[data-theme="dark"] .param {
  background: #2d2d2d !important;
  color: #d1d5db !important;
}

[data-theme="dark"] .sound-stats {
  border-top-color: #434343 !important;
}

/* 智能分析抽屉样式 */
.smart-analysis-drawer :deep(.ant-drawer-body) {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.smart-analysis-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.steps-container {
  margin-bottom: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  flex-shrink: 0;
}

/* 智能分析抽屉暗黑模式适配 */
[data-theme="dark"] .smart-analysis-drawer :deep(.ant-drawer-header) {
  background-color: #1f1f1f !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .smart-analysis-drawer :deep(.ant-drawer-title) {
  color: #fff !important;
}

[data-theme="dark"] .smart-analysis-drawer :deep(.ant-drawer-body) {
  background-color: #1f1f1f !important;
  color: #d1d5db !important;
}

[data-theme="dark"] .smart-analysis-drawer :deep(.ant-drawer-close) {
  color: #8c8c8c !important;
}

[data-theme="dark"] .smart-analysis-drawer :deep(.ant-drawer-close:hover) {
  color: #fff !important;
}

[data-theme="dark"] .steps-container {
  background: #2d2d2d !important;
  border: 1px solid #434343 !important;
}

[data-theme="dark"] .analysis-step h3 {
  color: #fff !important;
}

[data-theme="dark"] .analyzing-state h3,
[data-theme="dark"] .generating-state h3 {
  color: var(--primary-color) !important;
}

[data-theme="dark"] .analyzing-state p,
[data-theme="dark"] .generating-state p {
  color: #8c8c8c !important;
}

[data-theme="dark"] .scene-item {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .scene-header h4 {
  color: var(--primary-color) !important;
}

[data-theme="dark"] .prompt-item {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .prompt-header h4 {
  color: #fff !important;
}

[data-theme="dark"] .prompt-content code {
  background: #1f1f1f !important;
  color: #d1d5db !important;
  border: 1px solid #434343 !important;
}

[data-theme="dark"] .prompt-features {
  color: #8c8c8c !important;
}

[data-theme="dark"] .prompt-settings {
  color: #8c8c8c !important;
}

[data-theme="dark"] .logs-container {
  background: #1f1f1f !important;
  border: 1px solid #434343 !important;
  color: #d1d5db !important;
}

[data-theme="dark"] .log-time {
  color: #8c8c8c !important;
}

/* 智能分析抽屉内的卡片适配 */
[data-theme="dark"] .smart-analysis-drawer :deep(.ant-card) {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .smart-analysis-drawer :deep(.ant-card-head) {
  background: #2d2d2d !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .smart-analysis-drawer :deep(.ant-card-head-title) {
  color: #fff !important;
}

[data-theme="dark"] .smart-analysis-drawer :deep(.ant-card-body) {
  background: #2d2d2d !important;
  color: #d1d5db !important;
}

[data-theme="dark"] .smart-analysis-drawer :deep(.ant-descriptions-item-label) {
  color: #8c8c8c !important;
}

[data-theme="dark"] .smart-analysis-drawer :deep(.ant-descriptions-item-content) {
  color: #d1d5db !important;
}

[data-theme="dark"] .smart-analysis-drawer .narrative_analysis span {
  color: #8c8c8c !important;
}

.analysis-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.analyzing-state, .generating-state {
  text-align: center;
  padding: 40px 20px;
}

.analyzing-state h3, .generating-state h3, .matching-progress h2 {
  color: #1890ff;
  margin-bottom: 8px;
}

.matching-progress, .matching-result {
  text-align: center;
  max-width: 1000px;
  margin: 0 auto;
}

.progress-header {
  margin-bottom: 32px;
}

.progress-header h2 {
  margin: 16px 0 8px 0;
  color: #1890ff;
}

.scenes-list, .tracks-list {
  space-y: 16px;
}

.scene-item, .track-item {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;
}

.scene-header, .track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.scene-header h4, .track-header h4 {
  margin: 0;
  color: #1890ff;
}

.scene-details, .track-details {
  margin-bottom: 8px;
}

.scene-keywords, .track-keywords {
  margin-top: 8px;
}

.prompts-list {
  space-y: 20px;
}

.prompt-item {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  background: #fff;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.prompt-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
}

.prompt-content {
  margin-bottom: 12px;
}

.prompt-content code {
  background: #f6f8fa;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
}

.prompt-features {
  margin-bottom: 8px;
  color: #666;
}

.prompt-settings {
  font-size: 12px;
  color: #888;
}

.step-actions {
  margin-top: 24px;
  text-align: center;
}

.generation-progress {
  text-align: center;
}

.generation-logs {
  max-height: 200px;
  overflow-y: auto;
}

.logs-container {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 12px;
  font-family: monospace;
  font-size: 12px;
}

.log-item {
  display: flex;
  margin-bottom: 4px;
  line-height: 1.4;
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
  color: #52c41a;
}

.log-item.error .log-message {
  color: #ff4d4f;
}

.log-item.warning .log-message {
  color: #fa8c16;
}

.log-item.info .log-message {
  color: #1890ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .environment-sounds-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .sounds-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-section :deep(.ant-form-inline) {
    display: block;
  }
  
  .filter-section :deep(.ant-form-item) {
    margin-bottom: 16px;
  }

  /* 移动端抽屉全屏显示 */
  .smart-analysis-drawer :deep(.ant-drawer) {
    width: 100vw !important;
  }
  
  .smart-analysis-drawer :deep(.ant-drawer-body) {
    padding: 16px;
  }

  .prompt-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .step-actions {
    margin-top: 16px;
  }
  
  .step-actions :deep(.ant-space) {
    width: 100%;
    justify-content: center;
  }
  
  .steps-container {
    margin-bottom: 16px;
    padding: 12px;
  }
  
  .steps-container :deep(.ant-steps) {
    font-size: 12px;
  }
}

.track-item {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
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

.track-header h4, .track-header h5 {
  margin: 0;
  color: #333;
}

.track-details {
  margin-bottom: 8px;
}

.track-keywords {
  margin-top: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.chapter-tracks {
  margin-bottom: 24px;
}

.chapter-tracks h4 {
  color: #1890ff;
  margin-bottom: 16px;
  font-weight: 600;
}

.total-stats {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}

.track-match-info {
  margin-top: 8px;
}

.track-match-info .ant-alert {
  border-radius: 4px;
}

.matching-summary {
  background: #f0f9ff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e0f2fe;
}

.matching-summary h4 {
  margin-bottom: 12px;
  color: #0369a1;
}
</style> 