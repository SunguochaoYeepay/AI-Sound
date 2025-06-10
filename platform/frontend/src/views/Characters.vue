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
          <div class="stat-value">{{ ((averageQuality || 0) * 2).toFixed(1) }}</div>
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
                <span>{{ (voice.quality || 0).toFixed(1) }}</span>
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
            <div v-if="selectedVoice.audioUrl">
              <audio controls style="width: 100%;">
                <source :src="selectedVoice.audioUrl" type="audio/wav">
                您的浏览器不支持音频播放
              </audio>
            </div>
            <div v-else class="no-audio-message">
              <div style="text-align: center; padding: 20px; color: #6b7280;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="#d1d5db" style="margin-bottom: 12px;">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
                <p>暂无音频样本</p>
              </div>
            </div>
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

    <!-- 新增/编辑声音抽屉 -->
    <a-drawer
      v-model:open="showEditModal"
      :title="editingVoice.id ? '编辑声音' : '新增声音'"
      width="600"
      placement="right"
      :maskClosable="false"
      @close="cancelEdit"
    >
      <template #extra>
        <a-space>
          <a-button @click="cancelEdit">取消</a-button>
          <a-button type="primary" @click="saveVoice">保存</a-button>
        </a-space>
      </template>
      
      <a-form
        ref="editForm"
        :model="editingVoice"
        :rules="editRules"
        layout="vertical"
        class="voice-edit-form"
      >
        <a-form-item label="声音名称" name="name" required>
          <a-input v-model:value="editingVoice.name" placeholder="请输入声音名称" />
        </a-form-item>

        <a-form-item label="声音类型" name="type" required>
          <a-select v-model:value="editingVoice.type" placeholder="选择声音类型">
            <a-select-option value="male">男声</a-select-option>
            <a-select-option value="female">女声</a-select-option>
            <a-select-option value="child">童声</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="声音描述" name="description">
          <a-textarea 
            v-model:value="editingVoice.description" 
            placeholder="请输入声音描述信息"
            :rows="3"
          />
        </a-form-item>

        <!-- 当前文件显示样式 -->
        <div v-if="editingVoice.id && (editingVoice.referenceAudioUrl || editingVoice.latentFileUrl)" class="current-files-section">
          <a-divider>当前文件</a-divider>
          
          <!-- 当前音频文件 -->
          <div v-if="editingVoice.referenceAudioUrl" class="current-file-item">
            <div class="file-info">
              <div class="file-header">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="#10b981">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
                <span class="file-label">当前音频文件</span>
              </div>
              <div class="file-actions">
                <a-button size="small" type="text" @click="playCurrentAudio">
                  <template #icon>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
                    </svg>
                  </template>
                  播放
                </a-button>
              </div>
            </div>
          </div>
          
          <!-- 当前Latent文件 -->
          <div v-if="editingVoice.latentFileUrl" class="current-file-item">
            <div class="file-info">
              <div class="file-header">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="#10b981">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
                <span class="file-label">当前Latent文件</span>
              </div>
            </div>
          </div>
        </div>

        <a-form-item label="参考音频文件" :required="!editingVoice.id">
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
              <p style="font-size: 14px; color: #374151; margin: 0;">
                {{ editingVoice.id ? '更换音频文件（可选）' : '上传音频文件' }}
              </p>
              <p style="font-size: 12px; color: #9ca3af; margin: 4px 0 0 0;">支持 WAV, MP3, M4A 格式</p>
            </div>
          </a-upload-dragger>
        </a-form-item>

        <a-form-item label="Latent特征文件" :required="!editingVoice.id">
          <div style="margin-bottom: 8px; padding: 8px 12px; background: #fef3cd; border: 1px solid #fde68a; border-radius: 6px; color: #92400e; font-size: 13px;">
            ⚠️ MegaTTS3必需文件：需要与音频文件配对的.npy特征文件
          </div>
          <a-upload
            v-model:fileList="editingVoice.latentFileList"
            :multiple="false"
            :before-upload="beforeLatentUpload"
            @change="handleEditLatentChange"
            accept=".npy"
            :show-upload-list="false"
          >
            <a-button>
              <template #icon>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </template>
              {{ editingVoice.id ? '更换 .npy 文件（可选）' : '选择 .npy 文件' }}
            </a-button>
          </a-upload>
          
          <div v-if="editingVoice.latentFileInfo" class="file-info" style="margin-top: 12px;">
            <div class="file-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="#10b981">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
              </svg>
              <div class="file-details">
                <div class="file-name">{{ editingVoice.latentFileInfo.name }}</div>
                <div class="file-meta">{{ editingVoice.latentFileInfo.size }}</div>
              </div>
            </div>
          </div>
        </a-form-item>

        <a-divider>技术参数</a-divider>

        <a-form-item label="Time Step">
          <a-slider
            v-model:value="editingVoice.params.timeStep"
            :min="5"
            :max="100"
            :step="5"
          />
          <div class="param-display">{{ editingVoice.params.timeStep }} steps</div>
        </a-form-item>
        
        <a-form-item label="智能权重 (p_w)">
          <a-slider
            v-model:value="editingVoice.params.pWeight"
            :min="0"
            :max="2"
            :step="0.1"
          />
                        <div class="param-display">{{ (editingVoice.params.pWeight || 1.0).toFixed(1) }}</div>
        </a-form-item>
        
        <a-form-item label="相似度权重 (t_w)">
          <a-slider
            v-model:value="editingVoice.params.tWeight"
            :min="0"
            :max="2"
            :step="0.1"
          />
                        <div class="param-display">{{ (editingVoice.params.tWeight || 1.0).toFixed(1) }}</div>
        </a-form-item>

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
    </a-drawer>

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
import { ref, computed, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { charactersAPI } from '@/api'
import { API_BASE_URL } from '@/api/config'

// 响应式数据
const voiceLibrary = ref([])
const loading = ref(true)
const selectedVoice = ref(null)
const searchQuery = ref('')
const qualityFilter = ref('')
const typeFilter = ref('')
const viewMode = ref('grid')
const showDetailDrawer = ref(false)
const showEditModal = ref(false)
const showImportModal = ref(false)
const showUploadModal = ref(false)

// 编辑状态
const editingVoice = ref({})
const editForm = ref(null)

// 表单验证规则
const editRules = {
  name: [
    { required: true, message: '请输入声音名称', trigger: 'blur' },
    { min: 2, max: 20, message: '名称长度应在 2-20 字符之间', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择声音类型', trigger: 'change' }
  ]
}

// 颜色选项
const colorOptions = [
  '#06b6d4', '#f472b6', '#10b981', '#f59e0b', 
  '#ef4444', '#8b5cf6', '#06d6a0', '#fbbf24',
  '#3b82f6', '#6b7280', '#f97316', '#84cc16'
]

// 表格列定义
const tableColumns = [
  {
    title: '声音名称',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    fixed: 'left'
  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type',
    width: 80,
    filters: [
      { text: '男声', value: 'male' },
      { text: '女声', value: 'female' },
      { text: '童声', value: 'child' }
    ]
  },
  {
    title: '质量评分',
    dataIndex: 'quality',
    key: 'quality',
    width: 120,
    sorter: (a, b) => a.quality - b.quality
  },
  {
    title: '使用次数',
    dataIndex: 'usageCount',
    key: 'usageCount',
    width: 100,
    sorter: (a, b) => a.usageCount - b.usageCount
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 120
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right'
  }
]

// 从后端API加载声音库数据
const loadVoiceLibrary = async () => {
  try {
    loading.value = true
    const response = await charactersAPI.getCharacters()
    
    // axios响应的实际数据在response.data中
    const responseData = response.data
    
    if (responseData && responseData.success) {
      // 转换后端数据格式到前端格式
      voiceLibrary.value = responseData.data.map(voice => ({
        id: voice.id,
        name: voice.name,
        description: voice.description || '暂无描述',
        type: voice.type || 'female',
          quality: typeof voice.quality === 'number' ? voice.quality : 3.0,
        status: voice.status || 'active',
        color: voice.color || '#06b6d4',
          usageCount: typeof voice.usageCount === 'number' ? voice.usageCount : 0,
        audioUrl: voice.sampleAudioUrl || voice.referenceAudioUrl || '',
        referenceAudioUrl: voice.referenceAudioUrl || '',
        sampleAudioUrl: voice.sampleAudioUrl || '',
        latentFileUrl: voice.latentFileUrl || '',
        createdAt: voice.createdAt ? voice.createdAt.split('T')[0] : '',
        lastUsed: voice.lastUsed ? voice.lastUsed.split('T')[0] : '',
        params: voice.params || {
          timeStep: 20,
          pWeight: 1.0,
          tWeight: 1.0
        }
      }))
    } else {
      const errorMsg = responseData?.message || '未知错误'
      message.error('加载声音库失败：' + errorMsg)
      voiceLibrary.value = []
    }
  } catch (error) {
    console.error('加载声音库错误:', error)
    const errorMsg = error.response?.data?.message || error.message || '网络连接错误'
    message.error('加载声音库失败：' + errorMsg)
    voiceLibrary.value = []
  } finally {
    loading.value = false
  }
}

// 保存声音到后端
const saveVoiceToBackend = async (voiceData) => {
  try {
    // 调试：打印voiceData内容
    console.log('[DEBUG] 保存声音数据:', voiceData)
    
    // 构建FormData格式数据（后端期望Form格式）
    const formData = new FormData()
    formData.append('name', voiceData.name)
    formData.append('description', voiceData.description || '')
    formData.append('voice_type', voiceData.type) // 注意：后端期望voice_type字段
    formData.append('color', voiceData.color || '#06b6d4')
    formData.append('parameters', JSON.stringify(voiceData.params || {}))
    formData.append('tags', '') // 暂时为空，后续可添加标签功能
    
    // 调试：打印FormData内容
    console.log('[DEBUG] FormData内容:')
    for (let [key, value] of formData.entries()) {
      console.log(`  ${key}: ${value}`)
    }
    
    // 添加音频文件（如果有新上传的）
    if (voiceData.audioFileList && voiceData.audioFileList.length > 0) {
      const audioFile = voiceData.audioFileList[0].originFileObj
      if (audioFile) {
        formData.append('reference_audio', audioFile)
      }
    }
    
    // 添加latent文件（如果有新上传的）
    if (voiceData.latentFileList && voiceData.latentFileList.length > 0) {
      const latentFile = voiceData.latentFileList[0].originFileObj
      if (latentFile) {
        formData.append('latent_file', latentFile)
      }
    }
    
    let response
    if (voiceData.id) {
      // 更新现有声音
      response = await charactersAPI.updateCharacter(voiceData.id, formData)
    } else {
      // 创建新声音
      response = await charactersAPI.createCharacter(formData)
    }
    
    // axios响应处理
    const responseData = response.data
    if (responseData && responseData.success) {
      await loadVoiceLibrary() // 重新加载数据
      return true
    } else {
      const errorMsg = responseData?.message || '未知错误'
      message.error('保存失败：' + errorMsg)
      return false
    }
  } catch (error) {
    console.error('保存声音错误:', error)
    const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '网络连接错误'
    message.error('保存失败：' + errorMsg)
    return false
  }
}

// 删除声音
const deleteVoiceFromBackend = async (voiceId) => {
  try {
    const response = await charactersAPI.deleteCharacter(voiceId)
    // 修正：axios响应的实际数据在response.data中
    const responseData = response.data
    if (responseData && responseData.success) {
      await loadVoiceLibrary() // 重新加载数据
      message.success('删除成功')
      return true
    } else {
      const errorMsg = responseData?.message || '未知错误'
      message.error('删除失败：' + errorMsg)
      return false
    }
  } catch (error) {
    console.error('删除声音错误:', error)
    const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '网络连接错误'
    message.error('删除失败：' + errorMsg)
    return false
  }
}

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
      const quality = typeof voice.quality === 'number' ? voice.quality : 0
      if (qualityFilter.value === 'high') return quality >= 4.0
      if (qualityFilter.value === 'medium') return quality >= 3.0 && quality < 4.0
      if (qualityFilter.value === 'low') return quality < 3.0
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
  voiceLibrary.value.filter(v => typeof v.quality === 'number' && v.quality >= 4.0).length
)

const todayUsage = computed(() => 
  voiceLibrary.value.reduce((sum, v) => sum + (typeof v.usageCount === 'number' ? v.usageCount : 0), 0)
)

const averageQuality = computed(() => {
  if (voiceLibrary.value.length === 0) return 0
  const total = voiceLibrary.value.reduce((sum, v) => sum + (typeof v.quality === 'number' ? v.quality : 0), 0)
  const average = total / voiceLibrary.value.length
  return average || 0
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
  if (voice.audioUrl || voice.sampleAudioUrl || voice.referenceAudioUrl) {
    // 优先使用样本音频，然后是参考音频
    const audioUrl = voice.sampleAudioUrl || voice.audioUrl || voice.referenceAudioUrl
    const audio = new Audio(audioUrl)
    audio.play().then(() => {
      message.success(`正在播放：${voice.name}`)
    }).catch(error => {
      console.error('播放音频失败:', error)
      message.error('播放音频失败，请检查音频文件是否存在')
    })
  } else {
    message.warning('该声音暂无可播放的音频样本')
  }
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
    referenceAudioUrl: voice.audioUrl || voice.referenceAudioUrl,
    latentFileUrl: voice.latentFileUrl,
    audioFileList: [],
    latentFileList: [],
    audioFileInfo: null,
    latentFileInfo: null,
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
    latentFileList: [],
    audioFileInfo: null,
    latentFileInfo: null,
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
    
    // 调用后端API保存
    const success = await saveVoiceToBackend(editingVoice.value)
    
    if (success) {
      showEditModal.value = false
      message.success(editingVoice.value.id ? '声音更新成功' : '声音创建成功')
      // 数据已在saveVoiceToBackend中重新加载
    }
  } catch (error) {
    console.error('保存声音失败:', error)
  }
}

const cancelEdit = () => {
  showEditModal.value = false
  editForm.value?.resetFields()
}

const handleEditAudioChange = (info) => {
  console.log('音频文件变更:', info)
}

const beforeAudioUpload = (file) => {
  const isValidFormat = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/m4a'].includes(file.type)
  if (!isValidFormat) {
    message.error('请上传 WAV, MP3, 或 M4A 格式的音频文件！')
    return false
  }
  
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    message.error('音频文件大小不能超过 50MB！')
    return false
  }
  
  return false // 阻止自动上传
}

