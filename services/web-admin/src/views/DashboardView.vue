<template>
  <div class="dashboard">
    <page-header title="系统控制台" subtitle="MegaTTS3 系统状态与任务监控" />
    
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
import { useApiStore } from '@/store/api';
import PageHeader from '@/components/common/PageHeader.vue';
import { 
  DashboardOutlined, 
  RocketOutlined, 
  HddOutlined,
  SoundOutlined,
  ReadOutlined,
  LoadingOutlined
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
    LoadingOutlined
  },
  setup() {
    const apiStore = useApiStore();
    const apiStatus = ref(false);
    const loading = ref(false);
    
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
        const result = await apiStore.checkHealth();
        apiStatus.value = result.status === 'ok';
      } catch (error) {
        apiStatus.value = false;
        console.error('API状态检查失败', error);
      } finally {
        loading.value = false;
      }
    };
    
    // 获取系统信息
    const getSystemInfo = async () => {
      loading.value = true;
      try {
        systemInfo.value = await apiStore.getSystemInfo();
      } catch (error) {
        console.error('获取系统信息失败', error);
      } finally {
        loading.value = false;
      }
    };
    
    // 获取统计信息
    const getStats = async () => {
      loading.value = true;
      try {
        stats.value = await apiStore.getStats();
      } catch (error) {
        console.error('获取统计信息失败', error);
      } finally {
        loading.value = false;
      }
    };
    
    // 获取最近任务
    const getRecentTasks = async () => {
      loading.value = true;
      try {
        recentTasks.value = await apiStore.getRecentTasks(5);
      } catch (error) {
        console.error('获取最近任务失败', error);
      } finally {
        loading.value = false;
      }
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
          getRecentTasks()
        ]);
      }
      
      // 定时刷新数据
      setInterval(async () => {
        await checkApiStatus();
        if (apiStatus.value) {
          await Promise.all([
            getSystemInfo(),
            getStats(),
            getRecentTasks()
          ]);
        }
      }, 60000); // 每分钟刷新一次
    });
    
    return {
      apiStatus,
      loading,
      systemInfo,
      stats,
      recentTasks,
      columns,
      showDetails,
      getStatusColor,
      getStatusText
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
</style> 