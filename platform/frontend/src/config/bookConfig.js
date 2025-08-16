import { PlusOutlined } from '@ant-design/icons-vue'

/**
 * 书籍状态选项
 */
export const BOOK_STATUS_OPTIONS = [
  { value: 'draft', label: '草稿' },
  { value: 'published', label: '已发布' },
  { value: 'archived', label: '已归档' }
]

/**
 * 书籍排序选项
 */
export const BOOK_SORT_OPTIONS = [
  { value: 'updated_at', label: '更新时间' },
  { value: 'created_at', label: '创建时间' },
  { value: 'title', label: '标题' },
  { value: 'word_count', label: '字数' }
]

/**
 * 书籍表格列配置
 */
export const BOOK_TABLE_COLUMNS = [
  {
    title: '书籍信息',
    dataIndex: 'title',
    key: 'title',
    width: '30%'
  },
  {
    title: '作者',
    dataIndex: 'author',
    key: 'author',
    width: '15%'
  },
  {
    title: '统计',
    dataIndex: 'stats',
    key: 'stats',
    width: '15%'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: '10%'
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
    width: '15%'
  }
]

/**
 * 书籍搜索筛选器配置
 */
export const BOOK_SEARCH_FILTERS = [
  {
    key: 'status',
    type: 'select',
    placeholder: '状态筛选',
    width: '120px',
    allowClear: true,
    options: BOOK_STATUS_OPTIONS
  },
  {
    key: 'author',
    type: 'input',
    placeholder: '作者筛选',
    width: '150px'
  },
  {
    key: 'sort_by',
    type: 'select',
    placeholder: '排序方式',
    width: '120px',
    options: BOOK_SORT_OPTIONS
  }
]

/**
 * 书籍头部操作按钮配置
 */
export const BOOK_HEADER_ACTIONS = [
  {
    key: 'create',
    text: '新建书籍',
    type: 'primary',
    icon: PlusOutlined,
    action: 'create'
  }
]

/**
 * 书籍默认搜索参数
 */
export const BOOK_DEFAULT_SEARCH_PARAMS = {
  status: '',
  author: '',
  tags: '',
  sort_by: 'updated_at',
  sort_order: 'desc'
}

/**
 * 书籍页面配置
 */
export const BOOK_PAGE_CONFIG = {
  title: '书籍列表',
  titleIcon: 'BookOutlined',
  loadingTip: '加载书籍中...',
  searchPlaceholder: '搜索书籍标题、作者...',
  emptyTitle: '暂无书籍',
  emptyDescription: '创建您的第一本书籍',
  emptyAction: { text: '立即创建', action: 'create' }
}
