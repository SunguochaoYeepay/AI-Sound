<template>
  <div class="chapter-analysis">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" tip="加载智能分析结果...">
        <div style="height: 300px"></div>
      </a-spin>
    </div>

    <!-- 有分析数据 -->
    <div v-else-if="analysisData" class="analysis-content">
      <!-- 分析结果tabs -->
      <div class="analysis-tabs">
        <a-tabs v-model="activeTab" type="card">
          <template #rightExtra>
            <a-space>
              <!-- 🔥 新增：缓存状态指示器 -->
              <a-tooltip>
                <template #title>
                  <div>
                    <div>数据来源: {{ getCacheStatusText() }}</div>
                    <div v-if="cacheInfo.user_edited">用户已编辑</div>
                    <div>最后更新: {{ getLastUpdateTime() }}</div>
                  </div>
                </template>
                <a-tag :color="getCacheStatusColor()" size="small" style="cursor: help">
                  {{ getCacheStatusIcon() }} {{ getCacheStatusText() }}
                </a-tag>
              </a-tooltip>

              <!-- 🔥 新增：缓存控制按钮 -->
              <a-dropdown>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="refreshCache">
                      <ReloadOutlined />
                      强制刷新缓存
                    </a-menu-item>
                    <a-menu-item @click="clearEditCache">
                      <ClearOutlined />
                      清除编辑缓存
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item @click="clearAllCache" style="color: #ff4d4f">
                      <DeleteOutlined />
                      清除所有缓存
                    </a-menu-item>
                  </a-menu>
                </template>
                <a-button size="small" type="text">
                  <SettingOutlined />
                  缓存
                  <DownOutlined />
                </a-button>
              </a-dropdown>

              <a-button
                type="primary"
                @click="$emit('refresh')"
                size="small"
                :loading="preparingChapter"
                :disabled="isPreparationDisabled"
              >
                🤖 智能准备
              </a-button>
              <a-button
                type="default"
                @click="runIntelligentDetection"
                size="small"
                :loading="detecting"
                :disabled="!hasAnalysisData"
              >
                🔍 智能检测
              </a-button>
              <a-button
                type="primary"
                @click="saveChanges"
                size="small"
                :loading="saving"
              >
                💾 保存修改
              </a-button>
            </a-space>
          </template>

          <!-- 合成片段tab -->
          <a-tab-pane key="segments" tab="📝 合成片段">
            <div class="segments-editor">
              <div class="editor-header">
                <h4>合成片段配置</h4>

                <!-- 检测结果展示区域 -->
                <div
                  v-if="detectionResult && detectionResult.issues.length > 0"
                  class="detection-results"
                >
                  <a-alert
                    :message="`发现 ${detectionResult.issues.length} 个问题`"
                    :description="`严重: ${detectionResult.stats?.critical_count || 0}, 警告: ${detectionResult.stats?.warning_count || 0}, 信息: ${detectionResult.stats?.info_count || 0}`"
                    type="warning"
                    show-icon
                    closable
                    @close="clearDetectionResult"
                  >
                    <template #action>
                      <a-space>
                        <a-button size="small" @click="showDetectionDetails = true"
                          >查看详情</a-button
                        >
                        <a-button
                          v-if="detectionResult.fixable_count > 0"
                          size="small"
                          type="primary"
                          @click="applyAutoFix"
                          :loading="applyingFix"
                        >
                          自动修复 ({{ detectionResult.fixable_count }})
                        </a-button>
                      </a-space>
                    </template>
                  </a-alert>
                </div>

                <div class="editor-controls">
                  <a-button type="primary" ghost size="small" @click="addNewSegment">
                    <template #icon><PlusOutlined /></template>
                    添加段落
                  </a-button>
                  <a-button
                    type="text"
                    size="small"
                    @click="loadBookCharacters"
                    :loading="loadingBookCharacters"
                  >
                    <template #icon><ReloadOutlined /></template>
                    刷新角色
                  </a-button>
                  <a-select
                    v-model="highlightedCharacter"
                    placeholder="筛选角色"
                    style="width: 120px"
                    @change="handleCharacterFilter"
                    allowClear
                    size="small"
                  >
                    <a-select-option
                      v-for="character in editableCharacters"
                      :key="character.name"
                      :value="character.name"
                    >
                      {{ character.name }}
                    </a-select-option>
                  </a-select>
                  <span class="segment-count"> 共 {{ editableSegments.length }} 个片段 </span>
                </div>
              </div>

              <div class="segments-list">
                <draggable
                  v-model="editableSegments"
                  @end="handleSegmentSort"
                  :animation="200"
                  ghost-class="segment-ghost"
                  chosen-class="segment-chosen"
                  drag-class="segment-drag"
                  item-key="id"
                  tag="div"
                >
                  <template #item="{ element: segment, index }">
                    <div
                      class="segment-item"
                      :class="{
                        'segment-highlighted':
                          highlightedCharacter && segment.speaker === highlightedCharacter,
                        'segment-dimmed':
                          highlightedCharacter && segment.speaker !== highlightedCharacter
                      }"
                      :data-segment-index="index"
                    >
                      <div class="segment-header">
                        <span class="segment-index">#{{ index + 1 }}</span>
                        <a-select
                          v-model="segment.speaker"
                          placeholder="选择说话人"
                          style="width: 160px"
                          @change="markChanged"
                          allowClear
                          show-search
                          :filter-option="filterSpeakerOption"
                        >
                          <!-- 章节分析角色 -->
                          <a-select-opt-group label="📊 章节分析角色">
                            <a-select-option
                              v-for="character in editableCharacters"
                              :key="character.name"
                              :value="character.name"
                            >
                              {{ character.name }}
                            </a-select-option>
                          </a-select-opt-group>

                          <!-- 本书所有角色 -->
                          <a-select-opt-group
                            label="📚 本书所有角色"
                            v-if="bookCharacters.length > 0"
                          >
                            <a-select-option
                              v-for="character in bookCharacters"
                              :key="character.name"
                              :value="character.name"
                            >
                              <div class="character-option">
                                <span class="char-name">{{ character.name }}</span>
                                <a-tag
                                  v-if="character.is_voice_configured"
                                  color="green"
                                  size="small"
                                  >已配音</a-tag
                                >
                                <a-tag v-else color="orange" size="small">未配音</a-tag>
                              </div>
                            </a-select-option>
                          </a-select-opt-group>
                        </a-select>

                        <a-tag
                          v-if="segment.speaker"
                          :color="getCharacterColor(segment.speaker)"
                          size="small"
                        >
                          {{ segment.speaker }}
                        </a-tag>

                        <span
                          v-if="highlightedCharacter && segment.speaker === highlightedCharacter"
                          class="highlight-indicator"
                        >
                          🔍
                        </span>

                        <!-- 段落操作按钮 -->
                        <div class="segment-actions">
                          <a-button
                            type="text"
                            size="small"
                            @click="moveSegmentUp(index)"
                            title="上移段落"
                            :disabled="index === 0"
                          >
                            <template #icon><ArrowUpOutlined /></template>
                          </a-button>
                          <a-button
                            type="text"
                            size="small"
                            @click="moveSegmentDown(index)"
                            title="下移段落"
                            :disabled="index === editableSegments.length - 1"
                          >
                            <template #icon><ArrowDownOutlined /></template>
                          </a-button>
                          <a-button
                            type="text"
                            size="small"
                            @click="insertSegmentAfter(index)"
                            title="在此段落后插入新段落"
                          >
                            <template #icon><PlusOutlined /></template>
                          </a-button>
                          <a-button
                            type="text"
                            size="small"
                            danger
                            @click="deleteSegment(index)"
                            title="删除此段落"
                            :disabled="editableSegments.length <= 1"
                          >
                            <template #icon><DeleteOutlined /></template>
                          </a-button>
                        </div>
                      </div>

                      <div class="segment-content">
                        <a-textarea
                          v-model="segment.text"
                          :placeholder="segment.text ? '文本内容' : '⚠️ 此片段文本内容为空，请手动输入或重新分析'"
                          :auto-size="{ minRows: 2, maxRows: 10 }"
                          @change="markChanged"
                          :class="{ 'empty-text-warning': !segment.text || segment.text.trim() === '' }"
                        />
                        <div v-if="!segment.text || segment.text.trim() === ''" class="empty-text-hint">
                          💡 提示：此片段的文本内容为空，可能是AI分析时未能正确提取文本。您可以：
                          <br>1. 手动输入文本内容
                          <br>2. 重新进行智能分析
                          <br>3. 删除此空片段
                        </div>
                      </div>
                    </div>
                  </template>
                </draggable>
              </div>
            </div>
          </a-tab-pane>

          <!-- JSON数据tab -->
          <a-tab-pane key="json" tab="🔧 JSON数据">
            <div class="json-view">
              <div class="json-header">
                <a-space>
                  <a-button
                    size="small"
                    @click="toggleJsonEditMode"
                    :type="jsonEditMode ? 'primary' : 'default'"
                  >
                    {{ jsonEditMode ? '📖 预览模式' : '✏️ 编辑模式' }}
                  </a-button>
                  <a-button size="small" @click="copyJson"> 📋 复制JSON </a-button>
                  <a-button size="small" @click="formatJson"> 🎨 格式化 </a-button>
                  <a-button size="small" @click="downloadJson"> 💾 下载JSON </a-button>
                  <a-button
                    v-if="jsonEditMode"
                    size="small"
                    @click="saveJsonChanges"
                    type="primary"
                    :disabled="!hasJsonChanges"
                  >
                    💾 保存JSON
                  </a-button>
                </a-space>
              </div>

              <div class="json-editor">
                <!-- 编辑模式 -->
                <a-textarea
                  v-if="jsonEditMode"
                  v-model="editableJsonText"
                  :rows="25"
                  class="json-display editable"
                  placeholder="编辑JSON数据..."
                  @change="markJsonChanged"
                />
                <!-- 预览模式 -->
                <a-textarea
                  v-else
                  :value="getJsonPreview()"
                  :rows="25"
                  readonly
                  class="json-display"
                />
              </div>
            </div>
          </a-tab-pane>

          <!-- 角色信息tab -->
          <a-tab-pane key="characters" tab="🎭 角色信息">
            <div class="characters-view">
              <div class="characters-header">
                <div class="characters-title">
                  <h4>智能识别的角色 (共{{ editableCharacters.length }}个)</h4>
                  <span class="character-stats"> 总片段: {{ editableSegments.length }}个 </span>
                </div>

                <!-- 🔥 新增：批量角色管理操作 -->
                <div class="characters-actions">
                  <a-space>
                    <a-tag v-if="missingCharactersCount > 0" color="orange" size="small">
                      📝 {{ missingCharactersCount }} 个角色待添加到配音库
                    </a-tag>
                    <a-button
                      v-if="missingCharactersCount > 0"
                      type="primary"
                      size="small"
                      @click="showBatchCreateModal"
                      :loading="batchCreating"
                    >
                      🎭 批量添加到配音库
                    </a-button>
                    <a-button
                      size="small"
                      @click="refreshCharacterLibrary"
                      :loading="loadingBookCharacters"
                    >
                      🔄 刷新配音库
                    </a-button>
                  </a-space>
                </div>
              </div>

              <div class="characters-grid">
                <div
                  v-for="(character, index) in editableCharacters"
                  :key="index"
                  class="character-card"
                >
                  <!-- 角色头像和基本信息 -->
                  <div class="character-header">
                    <div class="character-avatar">
                      <a-avatar
                        :size="48"
                        :src="getCharacterAvatar(character)"
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
                        <a-tag :color="getCharacterTypeColor(character.voice_type)" size="small">
                          {{ getCharacterTypeText(character.voice_type) }}
                        </a-tag>
                        <a-tag color="blue" size="small"> 第{{ index + 1 }}位 </a-tag>
                        <a-tag :color="getCharacterStatusColor(character)" size="small">
                          {{ getCharacterStatusText(character) }}
                        </a-tag>
                        <a-tag v-if="character.in_character_library" color="green" size="small">
                          📚 配音库
                        </a-tag>
                        <a-tag v-else color="orange" size="small"> ❓ 待添加 </a-tag>
                      </div>
                    </div>
                  </div>

                  <!-- 角色统计信息 -->
                  <div class="character-stats-detail">
                    <a-row :gutter="8">
                      <a-col :span="12">
                        <a-statistic
                          title="出现次数"
                          :value="character.count || 0"
                          :value-style="{ fontSize: '16px', color: '#1890ff' }"
                        />
                      </a-col>
                      <a-col :span="12">
                        <a-statistic
                          title="占比"
                          :value="getCharacterPercentage(character)"
                          suffix="%"
                          :value-style="{ fontSize: '16px', color: '#52c41a' }"
                        />
                      </a-col>
                    </a-row>
                  </div>

                  <!-- 角色操作按钮 -->
                  <div class="character-actions">
                    <a-space>
                      <a-button
                        size="small"
                        @click="highlightCharacterSegments(character.name)"
                        :type="highlightedCharacter === character.name ? 'primary' : 'default'"
                      >
                        {{
                          highlightedCharacter === character.name ? '🔍 取消高亮' : '🔍 高亮片段'
                        }}
                      </a-button>
                      <a-button size="small" @click="exportCharacterSegments(character.name)">
                        📋 导出片段
                      </a-button>
                      <a-button
                        size="small"
                        @click="testCharacterVoice(character.name)"
                        :loading="testingVoice === character.name"
                      >
                        🔊 试听
                      </a-button>
                    </a-space>
                  </div>
                </div>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>

    <!-- 无分析数据 -->
    <div v-else class="no-analysis">
      <a-empty description="该章节暂无智能分析数据" :image="false">
        <div class="empty-icon">🤖</div>
        <p>请先对章节进行智能准备</p>
        <a-button type="primary" @click="$emit('refresh')"> 🎭 开始智能准备 </a-button>
      </a-empty>
    </div>

    <!-- 🔥 新增：批量创建角色抽屉 - 第一步：选择角色 -->
    <a-drawer
      v-model="batchCreateModalVisible"
      title="🎭 批量添加角色到配音库 - 选择角色"
      :width="800"
      placement="right"
      @close="cancelBatchCreate"
    >
      <div class="batch-create-content">
        <div
          class="drawer-footer"
          style="
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 16px;
            border-top: 1px solid #f0f0f0;
            background: white;
            z-index: 1000;
          "
        >
          <a-space style="float: right">
            <a-button @click="cancelBatchCreate">取消</a-button>
            <a-button
              type="primary"
              @click="goToAudioConfig"
              :disabled="selectedCharactersForBatch.length === 0"
            >
              下一步：配置音频 ({{ selectedCharactersForBatch.length }}个角色)
            </a-button>
          </a-space>
        </div>

        <div
          class="batch-create-body"
          style="padding-bottom: 80px; max-height: calc(100vh - 120px); overflow-y: auto"
        >
          <div class="batch-description">
            <a-alert
              message="智能角色检测"
              :description="`AI已从章节中检测到 ${missingCharacters.length} 个尚未加入配音库的角色，您可以选择批量添加并配置语音。`"
              type="info"
              show-icon
              style="margin-bottom: 16px"
            />
          </div>

          <div class="characters-selection">
            <div class="selection-header">
              <h4>选择要添加的角色</h4>
              <a-space>
                <a-button size="small" @click="selectAllMissingCharacters">全选</a-button>
                <a-button size="small" @click="deselectAllMissingCharacters">取消全选</a-button>
              </a-space>
            </div>

            <!-- 🔥 重构：使用表格显示角色列表 -->
            <div class="characters-table">
              <a-table
                :data-source="missingCharacters"
                :columns="characterTableColumns"
                :row-selection="characterRowSelection"
                :pagination="false"
                size="small"
                :scroll="{ y: 400 }"
                row-key="name"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'avatar'">
                    <a-avatar
                      :size="32"
                      :style="{ backgroundColor: getCharacterColor(record.name) }"
                    >
                      {{ getCharacterInitial(record.name) }}
                    </a-avatar>
                  </template>

                  <template v-if="column.key === 'name'">
                    <div class="character-name-cell">
                      <div class="name">{{ record.name }}</div>
                      <div class="meta">
                        <a-tag size="small" :color="getCharacterTypeColor(record.voice_type)">
                          {{ getCharacterTypeText(record.voice_type) }}
                        </a-tag>
                      </div>
                    </div>
                  </template>

                  <template v-if="column.key === 'count'">
                    <a-tag color="blue" size="small">{{ record.count }}次</a-tag>
                  </template>

                  <template v-if="column.key === 'description'">
                    <div class="description-cell">
                      {{ record.description || '暂无描述' }}
                    </div>
                  </template>
                </template>
              </a-table>
            </div>
          </div>

          <div v-if="selectedCharactersForBatch.length > 0" class="batch-summary">
            <a-divider />
            <div class="summary-info">
              <h4>📋 批量操作摘要</h4>
              <p>
                将创建 <strong>{{ selectedCharactersForBatch.length }}</strong> 个新角色到
                <strong>{{ chapter?.book_id ? '角色配音库' : '当前书籍' }}</strong>
              </p>
              <p class="summary-note">
                💡 创建完成后，这些角色将自动关联到合成计划中，您就可以立即开始语音合成了！
              </p>
            </div>
          </div>
        </div>
      </div>
    </a-drawer>

    <!-- 🔥 新增：第二个抽屉 - 统一音频配置 -->
    <a-drawer
      v-model="audioConfigModalVisible"
      title="🎧 统一配置音频文件"
      :width="700"
      placement="right"
      @close="cancelAudioConfig"
    >
      <div class="audio-config-content">
        <div
          class="drawer-footer"
          style="
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 16px;
            border-top: 1px solid #f0f0f0;
            background: white;
            z-index: 1000;
          "
        >
          <a-space style="float: right">
            <a-button @click="cancelAudioConfig">取消</a-button>
            <a-button @click="goBackToCharacterSelection">上一步</a-button>
            <a-button type="primary" @click="executeBatchCreate" :loading="batchCreating">
              创建 {{ selectedCharactersForBatch.length }} 个角色
            </a-button>
          </a-space>
        </div>

        <div
          class="audio-config-body"
          style="padding-bottom: 80px; max-height: calc(100vh - 120px); overflow-y: auto"
        >
          <!-- 选中角色摘要 -->
          <div class="selected-characters-summary">
            <a-alert
              message="即将创建的角色"
              :description="`已选择 ${selectedCharactersForBatch.length} 个角色：${selectedCharactersForBatch.join('、')}`"
              type="info"
              show-icon
              style="margin-bottom: 20px"
            />
          </div>

          <!-- 统一音频配置 -->
          <div class="unified-audio-config">
            <h3>🎧 统一音频配置</h3>
            <p class="config-description">
              为所有选中的角色设置相同的语音配置。如果某些角色需要个性化设置，您可以在创建后到角色配音库中单独修改。
            </p>

            <a-form layout="vertical" size="middle">
              <a-row :gutter="16">
                <a-col :span="12">
                  <a-form-item label="默认声音类型">
                    <a-select
                      v-model="unifiedVoiceType"
                      :options="voiceTypeOptions"
                      placeholder="选择默认声音类型"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="默认描述">
                    <a-input
                      v-model="unifiedDescription"
                      placeholder="如：温柔女声、沉稳男声等"
                    />
                  </a-form-item>
                </a-col>
              </a-row>

              <!-- 音频文件上传 -->
              <a-form-item label="统一语音示例文件（可选，用于声音克隆）">
                <div class="unified-audio-upload">
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="WAV 音频文件">
                        <a-upload
                          v-model="unifiedWavFileList"
                          name="unified_wav_file"
                          accept=".wav"
                          :max-count="1"
                          :before-upload="() => false"
                          @change="handleUnifiedFileChange($event, 'wav')"
                        >
                          <a-button size="large" type="dashed" style="width: 100%; height: 80px">
                            <div style="text-align: center">
                              <div>📁</div>
                              <div>选择 WAV 文件</div>
                              <div style="font-size: 12px; color: #666">将应用到所有角色</div>
                            </div>
                          </a-button>
                        </a-upload>
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="NPY 特征文件">
                        <a-upload
                          v-model="unifiedNpyFileList"
                          name="unified_npy_file"
                          accept=".npy"
                          :max-count="1"
                          :before-upload="() => false"
                          @change="handleUnifiedFileChange($event, 'npy')"
                        >
                          <a-button size="large" type="dashed" style="width: 100%; height: 80px">
                            <div style="text-align: center">
                              <div>📊</div>
                              <div>选择 NPY 文件</div>
                              <div style="font-size: 12px; color: #666">将应用到所有角色</div>
                            </div>
                          </a-button>
                        </a-upload>
                      </a-form-item>
                    </a-col>
                  </a-row>

                  <div class="upload-tips">
                    <a-alert
                      message="💡 统一配置说明"
                      description="上传的音频文件将作为所有选中角色的默认语音示例。WAV格式要求：单声道, 16kHz-48kHz采样率。NPY文件为对应的音频特征文件。"
                      type="info"
                      show-icon
                    />
                  </div>
                </div>
              </a-form-item>
            </a-form>
          </div>
        </div>
      </div>
    </a-drawer>

    <!-- 检测详情模态框 -->
    <a-modal v-model="showDetectionDetails" title="智能检测详情" width="800px" :footer="null">
      <div v-if="detectionResult" class="detection-details">
        <a-descriptions :column="2" bordered size="small" style="margin-bottom: 16px">
          <a-descriptions-item label="检测时间">{{
            detectionResult.detection_time
          }}</a-descriptions-item>
          <a-descriptions-item label="总问题数">{{
            detectionResult.issues.length
          }}</a-descriptions-item>
          <a-descriptions-item label="严重问题">{{
            detectionResult.stats.critical_count
          }}</a-descriptions-item>
          <a-descriptions-item label="警告问题">{{
            detectionResult.stats.warning_count
          }}</a-descriptions-item>
          <a-descriptions-item label="信息问题">{{
            detectionResult.stats.info_count
          }}</a-descriptions-item>
          <a-descriptions-item label="可自动修复">{{
            detectionResult.fixable_count
          }}</a-descriptions-item>
        </a-descriptions>

        <a-list
          :data-source="detectionResult.issues"
          size="small"
          :pagination="{ pageSize: 10, showSizeChanger: false }"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta>
                <template #title>
                  <a-space>
                    <a-tag
                      :color="
                        item.severity === 'critical'
                          ? 'red'
                          : item.severity === 'warning'
                            ? 'orange'
                            : 'blue'
                      "
                    >
                      {{
                        item.severity === 'critical'
                          ? '严重'
                          : item.severity === 'warning'
                            ? '警告'
                            : '信息'
                      }}
                    </a-tag>
                    <span>{{ item.message }}</span>
                    <a-tag v-if="item.fixable" color="green">可修复</a-tag>
                  </a-space>
                </template>
                <template #description>
                  <div>
                    <div v-if="item.segment_index !== undefined">
                      <strong>位置:</strong> 第 {{ item.segment_index + 1 }} 个片段
                    </div>
                    <div v-if="item.suggestion"><strong>建议:</strong> {{ item.suggestion }}</div>
                    <div v-if="item.context" class="issue-context">
                      <strong>上下文:</strong> {{ item.context }}
                    </div>
                  </div>
                </template>
              </a-list-item-meta>
              <template #actions>
                <a-button
                  v-if="item.fixable"
                  size="small"
                  type="link"
                  @click="applySingleFix(item)"
                >
                  修复此问题
                </a-button>
                <a-button
                  v-if="item.segment_index !== undefined"
                  size="small"
                  type="link"
                  @click="jumpToSegment(item.segment_index)"
                >
                  跳转到片段
                </a-button>
              </template>
            </a-list-item>
          </template>
        </a-list>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
  import { ref, computed, watch, onMounted, nextTick } from 'vue'
  import { message, Modal } from 'ant-design-vue'
  import { useAudioPlayerStore } from '@/stores/audioPlayer'
  import { charactersAPI } from '@/api'
  import draggable from 'vuedraggable'
  import {
    ReloadOutlined,
    ClearOutlined,
    DeleteOutlined,
    SettingOutlined,
    DownOutlined,
    PlusOutlined,
    ArrowUpOutlined,
    ArrowDownOutlined
  } from '@ant-design/icons-vue'
  // Removed unused imports: smartPrepareAPI, deepAnalyzeAPI

  // 在Vue 3 setup script中，导入的组件可以直接在模板中使用

  const props = defineProps({
    chapter: {
      type: Object,
      default: null
    },
    analysisData: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    },
    preparingChapter: {
      type: Boolean,
      default: false
    },
    preparationStatus: {
      type: Object,
      default: null
    }
  })

  const emit = defineEmits(['refresh', 'save'])

  const audioStore = useAudioPlayerStore()

  // 组件注册 - Vue 3版本的vuedraggable直接使用导入的组件

  const activeTab = ref('segments')
  const saving = ref(false)
  const hasChanges = ref(false)
  const highlightedCharacter = ref(null)
  const testingVoice = ref(null)
  const jsonEditMode = ref(false)

  // 智能检测相关状态
  const detecting = ref(false)
  const detectionResult = ref(null)
  const showDetectionDetails = ref(false)
  const applyingFix = ref(false)
  const editableJsonText = ref('')

  // 🔥 新增：缓存状态信息
  const cacheInfo = ref({
    data_source: 'synthesis_plan',
    user_edited: false,
    cache_status: 'cached',
    last_updated: null
  })

  // 可编辑的数据
  const editableCharacters = ref([])
  const editableSegments = ref([])
  const originalData = ref(null)

  // 🔥 新增：加载本书所有角色
  const loadingBookCharacters = ref(false)
  const bookCharacters = ref([])

  // 🔥 新增：批量创建角色相关状态
  const batchCreateModalVisible = ref(false)
  const batchCreating = ref(false)
  const selectedCharactersForBatch = ref([])

  // 🔥 新增：第二个抽屉相关状态
  const audioConfigModalVisible = ref(false)
  const unifiedVoiceType = ref('neutral')
  const unifiedDescription = ref('')
  const unifiedWavFileList = ref([])
  const unifiedNpyFileList = ref([])
  const unifiedWavFile = ref(null)
  const unifiedNpyFile = ref(null)

  // Removed unused variables: rawText, segments



  const loadBookCharacters = async () => {
    if (!props.chapter?.book_id) {
      console.warn('缺少书籍ID，无法加载角色')
      return
    }

    loadingBookCharacters.value = true
    try {
      const response = await charactersAPI.getCharacters({ book_id: props.chapter.book_id })
      if (response.data?.success && response.data.data) {
        bookCharacters.value = response.data.data.map((char) => ({
          ...char,
          is_voice_configured: char.is_voice_configured || false,
          avatarUrl: char.avatarUrl || null
        }))
        console.log('本书角色加载成功:', bookCharacters.value.length, '个角色')
      } else {
        console.warn('加载角色失败:', response.data?.message)
      }
    } catch (error) {
      console.error('加载角色失败:', error)
    } finally {
      loadingBookCharacters.value = false
    }
  }

  // 🔥 新增：获取不在角色配音库中的角色
  const missingCharacters = computed(() => {
    return editableCharacters.value.filter((char) => !char.in_character_library)
  })

  // 🔥 新增：待添加角色数量
  const missingCharactersCount = computed(() => {
    return missingCharacters.value.length
  })

  // 智能检测相关计算属性
  const hasAnalysisData = computed(() => {
    return (
      props.analysisData &&
      (editableSegments.value.length > 0 || editableCharacters.value.length > 0)
    )
  })

  // 🔥 新增：语音类型选项
  const voiceTypeOptions = [
    { label: '男声', value: 'male' },
    { label: '女声', value: 'female' },
    { label: '童声', value: 'child' },
    { label: '中性', value: 'neutral' },
    { label: '旁白', value: 'narrator' }
  ]

  // 🔥 新增：角色表格列配置
  const characterTableColumns = [
    {
      title: '头像',
      key: 'avatar',
      width: 60,
      align: 'center'
    },
    {
      title: '角色名称',
      key: 'name',
      width: 150
    },
    {
      title: '出现次数',
      key: 'count',
      width: 100,
      align: 'center'
    },
    {
      title: '角色描述',
      key: 'description',
      ellipsis: true
    }
  ]

  // 🔥 新增：表格行选择配置
  const characterRowSelection = {
    selectedRowKeys: selectedCharactersForBatch,
    onChange: (selectedRowKeys, _selectedRows) => { // eslint-disable-line no-unused-vars
      selectedCharactersForBatch.value = selectedRowKeys
      console.log('📋 选中角色:', selectedRowKeys)
    },
    onSelectAll: (selected, selectedRows, _changeRows) => { // eslint-disable-line no-unused-vars
      console.log(
        '📋 全选操作:',
        selected,
        selectedRows.map((r) => r.name)
      )
    }
  }

  // 🔥 新增：强制刷新方法
  const forceRefreshSegments = async () => {
    console.log('[角色分析] 强制刷新segments数据')
    await nextTick()
    // 触发响应式更新
    const temp = [...editableSegments.value]
    editableSegments.value = []
    await nextTick()
    editableSegments.value = temp
    console.log('[角色分析] 强制刷新完成，当前segments数量:', editableSegments.value.length)
  }

  // Removed unused computed property: processingInfo

  // 是否禁用准备按钮
  const isPreparationDisabled = computed(() => {
    return (
      props.preparingChapter ||
      props.preparationStatus?.analysis_status === 'processing' ||
      props.preparationStatus?.synthesis_status === 'processing'
    )
  })

  // 🔥 简化：初始化可编辑数据，直接使用JSON中的角色信息
  const initEditableData = async () => {
    if (!props.analysisData?.synthesis_json) {
      console.warn('[角色分析] 没有有效的分析结果数据')
      return
    }

    const synthesisJson = props.analysisData.synthesis_json

    try {
      // 🔥 优化：智能提取角色信息，优先使用characters字段，fallback到synthesis_plan
      console.log('[角色分析] 开始提取角色信息')

      if (synthesisJson.characters && synthesisJson.characters.length > 0) {
        // 如果有characters字段，直接使用
        console.log('[角色分析] 使用characters字段')
        editableCharacters.value = synthesisJson.characters.map((char) => ({
          ...char,
          character_id: char.character_id || null,
          voice_id: char.voice_id || '',
          voice_name: char.voice_name || char.name || '未分配',
          voice_type: char.voice_type || (char.name === '旁白' ? 'narrator' : 'neutral'),
          count: char.count || 0,
          in_character_library: char.in_character_library || false,
          is_voice_configured: char.is_voice_configured || false,
          avatarUrl: char.avatarUrl || null
        }))
      } else {
        // 如果没有characters字段，从synthesis_plan中提取
        console.log('[角色分析] 从synthesis_plan中提取角色信息')
        const segments = synthesisJson.synthesis_plan || []
        const characterMap = new Map()

        // 统计每个角色的出现次数和信息
        segments.forEach((segment) => {
          // 🔥 修复：使用正确的说话人字段映射，支持多种可能的字段名
          const speaker = segment.speaker || segment.speaker_name || segment.character_name || segment.character || '未知'
          if (!characterMap.has(speaker)) {
            characterMap.set(speaker, {
              name: speaker,
              character_id: segment.character_id || null,
              voice_id: segment.voice_id || '',
              voice_name: segment.voice_name || speaker,
              voice_type: speaker === '旁白' ? 'narrator' : 'neutral',
              count: 0,
              in_character_library: segment.character_id ? true : false,
              is_voice_configured: segment.voice_id ? true : false,
              avatarUrl: null
            })
          }
          characterMap.get(speaker).count++
        })

        // 转换为数组
        editableCharacters.value = Array.from(characterMap.values())
      }

      // 对角色按出现次数排序
      editableCharacters.value.sort((a, b) => (b.count || 0) - (a.count || 0))

      console.log('[角色分析] 最终角色信息:', editableCharacters.value)

      // 初始化可编辑的合成计划，确保包含所有必要字段
      editableSegments.value = (synthesisJson.synthesis_plan || []).map((segment, index) => {
        // 🔥 调试日志：打印原始segment数据
        console.log(`[字段映射调试] 原始segment ${index}:`, {
          segment_id: segment.segment_id,
          speaker: segment.speaker,
          text: segment.text ? segment.text.substring(0, 50) + '...' : 'NO_TEXT',
          voice_id: segment.voice_id,
          character_id: segment.character_id
        })

        // 🔥 修复：确保所有必要字段都正确映射
        const mappedSegment = {
          ...segment,
          // 确保ID字段正确
          id: segment.id || segment.segment_id || `segment_${index}_${Date.now()}`,
          segment_id: segment.segment_id || (index + 1),
          chapter_id: segment.chapter_id || props.chapter?.id || null,
          chapter_number: segment.chapter_number || props.chapter?.number || 1,
          // 🔥 关键修复：确保speaker和text字段正确显示
          speaker: segment.speaker || '未知说话人',
          text: segment.text || '',
          
          // 🔥 强制响应式更新
          _forceUpdate: Date.now(),
          
          // 语音配置字段
          character_id: segment.character_id || null,
          voice_id: segment.voice_id || '',
          voice_name: segment.voice_name || '未分配',
          
          // 其他必要字段
          text_type: segment.text_type || 'narration',
          confidence: segment.confidence || 0.9,
          detection_rule: segment.detection_rule || 'manual_input',
          timeStep: segment.timeStep || 32,
          pWeight: segment.pWeight || 2,
          tWeight: segment.tWeight || 3,
          narrator_mode: segment.narrator_mode !== undefined ? segment.narrator_mode : true,
          skip_ai_analysis: segment.skip_ai_analysis !== undefined ? segment.skip_ai_analysis : false
        }

        // 🔥 验证关键字段
        if (!mappedSegment.text) {
          console.warn(`⚠️ 段落 ${index} 缺少文本内容:`, segment)
        }
        if (!mappedSegment.speaker || mappedSegment.speaker === '未知说话人') {
          console.warn(`⚠️ 段落 ${index} 缺少说话人信息:`, segment)
        }

        console.log(`[字段映射调试] 映射后segment ${index}:`, {
          segment_id: mappedSegment.segment_id,
          speaker: mappedSegment.speaker,
          text: mappedSegment.text.substring(0, 50) + '...',
          character_id: mappedSegment.character_id,
          voice_id: mappedSegment.voice_id
        })

        return mappedSegment
      })

      // 保存原始数据用于比较变化
      originalData.value = JSON.parse(
        JSON.stringify({
          characters: editableCharacters.value,
          segments: editableSegments.value
        })
      )

      console.log('[角色分析] 数据初始化完成')
      
      // 🔥 修复：重置hasChanges状态，避免保存按钮被禁用
      hasChanges.value = false
      
      // 🔥 强制Vue重新渲染
      await nextTick()
      console.log('[角色分析] 强制重新渲染完成')
      
      // 🔥 调用强制刷新方法确保数据正确显示
      await forceRefreshSegments()
    } catch (error) {
      console.error('[角色分析] 初始化数据失败:', error)
      message.error('初始化角色分析数据失败')
    }
  }

  // 🔥 简化：监听分析数据变化
  watch(
    () => props.analysisData,
    (newData) => {
      if (newData) {
        initEditableData()
      }
    },
    { immediate: true, deep: true }
  )

  // 🔥 新增：监听章节变化，自动加载本书角色
  watch(
    () => props.chapter,
    (newChapter) => {
      if (newChapter?.book_id) {
        loadBookCharacters()
      }
    },
    { immediate: true }
  )

  // 🔥 新增：页面加载时初始化
  onMounted(() => {
    if (props.chapter?.book_id) {
      loadBookCharacters()
    }
  })

  // 🔥 新增：批量创建角色相关方法
  const showBatchCreateModal = () => {
    // 初始化缺失角色的配置
    missingCharacters.value.forEach((char) => {
      char.selected_voice_type = char.voice_type || 'neutral'
      char.description = char.description || ''
    })
    selectedCharactersForBatch.value = []
    batchCreateModalVisible.value = true
  }

  const cancelBatchCreate = () => {
    batchCreateModalVisible.value = false
    selectedCharactersForBatch.value = []
  }

  // 🔥 新增：进入音频配置步骤
  const goToAudioConfig = () => {
    if (selectedCharactersForBatch.value.length === 0) {
      message.warning('请先选择要创建的角色')
      return
    }

    // 关闭第一个抽屉，打开第二个抽屉
    batchCreateModalVisible.value = false
    audioConfigModalVisible.value = true

    // 重置统一配置
    unifiedVoiceType.value = 'neutral'
    unifiedDescription.value = ''
    unifiedWavFileList.value = []
    unifiedNpyFileList.value = []
    unifiedWavFile.value = null
    unifiedNpyFile.value = null
  }

  // 🔥 新增：取消音频配置
  const cancelAudioConfig = () => {
    audioConfigModalVisible.value = false
    selectedCharactersForBatch.value = []
    // 重置配置
    unifiedVoiceType.value = 'neutral'
    unifiedDescription.value = ''
    unifiedWavFileList.value = []
    unifiedNpyFileList.value = []
  }

  // 🔥 新增：返回角色选择
  const goBackToCharacterSelection = () => {
    audioConfigModalVisible.value = false
    batchCreateModalVisible.value = true
  }

  const selectAllMissingCharacters = () => {
    selectedCharactersForBatch.value = missingCharacters.value.map((char) => char.name)
  }

  const deselectAllMissingCharacters = () => {
    selectedCharactersForBatch.value = []
  }

  const refreshCharacterLibrary = async () => {
    await loadBookCharacters()
    // 重新检查角色配音库关联状态
    await initEditableData()
    message.success('角色配音库已刷新')
  }

  // 🔥 新增：统一文件上传处理
  const handleUnifiedFileChange = (info, fileType) => {
    console.log(`📁 统一文件变化 - 类型: ${fileType}`, info)

    if (fileType === 'wav') {
      unifiedWavFileList.value = info.fileList.slice(-1) // 保持最新的一个文件
      unifiedWavFile.value =
        unifiedWavFileList.value.length > 0 ? unifiedWavFileList.value[0].originFileObj : null
    } else if (fileType === 'npy') {
      unifiedNpyFileList.value = info.fileList.slice(-1) // 保持最新的一个文件
      unifiedNpyFile.value =
        unifiedNpyFileList.value.length > 0 ? unifiedNpyFileList.value[0].originFileObj : null
    }

    // 验证文件格式
    if (unifiedWavFile.value) {
      const fileName = unifiedWavFile.value.name.toLowerCase()
      if (!fileName.endsWith('.wav')) {
        message.warning('音频文件格式不正确，请选择 WAV 格式')
        unifiedWavFileList.value = []
        unifiedWavFile.value = null
        return
      }
    }

    if (unifiedNpyFile.value) {
      const fileName = unifiedNpyFile.value.name.toLowerCase()
      if (!fileName.endsWith('.npy')) {
        message.warning('特征文件格式不正确，请选择 NPY 格式')
        unifiedNpyFileList.value = []
        unifiedNpyFile.value = null
        return
      }
    }
  }

  const executeBatchCreate = async () => {
    if (selectedCharactersForBatch.value.length === 0) {
      message.warning('请选择要添加的角色')
      return
    }

    if (!props.chapter?.book_id) {
      message.error('缺少书籍ID，无法创建角色')
      return
    }

    batchCreating.value = true
    try {
      console.log('🎭 开始批量创建角色...')

      // 🔥 修改：使用统一配置创建角色数据
      const charactersToCreate = selectedCharactersForBatch.value.map((characterName) => {
        const character = missingCharacters.value.find((char) => char.name === characterName)
        return {
          name: character.name,
          voice_type: unifiedVoiceType.value || character.voice_type || 'neutral',
          description:
            unifiedDescription.value ||
            character.description ||
            `从第${props.chapter.number}章智能识别的角色`,
          chapter_id: props.chapter.id,
          frequency: character.count || 1,
          is_main_character: character.count > 5, // 出现超过5次认为是主要角色
          // 保留智能分析的原始信息
          detection_source: 'ai_analysis',
          confidence: character.confidence || 0.8
        }
      })

      console.log('📝 准备创建的角色数据:', charactersToCreate)

      // 调用批量创建API - 修正：使用FormData格式符合后端期望
      const formData = new FormData()
      formData.append('characters_data', JSON.stringify(charactersToCreate))
      formData.append('book_id', props.chapter.book_id)
      if (props.chapter.id) {
        formData.append('chapter_id', props.chapter.id)
      }

      // 🔥 修改：添加统一文件到FormData（为所有角色使用相同文件）
      if (unifiedWavFile.value || unifiedNpyFile.value) {
        selectedCharactersForBatch.value.forEach((characterName, index) => {
          // 为每个角色添加统一的WAV文件
          if (unifiedWavFile.value) {
            formData.append(
              `characters[${index}].wav_file`,
              unifiedWavFile.value,
              unifiedWavFile.value.name
            )
            console.log(`📁 添加统一WAV文件: ${characterName} -> ${unifiedWavFile.value.name}`)
          }

          // 为每个角色添加统一的NPY文件
          if (unifiedNpyFile.value) {
            formData.append(
              `characters[${index}].npy_file`,
              unifiedNpyFile.value,
              unifiedNpyFile.value.name
            )
            console.log(`📊 添加统一NPY文件: ${characterName} -> ${unifiedNpyFile.value.name}`)
          }
        })
      }

      const response = await charactersAPI.batchCreateCharacters(formData)

      console.log('✅ 批量创建角色响应:', response.data)

      if (response.data?.success) {
        const responseData = response.data.data || {}
        const createdCharacters = responseData.created || []
        const skippedCharacters = responseData.skipped || []

        console.log('📋 创建的角色:', createdCharacters)
        console.log('⏭️ 跳过的角色:', skippedCharacters)

        if (createdCharacters.length > 0) {
          // 🔥 重要：更新合成计划中的character_id
          // 注意：后端返回的角色数据可能没有直接的ID，需要重新查询
          await refreshCharacterLibrary()

          // 根据创建的角色名称更新合成计划
          await updateSynthesisPlanWithNewCharacterNames(createdCharacters.map((char) => char.name))

          message.success(
            `✅ 成功添加 ${createdCharacters.length} 个角色到配音库！${skippedCharacters.length > 0 ? ` (跳过 ${skippedCharacters.length} 个已存在的角色)` : ''}`
          )
        } else {
          message.warning('没有创建新角色，所选角色可能已存在')
        }

        // 关闭音频配置抽屉
        audioConfigModalVisible.value = false
        selectedCharactersForBatch.value = []

        // 标记为已修改
        markChanged()
      } else {
        throw new Error(response.data?.message || '批量创建角色失败')
      }
    } catch (error) {
      console.error('❌ 批量创建角色失败:', error)
      message.error(`批量创建角色失败: ${error.message || '未知错误'}`)
    } finally {
      batchCreating.value = false
    }
  }

  // 🔥 新增：根据角色名称更新合成计划中的character_id
  const updateSynthesisPlanWithNewCharacterNames = async (createdCharacterNames) => {
    console.log('🔄 根据角色名称更新合成计划中的character_id...', createdCharacterNames)

    if (!createdCharacterNames || createdCharacterNames.length === 0) {
      console.log('没有需要更新的角色名称')
      return
    }

    // 从刷新后的角色配音库中找到对应的角色ID
    const characterNameToIdMap = {}
    bookCharacters.value.forEach((char) => {
      if (createdCharacterNames.includes(char.name)) {
        characterNameToIdMap[char.name] = char.id
      }
    })

    console.log('📋 角色名称到ID映射:', characterNameToIdMap)

    let updatedCount = 0

    // 更新editableSegments中的character_id
    editableSegments.value.forEach((segment) => {
      const speaker = segment.speaker
      if (speaker && characterNameToIdMap[speaker]) {
        segment.character_id = characterNameToIdMap[speaker]
        segment.voice_id = '' // 清空旧的voice_id，优先使用新架构
        updatedCount++
        console.log(
          `🔗 更新段落 ${segment.segment_id}: ${speaker} -> character_id: ${characterNameToIdMap[speaker]}`
        )
      }
    })

    // 更新editableCharacters中的状态
    editableCharacters.value.forEach((char) => {
      if (characterNameToIdMap[char.name]) {
        char.character_id = characterNameToIdMap[char.name]
        char.in_character_library = true
        char.is_voice_configured = true
        console.log(
          `✅ 更新角色状态: ${char.name} -> character_id: ${characterNameToIdMap[char.name]}`
        )
      }
    })

    console.log(`🎉 共更新了 ${updatedCount} 个段落的character_id`)
  }

  // 标记为已修改
  const markChanged = () => {
    hasChanges.value = true
  }



  // 🔥 修复缺失字段的段落 - 保持原有segment_id不变
  const fixMissingFields = (segments) => {
    // 获取所有已有的segment_id
    const existingSegmentIds = segments.map((s) => s.segment_id).filter((id) => id)
    const maxSegmentId = Math.max(...existingSegmentIds, 0)

    let newSegmentCounter = 1

    return segments.map((segment, index) => {
      // 🔥 关键修复：只修复缺失字段，保持原有segment_id不变
      if (!segment.segment_id || !segment.chapter_id || !segment.text_type) {
        console.log(`[修复段落] 修复段落 ${index + 1} 的缺失字段`)

        // 只有在segment_id真正缺失时才分配新的ID
        let newSegmentId = segment.segment_id
        if (!newSegmentId) {
          // 为新段落分配新的segment_id，确保不重复
          newSegmentId = maxSegmentId + newSegmentCounter
          newSegmentCounter++
        }

        return {
          ...segment,
          segment_id: newSegmentId,
          chapter_id: segment.chapter_id || props.chapter?.id || null,
          chapter_number: segment.chapter_number || props.chapter?.number || 1,
          text_type: segment.text_type || 'narration',
          confidence: segment.confidence || 0.9,
          detection_rule: segment.detection_rule || 'manual_input',
          timeStep: segment.timeStep || 32,
          pWeight: segment.pWeight || 2,
          tWeight: segment.tWeight || 3,
          narrator_mode: segment.narrator_mode !== undefined ? segment.narrator_mode : true,
          skip_ai_analysis:
            segment.skip_ai_analysis !== undefined ? segment.skip_ai_analysis : false,
          character_id: segment.character_id || null,
          voice_id: segment.voice_id || ''
        }
      }
      // 🔥 关键：对于已有完整字段的段落，保持原样不变
      return segment
    })
  }

  // 保存修改
  const saveChanges = async () => {
    // 🔥 修复：即使hasChanges为false也允许保存，确保按钮有响应
    if (!hasChanges.value) {
      console.log('📝 没有检测到数据变化，但仍允许保存')
    }

    saving.value = true
    try {
      console.log('🚀 开始保存智能分析数据...')
      
      // 🔥 修复缺失字段的段落
      const fixedSegments = fixMissingFields(editableSegments.value)

      // 🔥 修复：同步更新total_segments字段
      const currentTotalSegments = fixedSegments.length
      console.log('💾 保存时更新total_segments:', {
        原始total_segments: props.analysisData.synthesis_json.project_info?.total_segments,
        实际段落数量: currentTotalSegments
      })

      const updatedData = {
        ...props.analysisData,
        synthesis_json: {
          ...props.analysisData.synthesis_json,
          project_info: {
            ...props.analysisData.synthesis_json.project_info,
            total_segments: currentTotalSegments
          },
          processing_info: {
            ...props.analysisData.synthesis_json.processing_info,
            total_segments: currentTotalSegments
          },
          characters: editableCharacters.value,
          synthesis_plan: fixedSegments
        }
      }

      console.log('📤 发送保存事件到父组件:', {
        chapterId: props.chapter?.id,
        dataLength: JSON.stringify(updatedData).length,
        segmentsCount: fixedSegments.length,
        charactersCount: editableCharacters.value.length,
        hasChanges: hasChanges.value
      })

      // 🔥 修复：强制触发保存事件
      emit('save', updatedData)
      
      // 🔥 修复：重置变更状态
      hasChanges.value = false
      message.success('保存成功！数据已更新到服务器')
    } catch (error) {
      console.error('❌ 保存失败:', error)
      message.error('保存失败: ' + (error.message || '未知错误'))
    } finally {
      saving.value = false
    }
  }

  // 获取JSON预览
  const getJsonPreview = () => {
    if (!props.analysisData) return ''

    // 🔥 修复缺失字段的段落
    const fixedSegments = fixMissingFields(editableSegments.value)

    // 🔥 修复：同步更新total_segments字段
    const currentTotalSegments = fixedSegments.length

    const previewData = {
      ...props.analysisData,
      synthesis_json: {
        ...props.analysisData.synthesis_json,
        project_info: {
          ...props.analysisData.synthesis_json.project_info,
          total_segments: currentTotalSegments
        },
        processing_info: {
          ...props.analysisData.synthesis_json.processing_info,
          total_segments: currentTotalSegments
        },
        characters: editableCharacters.value,
        synthesis_plan: fixedSegments
      }
    }

    return JSON.stringify(previewData, null, 2)
  }

  // 复制JSON
  const copyJson = async () => {
    try {
      await navigator.clipboard.writeText(getJsonPreview())
      message.success('JSON已复制到剪贴板')
    } catch (error) {
      message.error('复制失败')
    }
  }

  // 格式化JSON
  const formatJson = () => {
    message.info('JSON已格式化显示')
  }

  // 下载JSON
  const downloadJson = () => {
    const jsonContent = getJsonPreview()
    const blob = new Blob([jsonContent], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `第${props.chapter?.number}章_智能分析结果.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    message.success('JSON文件下载成功')
  }



  // 获取角色颜色
  const getCharacterColor = (name) => {
    const colors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
    const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[hash % colors.length]
  }



  // 获取角色类型颜色
  const getCharacterTypeColor = (type) => {
    const colors = {
      male: 'blue',
      female: 'pink',
      narrator: 'purple',
      neutral: 'default'
    }
    return colors[type] || 'default'
  }

  // 获取角色类型文本
  const getCharacterTypeText = (type) => {
    const texts = {
      male: '男性',
      female: '女性',
      narrator: '旁白',
      neutral: '中性'
    }
    return texts[type] || '未知'
  }

  // 获取角色占比
  const getCharacterPercentage = (character) => {
    const total = editableSegments.value.length
    if (total === 0) return 0
    return Math.round((character.count / total) * 100)
  }

  // 🔥 修复：获取角色头像，需要从角色配音库API获取avatarUrl
  const getCharacterAvatar = (character) => {
    // 由于JSON中没有直接包含avatarUrl，需要从角色配音库获取
    // 这里先返回null，等待后续从角色配音库API获取完整信息
    return character?.avatarUrl || null
  }

  // 获取角色首字母
  const getCharacterInitial = (name) => {
    if (!name) return '?'
    if (name.includes('旁白')) return '📖'
    return name.charAt(0)
  }

  // 获取角色排名标识
  const getCharacterRank = (character, index) => {
    if (index === 0) return '👑主角'
    if (index === 1) return '⭐重要配角'
    if (index <= 3) return '✨一般配角'
    if (character.name.includes('旁白')) return '📖旁白'
    return '👤其他'
  }



  // 🔥 简化：直接从角色信息获取状态颜色
  const getCharacterStatusColor = (character) => {
    if (!character?.in_character_library) return 'orange' // 不在角色配音库中
    if (character?.is_voice_configured) return 'green' // 已配置语音
    return 'blue' // 在配音库但未配置语音
  }

  // 🔥 简化：直接从角色信息获取状态文本
  const getCharacterStatusText = (character) => {
    if (!character?.in_character_library) return '未在配音库'
    if (character?.is_voice_configured) return '✅ 已配置语音'
    return '🔧 在配音库中'
  }

  // 高亮角色片段
  const highlightCharacterSegments = (characterName) => {
    if (highlightedCharacter.value === characterName) {
      highlightedCharacter.value = null
      message.info('取消高亮')
    } else {
      highlightedCharacter.value = characterName
      message.info(`高亮角色"${characterName}"的片段`)
      // 切换到片段tab
      activeSubTab.value = 'segments'
    }
  }

  // 导出角色片段
  const exportCharacterSegments = (characterName) => {
    const characterSegments = editableSegments.value
      .filter((segment) => segment.speaker === characterName)
      .map((segment, index) => `${index + 1}. ${segment.text}`)
      .join('\n\n')

    if (characterSegments) {
      const blob = new Blob([`角色"${characterName}"的片段：\n\n${characterSegments}`], {
        type: 'text/plain;charset=utf-8'
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `第${props.chapter?.number}章_${characterName}_片段.txt`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      message.success(`角色"${characterName}"的片段导出成功`)
    } else {
      message.warning(`角色"${characterName}"没有片段`)
    }
  }

  // 测试角色声音 - 简单直接，没配置就报错
  const testCharacterVoice = async (characterName) => {
    testingVoice.value = characterName
    try {
      console.log(`[试听] 开始测试角色: ${characterName}`)

      // 获取角色信息
      const character = editableCharacters.value.find((c) => c.name === characterName)
      const characterSegment = editableSegments.value.find((s) => s.speaker === characterName)

      if (!character) {
        message.error(`未找到角色"${characterName}"的配置信息`)
        return
      }

      console.log(`[试听] 角色信息:`, {
        name: character.name,
        character_id: character.character_id,
        voice_id: character.voice_id,
        in_character_library: character.in_character_library,
        is_voice_configured: character.is_voice_configured
      })

      // 检查角色配音库配置
      if (character.character_id && character.in_character_library) {
        if (!character.is_voice_configured) {
          message.error(
            `角色"${characterName}"在配音库中但未配置音频文件，请前往角色管理页面上传音频`
          )
          return
        }

        console.log(`[试听] 使用角色配音库ID: ${character.character_id}`)

        // 获取示例文本
        const sampleText =
          characterSegment?.text?.slice(0, 50) + '...' || `你好，我是${characterName}。`

        try {
          const response = await charactersAPI.testVoiceSynthesis(character.character_id, {
            text: sampleText
          })

          if (response.data?.success && response.data.audioUrl) {
            const audioInfo = {
              id: `character_test_${characterName}_${Date.now()}`,
              title: `${characterName} - 角色配音库试听`,
              url: response.data.audioUrl,
              type: 'character_test',
              metadata: {
                characterName,
                characterId: character.character_id,
                source: 'character_library'
              }
            }

            await audioStore.playAudio(audioInfo)
            message.success(`正在播放角色"${characterName}"的声音（来源：角色配音库）`)
            return
          } else {
            message.error(`角色配音库试听失败: ${response.data?.message || '未知错误'}`)
            return
          }
        } catch (error) {
          console.error('[试听] 角色配音库API调用失败:', error)
          message.error(`角色配音库试听失败: ${error.response?.data?.detail || error.message}`)
          return
        }
      }

      // 检查传统VoiceProfile配置
      if (character.voice_id) {
        console.log(`[试听] 使用传统VoiceProfile ID: ${character.voice_id}`)

        const sampleText =
          characterSegment?.text?.slice(0, 50) + '...' || `你好，我是${characterName}。`

        try {
          const response = await charactersAPI.testVoiceSynthesis(character.voice_id, {
            text: sampleText
          })

          if (response.data?.success && response.data.audioUrl) {
            const audioInfo = {
              id: `character_test_${characterName}_${Date.now()}`,
              title: `${characterName} - 传统语音档案试听`,
              url: response.data.audioUrl,
              type: 'character_test',
              metadata: {
                characterName,
                voiceId: character.voice_id,
                source: 'voice_profile'
              }
            }

            await audioStore.playAudio(audioInfo)
            message.success(`正在播放角色"${characterName}"的声音（来源：传统语音档案）`)
            return
          } else {
            message.error(`传统语音档案试听失败: ${response.data?.message || '未知错误'}`)
            return
          }
        } catch (error) {
          console.error('[试听] 传统语音档案API调用失败:', error)
          message.error(`传统语音档案试听失败: ${error.response?.data?.detail || error.message}`)
          return
        }
      }

      // 没有任何配置
      console.log(`[试听] 角色"${characterName}"没有任何声音配置`)
      message.error(`角色"${characterName}"未配置声音，请：
1. 前往角色管理页面创建角色并上传音频文件
2. 或在书籍角色管理中为该角色分配已有的声音配置`)
    } catch (error) {
      console.error('[试听] 测试失败:', error)
      message.error(`试听失败: ${error.message}`)
    } finally {
      testingVoice.value = null
    }
  }

  // JSON编辑模式切换
  const toggleJsonEditMode = () => {
    jsonEditMode.value = !jsonEditMode.value
    if (jsonEditMode.value) {
      editableJsonText.value = getJsonPreview()
    }
  }

  // 标记JSON为已修改
  const markJsonChanged = () => {
    // 在编辑模式下，每次文本变化都视为修改
    // 在预览模式下，只有保存按钮点击时才视为修改
    if (jsonEditMode.value) {
      hasChanges.value = true
    }
  }

  // 保存JSON修改
  const saveJsonChanges = async () => {
    if (!jsonEditMode.value) return
    if (!hasJsonChanges.value) return

    try {
      // 验证JSON格式
      const parsedJson = JSON.parse(editableJsonText.value)

      // 更新可编辑数据
      if (parsedJson.characters && Array.isArray(parsedJson.characters)) {
        editableCharacters.value = parsedJson.characters
      }
      if (parsedJson.synthesis_plan && Array.isArray(parsedJson.synthesis_plan)) {
        // 🔥 修复：确保每个segment都有唯一id并修复缺失字段
        const segmentsWithId = parsedJson.synthesis_plan.map((segment, index) => ({
          ...segment,
          id: segment.id || `segment_${index}_${Date.now()}`
        }))

        // 修复缺失字段
        editableSegments.value = fixMissingFields(segmentsWithId)
      }

      // 标记为已修改
      hasChanges.value = true
      message.success('JSON数据已应用到编辑器')

      // 切换回预览模式
      jsonEditMode.value = false
    } catch (error) {
      console.error('JSON格式错误:', error)
      message.error('JSON格式错误，请检查语法')
    }
  }

  // 判断JSON是否有变化
  const hasJsonChanges = computed(() => {
    if (!jsonEditMode.value) return false
    try {
      // 尝试解析JSON来验证格式
      JSON.parse(editableJsonText.value)
      return editableJsonText.value !== getJsonPreview()
    } catch {
      return true // 如果JSON格式错误，也认为有变化
    }
  })

  // 🔥 新增：缓存控制方法
  // 获取缓存状态文本
  const getCacheStatusText = () => {
    switch (cacheInfo.value.data_source) {
      case 'final_config':
        return '用户编辑'
      case 'synthesis_plan':
        return '智能准备'
      default:
        return '未知'
    }
  }

  // 获取缓存状态颜色
  const getCacheStatusColor = () => {
    if (cacheInfo.value.user_edited) return 'purple'
    if (cacheInfo.value.cache_status === 'fresh') return 'green'
    return 'blue'
  }

  // 获取缓存状态图标
  const getCacheStatusIcon = () => {
    if (cacheInfo.value.user_edited) return '✏️'
    if (cacheInfo.value.cache_status === 'fresh') return '🔄'
    return '💾'
  }

  // 获取最后更新时间
  const getLastUpdateTime = () => {
    if (!cacheInfo.value.last_updated) return '未知'
    try {
      const date = new Date(cacheInfo.value.last_updated)
      return date.toLocaleString('zh-CN')
    } catch {
      return '未知'
    }
  }

  // 强制刷新缓存
  const refreshCache = async () => {
    try {
      message.loading('正在刷新缓存...', 0)
      // 发送带有force_refresh参数的请求
      emit('refresh', { force_refresh: true })
      message.destroy()
      message.success('缓存已刷新，将显示最新数据')
    } catch (error) {
      message.destroy()
      message.error('刷新缓存失败')
      console.error('刷新缓存失败:', error)
    }
  }

  // 清除编辑缓存
  const clearEditCache = async () => {
    try {
      if (!props.chapter?.id) {
        message.error('缺少章节信息')
        return
      }

      message.loading('正在清除编辑缓存...', 0)

      // 调用API清除final_config缓存
      await charactersAPI.clearPreparationCache(props.chapter.id, 'final_config')

      message.destroy()
      message.success('编辑缓存已清除，将显示智能准备结果')

      // 刷新数据
      emit('refresh', { force_refresh: true })
    } catch (error) {
      message.destroy()
      message.error('清除编辑缓存失败')
      console.error('清除编辑缓存失败:', error)
    }
  }

  // 清除所有缓存
  const clearAllCache = async () => {
    try {
      if (!props.chapter?.id) {
        message.error('缺少章节信息')
        return
      }

      // 确认操作
      const confirmed = await new Promise((resolve) => {
        Modal.confirm({
          title: '确认清除所有缓存',
          content: '这将删除所有智能准备结果，需要重新进行智能准备。确定继续吗？',
          okText: '确认清除',
          cancelText: '取消',
          okButtonProps: { danger: true },
          onOk: () => resolve(true),
          onCancel: () => resolve(false)
        })
      })

      if (!confirmed) return

      message.loading('正在清除所有缓存...', 0)

      // 调用API清除所有缓存
      await charactersAPI.clearPreparationCache(props.chapter.id, 'all')

      message.destroy()
      message.success('所有缓存已清除，请重新进行智能准备')

      // 刷新数据
      emit('refresh')
    } catch (error) {
      message.destroy()
      message.error('清除所有缓存失败')
      console.error('清除所有缓存失败:', error)
    }
  }

  // 🔥 新增：添加新段落
  const addNewSegment = () => {
    const maxSegmentId = Math.max(...editableSegments.value.map((s) => s.segment_id || 0))

    const newSegment = {
      id: `segment_${Date.now()}`, // 临时ID
      segment_id: maxSegmentId + 1, // 递增的segment_id
      chapter_id: props.chapter?.id || null,
      chapter_number: props.chapter?.number || 1,
      text: '',
      speaker: '',
      voice_name: '未分配',
      text_type: 'narration', // 默认为旁白
      confidence: 0.9,
      detection_rule: 'manual_input', // 标记为手工输入
      timeStep: 32,
      pWeight: 2,
      tWeight: 3,
      narrator_mode: true,
      skip_ai_analysis: false,
      character_id: null,
      voice_id: ''
    }

    editableSegments.value.push(newSegment)
    markChanged()

    // 🔥 修复：显示更新后的段落数量
    const newTotalSegments = editableSegments.value.length
    console.log('➕ 添加段落后，段落总数更新为:', newTotalSegments)
    message.success(`已添加新段落，当前共 ${newTotalSegments} 个段落`)
  }

  // 🔥 新增：插入段落后
  const insertSegmentAfter = (index) => {
    const existingSegment = editableSegments.value[index]
    const maxSegmentId = Math.max(...editableSegments.value.map((s) => s.segment_id || 0))

    const newSegment = {
      id: `segment_${Date.now()}`, // 临时ID
      segment_id: maxSegmentId + 1, // 递增的segment_id
      chapter_id: existingSegment?.chapter_id || props.chapter?.id || null,
      chapter_number: existingSegment?.chapter_number || props.chapter?.number || 1,
      text: '',
      speaker: '',
      voice_name: '未分配',
      text_type: 'narration', // 默认为旁白
      confidence: 0.9,
      detection_rule: 'manual_input', // 标记为手工输入
      timeStep: 32,
      pWeight: 2,
      tWeight: 3,
      narrator_mode: true,
      skip_ai_analysis: false,
      character_id: null,
      voice_id: ''
    }

    editableSegments.value.splice(index + 1, 0, newSegment)
    markChanged()

    // 🔥 修复：显示更新后的段落数量
    const newTotalSegments = editableSegments.value.length
    console.log('➕ 插入段落后，段落总数更新为:', newTotalSegments)
    message.success(`已在此段落后插入新段落，当前共 ${newTotalSegments} 个段落`)
  }

  // 🔥 新增：删除段落
  const deleteSegment = (index) => {
    if (editableSegments.value.length <= 1) {
      message.warning('至少需要保留一个段落')
      return
    }
    editableSegments.value.splice(index, 1)
    markChanged()

    // 🔥 修复：显示更新后的段落数量
    const newTotalSegments = editableSegments.value.length
    console.log('➖ 删除段落后，段落总数更新为:', newTotalSegments)
    message.success(`已删除此段落，当前共 ${newTotalSegments} 个段落`)
  }

  // 🔥 新增：过滤角色选项
  const filterSpeakerOption = (input, option) => {
    return option.label.toLowerCase().includes(input.toLowerCase())
  }

  // 🔥 新增：角色筛选处理
  const handleCharacterFilter = (value) => {
    highlightedCharacter.value = value
    console.log('角色筛选:', value)
  }

  // 🔥 新增：段落排序方法 - 只改变显示顺序，保持原有segment_id不变
  const handleSegmentSort = (evt) => {
    markChanged()
    console.log('段落排序:', evt)
    console.log('📌 重要：段落排序只改变显示顺序，保持原有segment_id不变')
  }

  // 🔥 新增：上移段落
  const moveSegmentUp = (index) => {
    if (index === 0) return
    const temp = editableSegments.value[index]
    editableSegments.value[index] = editableSegments.value[index - 1]
    editableSegments.value[index - 1] = temp
    markChanged()
    message.success('段落已上移')
  }

  // 🔥 新增：下移段落
  const moveSegmentDown = (index) => {
    if (index === editableSegments.value.length - 1) return
    const temp = editableSegments.value[index]
    editableSegments.value[index] = editableSegments.value[index + 1]
    editableSegments.value[index + 1] = temp
    markChanged()
    message.success('段落已下移')
  }

  // 智能检测相关方法
  const runIntelligentDetection = async () => {
    if (!props.chapter?.id) {
      message.error('缺少章节信息')
      return
    }

    detecting.value = true
    try {
      const response = await fetch(`/api/v1/content-preparation/detect/${props.chapter.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          enable_ai_detection: true,
          auto_fix: false
        })
      })

      const result = await response.json()
      if (result.success) {
        // 确保detection_result包含所有必要的字段
        const detectionData = result.detection_result || {}
        detectionResult.value = {
          ...detectionData,
          stats: detectionData.stats || {
            critical_count: 0,
            warning_count: 0,
            info_count: 0,
            total_count: 0
          },
          issues: detectionData.issues || [],
          fixable_count: detectionData.fixable_count || 0
        }

        if (detectionResult.value.issues.length === 0) {
          message.success('检测完成，未发现问题')
        } else {
          message.warning(`检测完成，发现 ${detectionResult.value.issues.length} 个问题`)
        }
        // 🔥 重要：智能检测完成后标记有变更，启用保存按钮
        markChanged()
      } else {
        message.error(result.message || '检测失败')
      }
    } catch (error) {
      console.error('智能检测失败:', error)
      message.error('检测失败，请稍后重试')
    } finally {
      detecting.value = false
    }
  }

  const clearDetectionResult = () => {
    detectionResult.value = null
  }

  const applyAutoFix = async () => {
    if (!detectionResult.value || !props.chapter?.id) {
      return
    }

    applyingFix.value = true
    try {
      const response = await fetch(`/api/v1/content-preparation/detect/fix/${props.chapter.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          issues: detectionResult.value.issues.filter((issue) => issue.fixable)
        })
      })

      const result = await response.json()
      if (result.success) {
        message.success(`已修复 ${result.data.fixed_count} 个问题`)
        // 🔥 修复：智能修复后不自动触发智能准备，避免覆盖修复结果
        // emit('refresh') // 注释掉自动刷新，避免触发智能准备
        clearDetectionResult()
        // 🔥 重要：重置hasChanges状态，因为修复操作已经保存了数据
        hasChanges.value = false
        // 提示用户可以手动重新准备
        message.info('修复完成！如需更新智能准备结果，请手动点击"智能准备"按钮', 3)
      } else {
        message.error(result.message || '修复失败')
      }
    } catch (error) {
      console.error('自动修复失败:', error)
      message.error('修复失败，请稍后重试')
    } finally {
      applyingFix.value = false
    }
  }

  const applySingleFix = async (issue) => {
    if (!props.chapter?.id) {
      return
    }

    try {
      const response = await fetch(`/api/v1/content-preparation/detect/fix/${props.chapter.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          issues: [issue]
        })
      })

      const result = await response.json()
      if (result.success) {
        message.success('问题已修复')
        // 重新运行检测
        await runIntelligentDetection()
      } else {
        message.error(result.message || '修复失败')
      }
    } catch (error) {
      console.error('修复失败:', error)
      message.error('修复失败，请稍后重试')
    }
  }

  const jumpToSegment = (segmentIndex) => {
    // 跳转到指定片段
    const segmentElement = document.querySelector(`[data-segment-index="${segmentIndex}"]`)
    if (segmentElement) {
      segmentElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // 高亮显示
      segmentElement.style.backgroundColor = '#fff7e6'
      setTimeout(() => {
        segmentElement.style.backgroundColor = ''
      }, 2000)
    }
    showDetectionDetails.value = false
  }
