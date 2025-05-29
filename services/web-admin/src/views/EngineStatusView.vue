<template>
  <div class="engine-status-container">
    <a-card title="引擎状态监控" class="main-card">
      <template #extra>
        <a-space>
          <a-button type="primary" @click="refreshEngines" :loading="loading">
            <template #icon><ReloadOutlined /></template>
            刷新状态
          </a-button>
          <a-button @click="showAddEngineModal">
            <template #icon><PlusOutlined /></template>
            添加引擎
          </a-button>
        </a-space>
      </template>

      <!-- 引擎概览统计 -->
      <a-row :gutter="16" class="stats-row">
        <a-col :span="6">
          <a-statistic
            title="总引擎数"
            :value="engineStats.total"
            :value-style="{ color: '#1890ff' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="在线引擎"
            :value="engineStats.online"
            :value-style="{ color: '#52c41a' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="离线引擎"
            :value="engineStats.offline"
            :value-style="{ color: '#ff4d4f' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="错误引擎"
            :value="engineStats.error"
            :value-style="{ color: '#faad14' }"
          />
        </a-col>
      </a-row>

      <!-- 引擎列表 -->
      <a-table
        :columns="columns"
        :data-source="engines"
        :loading="loading"
        row-key="id"
        class="engine-table"
        :pagination="{ pageSize: 10 }"
      >
        <!-- 引擎类型 -->
        <template #engineType="{ record }">
          <a-tag :color="getEngineTypeColor(record.engine_type)">
            {{ getEngineTypeName(record.engine_type) }}
          </a-tag>
        </template>

        <!-- 状态 -->
        <template #status="{ record }">
          <a-badge
            :status="getStatusBadge(record.status)"
            :text="getStatusText(record.status)"
          />
        </template>

        <!-- 健康状态 -->
        <template #health="{ record }">
          <a-tooltip :title="record.health_info?.message || '无详细信息'">
            <a-tag :color="getHealthColor(record.health_status)">
              {{ getHealthText(record.health_status) }}
            </a-tag>
          </a-tooltip>
        </template>

        <!-- 最后检查时间 -->
        <template #lastCheck="{ record }">
          <span v-if="record.last_health_check">
            {{ formatTime(record.last_health_check) }}
          </span>
          <span v-else class="text-muted">从未检查</span>
        </template>

        <!-- 操作 -->
        <template #action="{ record }">
          <a-space>
            <a-button
              type="link"
              size="small"
              @click="checkEngineHealth(record.id)"
              :loading="checkingHealth[record.id]"
            >
              检查健康
            </a-button>
            <a-button
              type="link"
              size="small"
              @click="showEngineConfig(record)"
            >
              配置
            </a-button>
            <a-dropdown>
              <template #overlay>
                <a-menu>
                  <a-menu-item @click="editEngine(record)">
                    <EditOutlined /> 编辑
                  </a-menu-item>
                  <a-menu-item @click="restartEngine(record.id)">
                    <ReloadOutlined /> 重启
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item @click="deleteEngine(record)" danger>
                    <DeleteOutlined /> 删除
                  </a-menu-item>
                </a-menu>
              </template>
              <a-button type="link" size="small">
                更多 <DownOutlined />
              </a-button>
            </a-dropdown>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <!-- 添加引擎模态框 -->
    <a-modal
      v-model:open="addEngineVisible"
      title="添加引擎"
      @ok="handleAddEngine"
      @cancel="resetAddEngineForm"
      :confirm-loading="addingEngine"
    >
      <a-form
        ref="addEngineFormRef"
        :model="addEngineForm"
        :rules="addEngineRules"
        layout="vertical"
      >
        <a-form-item label="引擎名称" name="name">
          <a-input v-model:value="addEngineForm.name" placeholder="请输入引擎名称" />
        </a-form-item>
        
        <a-form-item label="引擎类型" name="engine_type">
          <a-select v-model:value="addEngineForm.engine_type" placeholder="请选择引擎类型">
            <a-select-option value="megatts3">MegaTTS3</a-select-option>
            <a-select-option value="espnet">ESPnet</a-select-option>
            <a-select-option value="bert_vits2">Bert-VITS2</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="引擎URL" name="url">
          <a-input v-model:value="addEngineForm.url" placeholder="http://localhost:7860" />
        </a-form-item>

        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="addEngineForm.description" placeholder="引擎描述（可选）" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 引擎配置模态框 -->
    <a-modal
      v-model:open="configVisible"
      title="引擎配置"
      width="800px"
      @ok="saveEngineConfig"
      @cancel="configVisible = false"
      :confirm-loading="savingConfig"
    >
      <a-form
        v-if="currentEngine"
        :model="currentEngine.config"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="最大并发数">
              <a-input-number
                v-model:value="currentEngine.config.max_concurrent"
                :min="1"
                :max="10"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="超时时间(秒)">
              <a-input-number
                v-model:value="currentEngine.config.timeout"
                :min="10"
                :max="300"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="其他配置">
          <a-textarea
            v-model:value="configJsonStr"
            placeholder="JSON格式的其他配置参数"
            :rows="6"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DownOutlined
} from '@ant-design/icons-vue'
import { engineAPI } from '../services/api'
import { wsService } from '../services/websocket'

