<template>
  <div class="table-actions">
    <a-button 
      v-if="showEdit"
      type="text" 
      size="small" 
      @click.stop="$emit('edit', record)"
    >
      编辑
    </a-button>
    <a-button 
      v-if="showView"
      type="text" 
      size="small" 
      @click.stop="$emit('view', record)"
    >
      查看
    </a-button>
    <a-button 
      v-if="showSynthesis"
      type="text" 
      size="small" 
      @click.stop="$emit('synthesis', record)"
    >
      合成
    </a-button>
    <a-button 
      v-if="showDelete"
      type="text" 
      size="small" 
      danger 
      @click.stop="$emit('delete', record)"
    >
      删除
    </a-button>
    <!-- 自定义操作插槽 -->
    <slot name="custom-actions" :record="record"></slot>
  </div>
</template>

<script setup>
// Props
defineProps({
  record: {
    type: Object,
    required: true
  },
  showEdit: {
    type: Boolean,
    default: true
  },
  showView: {
    type: Boolean,
    default: true
  },
  showSynthesis: {
    type: Boolean,
    default: false
  },
  showDelete: {
    type: Boolean,
    default: true
  }
})

// Emits
defineEmits(['edit', 'view', 'synthesis', 'delete'])
</script>

<style scoped>
.table-actions {
  display: flex;
  gap: 8px;
}
</style>
