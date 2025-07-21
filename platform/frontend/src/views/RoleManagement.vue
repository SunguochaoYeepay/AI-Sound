<template>
  <div class="role-management-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <TeamOutlined class="title-icon" />
            角色管理
          </h1>
          <p class="page-description">管理系统角色权限，配置用户访问控制</p>
        </div>
        <div class="action-section">
          <a-button type="primary" size="large" @click="showCreateModal = true">
            <template #icon>
              <PlusOutlined />
            </template>
            新建角色
          </a-button>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索角色名称、描述"
            @search="handleSearch"
            style="width: 100%"
          />
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="statusFilter"
            placeholder="状态筛选"
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="active">启用</a-select-option>
            <a-select-option value="inactive">禁用</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button @click="resetFilters">重置</a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 角色列表 -->
    <div class="table-section">
      <a-table
        :columns="columns"
        :data-source="filteredRoles"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="role-info">
              <div class="role-name">{{ record.display_name }}</div>
              <div class="role-code">{{ record.name }}</div>
            </div>
          </template>

          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'active' ? 'green' : 'red'">
              {{ record.status === 'active' ? '启用' : '禁用' }}
            </a-tag>
          </template>

          <template v-if="column.key === 'permissions'">
            <div class="permissions-container">
              <a-tag
                v-for="permission in record.permissions.slice(0, 3)"
                :key="permission.name"
                color="blue"
                style="margin-bottom: 4px"
              >
                {{ permission.display_name }}
              </a-tag>
              <a-tag v-if="record.permissions.length > 3" color="default">
                +{{ record.permissions.length - 3 }}
              </a-tag>
            </div>
          </template>

          <template v-if="column.key === 'user_count'">
            <a-badge :count="record.user_count" :number-style="{ backgroundColor: '#52c41a' }" />
          </template>

          <template v-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                type="link"
                size="small"
                @click="editRole(record)"
                :disabled="record.name === 'admin' && !currentUser.is_superuser"
              >
                编辑
              </a-button>
              <a-button type="link" size="small" @click="managePermissions(record)">
                权限管理
              </a-button>
              <a-popconfirm
                title="确定要删除这个角色吗？"
                @confirm="deleteRole(record)"
                :disabled="record.name === 'admin' || record.user_count > 0"
              >
                <a-button
                  type="link"
                  size="small"
                  danger
                  :disabled="record.name === 'admin' || record.user_count > 0"
                >
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 创建/编辑角色弹窗 -->
    <a-modal
      v-model:open="showCreateModal"
      :title="editingRole ? '编辑角色' : '新建角色'"
      width="600px"
      @ok="handleSubmit"
      @cancel="handleCancel"
      :confirm-loading="submitting"
    >
      <a-form ref="formRef" :model="roleForm" :rules="formRules" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="角色标识" name="name">
              <a-input
                v-model:value="roleForm.name"
                placeholder="请输入角色标识"
                :disabled="!!editingRole"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="角色名称" name="display_name">
              <a-input v-model:value="roleForm.display_name" placeholder="请输入角色名称" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="角色描述" name="description">
          <a-textarea v-model:value="roleForm.description" placeholder="请输入角色描述" :rows="3" />
        </a-form-item>

        <a-form-item label="状态" name="status">
          <a-select v-model:value="roleForm.status" placeholder="选择状态">
            <a-select-option value="active">启用</a-select-option>
            <a-select-option value="inactive">禁用</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="权限配置" name="permissions">
          <div class="permissions-config">
            <div v-for="group in permissionGroups" :key="group.name" class="permission-group">
              <div class="group-header">
                <a-checkbox
                  :checked="isGroupSelected(group)"
                  :indeterminate="isGroupIndeterminate(group)"
                  @change="toggleGroup(group)"
                >
                  {{ group.display_name }}
                </a-checkbox>
              </div>
              <div class="group-permissions">
                <a-checkbox-group v-model:value="roleForm.permissions" style="width: 100%">
                  <a-row>
                    <a-col
                      v-for="permission in group.permissions"
                      :key="permission.name"
                      :span="12"
                    >
                      <a-checkbox :value="permission.name">
                        {{ permission.display_name }}
                      </a-checkbox>
                    </a-col>
                  </a-row>
                </a-checkbox-group>
              </div>
            </div>
          </div>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 权限管理弹窗 -->
    <a-modal
      v-model:open="showPermissionModal"
      :title="`权限管理 - ${selectedRole?.display_name}`"
      width="800px"
      @ok="handlePermissionSave"
      @cancel="showPermissionModal = false"
      :confirm-loading="submitting"
    >
      <div class="permission-management">
        <div class="permission-summary">
          <a-statistic title="已分配权限" :value="selectedPermissions.length" suffix="个" />
          <a-statistic title="总权限数" :value="allPermissions.length" suffix="个" />
        </div>

        <a-divider />

        <div class="permission-groups">
          <div v-for="group in permissionGroups" :key="group.name" class="permission-group">
            <div class="group-header">
              <a-checkbox
                :checked="isGroupSelected(group, selectedPermissions)"
                :indeterminate="isGroupIndeterminate(group, selectedPermissions)"
                @change="toggleGroupPermission(group)"
              >
                {{ group.display_name }}
              </a-checkbox>
            </div>
            <div class="group-permissions">
              <a-checkbox-group v-model:value="selectedPermissions" style="width: 100%">
                <a-row>
                  <a-col v-for="permission in group.permissions" :key="permission.name" :span="12">
                    <a-checkbox :value="permission.name">
                      <div class="permission-item">
                        <div class="permission-name">{{ permission.display_name }}</div>
                        <div class="permission-desc">{{ permission.description }}</div>
                      </div>
                    </a-checkbox>
                  </a-col>
                </a-row>
              </a-checkbox-group>
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
  import { ref, reactive, computed, onMounted } from 'vue'
  import { message } from 'ant-design-vue'
  import { TeamOutlined, PlusOutlined } from '@ant-design/icons-vue'
  import { useAuthStore } from '@/stores/auth'

  // Store
  const authStore = useAuthStore()
  const currentUser = computed(() => authStore.user)

  // 响应式数据
  const loading = ref(false)
  const submitting = ref(false)
  const searchText = ref('')
  const statusFilter = ref('')
  const showCreateModal = ref(false)
  const showPermissionModal = ref(false)
  const editingRole = ref(null)
  const selectedRole = ref(null)
  const selectedPermissions = ref([])

  // 角色列表数据（模拟数据）
  const roles = ref([
    {
      id: 1,
      name: 'admin',
      display_name: '管理员',
      description: '系统管理员，拥有所有权限',
      status: 'active',
      user_count: 1,
      permissions: [
        { name: 'tts:create', display_name: 'TTS服务创建' },
        { name: 'user:manage', display_name: '用户管理' },
        { name: 'role:manage', display_name: '角色管理' }
      ],
      created_at: '2024-01-01 00:00:00'
    },
    {
      id: 2,
      name: 'user',
      display_name: '普通用户',
      description: '普通用户，基础功能权限',
      status: 'active',
      user_count: 5,
      permissions: [
        { name: 'tts:create', display_name: 'TTS服务创建' },
        { name: 'book:read', display_name: '书籍查看' }
      ],
      created_at: '2024-01-02 00:00:00'
    }
  ])

  // 所有权限列表
  const allPermissions = ref([
    {
      name: 'tts:create',
      display_name: 'TTS服务创建',
      description: '创建TTS转换任务',
      group: 'tts'
    },
    {
      name: 'tts:delete',
      display_name: 'TTS服务删除',
      description: '删除TTS转换记录',
      group: 'tts'
    },
    { name: 'user:create', display_name: '用户创建', description: '创建新用户', group: 'user' },
    { name: 'user:edit', display_name: '用户编辑', description: '编辑用户信息', group: 'user' },
    { name: 'user:delete', display_name: '用户删除', description: '删除用户', group: 'user' },
    { name: 'user:manage', display_name: '用户管理', description: '管理用户权限', group: 'user' },
    { name: 'role:create', display_name: '角色创建', description: '创建新角色', group: 'role' },
    { name: 'role:edit', display_name: '角色编辑', description: '编辑角色信息', group: 'role' },
    { name: 'role:delete', display_name: '角色删除', description: '删除角色', group: 'role' },
    { name: 'role:manage', display_name: '角色管理', description: '管理角色权限', group: 'role' },
    { name: 'book:create', display_name: '书籍创建', description: '创建新书籍', group: 'book' },
    { name: 'book:edit', display_name: '书籍编辑', description: '编辑书籍信息', group: 'book' },
    { name: 'book:delete', display_name: '书籍删除', description: '删除书籍', group: 'book' },
    { name: 'book:read', display_name: '书籍查看', description: '查看书籍内容', group: 'book' },
    {
      name: 'project:create',
      display_name: '项目创建',
      description: '创建新项目',
      group: 'project'
    },
    {
      name: 'project:edit',
      display_name: '项目编辑',
      description: '编辑项目信息',
      group: 'project'
    },
    { name: 'project:delete', display_name: '项目删除', description: '删除项目', group: 'project' },
    {
      name: 'system:config',
      display_name: '系统配置',
      description: '系统配置管理',
      group: 'system'
    },
    {
      name: 'system:monitor',
      display_name: '系统监控',
      description: '系统监控查看',
      group: 'system'
    }
  ])

  // 权限分组
  const permissionGroups = computed(() => {
    const groups = {}
    allPermissions.value.forEach((permission) => {
      if (!groups[permission.group]) {
        groups[permission.group] = {
          name: permission.group,
          display_name: getGroupDisplayName(permission.group),
          permissions: []
        }
      }
      groups[permission.group].permissions.push(permission)
    })
    return Object.values(groups)
  })

  // 表单数据
  const roleForm = reactive({
    name: '',
    display_name: '',
    description: '',
    status: 'active',
    permissions: []
  })

  // 表单验证规则
  const formRules = {
    name: [
      { required: true, message: '请输入角色标识', trigger: 'blur' },
      {
        pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/,
        message: '角色标识只能包含字母、数字和下划线',
        trigger: 'blur'
      }
    ],
    display_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
    description: [{ required: true, message: '请输入角色描述', trigger: 'blur' }]
  }

  // 表格列配置
  const columns = [
    {
      title: '角色信息',
      key: 'name',
      width: 200
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description'
    },
    {
      title: '状态',
      key: 'status',
      width: 100
    },
    {
      title: '权限',
      key: 'permissions',
      width: 250
    },
    {
      title: '用户数',
      key: 'user_count',
      width: 100
    },
    {
      title: '创建时间',
      key: 'created_at',
      width: 160
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right'
    }
  ]

  // 分页配置
  const pagination = reactive({
    current: 1,
    pageSize: 10,
    total: 0,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
  })

  // 计算属性
  const filteredRoles = computed(() => {
    let result = roles.value

    if (searchText.value) {
      result = result.filter(
        (role) =>
          role.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
          role.display_name.toLowerCase().includes(searchText.value.toLowerCase()) ||
          role.description.toLowerCase().includes(searchText.value.toLowerCase())
      )
    }

    if (statusFilter.value) {
      result = result.filter((role) => role.status === statusFilter.value)
    }

    pagination.total = result.length
    return result
  })

  // 方法
  const getGroupDisplayName = (groupName) => {
    const names = {
      tts: 'TTS服务',
      user: '用户管理',
      role: '角色管理',
      book: '书籍管理',
      project: '项目管理',
      system: '系统管理'
    }
    return names[groupName] || groupName
  }

  const isGroupSelected = (group, permissions = roleForm.permissions) => {
    return group.permissions.every((p) => permissions.includes(p.name))
  }

  const isGroupIndeterminate = (group, permissions = roleForm.permissions) => {
    const selected = group.permissions.filter((p) => permissions.includes(p.name))
    return selected.length > 0 && selected.length < group.permissions.length
  }

  const toggleGroup = (group) => {
    const isSelected = isGroupSelected(group)
    if (isSelected) {
      // 取消选择该组的所有权限
      roleForm.permissions = roleForm.permissions.filter(
        (p) => !group.permissions.some((gp) => gp.name === p)
      )
    } else {
      // 选择该组的所有权限
      const groupPermissions = group.permissions.map((p) => p.name)
      roleForm.permissions = [...new Set([...roleForm.permissions, ...groupPermissions])]
    }
  }

  const toggleGroupPermission = (group) => {
    const isSelected = isGroupSelected(group, selectedPermissions.value)
    if (isSelected) {
      selectedPermissions.value = selectedPermissions.value.filter(
        (p) => !group.permissions.some((gp) => gp.name === p)
      )
    } else {
      const groupPermissions = group.permissions.map((p) => p.name)
      selectedPermissions.value = [...new Set([...selectedPermissions.value, ...groupPermissions])]
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('zh-CN')
  }

  const handleSearch = () => {
    pagination.current = 1
  }

  const resetFilters = () => {
    searchText.value = ''
    statusFilter.value = ''
    handleSearch()
  }

  const handleTableChange = (pag) => {
    pagination.current = pag.current
    pagination.pageSize = pag.pageSize
  }

  const editRole = (role) => {
    editingRole.value = role
    Object.assign(roleForm, {
      name: role.name,
      display_name: role.display_name,
      description: role.description,
      status: role.status,
      permissions: role.permissions.map((p) => p.name)
    })
    showCreateModal.value = true
  }

  const managePermissions = (role) => {
    selectedRole.value = role
    selectedPermissions.value = role.permissions.map((p) => p.name)
    showPermissionModal.value = true
  }

  const deleteRole = async (role) => {
    try {
      loading.value = true
      // 这里应该调用API删除角色
      // await roleAPI.deleteRole(role.id)

      // 模拟删除
      const index = roles.value.findIndex((r) => r.id === role.id)
      if (index > -1) {
        roles.value.splice(index, 1)
      }

      message.success('角色删除成功')
    } catch (error) {
      message.error('删除失败：' + error.message)
    } finally {
      loading.value = false
    }
  }

  const handleSubmit = async () => {
    try {
      submitting.value = true

      // 这里应该调用API创建或更新角色
      if (editingRole.value) {
        // 更新角色
        const index = roles.value.findIndex((r) => r.id === editingRole.value.id)
        if (index > -1) {
          roles.value[index] = {
            ...roles.value[index],
            ...roleForm,
            permissions: allPermissions.value.filter((p) => roleForm.permissions.includes(p.name))
          }
        }
        message.success('角色更新成功')
      } else {
        // 创建角色
        const newRole = {
          id: Date.now(),
          ...roleForm,
          permissions: allPermissions.value.filter((p) => roleForm.permissions.includes(p.name)),
          user_count: 0,
          created_at: new Date().toISOString()
        }
        roles.value.unshift(newRole)
        message.success('角色创建成功')
      }

      handleCancel()
    } catch (error) {
      message.error('操作失败：' + error.message)
    } finally {
      submitting.value = false
    }
  }

  const handleCancel = () => {
    showCreateModal.value = false
    editingRole.value = null
    Object.assign(roleForm, {
      name: '',
      display_name: '',
      description: '',
      status: 'active',
      permissions: []
    })
  }

  const handlePermissionSave = async () => {
    try {
      submitting.value = true

      // 更新角色权限
      const index = roles.value.findIndex((r) => r.id === selectedRole.value.id)
      if (index > -1) {
        roles.value[index].permissions = allPermissions.value.filter((p) =>
          selectedPermissions.value.includes(p.name)
        )
      }

      message.success('权限更新成功')
      showPermissionModal.value = false
      selectedRole.value = null
      selectedPermissions.value = []
    } catch (error) {
      message.error('权限更新失败：' + error.message)
    } finally {
      submitting.value = false
    }
  }

  // 生命周期
  onMounted(() => {
    pagination.total = roles.value.length
  })
</script>

<style scoped>
  .role-management-container {
    border-radius: 8px;
    overflow: hidden;
  }

  .page-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 32px;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 0 auto;
  }

  .title-section {
    flex: 1;
  }

  .page-title {
    font-size: 28px;
    font-weight: 600;
    margin: 0 0 8px 0;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .title-icon {
    font-size: 32px;
  }

  .page-description {
    font-size: 16px;
    opacity: 0.9;
    margin: 0;
  }

  .action-section {
    display: flex;
    gap: 12px;
  }

  .search-section {
    padding: 24px;
    background: #fafafa;
    border-bottom: 1px solid #f0f0f0;
  }

  .table-section {
    padding: 24px;
  }

  .role-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .role-name {
    font-weight: 500;
    color: #1890ff;
  }

  .role-code {
    font-size: 12px;
    color: #666;
    font-family: 'Courier New', monospace;
  }

  .permissions-container {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .permissions-config {
    max-height: 400px;
    overflow-y: auto;
  }

  .permission-group {
    margin-bottom: 24px;
    border: 1px solid #f0f0f0;
    border-radius: 6px;
    padding: 16px;
  }

  .group-header {
    margin-bottom: 12px;
    font-weight: 500;
    border-bottom: 1px solid #f0f0f0;
    padding-bottom: 8px;
  }

  .group-permissions {
    padding-left: 24px;
  }

  .permission-management {
    max-height: 600px;
    overflow-y: auto;
  }

  .permission-summary {
    display: flex;
    gap: 24px;
    margin-bottom: 16px;
  }

  .permission-groups {
    max-height: 400px;
    overflow-y: auto;
  }

  .permission-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .permission-name {
    font-weight: 500;
  }

  .permission-desc {
    font-size: 12px;
    color: #666;
  }
</style>
