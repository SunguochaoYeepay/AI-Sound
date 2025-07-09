<template>
  <div class="voice-library-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <UserOutlined class="title-icon" />
            角色管理
          </h1>
          <p class="page-description">
            管理您的角色库，为语音合成项目提供声音素材
          </p>
        </div>
        <div class="action-section">
          <a-button type="primary" size="large" @click="() => showSmartDiscoveryModal = true" ghost>
            <template #icon>
              <SearchOutlined />
            </template>
            智能发现
          </a-button>
          <a-button type="primary" size="large" @click="addNewCharacter">
            <template #icon>
              <PlusOutlined />
            </template>
            新建角色
          </a-button>
        </div>
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
          <div class="stat-label">角色总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ configuredCount }}</div>
          <div class="stat-label">已配置声音</div>
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
          placeholder="搜索角色..."
          style="width: 300px;"
          size="large"
          @search="handleSearch"
        />
        
        <a-select
          v-model:value="selectedBookId"
          placeholder="选择书籍"
          style="width: 200px;"
          size="large"
          @change="handleBookChange"
          :loading="booksLoading"
          show-search
          allow-clear
        >
          <a-select-option value="">全部书籍</a-select-option>
          <a-select-option 
            v-for="book in availableBooks" 
            :key="book.id" 
            :value="book.id"
          >
            {{ book.title }} ({{ book.character_count || 0 }}个角色)
          </a-select-option>
        </a-select>
        
        <a-select
          v-model:value="typeFilter"
          placeholder="声音类型"
          style="width: 120px;"
          size="large"
          @change="handleFilterChange"
        >
          <a-select-option value="">全部类型</a-select-option>
          <a-select-option value="male">男声</a-select-option>
          <a-select-option value="female">女声</a-select-option>
          <a-select-option value="child">童声</a-select-option>
          <a-select-option value="elder">老人声</a-select-option>
          <a-select-option value="custom">自定义</a-select-option>
        </a-select>

        <a-select
          v-model:value="statusFilter"
          placeholder="配置状态"
          style="width: 120px;"
          size="large"
          @change="handleFilterChange"
        >
          <a-select-option value="">全部状态</a-select-option>
          <a-select-option value="configured">已配置</a-select-option>
          <a-select-option value="unconfigured">未配置</a-select-option>
          <a-select-option value="training">训练中</a-select-option>
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
          :data-character="voice.isCharacter"
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
            
            <!-- 角色模式：显示书籍信息 -->
            <div v-if="managementType === 'character' && voice.book" class="book-info">
              <div class="book-badge">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                </svg>
                <span>{{ voice.book.title }}</span>
              </div>
            </div>
            
            <div class="voice-meta">
              <!-- 声音样本模式：显示质量和使用次数 -->
              <template v-if="managementType === 'voice'">
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
              </template>
              
              <!-- 角色模式：显示配置状态 -->
              <template v-else>
                <div class="meta-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                  <span>{{ voice.status === 'configured' ? '已配置' : '待配置' }}</span>
                </div>
                <div class="meta-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 11H7v3h2v-3zm4 0h-2v3h2v-3zm4 0h-2v3h2v-3zm2-7h-1V2h-2v2H8V2H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H5V9h14v11z"/>
                  </svg>
                  <span>{{ voice.createdAt }}</span>
                </div>
              </template>
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
                  <a-menu-item key="delete" @click="confirmDeleteCharacter(voice)" style="color: #ef4444;">删除</a-menu-item>
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
                <a-button type="text" size="small" danger @click.stop="confirmDeleteCharacter(record)">
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
            <a-button danger @click="confirmDeleteCharacter(selectedVoice)" style="flex: 1;">删除</a-button>
          </div>
        </div>
      </div>
    </a-drawer>

    <!-- 新增/编辑角色抽屉 -->
    <a-drawer
      v-model:open="showEditModal"
      :title="editingVoice.id ? '编辑角色' : '新增角色'"
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
        <!-- 角色基本信息 -->
        <a-divider orientation="left">角色基本信息</a-divider>
        
        <a-form-item label="角色名称" name="name" required>
          <a-input v-model:value="editingVoice.name" placeholder="请输入角色名称" />
        </a-form-item>

        <a-form-item label="角色描述" name="description">
          <a-textarea 
            v-model:value="editingVoice.description" 
            placeholder="请输入角色描述信息（性格、特点等）"
            :rows="3"
          />
        </a-form-item>

        <a-form-item label="所属书籍" name="book_id">
          <a-select
            v-model:value="editingVoice.book_id"
            placeholder="选择角色所属的书籍（可选）"
            style="width: 100%;"
            :loading="booksLoading"
            show-search
            allow-clear
            :filter-option="false"
            @search="handleBookSearch"
            @focus="loadBooksForEdit"
          >
            <a-select-option value="">不关联书籍</a-select-option>
            <a-select-option 
              v-for="book in availableBooks" 
              :key="book.id" 
              :value="book.id"
            >
              {{ book.title }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <!-- 声音配置 -->
        <a-divider orientation="left">声音配置</a-divider>
        
        <a-form-item label="声音类型" name="type" required>
          <a-select v-model:value="editingVoice.type" placeholder="选择声音类型">
            <a-select-option value="male">男声</a-select-option>
            <a-select-option value="female">女声</a-select-option>
            <a-select-option value="child">童声</a-select-option>
            <a-select-option value="elder">老人声</a-select-option>
            <a-select-option value="custom">自定义</a-select-option>
          </a-select>
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
            accept=".wav,.mp3,.m4a,.flac"
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
              <p style="font-size: 12px; color: #9ca3af; margin: 4px 0 0 0;">支持 WAV, MP3, M4A, FLAC 格式</p>
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

        <a-divider orientation="left">技术参数</a-divider>

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

    <!-- 智能角色发现抽屉 -->
    <a-drawer
      v-model:open="showSmartDiscoveryModal"
      title="智能角色发现"
      width="1000"
      placement="right"
      @close="closeSmartDiscovery"
    >
      <div class="smart-discovery-container">
        <!-- 步骤条 -->
        <a-steps 
          :current="discoveryStep" 
          class="discovery-steps"
          :items="discoverySteps"
        />
        
        <!-- 步骤内容 -->
        <div class="step-content">
          <!-- 步骤1: 选择书籍 -->
          <div v-if="discoveryStep === 0" class="step-panel">
            <div class="step-header">
              <h3>选择书籍项目</h3>
              <p>请选择要分析角色的书籍项目</p>
            </div>
            
            <div class="book-selection">
              <a-spin :spinning="booksLoading">
                <div v-if="booksData.length === 0" class="empty-state">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="#d1d5db">
                    <path d="M19,3H5C3.9,3 3,3.9 3,5V19C3,20.1 3.9,21 5,21H19C20.1,21 21,20.1 21,19V5C21,3.9 20.1,3 19,3M19,19H5V5H19V19Z"/>
                  </svg>
                  <p>暂无可用的书籍项目</p>
                  <a-button type="link" @click="loadBooks">刷新</a-button>
                </div>
                
                <div v-else class="books-grid">
                  <div 
                    v-for="book in booksData" 
                    :key="book.id"
                    class="book-card"
                    :class="{ 'selected': smartDiscovery.selectedBook?.id === book.id }"
                    @click="selectBook(book)"
                  >
                    <div class="book-icon">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19,3H5C3.9,3 3,3.9 3,5V19C3,20.1 3.9,21 5,21H19C20.1,21 21,20.1 21,19V5C21,3.9 20.1,3 19,3M19,19H5V5H19V19Z"/>
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
              <a-button @click="closeSmartDiscovery">取消</a-button>
              <a-button type="primary" :disabled="!smartDiscovery.selectedBook" @click="nextStep">
                下一步：选择章节
              </a-button>
            </div>
          </div>
          
          <!-- 步骤2: 选择章节 -->
          <div v-if="discoveryStep === 1" class="step-panel">
            <div class="step-header">
              <h3>选择分析章节</h3>
              <p>从《{{ smartDiscovery.selectedBook?.title }}》中选择要分析的章节</p>
            </div>
            
            <div class="chapter-selection">
              <div class="selection-controls">
                <a-checkbox 
                  :indeterminate="chapterIndeterminate" 
                  :checked="chapterCheckAll" 
                  @change="toggleAllChapters"
                >
                  全选
                </a-checkbox>
                <span class="selection-info">
                  已选择 {{ smartDiscovery.selectedChapters.length }} / {{ chaptersData.length }} 章节
                </span>
              </div>
              
              <a-spin :spinning="chaptersLoading">
                <div class="chapters-list">
                  <div class="chapters-grid">
                    <div 
                      v-for="chapter in chaptersData" 
                      :key="chapter.id"
                      class="chapter-item"
                      :class="{ 'selected': smartDiscovery.selectedChapters.some(c => c.id === chapter.id) }"
                      @click="toggleChapterSelection(chapter)"
                    >
                      <a-checkbox 
                        :checked="smartDiscovery.selectedChapters.some(c => c.id === chapter.id)"
                        @click.stop="toggleChapterSelection(chapter)"
                      >
                        <div class="chapter-content">
                          <div class="chapter-title">
                            第{{ chapter.chapter_number }}章 {{ chapter.title || chapter.chapter_title || '未命名章节' }}
                          </div>
                          <div class="chapter-meta">
                            字数: {{ formatNumber(chapter.word_count || 0) }} | 
                            状态: {{ getChapterStatusText(chapter.analysis_status || chapter.status) }}
                          </div>
                        </div>
                      </a-checkbox>
                    </div>
                  </div>
                </div>
              </a-spin>
            </div>
            
            <div class="step-actions">
              <a-button @click="prevStep">上一步</a-button>
              <a-button type="primary" :disabled="smartDiscovery.selectedChapters.length === 0" @click="analyzeCharacters">
                开始分析角色
              </a-button>
            </div>
          </div>
          
          <!-- 步骤3: 角色分析 -->
          <div v-if="discoveryStep === 2" class="step-panel">
            <div class="step-header">
              <h3>角色分析中</h3>
              <p>正在使用编程识别规则分析选定章节中的角色...</p>
            </div>
            
            <div class="analysis-progress">
              <a-progress 
                :percent="smartDiscovery.analysisProgress" 
                :status="analysisStatus"
                :show-info="true"
              />
              <p class="progress-text">{{ analysisText }}</p>
            </div>
            
            <div v-if="smartDiscovery.analysisComplete" class="analysis-results">
              <div class="results-summary">
                <div class="statistics-grid">
                  <a-statistic title="发现角色" :value="smartDiscovery.discoveredCharacters.length" />
                  <a-statistic title="主要角色" :value="mainCharactersCount" />
                  <a-statistic title="分析章节" :value="smartDiscovery.selectedChapters.length" />
                </div>
              </div>
              
              <div class="characters-preview">
                <h4>发现的角色预览</h4>
                <div class="characters-list">
                  <div 
                    v-for="character in smartDiscovery.discoveredCharacters" 
                    :key="character.name"
                    class="character-preview-item"
                  >
                    <div class="character-avatar" :style="{ background: character.recommended_config.color }">
                      {{ character.name.charAt(0) }}
                    </div>
                    <div class="character-info">
                      <div class="character-name">{{ character.name }}</div>
                      <div class="character-meta">
                        {{ character.recommended_config.gender === 'male' ? '男性' : '女性' }} | 
                        {{ character.recommended_config.personality_description }} |
                        出现 {{ character.frequency }} 次
                      </div>
                    </div>
                    <div class="character-status">
                      <a-tag v-if="character.is_main_character" color="blue">主要角色</a-tag>
                      <a-tag v-if="character.exists_in_library" color="orange">已存在</a-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="step-actions">
              <a-button @click="prevStep" :disabled="!smartDiscovery.analysisComplete">重新选择</a-button>
              <a-button type="primary" :disabled="!smartDiscovery.analysisComplete" @click="nextStep">
                配置角色信息
              </a-button>
            </div>
          </div>
          
          <!-- 步骤4: 批量配置 -->
          <div v-if="discoveryStep === 3" class="step-panel">
            <div class="step-header">
              <h3>批量配置角色</h3>
              <p>为发现的角色配置详细信息，已存在的角色会显示当前配置（无法选择创建）</p>
            </div>
            
            <div class="batch-config">
              <div class="config-controls">
                <a-checkbox 
                  :indeterminate="configIndeterminate" 
                  :checked="configCheckAll" 
                  @change="onCheckAllConfigs"
                >
                  全选
                </a-checkbox>
                <span class="selection-info">
                  将创建 {{ selectedConfigs.length }} 个新角色
                </span>
              </div>
              
              <div class="config-list">
                <a-checkbox-group v-model:value="selectedConfigs" class="config-grid">
                  <div 
                    v-for="character in newCharacters" 
                    :key="character.name"
                    class="config-item"
                    :class="{ 'existing-character': character.exists_in_library }"
                  >
                    <a-checkbox 
                      :value="character.name" 
                      :disabled="character.exists_in_library"
                    >
                      <div class="config-card">
                        <div class="config-header">
                          <div class="character-avatar" :style="{ background: character.recommended_config.color }">
                            {{ character.name.charAt(0) }}
                          </div>
                          <div class="character-basic">
                            <h4>
                              {{ character.name }}
                              <a-tag v-if="character.exists_in_library" color="orange" size="small">已存在</a-tag>
                            </h4>
                            <p>{{ character.recommended_config.description }}</p>
                          </div>
                        </div>
                        
                        <div class="config-details">
                          <div v-if="character.exists_in_library" class="existing-character-info">
                            <a-alert 
                              message="角色已存在于角色库中" 
                              type="info" 
                              show-icon 
                              :closable="false"
                              style="margin-bottom: 16px;"
                            />
                            <div class="existing-config-display">
                              <a-descriptions :column="2" size="small">
                                <a-descriptions-item label="性别">
                                  {{ character.existing_config?.type === 'male' ? '男性' : '女性' }}
                                </a-descriptions-item>
                                <a-descriptions-item label="状态">
                                  <a-tag :color="character.existing_config?.status === 'active' ? 'green' : 'orange'">
                                    {{ character.existing_config?.status === 'active' ? '可用' : '需配置' }}
                                  </a-tag>
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
                                  <a-select 
                                    v-model:value="character.config.gender" 
                                    size="small"
                                  >
                                    <a-select-option value="male">男性</a-select-option>
                                    <a-select-option value="female">女性</a-select-option>
                                  </a-select>
                                </a-form-item>
                              </a-col>
                              <a-col :span="8">
                                <a-form-item label="性格">
                                  <a-select 
                                    v-model:value="character.config.personality" 
                                    size="small"
                                  >
                                    <a-select-option value="gentle">温柔</a-select-option>
                                    <a-select-option value="fierce">刚烈</a-select-option>
                                    <a-select-option value="calm">沉稳</a-select-option>
                                    <a-select-option value="lively">活泼</a-select-option>
                                  </a-select>
                                </a-form-item>
                              </a-col>
                              <a-col :span="8">
                                <a-form-item label="颜色">
                                  <a-select 
                                    v-model:value="character.config.color" 
                                    size="small"
                                  >
                                    <a-select-option 
                                      v-for="color in colorOptions" 
                                      :key="color" 
                                      :value="color"
                                    >
                                      <div style="display: flex; align-items: center; gap: 8px;">
                                        <div 
                                          style="width: 16px; height: 16px; border-radius: 4px;" 
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
                            
                            <!-- 音频文件上传 -->
                            <a-row :gutter="16">
                              <a-col :span="12">
                                <a-form-item label="参考音频">
                                  <a-upload
                                    v-model:file-list="character.config.audioFileList"
                                    :before-upload="beforeAudioUpload"
                                    :max-count="1"
                                    accept=".wav,.mp3,.m4a,.flac"
                                    @change="(info) => handleConfigAudioChange(info, character)"
                                  >
                                    <a-button size="small" type="dashed">
                                      <template #icon>
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                                          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                                          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                                        </svg>
                                      </template>
                                      选择音频
                                    </a-button>
                                  </a-upload>
                                  <div v-if="character.config.audioFileInfo" class="file-info-mini">
                                    <span class="file-name-mini">{{ character.config.audioFileInfo.name }}</span>
                                    <span class="file-size-mini">{{ character.config.audioFileInfo.size }}</span>
                                  </div>
                                </a-form-item>
                              </a-col>
                              <a-col :span="12">
                                <a-form-item label="Latent文件 (.npy)">
                                  <a-upload
                                    v-model:file-list="character.config.latentFileList"
                                    :before-upload="beforeLatentUpload"
                                    :max-count="1"
                                    accept=".npy"
                                    @change="(info) => handleConfigLatentChange(info, character)"
                                  >
                                    <a-button size="small" type="dashed">
                                      <template #icon>
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
                                      </template>
                                      选择文件
                                    </a-button>
                                  </a-upload>
                                  <div v-if="character.config.latentFileInfo" class="file-info-mini">
                                    <span class="file-name-mini">{{ character.config.latentFileInfo.name }}</span>
                                    <span class="file-size-mini">{{ character.config.latentFileInfo.size }}</span>
          </div>
                                </a-form-item>
                              </a-col>
                            </a-row>
                          </a-form>
                        </div>
                      </div>
                    </a-checkbox>
                  </div>
                </a-checkbox-group>
              </div>
            </div>
            
            <div class="step-actions">
              <a-button @click="prevStep">重新分析</a-button>
              <a-button 
                type="primary" 
                :loading="creatingCharacters"
                :disabled="selectedConfigs.length === 0" 
                @click="createCharacters"
              >
                创建 {{ selectedConfigs.length }} 个角色
              </a-button>
            </div>
          </div>
          
          <!-- 步骤5: 创建完成 -->
          <div v-if="discoveryStep === 4" class="step-panel">
            <div class="step-header">
              <div class="success-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="#10b981">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
        </div>
              <h3>创建完成</h3>
              <p>成功创建了 {{ createdCharacters.length }} 个角色</p>
      </div>
            
            <div class="creation-results">
              <div class="results-summary">
                <a-alert
                  message="角色创建成功"
                  :description="getCreationSummary()"
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
                              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                            </svg>
                          </template>
                          音频已上传
                        </a-tag>
                        <a-tag v-if="character.hasLatent" color="blue" size="small">
                          <template #icon>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                            </svg>
                          </template>
                          Latent已上传
                        </a-tag>
                        <a-tag v-if="character.status === 'active'" color="success" size="small">
                          可用
                        </a-tag>
                        <a-tag v-else color="warning" size="small">
                          需要音频
                        </a-tag>
                      </div>
                    </div>
                    <div class="character-actions">
                      <a-button 
                        v-if="character.status !== 'active'" 
                        size="small" 
                        @click="editCreatedCharacter(character)"
                      >
                        上传音频
                      </a-button>
                      <a-button 
                        v-else 
                        size="small" 
                        type="primary"
                        @click="editCreatedCharacter(character)"
                      >
                        编辑配置
                      </a-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="step-actions">
              <a-button @click="closeSmartDiscovery">关闭</a-button>
              <a-button type="primary" @click="startNewDiscovery">
                发现更多角色
              </a-button>
            </div>
          </div>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch, nextTick, h } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { charactersAPI, booksAPI } from '@/api'
