<template>
  <div class="dashboard">
    <page-header title="系统控制台" subtitle="AI-Sound 语音合成系统状态与任务监控" />
    
    <a-row :gutter="16">
      <a-col :span="12">
        <a-card title="系统状态">
          <div class="status-wrapper">
            <div class="status-item">
              <dashboard-outlined />
              <div class="status-content">
                <div class="status-title">API状态</div>
                <div :class="['status-value', apiStatus ? 'status-ok' : 'status-error']">
                  {{ apiStatus ? '运行中' : '离线' }}
                </div>
              </div>
            </div>
            <a-divider />
            <div class="status-item">
              <rocket-outlined />
              <div class="status-content">
                <div class="status-title">GPU状态</div>
                <div :class="['status-value', systemInfo.gpu_available ? 'status-ok' : 'status-warning']">
                  {{ systemInfo.gpu_available ? '可用' : '不可用' }}
                </div>
              </div>
            </div>
            <a-divider />
            <div class="status-item">
              <hdd-outlined />
              <div class="status-content">
                <div class="status-title">存储空间</div>
                <div class="status-value">
                  {{ systemInfo.storage_used }} / {{ systemInfo.storage_available }}
                </div>
              </div>
            </div>
          </div>
        </a-card>
      </a-col>
      
      <a-col :span="12">
        <a-card title="任务统计">
          <div class="stats-wrapper">
            <div class="stats-item">
              <sound-outlined />
              <div class="stats-content">
                <div class="stats-title">语音合成数</div>
                <div class="stats-value">{{ stats.tts_count }}</div>
              </div>
            </div>
            <a-divider />
            <div class="stats-item">
              <read-outlined />
              <div class="stats-content">
                <div class="stats-title">小说处理数</div>
                <div class="stats-value">{{ stats.novel_count }}</div>
              </div>
            </div>
            <a-divider />
            <div class="stats-item">
              <loading-outlined />
              <div class="stats-content">
                <div class="stats-title">待处理任务</div>
                <div class="stats-value">{{ stats.pending_tasks }}</div>
              </div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
    
    <!-- 引擎状态卡片 -->
    <a-row style="margin-top: 16px">
      <a-col :span="24">
        <a-card title="引擎状态" :loading="loadingEngines">
          <a-button style="margin-bottom: 16px" type="primary" size="small" @click="checkEnginesHealth">
            <reload-outlined />刷新状态
          </a-button>
          <a-row :gutter="16">
            <a-col :span="12" v-for="(status, engine) in enginesHealth" :key="engine">
              <a-card class="engine-card">
                <div class="engine-header">
                  <div class="engine-title">
                    <cloud-server-outlined />
                    <span>{{ getEngineName(engine) }}</span>
                  </div>
                  <a-tag :color="status.healthy ? 'green' : 'red'">
                    {{ status.healthy ? '正常' : '异常' }}
                  </a-tag>
                </div>
                <a-divider style="margin: 12px 0" />
                <div class="engine-info">
                  <div class="info-item">
                    <div class="info-label">上次检查</div>
                    <div class="info-value">{{ formatTime(status.last_check) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">状态信息</div>
                    <div class="info-value">{{ status.message || '正常' }}</div>
                  </div>
                </div>
              </a-card>
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>
    
    <a-row style="margin-top: 16px">
      <a-col :span="24">
        <a-card title="最近任务">
          <a-table
            :dataSource="recentTasks"
            :columns="columns"
            :pagination="false"
            rowKey="id"
            :loading="loading"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">
                  {{ getStatusText(record.status) }}
                </a-tag>
              </template>
              <template v-if="column.key === 'action'">
                <a-button 
                  type="link" 
                  size="small"
                  @click="showDetails(record.id)"
                >
                  查看详情
                </a-button>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted } from 'vue';
import { engineAPI, systemAPI } from '../services/api';
import PageHeader from '@/components/common/PageHeader.vue';
import axios from 'axios'; // 添加axios导入
import { 
  DashboardOutlined, 
  RocketOutlined, 
  HddOutlined,
  SoundOutlined,
  ReadOutlined,
  LoadingOutlined,
  ReloadOutlined,
  CloudServerOutlined
} from '@ant-design/icons-vue';

export default defineComponent({
  name: 'DashboardView',
  components: {
    PageHeader,
    DashboardOutlined,
    RocketOutlined,
    HddOutlined,
    SoundOutlined,
    ReadOutlined,
    LoadingOutlined,
    ReloadOutlined,
    CloudServerOutlined
  },
  setup() {
    // 移除 apiStore 引用
    const apiStatus = ref(false);
    const loading = ref(false);
    const loadingEngines = ref(false);
    
    const enginesHealth = ref({
      megatts3: { healthy: false, message: '未检查', last_check: 0 },
      espnet: { healthy: false, message: '未检查', last_check: 0 }
    });
    
    const systemInfo = ref({
      gpu_available: false,
      gpu_info: '未知',
      storage_used: '0 GB',
      storage_available: '0 GB'
    });
    
    const stats = ref({
      tts_count: 0,
      novel_count: 0,
      pending_tasks: 0,
      audio_count: 0
    });
    
    const recentTasks = ref([]);
    
    const columns = [
      {
        title: '任务ID',
        dataIndex: 'id',
        key: 'id',
        width: 220
      },
      {
        title: '任务类型',
        dataIndex: 'type',
        key: 'type',
        width: 100
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 160
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100
      },
      {
        title: '操作',
        key: 'action',
        width: 100
      }
    ];
    
    // 检查API状态
    const checkApiStatus = async () => {
      loading.value = true;
      try {
        await systemAPI.healthCheck();
        apiStatus.value = true;
      } catch (error) {
        apiStatus.value = false;
        console.error('API状态检查失败:', error);
      } finally {
        loading.value = false;
      }
    };
    
    // 获取系统信息
    const getSystemInfo = async () => {
      loading.value = true;
      try {
        const response = await systemAPI.getSystemInfo();
        systemInfo.value = response.data || {};
      } catch (error) {
        console.error('获取系统信息失败:', error);
      } finally {
        loading.value = false;
      }
    };
    
    // 获取统计信息
    const getStats = async () => {
      loading.value = true;
      try {
        const response = await systemAPI.getSystemStats();
        stats.value = response.data || {};
      } catch (error) {
        console.error('获取统计信息失败:', error);
      } finally {
        loading.value = false;
      }
    };
    
    // 获取最近任务
    const getRecentTasks = async () => {
      loading.value = true;
      try {
        // 暂时使用模拟数据
        recentTasks.value = [
          {
            id: 'task_001',
            type: '语音合成',
            created_at: '2024-01-15 10:30:00',
            status: 'completed'
          },
          {
            id: 'task_002',
            type: '小说处理',
            created_at: '2024-01-15 09:15:00',
            status: 'processing'
          }
        ];
      } catch (error) {
        console.error('获取最近任务失败:', error);
      } finally {
        loading.value = false;
      }
    };
    
    // 检查引擎健康状态
    const checkEnginesHealth = async () => {
      loadingEngines.value = true;
      try {
        // 使用新的API服务获取引擎列表
        const response = await engineAPI.getEngines();
        // axios拦截器已经处理了API响应格式，直接使用原来的逻辑
        const engines = response.data?.engines || [];
        
        // 重置引擎状态
        const newHealth = {};
        
        // 为每个引擎检查健康状态
        for (const engine of engines) {
          try {
            await engineAPI.checkHealth(engine.id);
            newHealth[engine.id] = {
              healthy: true,
              message: '运行正常',
              last_check: Date.now() / 1000
            };
          } catch (error) {
            newHealth[engine.id] = {
              healthy: false,
              message: '连接失败',
              last_check: Date.now() / 1000
            };
          }
        }
        
        enginesHealth.value = newHealth;
      } catch (error) {
        console.error('获取引擎健康状态失败', error);
        // 失败时提供默认值
        enginesHealth.value = {
          megatts3: { healthy: false, message: '请求失败', last_check: Date.now() / 1000 },
          espnet: { healthy: false, message: '请求失败', last_check: Date.now() / 1000 }
        };
      } finally {
        loadingEngines.value = false;
      }
    };
    
    // 获取引擎名称
    const getEngineName = (engineType) => {
      const names = {
        'megatts3': 'MegaTTS3',
        'espnet': 'ESPnet',
        'edge': 'Edge TTS',
        'baidu': '百度语音',
        'xunfei': '讯飞语音'
      };
      return names[engineType] || engineType;
    };
    
    // 格式化时间
    const formatTime = (timestamp) => {
      if (!timestamp) return '未知';
      const date = new Date(timestamp * 1000);
      return date.toLocaleString();
    };
    
    // 显示任务详情
    const showDetails = (taskId) => {
      console.log('查看任务详情', taskId);
      // 实现任务详情查看功能（待实现）
    };
    
    // 获取状态颜色
    const getStatusColor = (status) => {
      const colors = {
        'pending': 'blue',
        'processing': 'orange',
        'completed': 'green',
        'failed': 'red'
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
      return texts[status] || status;
    };
    
    onMounted(async () => {
      await checkApiStatus();
      if (apiStatus.value) {
        await Promise.all([
          getSystemInfo(),
          getStats(),
          getRecentTasks(),
          checkEnginesHealth()
        ]);
      }
      
      // 定时刷新数据
      setInterval(async () => {
        await checkApiStatus();
        if (apiStatus.value) {
          await Promise.all([
            getSystemInfo(),
            getStats(),
            getRecentTasks(),
              checkEnginesHealth()
        ]);
        }
      }, 60000); // 每分钟刷新一次
    });
    
    return {
      apiStatus,
      loading,
      loadingEngines,
      systemInfo,
      stats,
      recentTasks,
      enginesHealth,
      columns,
      showDetails,
      getStatusColor,
      getStatusText,
      checkEnginesHealth,
      getEngineName,
      formatTime
    };
  }
});
</script>

<style scoped>
.dashboard {
  padding: 0 24px 24px;
}

.status-wrapper, .stats-wrapper {
  padding: 0 8px;
}

.status-item, .stats-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.status-content, .stats-content {
  margin-left: 16px;
  flex: 1;
}

.status-title, .stats-title {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
}

.status-value, .stats-value {
  font-size: 18px;
  font-weight: 500;
  margin-top: 4px;
}

.stats-value {
  font-size: 24px;
}

.status-ok {
  color: #52c41a;
}

.status-warning {
  color: #faad14;
}

.status-error {
  color: #f5222d;
}

.engine-card {
  margin-bottom: 16px;
}

.engine-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.engine-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 500;
}

.engine-title :deep(.anticon) {
  margin-right: 8px;
  font-size: 20px;
}

.engine-info {
  margin-top: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.info-label {
  color: rgba(0, 0, 0, 0.45);
}
</style> 