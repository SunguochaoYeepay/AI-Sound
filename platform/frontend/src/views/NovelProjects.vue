<template>
  <PageContainer
    title="对话音合成"
    title-icon="SoundOutlined"
    :data="filteredProjects"
    :loading="loading"
    loading-tip="加载项目中..."
    
    :search-value="searchParams.search"
    search-placeholder="搜索项目名称..."
    :filters="searchFilters"
    :actions="headerActions"
    :table-columns="tableColumns"
    :show-pagination="true"
    :pagination="pagination"
    empty-title="暂无项目"
    empty-description="创建您的第一个语音合成项目"
    :empty-action="{ text: '立即创建', action: 'create' }"
    
    @search="handleSearch"
    @filter-change="handleFilterChange"
    @refresh="loadProjects"
    @action="handleAction"
    
    @item-click="openProject"
    @edit="openProject"
    @view="openProject"
    @delete="handleDeleteProject"
    @empty-action="goToCreatePage"
    @page-change="handlePageChange"
  >
    <!-- 自定义表格视图 -->
    <template #table-name="{ record }">
      <div style="display: flex; align-items: center; gap: 12px">
        <div class="table-avatar">
          {{ record.name ? record.name.charAt(0) : '项' }}
        </div>
        <div>
          <div style="font-weight: 500">{{ record.name }}</div>
          <div style="font-size: 12px; color: #6b7280">{{ record.description || '暂无描述' }}</div>
        </div>
      </div>
    </template>

    <template #table-status="{ record }">
      <a-tag :color="getStatusColor(record.status)">
        {{ getStatusText(record.status) }}
      </a-tag>
    </template>

    <template #table-progress="{ record }">
      <div style="display: flex; align-items: center; gap: 8px">
        <a-progress 
          :percent="getProgressPercent(record)" 
          :status="getProgressStatus(record)"
          size="small"
          style="flex: 1"
        />
        <span style="font-size: 12px; color: #6b7280">{{ getProgressText(record) }}</span>
      </div>
    </template>

    <template #table-created_at="{ record }">
      {{ formatDate(record.created_at) }}
    </template>

    <template #table-actions="{ record }">
      <TableActions
        :record="record"
        :show-edit="true"
        :show-view="true"
        :show-delete="true"
        @edit="openProject"
        @view="openProject"
        @delete="handleDeleteProject"
      />
    </template>
  </PageContainer>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { message, Modal } from 'ant-design-vue'
  import { readerAPI } from '@/api'
  import PageContainer from '@/components/common/PageContainer.vue'
  import TableActions from '@/components/common/TableActions.vue'
  import { useErrorHandler } from '@/composables/useErrorHandler'
  import { getStatusColor, getStatusText, formatDate } from '@/utils/formatters'
  import {
    PROJECT_TABLE_COLUMNS,
    PROJECT_SEARCH_FILTERS,
    PROJECT_HEADER_ACTIONS,
    PROJECT_DEFAULT_SEARCH_PARAMS
  } from '@/config/novelProjectsConfig'

  const router = useRouter()
  const { handleApiError } = useErrorHandler()

  // 响应式数据
  const loading = ref(false)
  const projects = ref([])

  // 搜索和筛选参数
  const searchParams = ref({ ...PROJECT_DEFAULT_SEARCH_PARAMS })
  const searchFilters = PROJECT_SEARCH_FILTERS
  const headerActions = PROJECT_HEADER_ACTIONS
  const tableColumns = PROJECT_TABLE_COLUMNS

  // 分页状态
  const pagination = ref({
    current: 1,
    pageSize: 12,
    total: 0,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
  })

  // 过滤后的项目列表
  const filteredProjects = computed(() => {
    let filtered = [...projects.value]

    // 搜索过滤
    if (searchParams.value.search) {
      const keyword = searchParams.value.search.toLowerCase()
      filtered = filtered.filter(
        (project) =>
          project.name.toLowerCase().includes(keyword) ||
          (project.description && project.description.toLowerCase().includes(keyword))
      )
    }

    // 状态过滤
    if (searchParams.value.status) {
      filtered = filtered.filter((project) => project.status === searchParams.value.status)
    }

    // 排序
    if (searchParams.value.sort_by) {
      filtered.sort((a, b) => {
        const aValue = a[searchParams.value.sort_by]
        const bValue = b[searchParams.value.sort_by]
        if (searchParams.value.sort_order === 'desc') {
          return bValue > aValue ? 1 : -1
        } else {
          return aValue > bValue ? 1 : -1
        }
      })
    }

    return filtered
  })

  // 页面加载
  onMounted(() => {
    loadProjects()
  })

  // 事件处理方法
  const handleSearch = (value) => {
    searchParams.value.search = value
    loadProjects()
  }

  const handleFilterChange = (filters) => {
    Object.assign(searchParams.value, filters)
    loadProjects()
  }

  const handleAction = (action) => {
    switch (action.action) {
      case 'create':
        goToCreatePage()
        break
      case 'refresh':
        loadProjects()
        break
    }
  }

  const handlePageChange = (page, pageSize) => {
    pagination.value.current = page
    pagination.value.pageSize = pageSize
    loadProjects()
  }

  // 加载项目列表
  const loadProjects = async () => {
    loading.value = true
    try {
      const response = await readerAPI.getProjects({
        page: 1,
        page_size: 100
      })

      if (response.data.success) {
        const projectList = response.data.data?.projects || []
        projects.value = Array.isArray(projectList) ? projectList : []
        pagination.value.total = projects.value.length
      } else {
        message.error('获取项目列表失败: ' + response.data.message)
      }
    } catch (error) {
      handleApiError(error, '获取项目列表')
    } finally {
      loading.value = false
    }
  }



  // 跳转到创建页面
  const goToCreatePage = () => {
    router.push('/novel-reader/create')
  }

  // 打开项目
  const openProject = (project) => {
    console.log('打开项目:', project.name, '项目ID:', project.id)
    router.push(`/synthesis/${project.id}`)
  }

  // 删除项目
  const handleDeleteProject = (project) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除项目 "${project.name}" 吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await readerAPI.deleteProject(project.id)
          message.success('项目删除成功')
          loadProjects()
        } catch (error) {
          handleApiError(error, '删除项目')
        }
      }
    })
  }

  // 工具函数
  const isProjectCompleted = (project) => {
    return project.status === 'completed' || 
           (project.audio_files && project.audio_files.length > 0 && 
            project.audio_files.every(file => file.status === 'completed'))
  }

  const hasAudioFiles = (project) => {
    return project.audio_files && project.audio_files.length > 0
  }

  const getProgressPercent = (project) => {
    if (isProjectCompleted(project)) return 100
    if (project.status === 'processing') return 50
    if (hasAudioFiles(project)) return 30
    return 0
  }

  const getProgressStatus = (project) => {
    if (isProjectCompleted(project)) return 'success'
    if (project.status === 'processing') return 'active'
    if (project.status === 'failed') return 'exception'
    return 'normal'
  }

  const getProgressText = (project) => {
    if (isProjectCompleted(project)) return '已完成'
    if (project.status === 'processing') return '处理中'
    if (hasAudioFiles(project)) return '部分完成'
    return '待处理'
  }
</script>

<style scoped>
  .table-avatar {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 16px;
  }
</style>