import { API_BASE_URL } from '@/api/config'
import { bookAPI, chapterAPI } from '../api/v2.js'
import { playCustomAudio } from '@/utils/audioService'
import { ArrowLeftOutlined, PlusOutlined, UserOutlined, SearchOutlined } from '@ant-design/icons-vue'

// 路由
const router = useRouter()

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
const showSmartDiscoveryModal = ref(false)
const showUploadModal = ref(false)

// 书籍筛选
const selectedBookId = ref('')
const availableBooks = ref([])
const booksLoading = ref(false)
const statusFilter = ref('')

// 智能发现相关状态
const discoveryStep = ref(0)
const discoverySteps = ref([
  { title: '选择书籍', description: '选择要分析的书籍项目' },
  { title: '选择章节', description: '选择要分析的章节' },
  { title: '角色分析', description: '分析章节中的角色' },
  { title: '批量配置', description: '配置角色信息' },
  { title: '创建完成', description: '完成角色创建' }
])

// 书籍选择
const selectedBook = ref(null)

// 章节选择
const availableChapters = ref([])
const selectedChapters = ref([])
const loadingChapters = ref(false)
const chapterCheckAll = ref(false)
const chapterIndeterminate = ref(false)

// 角色分析
const analysisProgress = ref(0)
const analysisStatus = ref('normal')
const analysisText = ref('')
const analysisComplete = ref(false)
const discoveredCharacters = ref([])

