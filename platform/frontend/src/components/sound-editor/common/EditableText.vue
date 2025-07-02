<template>
  <div class="editable-text" @click="startEdit" v-if="!editing">
    <span v-if="displayValue" class="text-content">{{ displayValue }}</span>
    <span v-else class="placeholder">{{ placeholder }}</span>
    <EditOutlined class="edit-icon" />
  </div>
  <div v-else class="edit-container">
    <a-input
      v-if="type === 'input'"
      v-model:value="editValue"
      @blur="confirmEdit"
      @keyup.enter="confirmEdit"
      @keyup.esc="cancelEdit"
      ref="inputRef"
      :placeholder="placeholder"
    />
    <a-textarea
      v-else
      v-model:value="editValue"
      @blur="confirmEdit"
      @keyup.esc="cancelEdit"
      ref="inputRef"
      :placeholder="placeholder"
      :rows="rows"
    />
    <div class="edit-actions">
      <a-button size="small" type="primary" @click="confirmEdit">保存</a-button>
      <a-button size="small" @click="cancelEdit">取消</a-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { EditOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  value: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '点击编辑'
  },
  type: {
    type: String,
    default: 'input' // 'input' 或 'textarea'
  },
  rows: {
    type: Number,
    default: 3
  }
})

const emit = defineEmits(['change'])

const editing = ref(false)
const editValue = ref('')
const inputRef = ref(null)

const displayValue = computed(() => {
  return props.value && props.value.trim() ? props.value : ''
})

async function startEdit() {
  editing.value = true
  editValue.value = props.value || ''
  
  await nextTick()
  if (inputRef.value) {
    inputRef.value.focus()
  }
}

function confirmEdit() {
  const newValue = editValue.value.trim()
  if (newValue !== props.value) {
    emit('change', newValue)
  }
  editing.value = false
}

function cancelEdit() {
  editing.value = false
  editValue.value = props.value || ''
}
</script>

<style scoped>
.editable-text {
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
  position: relative;
  min-height: 22px;
  display: flex;
  align-items: center;
}

.editable-text:hover {
  background-color: #f5f5f5;
}

.text-content {
  flex: 1;
}

.placeholder {
  color: #bfbfbf;
  font-style: italic;
  flex: 1;
}

.edit-icon {
  opacity: 0;
  transition: opacity 0.3s;
  margin-left: 8px;
  color: #1890ff;
}

.editable-text:hover .edit-icon {
  opacity: 1;
}

.edit-container {
  position: relative;
}

.edit-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}
</style> 