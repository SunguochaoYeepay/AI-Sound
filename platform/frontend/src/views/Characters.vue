<template>
  <div class="voice-library-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 style="margin: 0; color: white; font-size: 28px; font-weight: 700;">
          声音库管理
        </h1>
        <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
          管理已克隆的声音样本，评估质量并优化参数配置
        </p>
      </div>
      <div class="header-actions">
        <a-button type="primary" size="large" @click="showImportModal = true" ghost>
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </template>
          批量导入
        </a-button>
        <a-button size="large" @click="addNewVoice" style="background: white; color: #06b6d4; border-color: white;">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
            </svg>
          </template>
          添加声音
        </a-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ voiceLibrary.length }}</div>
          <div class="stat-label">声音样本总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ highQualityCount }}</div>
          <div class="stat-label">高质量样本</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ todayUsage }}</div>
          <div class="stat-label">今日使用次数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ (averageQuality * 2).toFixed(1) }}</div>
          <div class="stat-label">平均质量评分</div>
        </div>
      </div>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <div class="filter-controls">
        <a-input-search
          v-model:value="searchQuery"
          placeholder="搜索声音样本..."
          style="width: 300px;"
          size="large"
          @search="handleSearch"
        />
        
        <a-select
          v-model:value="qualityFilter"
          placeholder="质量筛选"
          style="width: 120px;"
          size="large"
          @change="handleFilterChange"
        >
          <a-select-option value="">全部</a-select-option>
          <a-select-option value="high">高质量</a-select-option>
          <a-select-option value="medium">中等质量</a-select-option>
          <a-select-option value="low">低质量</a-select-option>
        </a-select>

        <a-select
          v-model:value="typeFilter"
          placeholder="类型筛选"
          style="width: 120px;"
          size="large"
          @change="handleFilterChange"
        >
          <a-select-option value="">全部类型</a-select-option>
          <a-select-option value="male">男声</a-select-option>
          <a-select-option value="female">女声</a-select-option>
          <a-select-option value="child">童声</a-select-option>
        </a-select>
      </div>

      <div class="view-controls">
        <a-radio-group v-model:value="viewMode" size="large">
          <a-radio-button value="grid">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3,11H11V3H3M3,21H11V13H3M13,21H21V13H13M13,3V11H21V3"/>
            </svg>
          </a-radio-button>
          <a-radio-button value="list">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3,5H21V7H3V5M3,13V11H21V13H3M3,19V17H21V19H3Z"/>
            </svg>
          </a-radio-button>
        </a-radio-group>
      </div>
    </div>

    <!-- 声音库列表 -->
    <div class="voice-library-content">
      <!-- 网格视图 -->
      <div v-if="viewMode === 'grid'" class="grid-view">
        <div 
          v-for="voice in filteredVoices" 
          :key="voice.id"
          class="voice-card"
          @click="selectVoice(voice)"
          :class="{ 'selected': selectedVoice?.id === voice.id }"
        >
          <div class="voice-avatar">
            <div class="avatar-icon" :style="{ background: voice.color }">
              {{ voice.name.charAt(0) }}
            </div>
            <div class="voice-status" :class="voice.status">
              <div class="status-dot"></div>
            </div>
          </div>

          <div class="voice-info">
            <h3 class="voice-name">{{ voice.name }}</h3>
            <p class="voice-desc">{{ voice.description }}</p>
            
            <div class="voice-meta">
              <div class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
                <span>{{ voice.quality.toFixed(1) }}</span>
              </div>
              <div class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <span>{{ voice.usageCount }}</span>
              </div>
            </div>
          </div>

          <div class="voice-actions">
            <a-button type="text" size="small" @click.stop="playVoice(voice)">
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
                </svg>
              </template>
            </a-button>
            <a-dropdown @click.stop="">
              <a-button type="text" size="small">
                <template #icon>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z"/>
                  </svg>
                </template>
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="edit" @click="editVoice(voice)">编辑</a-menu-item>
                  <a-menu-item key="duplicate" @click="duplicateVoice(voice)">复制</a-menu-item>
                  <a-menu-item key="export" @click="exportVoice(voice)">导出</a-menu-item>
                  <a-menu-divider />
                  <a-menu-item key="delete" @click="deleteVoice(voice)" style="color: #ef4444;">删除</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </div>
      </div>

      <!-- 列表视图 -->
      <div v-else class="list-view">
        <a-table
          :columns="tableColumns"
          :data-source="filteredVoices"
          :pagination="{ pageSize: 10, showSizeChanger: true, showQuickJumper: true }"
          row-key="id"
          size="large"
          @row="(record) => ({ onClick: () => selectVoice(record) })"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <div style="display: flex; align-items: center; gap: 12px;">
                <div class="table-avatar" :style="{ background: record.color }">
                  {{ record.name.charAt(0) }}
                </div>
                <div>
                  <div style="font-weight: 500;">{{ record.name }}</div>
                  <div style="font-size: 12px; color: #6b7280;">{{ record.description }}</div>
                </div>
              </div>
            </template>

            <template v-if="column.key === 'quality'">
              <a-rate v-model:value="record.quality" disabled allow-half />
            </template>

            <template v-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>

            <template v-if="column.key === 'actions'">
              <div style="display: flex; gap: 8px;">
                <a-button type="text" size="small" @click.stop="playVoice(record)">
                  <template #icon>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
                    </svg>
                  </template>
                </a-button>
                <a-button type="text" size="small" @click.stop="editVoice(record)">
                  <template #icon>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
                    </svg>
                  </template>
                </a-button>
                <a-button type="text" size="small" danger @click.stop="deleteVoice(record)">
                  <template #icon>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                    </svg>
                  </template>
                </a-button>
              </div>
            </template>
          </template>
        </a-table>
      </div>
    </div>

    <!-- 声音详情面板 -->
    <a-drawer
      v-model:open="showDetailDrawer"
      title="声音详情"
      placement="right"
      width="500"
      :closable="true"
    >
      <div v-if="selectedVoice" class="voice-detail">
        <div class="detail-header">
          <div class="detail-avatar" :style="{ background: selectedVoice.color }">
            {{ selectedVoice.name.charAt(0) }}
          </div>
          <div class="detail-info">
            <h2>{{ selectedVoice.name }}</h2>
            <p>{{ selectedVoice.description }}</p>
            <a-rate v-model:value="selectedVoice.quality" disabled allow-half />
          </div>
        </div>

        <a-divider />

        <div class="detail-section">
          <h3>音频样本</h3>
          <div class="audio-sample">
            <audio controls style="width: 100%;">
              <source :src="selectedVoice.audioUrl" type="audio/wav">
            </audio>
          </div>
        </div>

        <div class="detail-section">
          <h3>技术参数</h3>
          <div class="params-list">
            <div class="param-row">
              <span class="param-label">Time Step:</span>
              <span class="param-value">{{ selectedVoice.params.timeStep }}</span>
            </div>
            <div class="param-row">
              <span class="param-label">智能权重 (p_w):</span>
              <span class="param-value">{{ selectedVoice.params.pWeight }}</span>
            </div>
            <div class="param-row">
              <span class="param-label">相似度权重 (t_w):</span>
              <span class="param-value">{{ selectedVoice.params.tWeight }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>使用统计</h3>
          <div class="stats-list">
            <div class="stat-row">
              <span class="stat-label">使用次数:</span>
              <span class="stat-value">{{ selectedVoice.usageCount }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">创建时间:</span>
              <span class="stat-value">{{ selectedVoice.createdAt }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">最后使用:</span>
              <span class="stat-value">{{ selectedVoice.lastUsed }}</span>
            </div>
          </div>
        </div>

        <div class="detail-actions">
          <a-button type="primary" block size="large" @click="useVoiceForTTS">
            使用此声音
          </a-button>
          <div style="display: flex; gap: 12px; margin-top: 12px;">
            <a-button @click="editVoice(selectedVoice)" style="flex: 1;">编辑</a-button>
            <a-button @click="duplicateVoice(selectedVoice)" style="flex: 1;">复制</a-button>
            <a-button danger @click="deleteVoice(selectedVoice)" style="flex: 1;">删除</a-button>
          </div>
        </div>
      </div>
    </a-drawer>

    <!-- 新增/编辑声音模态框 -->
    <a-modal
      v-model:open="showEditModal"
      :title="editingVoice.id ? '编辑声音' : '新增声音'"
      width="800"
      :maskClosable="false"
      @ok="saveVoice"
      @cancel="cancelEdit"
    >
      <a-form
        ref="editForm"
        :model="editingVoice"
        :rules="editRules"
        layout="vertical"
        class="voice-edit-form"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="声音名称" name="name" required>
              <a-input v-model:value="editingVoice.name" placeholder="请输入声音名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="声音类型" name="type" required>
              <a-select v-model:value="editingVoice.type" placeholder="选择声音类型">
                <a-select-option value="male">男声</a-select-option>
                <a-select-option value="female">女声</a-select-option>
                <a-select-option value="child">童声</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="声音描述" name="description">
          <a-textarea 
            v-model:value="editingVoice.description" 
            placeholder="请输入声音描述信息"
            :rows="3"
          />
        </a-form-item>

        <a-form-item label="参考音频文件" name="audioFile" required>
          <a-upload-dragger
            v-model:fileList="editingVoice.audioFileList"
            :multiple="false"
            :before-upload="beforeAudioUpload"
            @change="handleEditAudioChange"
            accept=".wav,.mp3,.m4a"
            class="edit-upload"
          >
            <div class="upload-content">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="#06b6d4" style="margin-bottom: 12px;">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
              <p style="font-size: 14px; color: #374151; margin: 0;">上传音频文件</p>
              <p style="font-size: 12px; color: #9ca3af; margin: 4px 0 0 0;">支持 WAV, MP3, M4A 格式</p>
            </div>
          </a-upload-dragger>
        </a-form-item>

        <a-divider>技术参数</a-divider>

        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="Time Step">
              <a-slider
                v-model:value="editingVoice.params.timeStep"
                :min="5"
                :max="100"
                :step="5"
              />
              <div class="param-display">{{ editingVoice.params.timeStep }} steps</div>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="智能权重 (p_w)">
              <a-slider
                v-model:value="editingVoice.params.pWeight"
                :min="0"
                :max="2"
                :step="0.1"
              />
              <div class="param-display">{{ editingVoice.params.pWeight.toFixed(1) }}</div>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="相似度权重 (t_w)">
              <a-slider
                v-model:value="editingVoice.params.tWeight"
                :min="0"
                :max="2"
                :step="0.1"
              />
              <div class="param-display">{{ editingVoice.params.tWeight.toFixed(1) }}</div>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="质量评分">
          <a-rate v-model:value="editingVoice.quality" allow-half />
          <span style="margin-left: 12px; color: #6b7280;">{{ editingVoice.quality }} 星</span>
        </a-form-item>

        <a-form-item label="状态">
          <a-radio-group v-model:value="editingVoice.status">
            <a-radio value="active">可用</a-radio>
            <a-radio value="training">训练中</a-radio>
            <a-radio value="inactive">未激活</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="标签颜色">
          <div class="color-picker">
            <div 
              v-for="color in colorOptions" 
              :key="color"
              class="color-option"
              :class="{ 'selected': editingVoice.color === color }"
              :style="{ background: color }"
              @click="editingVoice.color = color"
            ></div>
          </div>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 批量导入模态框 -->
    <a-modal
      v-model:open="showImportModal"
      title="批量导入声音"
      width="600"
      @ok="importVoices"
      @cancel="showImportModal = false"
    >
      <div class="import-section">
        <a-upload-dragger
          v-model:fileList="importFiles"
          :multiple="true"
          :before-upload="beforeImportUpload"
          accept=".zip,.rar"
          class="import-upload"
        >
          <div class="upload-content">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="#06b6d4" style="margin-bottom: 16px;">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
            <p style="font-size: 16px; color: #374151; margin: 0;">拖拽或点击上传压缩包</p>
            <p style="font-size: 14px; color: #9ca3af; margin: 8px 0 0 0;">支持包含音频文件的 ZIP 或 RAR 格式</p>
          </div>
        </a-upload-dragger>
        
        <a-divider />
        
        <div class="import-tips">
          <h4 style="color: #374151; margin-bottom: 12px;">导入说明：</h4>
          <ul style="color: #6b7280; line-height: 1.6;">
            <li>压缩包内应包含音频文件（.wav, .mp3, .m4a）</li>
            <li>文件名将作为声音名称</li>
            <li>系统会自动分析并生成默认参数</li>
            <li>导入后可在声音库中进一步编辑</li>
          </ul>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { message } from 'ant-design-vue'

// 响应式数据
const searchQuery = ref('')
const qualityFilter = ref('')
const typeFilter = ref('')
const viewMode = ref('grid')
const selectedVoice = ref(null)
const showDetailDrawer = ref(false)
const showImportModal = ref(false)
const showUploadModal = ref(false)
const showEditModal = ref(false)
const editForm = ref(null)
const importFiles = ref([])

// 编辑表单数据
const editingVoice = ref({
  id: null,
  name: '',
  description: '',
  type: '',
  quality: 3.0,
  status: 'active',
  color: '#06b6d4',
  audioFileList: [],
  params: {
    timeStep: 20,
    pWeight: 1.0,
    tWeight: 1.0
  }
})

// 表单验证规则
const editRules = {
  name: [
    { required: true, message: '请输入声音名称', trigger: 'blur' },
    { min: 2, max: 20, message: '名称长度应在 2-20 字符之间', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择声音类型', trigger: 'change' }
  ],
  audioFile: [
    { required: true, message: '请上传音频文件', trigger: 'change' }
  ]
}

// 颜色选项
const colorOptions = [
  '#06b6d4', '#f472b6', '#10b981', '#f59e0b', 
  '#ef4444', '#8b5cf6', '#06d6a0', '#fbbf24',
  '#3b82f6', '#6b7280', '#f97316', '#84cc16'
]

// 模拟声音库数据
const voiceLibrary = ref([
  {
    id: 1,
    name: '温柔女声',
    description: '柔和亲切的女性声音，适合儿童故事',
    type: 'female',
    quality: 4.5,
    status: 'active',
    color: '#06b6d4',
    usageCount: 156,
    audioUrl: '/audio/sample1.wav',
    createdAt: '2024-01-15',
    lastUsed: '2024-01-20',
    params: { timeStep: 20, pWeight: 1.2, tWeight: 0.8 }
  },
  {
    id: 2,
    name: '磁性男声',
    description: '低沉有磁性的男性声音，适合朗读',
    type: 'male',
    quality: 4.8,
    status: 'active',
    color: '#ff7b54',
    usageCount: 203,
    audioUrl: '/audio/sample2.wav',
    createdAt: '2024-01-10',
    lastUsed: '2024-01-19',
    params: { timeStep: 25, pWeight: 1.0, tWeight: 1.2 }
  },
  {
    id: 3,
    name: '童声',
    description: '活泼可爱的儿童声音',
    type: 'child',
    quality: 3.8,
    status: 'training',
    color: '#10b981',
    usageCount: 89,
    audioUrl: '/audio/sample3.wav',
    createdAt: '2024-01-18',
    lastUsed: '2024-01-18',
    params: { timeStep: 15, pWeight: 0.8, tWeight: 1.0 }
  },
  {
    id: 4,
    name: '专业主播',
    description: '专业新闻播音员声音',
    type: 'female',
    quality: 4.9,
    status: 'active',
    color: '#f59e0b',
    usageCount: 312,
    audioUrl: '/audio/sample4.wav',
    createdAt: '2024-01-05',
    lastUsed: '2024-01-20',
    params: { timeStep: 30, pWeight: 1.5, tWeight: 1.1 }
  },
  {
    id: 5,
    name: '老者声音',
    description: '慈祥的老年男性声音',
    type: 'male',
    quality: 3.5,
    status: 'inactive',
    color: '#6b7280',
    usageCount: 45,
    audioUrl: '/audio/sample5.wav',
    createdAt: '2024-01-12',
    lastUsed: '2024-01-15',
    params: { timeStep: 20, pWeight: 0.9, tWeight: 1.3 }
  }
])

// 表格列定义
const tableColumns = [
  { title: '名称', dataIndex: 'name', key: 'name', width: 200 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '质量', dataIndex: 'quality', key: 'quality', width: 150 },
  { title: '使用次数', dataIndex: 'usageCount', key: 'usageCount', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '操作', key: 'actions', width: 150 }
]

// 计算属性
const filteredVoices = computed(() => {
  let voices = voiceLibrary.value

  // 搜索过滤
  if (searchQuery.value) {
    voices = voices.filter(voice => 
      voice.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      voice.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }

  // 质量过滤
  if (qualityFilter.value) {
    voices = voices.filter(voice => {
      if (qualityFilter.value === 'high') return voice.quality >= 4.0
      if (qualityFilter.value === 'medium') return voice.quality >= 3.0 && voice.quality < 4.0
      if (qualityFilter.value === 'low') return voice.quality < 3.0
      return true
    })
  }

  // 类型过滤
  if (typeFilter.value) {
    voices = voices.filter(voice => voice.type === typeFilter.value)
  }

  return voices
})

const highQualityCount = computed(() => 
  voiceLibrary.value.filter(v => v.quality >= 4.0).length
)

const todayUsage = computed(() => 
  voiceLibrary.value.reduce((sum, v) => sum + v.usageCount, 0)
)

const averageQuality = computed(() => {
  const total = voiceLibrary.value.reduce((sum, v) => sum + v.quality, 0)
  return total / voiceLibrary.value.length
})

// 方法
const handleSearch = (value) => {
  searchQuery.value = value
}

const handleFilterChange = () => {
  // 过滤逻辑已在计算属性中处理
}

const selectVoice = (voice) => {
  selectedVoice.value = voice
  showDetailDrawer.value = true
}

const playVoice = (voice) => {
  message.success(`播放声音：${voice.name}`)
}

const editVoice = (voice) => {
  editingVoice.value = {
    id: voice.id,
    name: voice.name,
    description: voice.description,
    type: voice.type,
    quality: voice.quality,
    status: voice.status,
    color: voice.color,
    audioFileList: [],
    params: { ...voice.params }
  }
  showEditModal.value = true
}

const addNewVoice = () => {
  editingVoice.value = {
    id: null,
    name: '',
    description: '',
    type: '',
    quality: 3.0,
    status: 'active',
    color: '#06b6d4',
    audioFileList: [],
    params: {
      timeStep: 20,
      pWeight: 1.0,
      tWeight: 1.0
    }
  }
  showEditModal.value = true
  showUploadModal.value = false
}

const saveVoice = async () => {
  try {
    await editForm.value.validate()
    
    if (editingVoice.value.id) {
      // 编辑现有声音
      const index = voiceLibrary.value.findIndex(v => v.id === editingVoice.value.id)
      if (index !== -1) {
        voiceLibrary.value[index] = {
          ...voiceLibrary.value[index],
          ...editingVoice.value,
          audioUrl: '/audio/sample_updated.wav',
          createdAt: voiceLibrary.value[index].createdAt,
          lastUsed: new Date().toISOString().split('T')[0],
          usageCount: voiceLibrary.value[index].usageCount
        }
      }
      message.success('声音更新成功')
    } else {
      // 新增声音
      const newVoice = {
        ...editingVoice.value,
        id: voiceLibrary.value.length + 1,
        audioUrl: '/audio/sample_new.wav',
        createdAt: new Date().toISOString().split('T')[0],
        lastUsed: new Date().toISOString().split('T')[0],
        usageCount: 0
      }
      voiceLibrary.value.push(newVoice)
      message.success('声音添加成功')
    }
    
    showEditModal.value = false
  } catch (error) {
    console.error('保存失败:', error)
  }
}

const cancelEdit = () => {
  showEditModal.value = false
  editForm.value?.resetFields()
}

const handleEditAudioChange = (info) => {
  console.log('音频文件变更:', info)
}

const beforeImportUpload = (file) => {
  const isValidFormat = ['application/zip', 'application/x-rar-compressed'].includes(file.type)
  if (!isValidFormat) {
    message.error('请上传 ZIP 或 RAR 格式的压缩文件！')
    return false
  }
  
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    message.error('文件大小不能超过 50MB！')
    return false
  }
  
  return false
}

const importVoices = () => {
  message.success('批量导入功能开发中...')
  showImportModal.value = false
}

const duplicateVoice = (voice) => {
  message.success(`已复制声音：${voice.name}`)
}

const exportVoice = (voice) => {
  message.success(`导出声音：${voice.name}`)
}

const deleteVoice = (voice) => {
  message.success(`已删除声音：${voice.name}`)
}

const useVoiceForTTS = () => {
  message.success(`已选择声音用于TTS生成`)
  showDetailDrawer.value = false
}

const getStatusColor = (status) => {
  const colors = {
    'active': 'success',
    'training': 'processing',
    'inactive': 'default'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    'active': '可用',
    'training': '训练中',
    'inactive': '未激活'
  }
  return texts[status] || '未知'
}
</script>

<style scoped>
.voice-library-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding: 32px;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  border-radius: 16px;
  color: white;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-top: 4px;
}

.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.filter-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.voice-library-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 24px;
}

.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.voice-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.voice-card:hover {
  border-color: #06b6d4;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(6, 182, 212, 0.15);
}

.voice-card.selected {
  border-color: #06b6d4;
  background: #f0f9ff;
}

.voice-avatar {
  position: relative;
  margin-bottom: 16px;
}

.avatar-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  font-weight: 600;
}

.voice-status {
  position: absolute;
  bottom: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.voice-status.active .status-dot { background: #10b981; }
.voice-status.training .status-dot { background: #f59e0b; }
.voice-status.inactive .status-dot { background: #6b7280; }

.voice-info {
  margin-bottom: 16px;
}

.voice-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.voice-desc {
  margin: 0 0 12px 0;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
}

.voice-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6b7280;
}

.voice-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.table-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.voice-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.detail-avatar {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 32px;
  font-weight: 600;
}

.detail-info {
  flex: 1;
}

.detail-info h2 {
  margin: 0 0 8px 0;
  color: #2c3e50;
}

.detail-info p {
  margin: 0 0 12px 0;
  color: #6b7280;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h3 {
  margin: 0 0 16px 0;
  color: #374151;
  font-size: 16px;
  font-weight: 600;
}

.params-list, .stats-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.param-row, .stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}

.param-label, .stat-label {
  color: #6b7280;
  font-size: 14px;
}

.param-value, .stat-value {
  color: #374151;
  font-weight: 500;
  font-size: 14px;
}

.detail-actions {
  margin-top: auto;
  padding-top: 24px;
}

.voice-edit-form .ant-form-item {
  margin-bottom: 20px;
}

.edit-upload {
  border-radius: 8px !important;
  border-color: #d1d5db !important;
  background: #f9fafb !important;
}

.edit-upload .upload-content {
  padding: 24px;
  text-align: center;
}

.param-display {
  text-align: center;
  font-weight: 600;
  color: #06b6d4;
  font-size: 12px;
  margin-top: 4px;
}

.color-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.color-option {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.3s;
}

.color-option:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.color-option.selected {
  border-color: #374151;
  box-shadow: 0 0 0 2px rgba(55, 65, 81, 0.2);
}

.import-upload {
  border-radius: 12px !important;
  border-color: #d1d5db !important;
  background: #f9fafb !important;
}

.import-upload .upload-content {
  padding: 32px;
  text-align: center;
}

.import-tips {
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.import-tips ul {
  margin: 0;
  padding-left: 16px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-section {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-controls {
    flex-wrap: wrap;
  }
  
  .grid-view {
    grid-template-columns: 1fr;
  }
}
</style>