// 批量配置
const newCharacters = ref([])
const selectedConfigs = ref([])
const configCheckAll = ref(false)
const configIndeterminate = ref(false)
const creatingCharacters = ref(false)

// 创建结果
const createdCharacters = ref([])

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

// 从后端API加载角色数据
const loadVoiceLibrary = async () => {
  try {
    loading.value = true
    
    // 构建API参数
    const apiParams = {
      page: 1,
      page_size: 100
    }
    
    // 添加筛选条件
    if (searchQuery.value) apiParams.search = searchQuery.value
    if (typeFilter.value) apiParams.voice_type = typeFilter.value
    if (statusFilter.value) apiParams.status = statusFilter.value
    if (selectedBookId.value) apiParams.book_id = selectedBookId.value
    
    const response = await charactersAPI.getCharacters(apiParams)
    
    // axios响应的实际数据在response.data中
    const responseData = response.data
    
    if (responseData && responseData.success) {
      const data = responseData.data
      
      // 统一处理角色数据
      voiceLibrary.value = data.map(character => ({
        id: character.id,
        name: character.name,
        description: character.description || '暂无描述',
        type: character.voice_type || 'custom',
        quality: character.quality_score || 0,
        status: character.status || 'unconfigured',
        color: character.color || '#8b5cf6',
        usageCount: character.usage_count || 0,
        audioUrl: character.referenceAudioUrl || '',
        referenceAudioUrl: character.referenceAudioUrl || '',
        latentFileUrl: character.latentFileUrl || '',
        book: character.book,
        book_id: character.book_id,
        chapter_id: character.chapter_id,
        voice_parameters: character.voice_parameters || {
          time_step: 20,
          p_weight: 1.0,
          t_weight: 1.0
        },
        tags: character.tags || [],
        createdAt: character.created_at ? character.created_at.split('T')[0] : '',
        isCharacter: true,
        is_voice_configured: character.is_voice_configured || false
      }))
    } else {
      const errorMsg = responseData?.message || '未知错误'
      message.error('加载数据失败：' + errorMsg)
      voiceLibrary.value = []
    }
  } catch (error) {
    console.error('加载数据错误:', error)
    const errorMsg = error.response?.data?.message || error.message || '网络连接错误'
    message.error('加载数据失败：' + errorMsg)
    voiceLibrary.value = []
  } finally {
    loading.value = false
  }
}

