<template>
  <a-layout-footer class="footer">
    MegaTTS3 &copy; {{ currentYear }} | 基于深度学习的文本转语音系统
  </a-layout-footer>
</template>

<script>
import { defineComponent, computed } from 'vue';

export default defineComponent({
  name: 'AppFooter',
  setup() {
    const currentYear = computed(() => new Date().getFullYear());
    
    return {
      currentYear
    };
  }
});
</script>

<style scoped>
.footer {
  text-align: center;
  background: #f0f2f5;
  padding: 12px;
  color: rgba(0, 0, 0, 0.45);
}
</style> 