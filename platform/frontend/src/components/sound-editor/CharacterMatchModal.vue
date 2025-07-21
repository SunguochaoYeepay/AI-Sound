<template>
  <a-modal
    v-model:open="visible"
    title="角色配置匹配结果"
    :width="700"
    @ok="handleOk"
    @cancel="handleCancel"
    :okText="'应用匹配'"
    :cancelText="'取消'"
  >
    <div class="match-results">
      <!-- 匹配成功的角色 -->
      <div v-if="matchedCharacters.length > 0" class="section">
        <h3>匹配成功的角色 ({{ matchedCharacters.length }}个)</h3>
        <a-table
          :dataSource="matchedCharacters"
          :columns="columns"
          :pagination="{ pageSize: 5 }"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'config'">
              <div class="config-diff">
                <div class="old-config">
                  <div class="label">当前配置：</div>
                  <div>{{ record.currentConfig }}</div>
                </div>
                <div class="new-config">
                  <div class="label">匹配配置：</div>
                  <div>{{ record.matchedConfig }}</div>
                </div>
              </div>
            </template>
          </template>
        </a-table>
      </div>

      <!-- 未匹配的角色 -->
      <div v-if="unMatchedCharacters.length > 0" class="section">
        <h3>未匹配的角色 ({{ unMatchedCharacters.length }}个)</h3>
        <a-list :dataSource="unMatchedCharacters" :grid="{ gutter: 16, column: 3 }">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-card size="small">
                {{ item.name }}
              </a-card>
            </a-list-item>
          </template>
        </a-list>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
  import { ref, defineProps, defineEmits } from 'vue'

  const props = defineProps({
    visible: {
      type: Boolean,
      default: false
    },
    matchedCharacters: {
      type: Array,
      default: () => []
    },
    unMatchedCharacters: {
      type: Array,
      default: () => []
    }
  })

  const emit = defineEmits(['update:visible', 'ok', 'cancel'])

  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      width: 120
    },
    {
      title: '配置对比',
      dataIndex: 'config',
      key: 'config'
    }
  ]

  const handleOk = () => {
    emit('ok')
  }

  const handleCancel = () => {
    emit('cancel')
  }
</script>

<style scoped>
  .match-results {
    max-height: 600px;
    overflow-y: auto;
  }

  .section {
    margin-bottom: 24px;
  }

  .section h3 {
    margin-bottom: 16px;
  }

  .config-diff {
    .old-config,
    .new-config {
      margin-bottom: 8px;

      .label {
        font-weight: bold;
        margin-bottom: 4px;
      }
    }

    .new-config {
      color: #52c41a;
    }
  }
</style>
