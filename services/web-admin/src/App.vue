<template>
  <a-config-provider :locale="zhCN">
    <a-layout class="layout-container">
      <AppSidebar />
      
      <a-layout>
        <AppHeader />
        
        <a-layout-content class="main-content">
          <div class="main-container">
            <router-view />
          </div>
        </a-layout-content>
        
        <AppFooter />
      </a-layout>
    </a-layout>
  </a-config-provider>
</template>

<script>
import { defineComponent } from 'vue';
import { useRouter } from 'vue-router';
import zhCN from 'ant-design-vue/es/locale/zh_CN';
import AppHeader from './components/common/AppHeader.vue';
import AppSidebar from './components/common/AppSidebar.vue';
import AppFooter from './components/common/AppFooter.vue';

export default defineComponent({
  name: 'App',
  components: {
    AppHeader,
    AppSidebar,
    AppFooter,
  },
  setup() {
    const router = useRouter();

    // 如果用户访问根路径，重定向到仪表盘
    if (window.location.pathname === '/') {
      router.push('/dashboard');
    }

    return {
      zhCN
    };
  }
});
</script>

<style>
.layout-container {
  min-height: 100vh;
}

.main-content {
  padding: 24px;
  background: #f0f2f5;
}

.main-container {
  padding: 24px;
  background: #fff;
  border-radius: 4px;
  min-height: calc(100vh - 64px - 70px - 48px);
}
</style>