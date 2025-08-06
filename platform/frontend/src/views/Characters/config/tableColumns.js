import { h } from 'vue'

export const getTableColumns = (getStatusColor, getStatusText, getVoiceTypeLabel) => [
  {
    title: '角色名称',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    fixed: 'left'
  },
  {
    title: '声音类型',
    dataIndex: 'type',
    key: 'type',
    width: 100,
    customRender: ({ text }) => getVoiceTypeLabel(text)
  },
  {
    title: '质量评分',
    dataIndex: 'quality',
    key: 'quality',
    width: 120,
    customRender: ({ text }) => h('a-rate', { value: text, disabled: true, allowHalf: true })
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    customRender: ({ text }) => h('a-tag', { color: getStatusColor(text) }, () => getStatusText(text))
  },
  {
    title: '使用次数',
    dataIndex: 'usageCount',
    key: 'usageCount',
    width: 100,
    sorter: (a, b) => (a.usageCount || 0) - (b.usageCount || 0)
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 150,
    sorter: (a, b) => new Date(a.createdAt) - new Date(b.createdAt)
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right'
  }
] 