// 响应式数据
const loading = ref(false)
const engines = ref([])
const checkingHealth = ref({})
const addEngineVisible = ref(false)
const addingEngine = ref(false)
const configVisible = ref(false)
const savingConfig = ref(false)
const currentEngine = ref(null)
const configJsonStr = ref('')

// 添加引擎表单
const addEngineFormRef = ref()
const addEngineForm = reactive({
  name: '',
  engine_type: '',
  url: '',
  description: ''
})

const addEngineRules = {
  name: [{ required: true, message: '请输入引擎名称' }],
  engine_type: [{ required: true, message: '请选择引擎类型' }],
  url: [{ required: true, message: '请输入引擎URL' }]
}

// 表格列定义
const columns = [
  {
    title: '引擎名称',
    dataIndex: 'name',
    key: 'name',
    width: 150
  },
  {
    title: '引擎类型',
    dataIndex: 'engine_type',
    key: 'engine_type',
    slots: { customRender: 'engineType' },
    width: 120
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    slots: { customRender: 'status' },
    width: 100
  },
  {
    title: '健康状态',
    dataIndex: 'health_status',
    key: 'health_status',
    slots: { customRender: 'health' },
    width: 120
  },
  {
    title: 'URL',
    dataIndex: 'url',
    key: 'url',
    ellipsis: true
  },
  {
    title: '最后检查',
    dataIndex: 'last_health_check',
    key: 'last_health_check',
    slots: { customRender: 'lastCheck' },
    width: 150
  },
  {
    title: '操作',
    key: 'action',
    slots: { customRender: 'action' },
    width: 200,
    fixed: 'right'
  }
]

// 计算属性 - 引擎统计
const engineStats = computed(() => {
  const stats = {
    total: engines.value.length,
    online: 0,
    offline: 0,
    error: 0
  }
  
  engines.value.forEach(engine => {
    if (engine.status === 'healthy' || engine.health_status === 'healthy') {
      stats.online++
    } else if (engine.status === 'unhealthy' || engine.status === 'stopped') {
      stats.offline++
    } else {
      stats.error++
    }
  })
  
  return stats
})