</script>

<style scoped>
  .chapter-analysis {
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .loading-wrapper {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .analysis-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .analysis-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
  }

  .analysis-tabs {
    flex: 1;
    overflow: hidden;

    :deep(.ant-tabs) {

      height: 100%;
      display: flex;
      flex-direction: column;

      .ant-tabs-nav {
        background: var(--component-background);
        border-bottom: 1px solid var(--border-color-base);
        display: flex;
        justify-content: space-between;
        align-items: center;

        &::before {
          display: none;
        }

        .ant-tabs-nav-wrap {
          flex: 1;
        }

        .ant-tabs-extra-content {
          margin-left: 16px;
        }
      }
    }

    :deep(.ant-tabs-content-holder) {
      flex: 1;
      overflow: auto;
    }
  }

  .segments-view {
    padding: 16px;
    height: 100%;
    overflow-y: auto;
  }

  .segments-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .segments-header h4 {
    margin: 0;
    color: #1f2937;
  }

  .segment-count {
    font-size: 12px;
    color: #6b7280;
  }

  /* 段落编辑器样式 */
  .segments-editor {
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    overflow: hidden;
  }

  .editor-header {
    padding: 12px 16px;
    border-bottom: 1px solid #e8e8e8;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .editor-header h4 {
    margin: 0;
    font-size: 14px;
    color: #333;
  }

  .editor-controls {
    display: flex;
    gap: 8px;
  }

  /* .segments-list 样式已移除，使用默认样式 */

  .segment-item {
    padding: 12px 16px;
    border-bottom: 1px solid #f0f0f0;
    transition: all 0.2s ease;
  }

  .segment-item:hover {
    background: #fafafa;
  }

  .segment-item:last-child {
    border-bottom: none;
  }

  .segment-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .segment-index {
    font-weight: 500;
    color: #666;
    min-width: 40px;
  }

  .segment-actions {
    display: flex;
    gap: 4px;
    margin-left: auto;
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  .segment-item:hover .segment-actions {
    opacity: 1;
  }

  .character-option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
  }

  .char-name {
    flex: 1;
    margin-right: 8px;
  }

  /* 段落高亮样式 */
  .segment-highlighted {
    background: #e6f7ff;
    border-left: 3px solid #1890ff;
  }

  .segment-dimmed {
    opacity: 0.5;
  }

  /* 拖拽排序样式 */
  .segment-ghost {
    opacity: 0.5;
    background: #f0f0f0;
    border: 2px dashed #d9d9d9;
  }

  .segment-chosen {
    background: #e6f7ff;
    border-left: 3px solid #1890ff;
  }

  .segment-drag {
    background: #fff;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    border: 1px solid #1890ff;
    border-radius: 4px;
    transform: rotate(5deg);
  }

  /* 响应式设计 */
  @media (max-width: 768px) {
    .editor-header {
      flex-direction: column;
      gap: 8px;
      align-items: flex-start;
    }

    .editor-controls {
      width: 100%;
      justify-content: flex-end;
    }

    .segment-header {
      flex-wrap: wrap;
      gap: 4px;
    }

    .segment-actions {
      opacity: 1; /* 移动端始终显示 */
    }
  }

  .segment-content {
    margin-top: 8px;
  }

  .json-view {
    padding: 16px;
    height: 100%;
    overflow-y: auto;
  }

  .json-header {
    margin-bottom: 16px;
    padding: 8px 0;
    border-bottom: 1px solid #f0f0f0;
  }

  .json-editor {
    height: calc(100% - 100px);
  }

  .json-display {
    font-family: 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.4;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    resize: none;
    height: 100%;
  }

  .json-display.editable {
    border-color: #40a9ff;
    box-shadow: 0 0 0 2px rgba(64, 169, 255, 0.2);
    background-color: #fafafa;
  }

  .json-display.editable:focus {
    border-color: #40a9ff;
    box-shadow: 0 0 0 2px rgba(64, 169, 255, 0.3);
  }

  .characters-view {
    padding: 16px;
    height: 100%;
    overflow-y: auto;
  }

  .characters-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .characters-header h4 {
    margin: 0;
    color: #1f2937;
  }

  .character-stats {
    font-size: 12px;
    color: #6b7280;
  }

  .characters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
    margin-top: 16px;
  }

  .character-card {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px;
    background: #fff;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
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
    min-width: 0;
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
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .character-rank {
    font-size: 12px;
    color: #6b7280;
    flex-shrink: 0;
  }

  .character-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 4px;
  }

  .character-details {
    margin-top: 12px;
  }

  .character-actions {
    margin-top: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }

  .no-analysis {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
  }

  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
  }

  .no-analysis p {
    color: #6b7280;
    margin: 8px 0 16px 0;
  }

  /* 🔥 新增：角色头部布局样式 */
  .characters-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f0f0f0;
  }

  .characters-title {
    flex: 1;
  }

  .characters-actions {
    flex-shrink: 0;
  }

  /* 🔥 新增：批量创建抽屉样式 */
  .batch-create-content {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .batch-create-body {
    flex: 1;
    padding-right: 8px;
  }

  .selection-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .selection-header h4 {
    margin: 0;
  }

  .characters-grid-batch {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
    max-height: 400px;
    overflow-y: auto;
    padding: 8px;
    border: 1px solid #f0f0f0;
    border-radius: 6px;
  }

  .character-batch-item {
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    padding: 12px;
    transition: all 0.2s ease;
  }

  .character-batch-item:hover {
    border-color: #1890ff;
    background-color: #f6f9ff;
  }

  .character-batch-info {
    width: 100%;
  }

  .character-batch-header {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .character-batch-details {
    flex: 1;
  }

  .character-batch-details .character-name {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 4px;
  }

  .character-batch-details .character-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #666;
  }

  .character-count {
    background: #f0f0f0;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
  }

  .voice-config-form {
    background: #fafafa;
    padding: 12px;
    border-radius: 6px;
    margin-top: 8px;
  }

  .batch-summary {
    margin-top: 16px;
  }

  .summary-info h4 {
    margin: 0 0 8px 0;
    color: #1890ff;
  }

  .summary-info p {
    margin: 4px 0;
  }

  .summary-note {
    color: #52c41a;
    font-size: 13px;
    background: #f6ffed;
    padding: 8px;
    border-radius: 4px;
    border-left: 3px solid #52c41a;
  }

  /* 🔥 新增：音频上传样式 */
  .audio-upload-section {
    margin-top: 8px;
  }

  .upload-tips {
    margin-top: 8px;
  }

  .upload-tips .ant-alert {
    border-radius: 4px;
  }

  /* 优化抽屉footer */
  .drawer-footer {
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
  }

  /* 文件上传按钮样式 */
  .audio-upload-section .ant-upload {
    display: block;
    width: 100%;
  }

  .audio-upload-section .ant-btn {
    height: 32px;
    font-size: 12px;
  }

  /* 🔥 新增：角色表格样式 */
  .characters-table {
    margin-top: 16px;
  }

  .character-name-cell .name {
    font-weight: 500;
    margin-bottom: 4px;
  }

  .character-name-cell .meta {
    display: flex;
    gap: 8px;
  }

  .description-cell {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* 🔥 新增：统一音频配置样式 */
  .audio-config-content {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .audio-config-body {
    flex: 1;
    padding-right: 8px;
  }

  .config-description {
    color: #666;
    font-size: 14px;
    margin-bottom: 20px;
    line-height: 1.6;
  }

  .unified-audio-upload {
    margin-top: 12px;
  }

  .unified-audio-upload .ant-btn {
    border-style: dashed;
    color: #666;
  }

  .unified-audio-upload .ant-btn:hover {
    border-color: #1890ff;
    color: #1890ff;
  }

  /* 🔥 新增：智能检测样式 */
  .detection-results {
    margin-bottom: 16px;
  }

  .detection-details .issue-context {
    color: #666;
    font-size: 12px;
    margin-top: 4px;
    padding: 4px 8px;
    background: #f5f5f5;
    border-radius: 4px;
    max-width: 100%;
    word-break: break-all;
  }

  .detection-details .ant-list-item {
    padding: 12px 0;
  }

  .detection-details .ant-list-item-meta-title {
    margin-bottom: 8px;
  }

  .detection-details .ant-descriptions {
    background: #fafafa;
  }

  /* 空文本警告样式 */
  .empty-text-warning {
    border-color: #ff7875 !important;
    background-color: #fff2f0 !important;
  }

  .empty-text-warning:focus {
    border-color: #ff7875 !important;
    box-shadow: 0 0 0 2px rgba(255, 120, 117, 0.2) !important;
  }

  .empty-text-hint {
    margin-top: 8px;
    padding: 8px 12px;
    background: #fff7e6;
    border: 1px solid #ffd591;
    border-radius: 6px;
    font-size: 12px;
    color: #d46b08;
    line-height: 1.5;
  }

  .empty-text-hint br {
    margin: 2px 0;
  }
</style>