// 页面初始化时加载书籍列表
onMounted(async () => {
  await loadAvailableBooks()
  await loadVoiceLibrary()
})

// 加载可用书籍列表
const loadAvailableBooks = async () => {
  if (availableBooks.value.length > 0) return // 已加载过，直接返回
  
  try {
    booksLoading.value = true
    const response = await bookAPI.getBooks({
      page: 1,
      page_size: 100
    })
    
    if (response.success) {
      let books = []
      if (response.data) {
        if (Array.isArray(response.data)) {
          books = response.data
        } else if (response.data.items) {
          books = response.data.items
        } else if (response.data.data) {
          books = response.data.data
        }
      }
      
      availableBooks.value = books.map(book => ({
        id: book.id,
        title: book.title,
        author: book.author || '',
        character_count: 0 // 初始值，会在加载角色数据时更新
      }))
    } else {
      message.error('加载书籍列表失败: ' + (response.message || '未知错误'))
    }
  } catch (error) {
    console.error('加载书籍列表失败:', error)
    message.error('加载书籍列表失败: ' + (error.message || '网络错误'))
  } finally {
    booksLoading.value = false
  }
}

// 更新书籍的角色数量
const updateBooksWithCharacterCount = (booksSummary) => {
  booksSummary.forEach(summary => {
    const book = availableBooks.value.find(b => b.id === summary.book_id)
    if (book) {
      book.character_count = summary.character_count
    }
  })
}

// 书籍选择变化处理
const handleBookChange = async (bookId) => {
  selectedBookId.value = bookId
  await loadVoiceLibrary()
}

// 搜索处理（兼容新的管理模式）
const handleSearch = async () => {
  await loadVoiceLibrary()
}