// 方法
const refreshEngines = async () => {
  loading.value = true
  try {
    const response = await engineAPI.getEngines()
    // axios拦截器已经处理了API响应格式，直接使用原来的逻辑
    const rawEngines = response.data?.engines || []
    engines.value = rawEngines.map(engine => ({
      ...engine,
      engine_type: engine.type || 'espnet', // 映射 type 到 engine_type
      health_status: engine.status === 'healthy' ? 'healthy' : 'unknown', // 映射状态
      url: engine.config?.endpoint || 'N/A', // 从配置中获取URL
      last_health_check: engine.last_health_check || engine.updated_at
    }))
    message.success('引擎列表刷新成功')
  } catch (error) {
    console.error('获取引擎列表失败:', error)
    message.error('获取引擎列表失败: ' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

const checkEngineHealth = async (engineId) => {
  checkingHealth.value[engineId] = true
  try {
    await engineAPI.checkHealth(engineId)
    message.success('健康检查完成')
    await refreshEngines()
  } catch (error) {
    console.error('健康检查失败:', error)
    message.error('健康检查失败: ' + (error.response?.data?.message || error.message))
  } finally {
    checkingHealth.value[engineId] = false
  }
}

const showAddEngineModal = () => {
  addEngineVisible.value = true
}

const resetAddEngineForm = () => {
  addEngineFormRef.value?.resetFields()
  Object.assign(addEngineForm, {
    name: '',
    engine_type: '',
    url: '',
    description: ''
  })
  addEngineVisible.value = false
}

const handleAddEngine = async () => {
  try {
    await addEngineFormRef.value.validate()
    addingEngine.value = true
    
    await engineAPI.createEngine(addEngineForm)
    message.success('引擎添加成功')
    resetAddEngineForm()
    await refreshEngines()
  } catch (error) {
    if (error.errorFields) {
      return // 表单验证错误
    }
    console.error('添加引擎失败:', error)
    message.error('添加引擎失败: ' + (error.response?.data?.message || error.message))
  } finally {
    addingEngine.value = false
  }
}

const showEngineConfig = (engine) => {
  currentEngine.value = { ...engine }
  configJsonStr.value = JSON.stringify(engine.config || {}, null, 2)
  configVisible.value = true
}

const saveEngineConfig = async () => {
  try {
    savingConfig.value = true
    
    // 解析JSON配置
    let additionalConfig = {}
    if (configJsonStr.value.trim()) {
      additionalConfig = JSON.parse(configJsonStr.value)
    }
    
    const config = {
      ...currentEngine.value.config,
      ...additionalConfig
    }
    
    await engineAPI.updateConfig(currentEngine.value.id, config)
    message.success('配置保存成功')
    configVisible.value = false
    await refreshEngines()
  } catch (error) {
    console.error('保存配置失败:', error)
    message.error('保存配置失败: ' + (error.response?.data?.message || error.message))
  } finally {
    savingConfig.value = false
  }
}

const editEngine = (engine) => {
  // TODO: 实现编辑引擎功能
  message.info('编辑功能开发中...')
}

const restartEngine = async (engineId) => {
  try {
    await engineAPI.restartEngine(engineId)
    message.success('引擎重启成功')
    await refreshEngines()
  } catch (error) {
    console.error('重启引擎失败:', error)
    message.error('重启引擎失败: ' + (error.response?.data?.message || error.message))
  }
}

const deleteEngine = (engine) => {
  // TODO: 实现删除引擎功能
  message.info('删除功能开发中...')
}

// 工具方法
const getEngineTypeColor = (type) => {
  const colors = {
    megatts3: 'blue',
    espnet: 'green',
    bert_vits2: 'orange'
  }
  return colors[type] || 'default'
}

const getEngineTypeName = (type) => {
  const names = {
    megatts3: 'MegaTTS3',
    espnet: 'ESPnet',
    bert_vits2: 'Bert-VITS2'
  }
  return names[type] || type
}

const getStatusBadge = (status) => {
  const badges = {
    healthy: 'processing',
    unhealthy: 'error',
    ready: 'processing',
    running: 'processing', 
    stopped: 'default',
    error: 'error'
  }
  return badges[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    healthy: '健康',
    unhealthy: '不健康',
    ready: '就绪',
    running: '运行中',
    stopped: '已停止',
    error: '错误'
  }
  return texts[status] || status
}

const getHealthColor = (health) => {
  const colors = {
    healthy: 'success',
    unhealthy: 'error',
    unknown: 'warning'
  }
  return colors[health] || 'default'
}

const getHealthText = (health) => {
  const texts = {
    healthy: '健康',
    unhealthy: '不健康',
    unknown: '未知'
  }
  return texts[health] || health
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString('zh-CN')
}

// WebSocket事件处理
const handleEngineStatusUpdate = (data) => {
  const { engine_id, status, health_status, health_info } = data
  const engineIndex = engines.value.findIndex(e => e.id === engine_id)
  if (engineIndex > -1) {
    engines.value[engineIndex] = {
      ...engines.value[engineIndex],
      status,
      health_status,
      health_info,
      last_health_check: new Date().toISOString()
    }
  }
}

// 生命周期
onMounted(() => {
  refreshEngines()
  
  // 连接WebSocket
  if (!wsService.isConnected()) {
    wsService.connect()
  }
  
  // 监听引擎状态更新
  wsService.on('engineStatusUpdate', handleEngineStatusUpdate)
  wsService.on('connected', () => {
    wsService.subscribeEngineStatus()
  })
})

// 组件卸载时清理
onUnmounted(() => {
  wsService.off('engineStatusUpdate', handleEngineStatusUpdate)
})
</script>

<style scoped>
.engine-status-container {
  padding: 24px;
}

.main-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stats-row {
  margin-bottom: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.engine-table {
  margin-top: 16px;
}

.text-muted {
  color: #999;
}

:deep(.ant-table-thead > tr > th) {
  background: #fafafa;
  font-weight: 600;
}

:deep(.ant-statistic-title) {
  font-size: 14px;
  color: #666;
}

:deep(.ant-statistic-content) {
  font-size: 24px;
  font-weight: 600;
}
</style>