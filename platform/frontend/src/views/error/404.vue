<template>
  <div class="not-found-container">
    <a-result
      status="404"
      title="404"
      sub-title="抱歉，您访问的页面不存在"
    >
      <template #extra>
        <a-button type="primary" @click="$router.push('/')">
          返回首页
        </a-button>
        <a-button @click="$router.go(-1)" style="margin-left: 8px">
          返回上一页
        </a-button>
      </template>
    </a-result>
  </div>
</template>

<script setup>
// 使用 Ant Design Vue 的 Result 组件展示 404 页面
</script>

<style scoped>
.not-found-container {
  padding: 32px;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}
</style>