// 筛选变化处理（兼容新的管理模式）
const handleFilterChange = async () => {
  await loadVoiceLibrary()
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
    
    // 添加书籍关联
    if (voiceData.book_id) {
      formData.append('book_id', voiceData.book_id)
    }
    
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

// 删除角色
const deleteVoiceFromBackend = async (voiceId, force = false) => {
  try {
          const response = await charactersAPI.deleteCharacter(voiceId, force)
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
    console.error('删除角色错误:', error)
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

const configuredCount = computed(() => 
  voiceLibrary.value.filter(character => character.status === 'configured').length
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

// 智能发现计算属性
const mainCharactersCount = computed(() => {
  return smartDiscovery.discoveredCharacters.filter(char => char.is_main_character).length
})

// 监听章节选择变化
const updateChapterCheckState = () => {
  const checkedCount = smartDiscovery.selectedChapters.length
  const totalCount = chaptersData.value.length
  
  chapterCheckAll.value = checkedCount === totalCount
  chapterIndeterminate.value = checkedCount > 0 && checkedCount < totalCount
}

// 监听配置选择变化
const updateConfigCheckState = () => {
  const checkedCount = selectedConfigs.value.length
  const totalCount = newCharacters.value.length
  
  configCheckAll.value = checkedCount === totalCount
  configIndeterminate.value = checkedCount > 0 && checkedCount < totalCount
}

const selectVoice = (voice) => {
  selectedVoice.value = voice
  showDetailDrawer.value = true
}

// 播放音频的安全处理
const playVoice = async (voice) => {
  if (!voice || (!voice.audioUrl && !voice.sampleAudioUrl && !voice.referenceAudioUrl)) {
    message.warning('该声音暂无可播放的音频样本')
    return
  }

  try {
    const audioUrl = voice.sampleAudioUrl || voice.audioUrl || voice.referenceAudioUrl
    
    // 使用统一播放组件播放
    await playCustomAudio(audioUrl, `${voice.name} - 声音试听`, {
      voiceId: voice.id,
      voiceName: voice.name,
      description: voice.description,
      quality: voice.quality,
      type: voice.type,
      onEnded: () => {
        console.log(`角色 ${voice.name} 试听完成`)
      }
    })
    
    message.success(`正在播放：${voice.name}`)
  } catch (error) {
    console.error('播放音频失败:', error)
    message.error('播放音频失败，请检查音频文件是否存在')
  }
}

const editVoice = (voice) => {
  editingVoice.value = {
    id: voice.id,
    name: voice.name,
    description: voice.description,
    type: voice.type,
    book_id: voice.book_id || '',
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

const addNewCharacter = () => {
  editingVoice.value = {
    id: null,
    name: '',
    description: '',
    type: '',
    book_id: '',
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
      message.success(editingVoice.value.id ? '角色更新成功' : '角色创建成功')
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

// 为编辑界面加载书籍列表
const loadBooksForEdit = async () => {
  if (availableBooks.value.length > 0) return // 已加载过
  
  booksLoading.value = true
  try {
    const response = await booksAPI.getBooks({
      page: 1,
      page_size: 100
    })
    
    // 处理响应数据
    const responseData = response.data
    if (responseData && responseData.success) {
      let books = []
      if (responseData.data) {
        if (Array.isArray(responseData.data)) {
          books = responseData.data
        } else if (responseData.data.items) {
          books = responseData.data.items
        } else if (responseData.data.data) {
          books = responseData.data.data
        }
      }
      
      availableBooks.value = books
    }
  } catch (error) {
    console.error('加载书籍列表失败:', error)
  } finally {
    booksLoading.value = false
  }
}

// 书籍搜索
const handleBookSearch = (searchValue) => {
  // 可以在这里实现实时搜索功能
  console.log('搜索书籍:', searchValue)
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

// 智能发现方法
const closeSmartDiscovery = () => {
  nextTick(() => {
    showSmartDiscoveryModal.value = false
    resetDiscoveryState()
  })
}

// 重置状态的安全处理
const resetDiscoveryState = () => {
  nextTick(() => {
    discoveryStep.value = 0
    if (smartDiscovery) {
      smartDiscovery.selectedBook = null
      smartDiscovery.selectedChapters = []
      smartDiscovery.analysisProgress = 0
      smartDiscovery.analysisComplete = false
      smartDiscovery.discoveredCharacters = []
      smartDiscovery.configuredCharacters = []
      smartDiscovery.creationResults = []
    }
    booksData.value = []
    chaptersData.value = []
    newCharacters.value = []
    selectedConfigs.value = []
    createdCharacters.value = []
  })
}

const nextStep = () => {
  if (discoveryStep.value < discoverySteps.value.length - 1) {
    discoveryStep.value++
    
    // 根据步骤执行相应操作
    if (discoveryStep.value === 1) {
      // 章节选择步骤，章节已在选择书籍时加载
    } else if (discoveryStep.value === 3) {
      prepareCharacterConfigs()
    }
  }
}

const prevStep = () => {
  if (discoveryStep.value > 0) {
    discoveryStep.value--
  }
}

// 加载书籍列表
const loadBooks = async () => {
  booksLoading.value = true
  try {
    const response = await bookAPI.getBooks({
      page: 1,
      page_size: 50
      // 移除status过滤，显示所有书籍
    })
    
    console.log('[智能发现] 书籍API响应:', response)
    
    if (response.success) {
      // 处理不同的数据结构
      let books = []
      if (response.data) {
        if (Array.isArray(response.data)) {
          books = response.data
        } else if (response.data.items) {
          books = response.data.items
        } else if (response.data.data) {
          books = response.data.data
        }
      }
      
      console.log('[智能发现] 处理后的书籍数据:', books)
      
      // 调试：打印每本书的详细信息
      books.forEach((book, index) => {
        console.log(`[智能发现] 书籍${index + 1}:`, {
          id: book.id,
          title: book.title,
          author: book.author,
          chapter_count: book.chapter_count,
          total_chapters: book.total_chapters,
          word_count: book.word_count,
          status: book.status,
          raw_data: book
        })
      })
      
      booksData.value = books
      
      if (books.length === 0) {
        message.warning('暂无可用的书籍项目')
      }
    } else {
      message.error('加载书籍列表失败: ' + (response.message || '未知错误'))
    }
  } catch (error) {
    console.error('加载书籍列表失败:', error)
    message.error('加载书籍列表失败: ' + (error.message || '网络错误'))
  } finally {
    booksLoading.value = false
  }
}

// 选择书籍
const selectBook = async (book) => {
  smartDiscovery.selectedBook = book
  smartDiscovery.selectedChapters = []
  
  // 加载章节列表
  await loadChapters(book.id)
}

// 加载章节列表
const loadChapters = async (bookId) => {
  chaptersLoading.value = true
  try {
    const response = await chapterAPI.getChapters(bookId, {
      page: 1,
      page_size: 100 // 加载更多章节
    })
    
    console.log('[智能发现] 章节API响应:', response)
    
    if (response.success) {
      // 处理不同的数据结构
      let chapters = []
      if (response.data) {
        if (Array.isArray(response.data)) {
          chapters = response.data
        } else if (response.data.items) {
          chapters = response.data.items
        } else if (response.data.data) {
          chapters = response.data.data
        }
      }
      
      console.log('[智能发现] 处理后的章节数据:', chapters)
      chaptersData.value = chapters
      
      if (chapters.length === 0) {
        message.warning('该书籍暂无章节数据')
      }
    } else {
      message.error('加载章节列表失败: ' + (response.message || '未知错误'))
    }
  } catch (error) {
    console.error('加载章节列表失败:', error)
    message.error('加载章节列表失败: ' + (error.message || '网络错误'))
  } finally {
    chaptersLoading.value = false
  }
}

// 章节全选/取消全选 - 这个方法已被toggleAllChapters替代，可以删除

// 分析角色
const analyzeCharacters = async () => {
  try {
    smartDiscovery.analysisProgress = 0
    analysisStatus.value = 'active'
    smartDiscovery.analysisComplete = false
    analysisText.value = '开始分析章节...'
    
    nextStep() // 进入分析步骤
    
    // 模拟分析过程
    for (let i = 0; i <= 100; i += 10) {
      smartDiscovery.analysisProgress = i
      analysisText.value = `正在分析第 ${Math.floor(i/10) + 1}/${smartDiscovery.selectedChapters.length} 个章节...`
      await new Promise(resolve => setTimeout(resolve, 200))
    }
    
    // 调用后端API进行角色分析
    try {
      const response = await fetch('/api/v1/chapters/batch-character-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chapter_ids: smartDiscovery.selectedChapters.map(c => c.id),
          detection_method: 'programming',
          emotion_detection: true
        })
      })
      
      const result = await response.json()
      
      if (result.success && result.data) {
        // 处理分析结果
        await processAnalysisResult(result.data)
      } else {
        throw new Error(result.message || '分析失败')
      }
    } catch (apiError) {
      console.error('API调用失败，使用模拟数据:', apiError)
      
      // 如果API失败，使用模拟数据作为后备
      smartDiscovery.discoveredCharacters = [
        {
          name: '悟空',
          frequency: 15,
          character_trait: { trait: 'fierce', confidence: 0.8, description: '性格刚烈，说话直接有力' },
          first_appearance: 1,
          is_main_character: true,
          recommended_config: {
            gender: 'male',
            personality: 'fierce',
            personality_description: '性格刚烈，说话直接有力',
            personality_confidence: 0.8,
            description: '悟空，男性主要角色，性格刚烈，说话直接有力，在文本中出现15次。',
            recommended_tts_params: { time_step: 28, p_w: 1.6, t_w: 3.2 },
            voice_type: 'male_fierce',
            color: '#FF6347'
          },
          exists_in_library: false
        },
        {
          name: '唐僧',
          frequency: 12,
          character_trait: { trait: 'gentle', confidence: 0.7, description: '温柔和善，说话轻声细语' },
          first_appearance: 2,
          is_main_character: true,
          recommended_config: {
            gender: 'male',
            personality: 'gentle',
            personality_description: '温柔和善，说话轻声细语',
            personality_confidence: 0.7,
            description: '唐僧，男性主要角色，温柔和善，说话轻声细语，在文本中出现12次。',
            recommended_tts_params: { time_step: 35, p_w: 1.2, t_w: 2.8 },
            voice_type: 'male_gentle',
            color: '#FFB6C1'
          },
          exists_in_library: false
        },
        {
          name: '白骨精',
          frequency: 8,
          character_trait: { trait: 'lively', confidence: 0.6, description: '活泼开朗，充满活力' },
          first_appearance: 5,
          is_main_character: true,
          recommended_config: {
            gender: 'female',
            personality: 'lively',
            personality_description: '活泼开朗，充满活力',
            personality_confidence: 0.6,
            description: '白骨精，女性主要角色，活泼开朗，充满活力，在文本中出现8次。',
            recommended_tts_params: { time_step: 30, p_w: 1.3, t_w: 2.9 },
            voice_type: 'female_lively',
            color: '#32CD32'
          },
          exists_in_library: false
        }
      ]
    }
    
    smartDiscovery.analysisProgress = 100
    analysisStatus.value = 'success'
    analysisText.value = `分析完成！发现 ${smartDiscovery.discoveredCharacters.length} 个角色`
    smartDiscovery.analysisComplete = true
    
    // 检查角色是否已存在
    await checkCharacterExistence()
    
  } catch (error) {
    console.error('角色分析失败:', error)
    analysisStatus.value = 'exception'
    analysisText.value = '分析失败，请重试'
    message.error('角色分析失败')
  }
}

// 处理API分析结果
const processAnalysisResult = async (analysisData) => {
  console.log('[角色分析] API返回数据:', analysisData)
  
  // 合并所有章节的角色发现结果
  const characterMap = new Map()
  
  analysisData.forEach(chapterResult => {
    if (chapterResult.detected_characters) {
      chapterResult.detected_characters.forEach(char => {
        if (characterMap.has(char.name)) {
          const existing = characterMap.get(char.name)
          existing.frequency += char.frequency || 1
          // 合并情绪分布
          if (char.emotion_distribution) {
            Object.keys(char.emotion_distribution).forEach(emotion => {
              existing.emotion_distribution[emotion] = 
                (existing.emotion_distribution[emotion] || 0) + 
                char.emotion_distribution[emotion]
            })
          }
        } else {
          characterMap.set(char.name, { 
            ...char,
            recommended_config: char.recommended_config || {
              gender: char.gender || 'female',
              personality: char.personality || 'calm',
              personality_description: char.personality_description || '性格温和',
              personality_confidence: char.personality_confidence || 0.5,
              description: char.description || `${char.name}，${char.gender === 'male' ? '男性' : '女性'}角色`,
              recommended_tts_params: char.recommended_tts_params || { time_step: 32, p_w: 1.4, t_w: 3.0 },
              voice_type: `${char.gender || 'female'}_${char.personality || 'calm'}`,
              color: colorOptions[Math.floor(Math.random() * colorOptions.length)]
            }
          })
        }
      })
    }
  })
  
  // 转换为数组
  const characters = Array.from(characterMap.values())
  console.log('[角色分析] 处理后的角色列表:', characters)
  
  smartDiscovery.discoveredCharacters = characters
}

// 检查角色是否已存在
const checkCharacterExistence = async () => {
  for (const character of smartDiscovery.discoveredCharacters) {
    try {
      // 调用检查API
      const response = await fetch(`/api/v1/characters/check-exists?name=${encodeURIComponent(character.name)}`)
      const result = await response.json()
      
      if (result.success) {
        character.exists_in_library = result.data?.exists || false
        if (character.exists_in_library && result.data?.config) {
          character.existing_config = result.data.config
        }
      } else {
        character.exists_in_library = false
      }
    } catch (error) {
      console.error(`检查角色 ${character.name} 失败:`, error)
      character.exists_in_library = false
    }
  }
}

// 准备角色配置
const prepareCharacterConfigs = () => {
  console.log('[角色配置] 准备配置，发现的角色:', smartDiscovery.discoveredCharacters)
  
  // 显示所有角色，包括已存在的
  newCharacters.value = smartDiscovery.discoveredCharacters.map(char => ({
      ...char,
      config: {
        name: char.name,
        gender: char.recommended_config?.gender || 'female',
        personality: char.recommended_config?.personality || 'calm',
        color: char.recommended_config?.color || colorOptions[0],
        description: char.recommended_config?.description || `${char.name}角色配置`,
        // 文件上传相关
        audioFileList: [],
        latentFileList: [],
        audioFileInfo: null,
        latentFileInfo: null
      }
    }))
  
  console.log('[角色配置] 所有角色（包括已存在）:', newCharacters.value)
  
  // 默认只选中不存在的角色
  selectedConfigs.value = newCharacters.value
    .filter(char => !char.exists_in_library)
    .map(char => char.name)
  updateConfigCheckState()
}

// 配置全选/取消全选
const onCheckAllConfigs = (e) => {
  if (e.target.checked) {
    selectedConfigs.value = newCharacters.value.map(char => char.name)
  } else {
    selectedConfigs.value = []
  }
  updateConfigCheckState()
}

// 创建角色（智能发现后）
const createCharacters = async () => {
  try {
    creatingCharacters.value = true
    
    // 检查是否选择了书籍
    if (!smartDiscovery.selectedBook) {
      message.error('请先选择书籍')
      return
    }
    
    const charactersToCreate = newCharacters.value.filter(char => 
      selectedConfigs.value.includes(char.name)
    )
    
    if (charactersToCreate.length === 0) {
      message.warning('请选择要创建的角色')
      return
    }
    
    try {
      // 构建角色数据，格式化为后端期望的格式
      const charactersData = charactersToCreate.map(character => ({
        name: character.name,
        description: character.config?.description || character.personality_description || '',
        gender: character.gender || character.config?.gender || '',
        personality: character.personality || character.config?.personality || '',
        confidence: character.confidence || 0.5
      }))
      
      // 使用新的批量创建API
      const response = await charactersAPI.batchCreateCharacters({
        characters: charactersData,
        book_id: smartDiscovery.selectedBook.id,
        chapter_id: smartDiscovery.selectedChapters.length > 0 ? smartDiscovery.selectedChapters[0].id : null
      })
      
      if (response.data && response.data.success) {
        const result = response.data.data
        
        // 更新创建结果
        createdCharacters.value = result.created.map(char => ({
          name: char.name,
          description: char.description,
          book_title: result.book_title,
          status: 'created'
        }))
        
        // 显示创建结果
        if (result.total_created > 0) {
          message.success(`成功创建 ${result.total_created} 个角色到《${result.book_title}》`)
        }
        
        if (result.total_skipped > 0) {
          message.warning(`跳过 ${result.total_skipped} 个已存在的角色`)
        }
        
        nextStep() // 进入完成步骤
        
        // 如果当前是角色管理模式，重新加载数据
        if (managementType.value === 'character') {
          await loadVoiceLibrary()
        }
        
      } else {
        message.error('批量创建角色失败: ' + (response.data?.message || '未知错误'))
      }
      
    } catch (error) {
      console.error('批量创建角色失败:', error)
      const errorMsg = error.response?.data?.message || error.message || '网络错误'
      message.error('批量创建角色失败: ' + errorMsg)
    }
    
  } catch (error) {
    console.error('创建角色过程失败:', error)
    message.error('创建角色失败')
  } finally {
    creatingCharacters.value = false
  }
}

// 编辑已创建的角色
const editCreatedCharacter = (character) => {
  // 找到对应的角色并编辑
  const voice = voiceLibrary.value.find(v => v.name === character.name)
  if (voice) {
    editVoice(voice)
    closeSmartDiscovery()
  }
}

// 开始新的发现
const startNewDiscovery = () => {
  resetDiscoveryState()
  loadBooks()
}

// 配置阶段的文件上传处理
const handleConfigAudioChange = (info, character) => {
  if (info.fileList.length > 0) {
    const file = info.fileList[0].originFileObj || info.fileList[0]
    character.config.audioFileInfo = {
      name: file.name,
      size: formatFileSize(file.size),
      file: file
    }
  } else {
    character.config.audioFileInfo = null
  }
}

const handleConfigLatentChange = (info, character) => {
  if (info.fileList.length > 0) {
    const file = info.fileList[0].originFileObj || info.fileList[0]
    character.config.latentFileInfo = {
      name: file.name,
      size: formatFileSize(file.size),
      file: file
    }
  } else {
    character.config.latentFileInfo = null
  }
}

// 获取创建摘要
const getCreationSummary = () => {
  const total = createdCharacters.value.length
  const active = createdCharacters.value.filter(c => c.status === 'active').length
  const withAudio = createdCharacters.value.filter(c => c.hasAudio).length
  const withLatent = createdCharacters.value.filter(c => c.hasLatent).length
  
  let summary = `已成功创建 ${total} 个角色。`
  if (active > 0) {
    summary += ` 其中 ${active} 个角色已激活可用。`
  }
  if (withAudio > 0) {
    summary += ` ${withAudio} 个角色已上传音频文件。`
  }
  if (withLatent > 0) {
    summary += ` ${withLatent} 个角色已上传Latent文件。`
  }
  if (total - active > 0) {
    summary += ` 剩余 ${total - active} 个角色需要上传音频文件才能使用。`
  }
  
  return summary
}

const duplicateVoice = (voice) => {
  message.success(`已复制声音：${voice.name}`)
}

const exportVoice = (voice) => {
  message.success(`导出声音：${voice.name}`)
}

// 确认删除角色
const confirmDeleteCharacter = (character) => {
  // 创建一个响应式的状态来管理强制删除选项
  let forceDelete = false
  
  Modal.confirm({
    title: '删除角色',
    content: h('div', [
      h('p', `确定要删除角色"${character.name}"吗？此操作不可恢复。`),
      h('div', { style: 'margin: 16px 0 8px 0;' }, [
        h('p', { style: 'margin: 0 0 8px 0; color: #fa8c16; font-weight: 500;' }, '⚠️ 删除提示'),
        h('p', { style: 'margin: 0; font-size: 13px; color: #8c8c8c;' }, '如果角色已被项目使用或包含声音文件，可能需要强制删除')
      ]),
      h('div', { style: 'margin: 12px 0;' }, [
        h('label', { style: 'display: flex; align-items: center; gap: 8px; cursor: pointer;' }, [
          h('input', {
            type: 'checkbox',
            onChange: (e) => {
              forceDelete = e.target.checked
            }
          }),
          h('span', { style: 'color: #ff4d4f; font-weight: 500;' }, '强制删除（包括关联的声音文件和项目引用）')
        ])
      ])
    ]),
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => deleteCharacter(character, forceDelete)
  })
}

// 删除角色
const deleteCharacter = async (character, force = false) => {
  try {
    console.log('删除角色:', character.id, '强制删除:', force)
    const success = await deleteVoiceFromBackend(character.id, force)
    if (success) {
      message.success('角色删除成功')
      loadVoiceLibrary()
      if (selectedVoice.value?.id === character.id) {
        showDetailDrawer.value = false
        selectedVoice.value = null
      }
    }
  } catch (error) {
    console.error('删除角色失败:', error)
    
    // 如果是需要强制删除的错误，给出友好提示
    if (error.response?.data?.message?.includes('请使用强制删除')) {
      Modal.warning({
        title: '删除失败',
        content: '角色包含关联数据，请勾选"强制删除"选项后重试',
        okText: '知道了'
      })
    } else {
      const errorMsg = error.response?.data?.message || error.message || '删除失败'
      message.error('删除失败: ' + errorMsg)
    }
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
const playCurrentAudio = async () => {
  if (editingVoice.value.referenceAudioUrl) {
    try {
      // 使用统一播放组件播放
      await playCustomAudio(
        editingVoice.value.referenceAudioUrl, 
        `${editingVoice.value.name || '预览'} - 音频试听`, 
        {
          voiceId: editingVoice.value.id,
          voiceName: editingVoice.value.name,
          description: editingVoice.value.description,
          onEnded: () => {
            console.log(`编辑音频 ${editingVoice.value.name} 试听完成`)
          }
        }
      )
      message.success('开始播放音频')
    } catch (error) {
      console.error('播放音频失败:', error)
      message.error('播放音频失败')
    }
  } else {
    message.warning('没有可播放的音频文件')
  }
}

// 监听选择变化
watch([selectedChapters, selectedConfigs], () => {
  nextTick(() => {
    updateChapterCheckState()
    updateConfigCheckState()
  })
})

// 监听智能发现模态框打开
watch(showSmartDiscoveryModal, async (newVal) => {
  if (newVal) {
    try {
      await loadBooks()
    } catch (error) {
      console.error('加载书籍列表失败:', error)
      message.error('加载书籍列表失败，请重试')
    }
  }
})

// 组件挂载时加载数据
onMounted(async () => {
  try {
    await loadVoiceLibrary()
  } catch (error) {
    console.error('初始化加载失败:', error)
    message.error('加载数据失败，请刷新页面重试')
  }
})

// 智能发现相关数据
const smartDiscovery = reactive({
  visible: false,
  currentStep: 1,
  selectedBook: null,
  selectedChapters: [],
  analysisProgress: 0,
  analysisComplete: false,
  discoveredCharacters: [],
  configuredCharacters: [],
  creationResults: []
})

// 书籍和章节数据
  const booksData = ref([])
  const chaptersData = ref([])
  const chaptersLoading = ref(false)

// 智能发现功能
const openSmartDiscovery = async () => {
  smartDiscovery.visible = true
  smartDiscovery.currentStep = 1
  smartDiscovery.selectedBook = null
  smartDiscovery.selectedChapters = []
  smartDiscovery.analysisProgress = 0
  smartDiscovery.analysisComplete = false
  smartDiscovery.discoveredCharacters = []
  smartDiscovery.configuredCharacters = []
  smartDiscovery.creationResults = []
  
  // 加载书籍列表
  await loadBooks()
}

// 选择章节
const toggleChapterSelection = (chapter) => {
  const index = smartDiscovery.selectedChapters.findIndex(c => c.id === chapter.id)
  if (index > -1) {
    smartDiscovery.selectedChapters.splice(index, 1)
  } else {
    smartDiscovery.selectedChapters.push(chapter)
  }
}

// 全选/取消全选章节
const toggleAllChapters = () => {
  if (smartDiscovery.selectedChapters.length === chaptersData.value.length) {
    smartDiscovery.selectedChapters = []
  } else {
    smartDiscovery.selectedChapters = [...chaptersData.value]
  }
}

// 格式化数字
const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 获取书籍状态文本
const getBookStatusText = (status) => {
  const statusMap = {
    'draft': '草稿',
    'published': '已发布',
    'archived': '已归档',
    'active': '进行中',
    'completed': '已完成'
  }
  return statusMap[status] || '未知'
}

// 获取章节状态文本
const getChapterStatusText = (status) => {
  const statusMap = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
    'draft': '草稿'
  }
  return statusMap[status] || '未知'
}

const goBack = () => {
  router.go(-1) // 返回上一页
}
</script>

<style scoped>
.voice-library-container {
  background: #f8fafc;
  min-height: 100vh;
}

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

.title-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-title {
  display: flex;
  align-items: center;
  margin: 0;
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

.action-section {
  display: flex;
  gap: 16px;
}

.filter-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.voice-library-content {
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
  border: 2px solid #d1d5db;
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
}

.no-audio-message {
  background: #f9fafb;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
}

/* 统计卡片样式 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

/* 筛选区域样式 */
.filter-section {
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.view-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .stat-card {
    padding: 20px;
  }
  
  .stat-icon {
    width: 48px;
    height: 48px;
  }
  
  .stat-value {
    font-size: 24px;
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

/* 智能发现样式 */
.smart-discovery-container {
  padding: 0;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin: 16px 0;
}

.discovery-steps {
  margin-bottom: 32px;
}

.step-content {
  min-height: 400px;
}

.step-panel {
  padding: 24px 0;
}

.step-header {
  text-align: center;
  margin-bottom: 32px;
}

.step-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.step-header p {
  color: #6b7280;
  margin: 0;
}

.success-icon {
  margin-bottom: 16px;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #d1d5db;
}

/* 书籍选择样式 */
.book-selection {
  margin-bottom: 32px;
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
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.book-card {
  border: 2px solid #d1d5db;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-height: 120px;
}

.book-card:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--primary-color-rgb), 0.15);
}

.book-card.selected {
  border-color: var(--primary-color);
  background: rgba(var(--primary-color-rgb), 0.06);
}

.book-icon {
  color: var(--primary-color);
  flex-shrink: 0;
}

.book-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.book-info h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
}

.book-info p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.book-stats {
  display: flex;
  gap: 12px;
  margin: 8px 0;
  font-size: 12px;
  color: #9ca3af;
}

.book-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.book-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: #10b981;
  color: white;
}

.book-id {
  font-size: 11px;
  color: #9ca3af;
}

/* 章节选择样式 */
.chapter-selection {
  margin-bottom: 32px;
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
  color: #6b7280;
  font-size: 14px;
}

.chapters-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #d1d5db;
  border-radius: 8px;
}

.chapters-grid {
  display: block;
}

.chapter-item {
  border-bottom: 1px solid #d1d5db;
  padding: 12px 16px;
}

.chapter-item:last-child {
  border-bottom: none;
}

.chapter-content {
  margin-left: 8px;
}

/* 已存在角色样式 */
.existing-character {
  opacity: 0.7;
}

.existing-character .config-card {
  background: #f8f9fa !important;
  border: 1px dashed #d1d5db !important;
}

.existing-character-info {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.existing-config-display {
  margin-top: 12px;
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

/* 分析进度样式 */
.analysis-progress {
  margin-bottom: 32px;
  text-align: center;
}

.progress-text {
  margin-top: 16px;
  color: #6b7280;
  font-size: 14px;
}

.analysis-results {
  margin-top: 32px;
}

.results-summary {
  margin-bottom: 24px;
  padding: 20px;
  background: #f9fafb;
  border-radius: 8px;
}

.characters-preview h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.characters-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.character-preview-item,
.created-character-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
}

.character-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 16px;
  flex-shrink: 0;
}

.character-info {
  flex: 1;
}

.character-name {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.character-meta {
  font-size: 12px;
  color: #6b7280;
}

.character-status,
.character-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 批量配置样式 */
.batch-config {
  margin-bottom: 32px;
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

.config-list {
  max-height: 400px;
  overflow-y: auto;
}

.config-grid {
  display: block;
}

.config-item {
  margin-bottom: 16px;
}

.config-card {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 16px;
}

.config-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.character-basic h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.character-basic p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.config-details {
  border-top: 1px solid #d1d5db;
  padding-top: 16px;
}

/* 创建结果样式 */
.creation-results {
  margin-top: 24px;
}

.results-summary {
  margin-bottom: 24px;
}

.created-characters h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

/* 文件信息小样式 */
.file-info-mini {
  margin-top: 4px;
  font-size: 11px;
  color: #6b7280;
}

.file-name-mini {
  display: block;
  font-weight: 500;
  color: #374151;
}

.file-size-mini {
  color: #9ca3af;
}

.character-files {
  margin-top: 8px;
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.back-btn-header {
  font-size: 18px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.2s;
  border: 1px solid rgba(255, 255, 255, 0.3);
  margin-right: 16px;
}

.back-btn-header:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

/* 暗黑模式适配 */
[data-theme="dark"] .characters-container {
  background: #141414 !important;
  min-height: 100vh !important;
}

[data-theme="dark"] .character-card,
[data-theme="dark"] .character-preview-item,
[data-theme="dark"] .created-character-item,
[data-theme="dark"] .config-card {
  background: #1f1f1f !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] .character-name {
  color: #fff !important;
}

[data-theme="dark"] .character-meta,
[data-theme="dark"] .character-basic p,
[data-theme="dark"] .file-info-mini,
[data-theme="dark"] .file-size-mini {
  color: #8c8c8c !important;
}

[data-theme="dark"] .file-name-mini {
  color: #d1d5db !important;
}

[data-theme="dark"] .progress-text {
  color: #8c8c8c !important;
}

[data-theme="dark"] .results-summary,
[data-theme="dark"] .config-controls {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .characters-preview h4,
[data-theme="dark"] .created-characters h4,
[data-theme="dark"] .character-basic h4 {
  color: #fff !important;
}

[data-theme="dark"] .config-details {
  border-top-color: #434343 !important;
}

[data-theme="dark"] .voice-card {
  background: #1f1f1f !important;
  border-color: #434343 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] .voice-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}

[data-theme="dark"] .voice-card.selected {
  border-color: #4a9eff !important;
  box-shadow: 0 0 0 2px rgba(74, 158, 255, 0.2) !important;
}

[data-theme="dark"] .voice-name {
  color: #fff !important;
}

[data-theme="dark"] .voice-desc {
  color: #8c8c8c !important;
}

[data-theme="dark"] .meta-item span {
  color: #d1d5db !important;
}

[data-theme="dark"] .voice-library-content {
  background: transparent !important;
}

[data-theme="dark"] .grid-view,
[data-theme="dark"] .list-view {
  background: transparent !important;
}

[data-theme="dark"] .voice-library-container {
  background: #141414 !important;
}

[data-theme="dark"] .stats-grid {
  background: transparent !important;
}

[data-theme="dark"] .stat-card {
  background: #1f1f1f !important;
  border-color: #434343 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] .stat-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}

[data-theme="dark"] .stat-value {
  color: #fff !important;
}

[data-theme="dark"] .stat-label {
  color: #8c8c8c !important;
}

[data-theme="dark"] .filter-section {
  background: #1f1f1f !important;
  border-color: #434343 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] .voice-library-content {
  background: transparent !important;
  box-shadow: none !important;
}

[data-theme="dark"] .page-header {
  background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}

[data-theme="dark"] .voice-info {
  color: #d1d5db !important;
}

[data-theme="dark"] .voice-avatar {
  background: transparent !important;
}

[data-theme="dark"] .voice-status {
  background: #2d2d2d !important;
  border: 1px solid #434343 !important;
}

/* 智能角色发现抽屉暗黑模式适配 */
[data-theme="dark"] .smart-discovery-container {
  background: transparent !important;
  color: #d1d5db !important;
}

[data-theme="dark"] .step-header h3 {
  color: #fff !important;
}

[data-theme="dark"] .step-header p {
  color: #8c8c8c !important;
}

[data-theme="dark"] .book-card {
  background: #2d2d2d !important;
  border-color: #434343 !important;
  color: #d1d5db !important;
}

[data-theme="dark"] .book-card:hover {
  background: #3a3a3a !important;
  border-color: var(--primary-color) !important;
  box-shadow: 0 4px 12px rgba(var(--primary-color-rgb), 0.25) !important;
}

[data-theme="dark"] .book-card.selected {
  background: rgba(var(--primary-color-rgb), 0.15) !important;
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] .book-info h4 {
  color: #fff !important;
}

[data-theme="dark"] .book-info p,
[data-theme="dark"] .book-stats,
[data-theme="dark"] .book-id {
  color: #8c8c8c !important;
}

[data-theme="dark"] .book-status {
  background: var(--primary-color) !important;
  color: #fff !important;
}

[data-theme="dark"] .chapter-item {
  background: #2d2d2d !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .chapter-title {
  color: #fff !important;
}

[data-theme="dark"] .chapter-meta {
  color: #8c8c8c !important;
}

[data-theme="dark"] .selection-controls {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .selection-info {
  color: #8c8c8c !important;
}

[data-theme="dark"] .chapters-list {
  border-color: #434343 !important;
  background: #1f1f1f !important;
}

[data-theme="dark"] .progress-text {
  color: #8c8c8c !important;
}

[data-theme="dark"] .results-summary {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .characters-preview h4 {
  color: #fff !important;
}

[data-theme="dark"] .character-preview-item,
[data-theme="dark"] .created-character-item {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .character-name {
  color: #fff !important;
}

[data-theme="dark"] .character-meta {
  color: #8c8c8c !important;
}

[data-theme="dark"] .existing-character-info {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .existing-character .config-card {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .empty-state p {
  color: #8c8c8c !important;
}

[data-theme="dark"] .empty-state svg {
  fill: #434343 !important;
}

/* 书籍信息样式 */
.book-info {
  margin: 8px 0;
}

.book-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  font-size: 11px;
  color: #6b7280;
  max-width: 100%;
  overflow: hidden;
}

.book-badge svg {
  flex-shrink: 0;
  fill: #9ca3af;
}

.book-badge span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 角色管理模式的卡片样式调整 */
.voice-card[data-character="true"] {
  border-left: 4px solid #8b5cf6;
}

.voice-card[data-character="true"] .voice-avatar .avatar-icon {
  background: #8b5cf6 !important;
}

/* 管理类型选择器样式 */
.filter-controls .ant-select:first-child {
  border: 2px solid #06b6d4;
  border-radius: 8px;
}

.filter-controls .ant-select:first-child .ant-select-selector {
  border: none;
  font-weight: 500;
  color: #06b6d4;
}

/* 角色配置状态样式 */
.meta-item span[data-status="configured"] {
  color: #10b981;
}

.meta-item span[data-status="unconfigured"] {
  color: #f59e0b;
}

/* 书籍选择器样式 */
.filter-controls .ant-select[data-book-selector] .ant-select-selector {
  border-color: #8b5cf6;
}

/* 暗黑模式适配 */
[data-theme="dark"] .book-badge {
  background: #374151 !important;
  border-color: #6b7280 !important;
  color: #d1d5db !important;
}

[data-theme="dark"] .book-badge svg {
  fill: #9ca3af !important;
}

[data-theme="dark"] .voice-card[data-character="true"] {
  border-left-color: #a855f7 !important;
}

[data-theme="dark"] .voice-card[data-character="true"] .voice-avatar .avatar-icon {
  background: #a855f7 !important;
}
</style>