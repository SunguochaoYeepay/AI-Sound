<template>
  <div class="forbidden-container">
    <a-result
      status="403"
      title="403"
      sub-title="抱歉，您没有权限访问此页面"
    >
      <template #extra>
        <a-button type="primary" @click="$router.push('/')">
          返回首页
        </a-button>
      </template>
    </a-result>
  </div>
</template>

<script setup>
// 使用 Ant Design Vue 的 Result 组件展示 403 页面
</script>

<style scoped>
.forbidden-container {
  padding: 32px;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}
</style>