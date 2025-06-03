<template>
  <div class="task-monitor">
    <a-row :gutter="16" class="mb-16">
      <a-col :span="24">
        <a-card title="任务监控" :bordered="false">
          <template #extra>
            <a-button type="primary" @click="refreshTasks">
              <template #icon><reload-outlined /></template>
              刷新
            </a-button>
          </template>
          <p>查看所有任务的进度与状态，支持实时监控</p>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16">
      <!-- 任务列表 -->
      <a-col :span="16">
        <a-card :loading="loading">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="all" tab="所有任务">
              <a-table
                :columns="columns"
                :data-source="tasks"
                :pagination="{ pageSize: 5 }"
                :rowKey="record => record.taskId"
                @change="handleTableChange"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'status'">
                    <a-tag :color="getStatusColor(record.status)">
                      {{ getStatusText(record.status) }}
                    </a-tag>
                  </template>
                  
                  <template v-else-if="column.key === 'progress'">
                    <a-progress
                      :percent="Math.floor(record.progress * 100)"
                      size="small"
                      :status="getProgressStatus(record.status)"
                    />
                  </template>
                  
                  <template v-else-if="column.key === 'action'">
                    <a-space>
                      <a-button type="link" @click="viewTaskDetail(record.taskId)">
                        查看
                      </a-button>
                      <a-button
                        v-if="record.status === 'completed'"
                        type="link"
                        @click="downloadResult(record.taskId)"
                      >
                        下载
                      </a-button>
                    </a-space>
                  </template>
                </template>
              </a-table>
            </a-tab-pane>
            <a-tab-pane key="processing" tab="处理中">
              <a-table
                :columns="columns"
                :data-source="processingTasks"
                :pagination="{ pageSize: 5 }"
                :rowKey="record => record.taskId"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'status'">
                    <a-tag :color="getStatusColor(record.status)">
                      {{ getStatusText(record.status) }}
                    </a-tag>
                  </template>
                  
                  <template v-else-if="column.key === 'progress'">
                    <a-progress
                      :percent="Math.floor(record.progress * 100)"
                      size="small"
                      :status="getProgressStatus(record.status)"
                    />
                  </template>
                  
                  <template v-else-if="column.key === 'action'">
                    <a-button type="link" @click="viewTaskDetail(record.taskId)">
                      查看
                    </a-button>
                  </template>
                </template>
              </a-table>
            </a-tab-pane>
            <a-tab-pane key="completed" tab="已完成">
              <a-table
                :columns="columns"
                :data-source="completedTasks"
                :pagination="{ pageSize: 5 }"
                :rowKey="record => record.taskId"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'status'">
                    <a-tag :color="getStatusColor(record.status)">
                      {{ getStatusText(record.status) }}
                    </a-tag>
                  </template>
                  
                  <template v-else-if="column.key === 'progress'">
                    <a-progress
                      :percent="Math.floor(record.progress * 100)"
                      size="small"
                      :status="getProgressStatus(record.status)"
                    />
                  </template>
                  
                  <template v-else-if="column.key === 'action'">
                    <a-space>
                      <a-button type="link" @click="viewTaskDetail(record.taskId)">
                        查看
                      </a-button>
                      <a-button type="link" @click="downloadResult(record.taskId)">
                        下载
                      </a-button>
                    </a-space>
                  </template>
                </template>
              </a-table>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
      
      <!-- 任务详情 -->
      <a-col :span="8">
        <a-card title="任务详情" :loading="detailLoading">
          <div v-if="!currentTask">
            <a-empty description="请选择任务查看详情" />
          </div>
          <div v-else>
            <a-descriptions bordered :column="1">
              <a-descriptions-item label="任务ID">
                {{ currentTask.taskId }}
              </a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag :color="getStatusColor(currentTask.status)">
                  {{ getStatusText(currentTask.status) }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="进度">
                <a-progress
                  :percent="Math.floor(currentTask.progress * 100)"
                  :status="getProgressStatus(currentTask.status)"
                />
              </a-descriptions-item>
              <a-descriptions-item label="创建时间">
                {{ formatTime(currentTask.created_at) }}
              </a-descriptions-item>
              <a-descriptions-item label="小说路径">
                {{ currentTask.novel_path }}
              </a-descriptions-item>
              <a-descriptions-item label="输出目录">
                {{ currentTask.output_dir }}
              </a-descriptions-item>
            </a-descriptions>
            
            <div v-if="currentTask.status === 'processing'" class="mt-16">
              <div>
                <span class="progress-label">章节进度:</span>
                {{ currentTask.current_chapter || 0 }}/{{ currentTask.total_chapters || 0 }}
              </div>
              <div class="task-message">{{ currentTask.message }}</div>
              <a-button 
                block 
                type="primary" 
                :loading="pollingActive" 
                @click="togglePolling"
              >
                {{ pollingActive ? '停止自动刷新' : '开始自动刷新' }}
              </a-button>
            </div>
            
            <div v-if="currentTask.status === 'completed'" class="mt-16">
              <a-button block type="primary" @click="downloadResult(currentTask.taskId)">
                <template #icon><download-outlined /></template>
                下载结果
              </a-button>
              
              <!-- 音频预览 -->
              <div class="audio-preview mt-16" v-if="currentTask.result && currentTask.result.preview_file">
                <div class="preview-title">音频预览:</div>
                <a-divider style="margin: 8px 0" />
                <audio 
                  controls 
                  style="width: 100%" 
                  :src="`/api/tts/download/${currentTask.result.preview_file}`"
                ></audio>
                <div class="preview-info">
                  <p>总生成章节: {{ currentTask.result.completed_chapters || 0 }}</p>
                  <p>总时长: {{ formatDuration(currentTask.result.total_duration || 0) }}</p>
                </div>
              </div>
            </div>
            
            <div v-if="currentTask.status === 'failed'" class="mt-16">
              <a-alert type="error" show-icon :message="currentTask.error" />
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script>
import { defineComponent, ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { 
  ReloadOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import { ttsAPI } from '../services/api';

export default defineComponent({
  name: 'TaskMonitorView',
  components: {
    ReloadOutlined,
    DownloadOutlined
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    // 移除 apiStore 引用
    
    // 状态变量
    const loading = ref(false);
    const detailLoading = ref(false);
    const activeTab = ref('all');
    const currentTask = ref(null);
    const tasks = ref([]);
    const pollingActive = ref(false);
    let pollingTimer = null;
    
    // 表格列配置
    const columns = [
      {
        title: '任务ID',
        dataIndex: 'taskId',
        key: 'taskId',
        width: '25%',
        ellipsis: true
      },
      {
        title: '类型',
        dataIndex: 'type',
        key: 'type',
        width: '10%'
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: '15%'
      },
      {
        title: '进度',
        dataIndex: 'progress',
        key: 'progress',
        width: '25%'
      },
      {
        title: '操作',
        key: 'action',
        width: '15%'
      }
    ];
    
    // 根据状态过滤的任务列表
    const processingTasks = computed(() => {
      return tasks.value?.filter(task => 
        task.status === 'pending' || task.status === 'processing'
      );
    });
    
    const completedTasks = computed(() => {
      return tasks.value?.filter(task => task.status === 'completed');
    });
    
    // 获取状态对应的颜色
    const getStatusColor = (status) => {
      const colors = {
        'pending': 'blue',
        'processing': 'processing',
        'completed': 'success',
        'failed': 'error'
      };
      return colors[status] || 'default';
    };
    
    // 获取状态文本
    const getStatusText = (status) => {
      const texts = {
        'pending': '等待中',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败'
      };
      return texts[status] || '未知';
    };
    
    // 获取进度条状态
    const getProgressStatus = (status) => {
      if (status === 'failed') return 'exception';
      if (status === 'completed') return 'success';
      return 'active';
    };
    
    // 格式化时间
    const formatTime = (timestamp) => {
      if (!timestamp) return '-';
      const date = new Date(timestamp * 1000);
      return date.toLocaleString();
    };
    
    // 格式化时长
    const formatDuration = (seconds) => {
      if (!seconds) return '0秒';
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const remainingSeconds = Math.floor(seconds % 60);
      
      let result = '';
      if (hours > 0) result += `${hours}小时`;
      if (minutes > 0) result += `${minutes}分钟`;
      if (remainingSeconds > 0 || result === '') result += `${remainingSeconds}秒`;
      
      return result;
    };
    
    // 加载所有任务
    const loadTasks = async () => {
      loading.value = true;
      try {
        const response = await ttsAPI.getTasks();
        tasks.value = response.data || [];
      } catch (error) {
        console.error('加载任务列表失败:', error);
        message.error('加载任务列表失败: ' + (error.response?.data?.message || error.message));
      } finally {
        loading.value = false;
      }
    };
    
    // 查看任务详情
    const viewTaskDetail = async (taskId) => {
      detailLoading.value = true;
      try {
        const response = await ttsAPI.getTaskStatus(taskId);
        currentTask.value = response.data;
        
        // 开始轮询，如果任务正在处理中
        if (response.data.status === 'processing') {
          startPolling();
        } else {
          stopPolling();
        }
      } catch (error) {
        console.error('加载任务详情失败:', error);
        message.error('加载任务详情失败: ' + (error.response?.data?.message || error.message));
      } finally {
        detailLoading.value = false;
      }
    };
    
    // 刷新当前任务详情
    const refreshCurrentTask = async () => {
      if (!currentTask.value) return;
      
      try {
        const response = await ttsAPI.getTaskStatus(currentTask.value.task_id || currentTask.value.taskId);
        currentTask.value = response.data;
        
        // 如果任务已经完成或失败，停止轮询
        if (response.data.status !== 'processing' && response.data.status !== 'pending') {
          stopPolling();
          
          // 也刷新任务列表，反映新状态
          loadTasks();
        }
      } catch (error) {
        console.error('刷新任务详情失败:', error);
      }
    };
    
    // 刷新所有任务
    const refreshTasks = () => {
      loadTasks();
      if (currentTask.value) {
        refreshCurrentTask();
      }
    };
    
    // 下载任务结果
    const downloadResult = async (taskId) => {
      try {
        const response = await ttsAPI.downloadTask(taskId);
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `task_${taskId}.zip`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('下载任务结果失败:', error);
        message.error('下载任务结果失败: ' + (error.response?.data?.message || error.message));
      }
    };
    
    // 开始轮询
    const startPolling = () => {
      pollingActive.value = true;
      stopPolling(); // 先停止已有轮询
      
      pollingTimer = setInterval(() => {
        refreshCurrentTask();
      }, 5000); // 每5秒刷新一次
    };
    
    // 停止轮询
    const stopPolling = () => {
      if (pollingTimer) {
        clearInterval(pollingTimer);
        pollingTimer = null;
      }
      pollingActive.value = false;
    };
    
    // 切换轮询状态
    const togglePolling = () => {
      if (pollingActive.value) {
        stopPolling();
      } else {
        startPolling();
      }
    };
    
    // 表格变化处理
    const handleTableChange = (pagination, filters, sorter) => {
      // 可以根据需要处理排序和过滤
      console.log('Table params:', pagination, filters, sorter);
    };
    
    // 组件挂载时加载数据
    onMounted(() => {
      loadTasks();
      
      // 定时刷新任务列表（每30秒）
      const refreshInterval = setInterval(loadTasks, 30000);
      
      // 卸载组件时清理
      onUnmounted(() => {
        clearInterval(refreshInterval);
        stopPolling();
      });
    });
    
    return {
      loading,
      detailLoading,
      activeTab,
      tasks,
      processingTasks,
      completedTasks,
      currentTask,
      columns,
      pollingActive,
      getStatusColor,
      getStatusText,
      getProgressStatus,
      formatTime,
      formatDuration,
      viewTaskDetail,
      refreshTasks,
      downloadResult,
      togglePolling,
      handleTableChange
    };
  }
});
</script>

<style scoped>
.task-monitor {
  width: 100%;
}

.progress-label {
  font-weight: bold;
  margin-right: 8px;
}

.task-message {
  margin: 12px 0;
  color: rgba(0, 0, 0, 0.65);
}

.audio-preview {
  margin-top: 16px;
}

.preview-title {
  font-weight: bold;
  margin-bottom: 8px;
}

.preview-info {
  margin-top: 8px;
  color: rgba(0, 0, 0, 0.65);
}
</style>