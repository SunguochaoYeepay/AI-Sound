import { BulbOutlined } from '@ant-design/icons-vue'

/**
 * 环境音项目状态选项
 */
export const ENVIRONMENT_PROJECT_STATUS_OPTIONS = [
  { value: 'pending', label: '待处理' },
  { value: 'processing', label: '处理中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' }
]

/**
 * 环境音项目排序选项
 */
export const ENVIRONMENT_PROJECT_SORT_OPTIONS = [
  { value: 'created_at', label: '创建时间' },
  { value: 'updated_at', label: '更新时间' },
  { value: 'name', label: '项目名称' },
  { value: 'status', label: '状态' }
]

/**
 * 环境音项目表格列配置
 */
export const ENVIRONMENT_PROJECT_TABLE_COLUMNS = [
  {
    title: '项目信息',
    dataIndex: 'name',
    key: 'name',
    width: '30%'
  },
  {
    title: '书籍',
    dataIndex: 'book',
    key: 'book',
    width: '20%'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: '15%'
  },
  {
    title: '生成数量',
    dataIndex: 'soundCount',
    key: 'soundCount',
    width: '15%'
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: '15%'
  },
  {
    title: '操作',
    dataIndex: 'actions',
    key: 'actions',
    width: '20%',
    fixed: 'right'
  }
]

/**
 * 环境音项目搜索筛选器配置
 */
export const ENVIRONMENT_PROJECT_SEARCH_FILTERS = [
  {
    key: 'status',
    type: 'select',
    placeholder: '状态筛选',
    width: '120px',
    allowClear: true,
    options: ENVIRONMENT_PROJECT_STATUS_OPTIONS
  },
  {
    key: 'sort_by',
    type: 'select',
    placeholder: '排序方式',
    width: '120px',
    options: ENVIRONMENT_PROJECT_SORT_OPTIONS
  }
]

/**
 * 环境音项目头部操作按钮配置
 */
export const ENVIRONMENT_PROJECT_HEADER_ACTIONS = [
  {
    key: 'create',
    text: '新建环境音分析',
    type: 'primary',
    icon: BulbOutlined,
    action: 'create'
  }
]

/**
 * 环境音项目默认搜索参数
 */
export const ENVIRONMENT_PROJECT_DEFAULT_SEARCH_PARAMS = {
  status: '',
  sort_by: 'created_at',
  sort_order: 'desc'
}

/**
 * 环境音项目页面配置
 */
export const ENVIRONMENT_PROJECT_PAGE_CONFIG = {
  title: '环境音合成',
  titleIcon: 'SoundOutlined',
  loadingTip: '加载环境音项目中...',
  searchPlaceholder: '搜索项目名称...',
  emptyTitle: '暂无环境音项目',
  emptyDescription: '创建您的第一个环境音分析项目',
  emptyAction: { text: '立即创建', action: 'create' }
}