const beforeLatentUpload = (file) => {
  const isNpy = file.name.endsWith('.npy')
  if (!isNpy) {
    message.error('请上传 .npy 格式的文件！')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('Latent文件大小不能超过 10MB！')
    return false
  }
  
  return false // 阻止自动上传
}

const handleEditLatentChange = (info) => {
  if (info.fileList.length > 0) {
    const file = info.fileList[0].originFileObj
    editingVoice.value.latentFileInfo = {
      name: file.name,
      size: formatFileSize(file.size)
    }
  } else {
    editingVoice.value.latentFileInfo = null
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
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

const deleteVoice = async (voice) => {
  try {
    const success = await deleteVoiceFromBackend(voice.id)
    if (success && selectedVoice.value?.id === voice.id) {
      showDetailDrawer.value = false
      selectedVoice.value = null
    }
  } catch (error) {
    console.error('删除声音失败:', error)
  }
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

// 添加播放当前音频的功能
const playCurrentAudio = () => {
  if (editingVoice.value.referenceAudioUrl) {
    const audio = new Audio(editingVoice.value.referenceAudioUrl)
    audio.play().catch(error => {
      console.error('播放音频失败:', error)
      message.error('播放音频失败')
    })
  } else {
    message.warning('没有可播放的音频文件')
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadVoiceLibrary()
})
</script>

<style scoped>
.voice-library-container {
  
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

.voice-edit-form {
  padding-bottom: 80px;
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
  color: #6b7280;
  font-size: 12px;
  margin-top: 4px;
}

.color-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.color-option {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.3s;
}

.color-option:hover,
.color-option.selected {
  border-color: #374151;
  transform: scale(1.1);
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f0f9ff;
  border-radius: 6px;
  border: 1px solid #e0f2fe;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.file-meta {
  font-size: 12px;
  color: #6b7280;
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

/* 当前文件显示样式 */
.current-files-section {
  margin-bottom: 24px;
}

.current-file-item {
  margin-bottom: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.file-actions {
  display: flex;
  gap: 8px;
}

/* 音频样本样式 */
.audio-sample {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
}

.audio-sample audio {
  border-radius: 4px;
  background: white;
}

.no-audio-message {
  background: #f9fafb;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
}

/* 响应式设计 */
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
  
  .ant-layout-sider {
    position: fixed !important;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 1000;
  }
  
  .ant-layout-content {
    margin-left: 0 !important;
  }
  
  .logo-text h3 {
    font-size: 14px !important;
  }
}
</style>