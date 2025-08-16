import { 
  SoundOutlined, 
  PlusOutlined,
  ReloadOutlined,
  AppstoreOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  StarOutlined
} from '@ant-design/icons-vue'

/**
 * 对话音合成项目状态选项
 */
export const PROJECT_STATUS_OPTIONS = [
  { value: 'pending', label: '待处理' },
  { value: 'processing', label: '处理中' },
  { value: 'completed', label: '已完成' },
  { value: 'partial_completed', label: '部分完成' },
  { value: 'failed', label: '失败' }
]

/**
 * 对话音合成排序选项
 */
export const PROJECT_SORT_OPTIONS = [
  { value: 'created_at', label: '创建时间' },
  { value: 'updated_at', label: '更新时间' },
  { value: 'name', label: '项目名称' },
  { value: 'status', label: '状态' }
]

/**
 * 对话音合成表格列配置
 */
export const PROJECT_TABLE_COLUMNS = [
  {
    title: '项目信息',
    dataIndex: 'name',
    key: 'name',
    width: '25%'
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
    width: '20%'
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: '20%'
  },
  {
    title: '操作',
    dataIndex: 'actions',
    key: 'actions',
    width: '20%'
  }
]

/**
 * 对话音合成搜索筛选器配置
 */
export const PROJECT_SEARCH_FILTERS = [
  {
    key: 'status',
    type: 'select',
    placeholder: '项目状态',
    width: '130px',
    allowClear: true,
    options: PROJECT_STATUS_OPTIONS
  },
  {
    key: 'sort_by',
    type: 'select',
    placeholder: '排序方式',
    width: '120px',
    options: PROJECT_SORT_OPTIONS
  }
]

/**
 * 对话音合成头部操作按钮配置
 */
export const PROJECT_HEADER_ACTIONS = [
  {
    key: 'create',
    text: '新建项目',
    type: 'primary',
    icon: PlusOutlined,
    action: 'create'
  },
  {
    key: 'refresh',
    text: '刷新',
    type: 'default',
    icon: ReloadOutlined,
    action: 'refresh'
  }
]

/**
 * 对话音合成默认搜索参数
 */
export const PROJECT_DEFAULT_SEARCH_PARAMS = {
  status: '',
  sort_by: 'created_at',
  sort_order: 'desc'
}

/**
 * 对话音合成页面配置
 */
export const PROJECT_PAGE_CONFIG = {
  title: '对话音合成',
  titleIcon: 'SoundOutlined',
  loadingTip: '加载项目中...',
  searchPlaceholder: '搜索项目名称...',
  emptyTitle: '暂无项目',
  emptyDescription: '创建您的第一个语音合成项目',
  emptyAction: { text: '立即创建', action: 'create' }
}

/**
 * 统计卡片配置
 */
export const PROJECT_STATS_CONFIG = [
  {
    key: 'total',
    title: '总项目',
    icon: AppstoreOutlined,
    type: 'total',
    color: '#06b6d4',
    formatter: (value) => value
  },
  {
    key: 'completed',
    title: '已完成',
    icon: CheckCircleOutlined,
    type: 'completed',
    color: '#10b981',
    formatter: (value) => value
  },
  {
    key: 'processing',
    title: '处理中',
    icon: ClockCircleOutlined,
    type: 'processing',
    color: '#f59e0b',
    formatter: (value) => value
  },
  {
    key: 'partialCompleted',
    title: '部分完成',
    icon: StarOutlined,
    type: 'partial',
    color: '#eab308',
    formatter: (value) => value
  },
  {
    key: 'pending',
    title: '待处理',
    icon: DatabaseOutlined,
    type: 'pending',
    color: '#ef4444',
    formatter: (value) => value
  }
]
