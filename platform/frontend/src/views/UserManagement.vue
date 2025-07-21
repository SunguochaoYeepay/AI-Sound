<template>
  <div class="user-management-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <UserOutlined class="title-icon" />
            用户管理
          </h1>
          <p class="page-description">管理系统用户账户、角色权限和访问控制</p>
        </div>
        <div class="action-section">
          <a-button type="primary" size="large" @click="showCreateModal = true">
            <template #icon>
              <PlusOutlined />
            </template>
            新建用户
          </a-button>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索用户名、邮箱"
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
            <a-select-option value="active">活跃</a-select-option>
            <a-select-option value="inactive">停用</a-select-option>
            <a-select-option value="pending">待激活</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="roleFilter"
            placeholder="角色筛选"
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="">全部角色</a-select-option>
            <a-select-option value="admin">管理员</a-select-option>
            <a-select-option value="user">普通用户</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button @click="resetFilters">重置</a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 用户列表 -->
    <div class="table-section">
      <a-table
        :columns="columns"
        :data-source="filteredUsers"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #headerCell="{ column }">
          <template v-if="column.key === 'username'">
            <UserOutlined />
            用户名
          </template>
        </template>

        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'avatar'">
            <a-avatar :size="40">
              <template v-if="record.avatar">
                <img :src="record.avatar" alt="avatar" />
              </template>
              <template v-else>
                {{ record.username.charAt(0).toUpperCase() }}
              </template>
            </a-avatar>
          </template>

          <template v-if="column.key === 'username'">
            <div class="user-info">
              <div class="username">{{ record.username }}</div>
              <div class="full-name">{{ record.full_name }}</div>
            </div>
          </template>

          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>

          <template v-if="column.key === 'roles'">
            <div class="roles-container">
              <a-tag v-for="role in record.roles" :key="role.name" :color="getRoleColor(role.name)">
                {{ role.display_name }}
              </a-tag>
            </div>
          </template>

          <template v-if="column.key === 'is_superuser'">
            <a-tag v-if="record.is_superuser" color="red">
              <CrownOutlined />
              超级管理员
            </a-tag>
            <span v-else>-</span>
          </template>

          <template v-if="column.key === 'last_login'">
            <div v-if="record.last_login">
              {{ formatDate(record.last_login) }}
            </div>
            <span v-else class="text-muted">从未登录</span>
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                type="link"
                size="small"
                @click="editUser(record)"
                :disabled="record.is_superuser && !currentUser.is_superuser"
              >
                编辑
              </a-button>
              <a-button
                type="link"
                size="small"
                @click="resetPassword(record)"
                :disabled="record.is_superuser && !currentUser.is_superuser"
              >
                重置密码
              </a-button>
              <a-popconfirm
                title="确定要删除这个用户吗？"
                @confirm="deleteUser(record)"
                :disabled="record.is_superuser"
              >
                <a-button type="link" size="small" danger :disabled="record.is_superuser">
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 创建/编辑用户弹窗 -->
    <a-modal
      v-model:open="showCreateModal"
      :title="editingUser ? '编辑用户' : '新建用户'"
      width="600px"
      @ok="handleSubmit"
      @cancel="handleCancel"
      :confirm-loading="submitting"
    >
      <a-form ref="formRef" :model="userForm" :rules="formRules" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="用户名" name="username">
              <a-input
                v-model:value="userForm.username"
                placeholder="请输入用户名"
                :disabled="!!editingUser"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="邮箱" name="email">
              <a-input v-model:value="userForm.email" placeholder="请输入邮箱" type="email" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="姓名" name="full_name">
              <a-input v-model:value="userForm.full_name" placeholder="请输入姓名" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="状态" name="status">
              <a-select v-model:value="userForm.status" placeholder="选择状态">
                <a-select-option value="active">活跃</a-select-option>
                <a-select-option value="inactive">停用</a-select-option>
                <a-select-option value="pending">待激活</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item v-if="!editingUser" label="密码" name="password">
          <a-input-password v-model:value="userForm.password" placeholder="请输入密码" />
        </a-form-item>

        <a-form-item label="角色" name="roles">
          <a-select
            v-model:value="userForm.roles"
            mode="multiple"
            placeholder="选择角色"
            style="width: 100%"
          >
            <a-select-option v-for="role in availableRoles" :key="role.name" :value="role.name">
              {{ role.display_name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="每日配额" name="daily_quota">
          <a-input-number
            v-model:value="userForm.daily_quota"
            :min="0"
            :max="100000"
            placeholder="每日TTS使用配额"
            style="width: 100%"
          />
        </a-form-item>

        <a-form-item name="is_superuser">
          <a-checkbox v-model:checked="userForm.is_superuser"> 设为超级管理员 </a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 重置密码弹窗 -->
    <a-modal
      v-model:open="showPasswordModal"
      title="重置密码"
      @ok="handlePasswordReset"
      @cancel="showPasswordModal = false"
      :confirm-loading="submitting"
    >
      <a-form :model="passwordForm" layout="vertical">
        <a-form-item label="新密码">
          <a-input-password v-model:value="passwordForm.password" placeholder="请输入新密码" />
        </a-form-item>
        <a-form-item label="确认密码">
          <a-input-password
            v-model:value="passwordForm.confirmPassword"
            placeholder="请再次输入密码"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
  import { ref, reactive, computed, onMounted } from 'vue'
  import { message } from 'ant-design-vue'
  import { UserOutlined, PlusOutlined, CrownOutlined } from '@ant-design/icons-vue'
  import { useAuthStore } from '@/stores/auth'

  // Store
  const authStore = useAuthStore()
  const currentUser = computed(() => authStore.user)

  // 响应式数据
  const loading = ref(false)
  const submitting = ref(false)
  const searchText = ref('')
  const statusFilter = ref('')
  const roleFilter = ref('')
  const showCreateModal = ref(false)
  const showPasswordModal = ref(false)
  const editingUser = ref(null)

  // 用户列表数据（模拟数据）
  const users = ref([
    {
      id: 1,
      username: 'admin',
      email: 'admin@ai-sound.local',
      full_name: '系统管理员',
      status: 'active',
      is_superuser: true,
      is_verified: true,
      roles: [{ name: 'admin', display_name: '管理员' }],
      daily_quota: 10000,
      used_quota: 150,
      last_login: '2024-01-15 10:30:00',
      created_at: '2024-01-01 00:00:00'
    },
    {
      id: 2,
      username: 'user1',
      email: 'user1@example.com',
      full_name: '张三',
      status: 'active',
      is_superuser: false,
      is_verified: true,
      roles: [{ name: 'user', display_name: '普通用户' }],
      daily_quota: 1000,
      used_quota: 250,
      last_login: '2024-01-14 15:20:00',
      created_at: '2024-01-02 00:00:00'
    }
  ])

  // 可用角色
  const availableRoles = ref([
    { name: 'admin', display_name: '管理员' },
    { name: 'user', display_name: '普通用户' }
  ])

  // 表单数据
  const userForm = reactive({
    username: '',
    email: '',
    full_name: '',
    password: '',
    status: 'active',
    roles: [],
    daily_quota: 1000,
    is_superuser: false
  })

  const passwordForm = reactive({
    password: '',
    confirmPassword: ''
  })

  // 表单验证规则
  const formRules = {
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
    ],
    email: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
    ],
    full_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, message: '密码至少6位', trigger: 'blur' }
    ]
  }

  // 表格列配置
  const columns = [
    {
      title: '头像',
      key: 'avatar',
      width: 80
    },
    {
      title: '用户信息',
      key: 'username',
      width: 200
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email'
    },
    {
      title: '状态',
      key: 'status',
      width: 100
    },
    {
      title: '角色',
      key: 'roles',
      width: 150
    },
    {
      title: '超级管理员',
      key: 'is_superuser',
      width: 120
    },
    {
      title: '最后登录',
      key: 'last_login',
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
  const filteredUsers = computed(() => {
    let result = users.value

    if (searchText.value) {
      result = result.filter(
        (user) =>
          user.username.toLowerCase().includes(searchText.value.toLowerCase()) ||
          user.email.toLowerCase().includes(searchText.value.toLowerCase()) ||
          user.full_name.toLowerCase().includes(searchText.value.toLowerCase())
      )
    }

    if (statusFilter.value) {
      result = result.filter((user) => user.status === statusFilter.value)
    }

    if (roleFilter.value) {
      result = result.filter((user) => user.roles.some((role) => role.name === roleFilter.value))
    }

    pagination.total = result.length
    return result
  })

  // 方法
  const getStatusColor = (status) => {
    const colors = {
      active: 'green',
      inactive: 'red',
      pending: 'orange'
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status) => {
    const texts = {
      active: '活跃',
      inactive: '停用',
      pending: '待激活'
    }
    return texts[status] || status
  }

  const getRoleColor = (roleName) => {
    const colors = {
      admin: 'red',
      user: 'blue'
    }
    return colors[roleName] || 'default'
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
    roleFilter.value = ''
    handleSearch()
  }

  const handleTableChange = (pag) => {
    pagination.current = pag.current
    pagination.pageSize = pag.pageSize
  }

  const editUser = (user) => {
    editingUser.value = user
    Object.assign(userForm, {
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      status: user.status,
      roles: user.roles.map((role) => role.name),
      daily_quota: user.daily_quota,
      is_superuser: user.is_superuser
    })
    showCreateModal.value = true
  }

  const resetPassword = (user) => {
    editingUser.value = user
    passwordForm.password = ''
    passwordForm.confirmPassword = ''
    showPasswordModal.value = true
  }

  const deleteUser = async (user) => {
    try {
      loading.value = true
      // 这里应该调用API删除用户
      // await userAPI.deleteUser(user.id)

      // 模拟删除
      const index = users.value.findIndex((u) => u.id === user.id)
      if (index > -1) {
        users.value.splice(index, 1)
      }

      message.success('用户删除成功')
    } catch (error) {
      message.error('删除失败：' + error.message)
    } finally {
      loading.value = false
    }
  }

  const handleSubmit = async () => {
    try {
      submitting.value = true

      // 这里应该调用API创建或更新用户
      if (editingUser.value) {
        // 更新用户
        const index = users.value.findIndex((u) => u.id === editingUser.value.id)
        if (index > -1) {
          users.value[index] = {
            ...users.value[index],
            ...userForm,
            roles: availableRoles.value.filter((role) => userForm.roles.includes(role.name))
          }
        }
        message.success('用户更新成功')
      } else {
        // 创建用户
        const newUser = {
          id: Date.now(),
          ...userForm,
          roles: availableRoles.value.filter((role) => userForm.roles.includes(role.name)),
          is_verified: true,
          used_quota: 0,
          created_at: new Date().toISOString(),
          last_login: null
        }
        users.value.unshift(newUser)
        message.success('用户创建成功')
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
    editingUser.value = null
    Object.assign(userForm, {
      username: '',
      email: '',
      full_name: '',
      password: '',
      status: 'active',
      roles: [],
      daily_quota: 1000,
      is_superuser: false
    })
  }

  const handlePasswordReset = async () => {
    if (passwordForm.password !== passwordForm.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }

    try {
      submitting.value = true
      // 这里应该调用API重置密码
      // await userAPI.resetPassword(editingUser.value.id, passwordForm.password)

      message.success('密码重置成功')
      showPasswordModal.value = false
      editingUser.value = null
    } catch (error) {
      message.error('密码重置失败：' + error.message)
    } finally {
      submitting.value = false
    }
  }

  // 生命周期
  onMounted(() => {
    // 初始化数据
    pagination.total = users.value.length
  })
</script>

<style scoped>
  .user-management-container {
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
  }

  .table-section {
    padding: 24px;
  }

  .user-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .username {
    font-weight: 500;
    color: #1890ff;
  }

  .full-name {
    font-size: 12px;
    color: #666;
  }

  .roles-container {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .text-muted {
    color: #999;
  }
</style>
