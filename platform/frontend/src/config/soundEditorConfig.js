import { 
  SoundOutlined, 
  PlusOutlined,
  ReloadOutlined,
  AppstoreOutlined,
  ClockCircleOutlined,
  DatabaseOutlined
} from '@ant-design/icons-vue'

/**
 * 合成中心项目状态选项
 */
export const PROJECT_STATUS_OPTIONS = [
  { value: 'pending', label: '待开始' },
  { value: 'processing', label: '处理中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' }
]

/**
 * 合成中心项目类型选项
 */
export const PROJECT_TYPE_OPTIONS = [
  { value: 'dialogue', label: '对话项目' },
  { value: 'environment', label: '环境音项目' },
  { value: 'music', label: '音乐项目' },
  { value: 'mixed', label: '混合项目' }
]

/**
 * 合成中心排序选项
 */
export const PROJECT_SORT_OPTIONS = [
  { value: 'created_at', label: '创建时间' },
  { value: 'updated_at', label: '更新时间' },
  { value: 'name', label: '项目名称' },
  { value: 'status', label: '状态' }
]

/**
 * 合成中心表格列配置
 */
export const PROJECT_TABLE_COLUMNS = [
  {
    title: '项目信息',
    dataIndex: 'name',
    key: 'name',
    width: '25%'
  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type',
    width: '15%'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: '15%'
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
    width: '25%'
  }
]

/**
 * 合成中心搜索筛选器配置
 */
export const PROJECT_SEARCH_FILTERS = [
  {
    key: 'type',
    type: 'select',
    placeholder: '项目类型',
    width: '150px',
    allowClear: true,
    options: PROJECT_TYPE_OPTIONS
  },
  {
    key: 'status',
    type: 'select',
    placeholder: '状态筛选',
    width: '120px',
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
 * 合成中心头部操作按钮配置
 */
export const PROJECT_HEADER_ACTIONS = [
  {
    key: 'create',
    text: '新建混合项目',
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
 * 合成中心默认搜索参数
 */
export const PROJECT_DEFAULT_SEARCH_PARAMS = {
  type: '',
  status: '',
  sort_by: 'created_at',
  sort_order: 'desc'
}

/**
 * 合成中心页面配置
 */
export const PROJECT_PAGE_CONFIG = {
  title: '合成中心',
  titleIcon: 'SoundOutlined',
  loadingTip: '加载项目中...',
  searchPlaceholder: '搜索项目名称...',
  emptyTitle: '暂无混合项目',
  emptyDescription: '创建您的第一个混合项目',
  emptyAction: { text: '立即创建', action: 'create' }
}

/**
 * 统计卡片配置
 */
export const PROJECT_STATS_CONFIG = [
  {
    key: 'total_projects',
    title: '总项目数',
    icon: AppstoreOutlined,
    type: 'total',
    color: '#1890ff',
    formatter: (value) => value
  },
  {
    key: 'completed_projects',
    title: '已完成',
    icon: SoundOutlined,
    type: 'completed',
    color: '#52c41a',
    formatter: (value) => value
  },
  {
    key: 'processing_projects',
    title: '处理中',
    icon: ClockCircleOutlined,
    type: 'processing',
    color: '#faad14',
    formatter: (value) => value
  },
  {
    key: 'failed_projects',
    title: '失败',
    icon: DatabaseOutlined,
    type: 'failed',
    color: '#ff4d4f',
    formatter: (value) => value
  }
]
