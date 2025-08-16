import { 
  SoundOutlined, 
  PlusOutlined, 
  ReloadOutlined,
  AppstoreOutlined,
  ClockCircleOutlined,
  DatabaseOutlined
} from '@ant-design/icons-vue'

/**
 * 背景音乐状态选项
 */
export const MUSIC_STATUS_OPTIONS = [
  { value: 'completed', label: '已完成' },
  { value: 'processing', label: '处理中' },
  { value: 'failed', label: '失败' }
]

/**
 * 背景音乐排序选项
 */
export const MUSIC_SORT_OPTIONS = [
  { value: 'created_at', label: '创建时间' },
  { value: 'updated_at', label: '更新时间' },
  { value: 'name', label: '音乐名称' },
  { value: 'duration', label: '时长' },
  { value: 'file_size', label: '文件大小' }
]

/**
 * 背景音乐表格列配置
 */
export const MUSIC_TABLE_COLUMNS = [
  {
    title: '音乐信息',
    dataIndex: 'name',
    key: 'name',
    width: '25%'
  },
  {
    title: '分类',
    dataIndex: 'category',
    key: 'category',
    width: '15%'
  },
  {
    title: '时长',
    dataIndex: 'duration',
    key: 'duration',
    width: '15%'
  },
  {
    title: '文件大小',
    dataIndex: 'file_size',
    key: 'file_size',
    width: '15%'
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: '15%'
  },
  {
    title: '操作',
    dataIndex: 'actions',
    key: 'actions',
    width: '15%'
  }
]

/**
 * 背景音乐搜索筛选器配置
 */
export const MUSIC_SEARCH_FILTERS = [
  {
    key: 'category_id',
    type: 'select',
    placeholder: '分类筛选',
    width: '120px',
    allowClear: true,
    options: [] // 动态加载分类选项
  },
  {
    key: 'status',
    type: 'select',
    placeholder: '状态筛选',
    width: '120px',
    allowClear: true,
    options: MUSIC_STATUS_OPTIONS
  },
  {
    key: 'sort_by',
    type: 'select',
    placeholder: '排序方式',
    width: '120px',
    options: MUSIC_SORT_OPTIONS
  }
]

/**
 * 背景音乐头部操作按钮配置
 */
export const MUSIC_HEADER_ACTIONS = [
  {
    key: 'generate',
    text: '合成音乐',
    type: 'primary',
    icon: SoundOutlined,
    action: 'generate'
  },
  {
    key: 'upload',
    text: '上传音乐',
    type: 'default',
    icon: PlusOutlined,
    action: 'upload'
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
 * 背景音乐默认搜索参数
 */
export const MUSIC_DEFAULT_SEARCH_PARAMS = {
  category_id: '',
  status: '',
  sort_by: 'created_at',
  sort_order: 'desc'
}

/**
 * 背景音乐页面配置
 */
export const MUSIC_PAGE_CONFIG = {
  title: '背景音效',
  titleIcon: 'SoundOutlined',
  loadingTip: '加载音乐列表中...',
  searchPlaceholder: '搜索音乐名称...',
  emptyTitle: '暂无背景音乐',
  emptyDescription: '创建您的第一首背景音乐',
  emptyAction: { text: '立即创建', action: 'generate' }
}

/**
 * 统计卡片配置
 */
export const MUSIC_STATS_CONFIG = [
  {
    key: 'total_music',
    title: '总音乐数',
    icon: SoundOutlined,
    type: 'total',
    color: '#1890ff',
    formatter: (value) => value
  },
  {
    key: 'total_categories',
    title: '音乐分类',
    icon: AppstoreOutlined,
    type: 'completed',
    color: '#52c41a',
    formatter: (value) => value
  },
  {
    key: 'total_duration',
    title: '总时长',
    icon: ClockCircleOutlined,
    type: 'processing',
    color: '#faad14',
    formatter: (value) => value
  },
  {
    key: 'total_size',
    title: '总大小',
    icon: DatabaseOutlined,
    type: 'default',
    color: '#722ed1',
    formatter: (value) => value
  }
]
