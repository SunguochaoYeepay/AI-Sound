<template>
  <a-modal
    :open="visible"
    title="AI生成角色头像"
    width="600"
    :maskClosable="false"
    @ok="$emit('generate')"
    @cancel="$emit('cancel')"
    :confirmLoading="generating"
    okText="生成头像"
    cancelText="取消"
  >
    <div class="avatar-generation-form">
      <a-form layout="vertical">
        <a-form-item label="角色名称">
          <a-input :value="characterName" disabled />
        </a-form-item>
        
                 <a-form-item label="风格偏好">
           <a-radio-group :value="config.style" class="style-radio-group" @change="$emit('update:config', { ...config, style: $event })">
             <a-radio value="realistic">写实风格</a-radio>
             <a-radio value="anime">动漫风格</a-radio>
             <a-radio value="cartoon">卡通风格</a-radio>
             <a-radio value="artistic">艺术风格</a-radio>
           </a-radio-group>
         </a-form-item>
         
         <a-form-item label="图片尺寸">
           <a-select :value="config.size" @change="$emit('update:config', { ...config, size: $event })">
             <a-select-option value="512x512">512x512 (标准)</a-select-option>
             <a-select-option value="768x768">768x768 (高清)</a-select-option>
             <a-select-option value="1024x1024">1024x1024 (超高清)</a-select-option>
           </a-select>
         </a-form-item>
        
        <!-- 参考图像上传 -->
        <a-form-item label="参考图像（可选）">
          <a-upload
            v-model:file-list="config.referenceImageList"
            :before-upload="beforeReferenceImageUpload"
            :on-remove="removeReferenceImage"
            list-type="picture-card"
            :max-count="1"
            accept="image/*"
          >
            <template v-if="config.referenceImageList.length < 1">
              <div>
                <plus-outlined />
                <div style="margin-top: 8px">上传参考图像</div>
              </div>
            </template>
          </a-upload>
          <div class="tips">
            <small>上传参考图像可以让AI生成更符合您期望的头像风格</small>
          </div>
        </a-form-item>
        
                 <a-form-item label="自定义提示词（可选）">
           <a-textarea 
             :value="config.customPrompt"
             placeholder="如果您有特定的外貌要求，可以在这里描述..."
             :rows="3"
             @input="$emit('update:config', { ...config, customPrompt: $event.target.value })"
           />
          <div class="tips">
            <small>留空将使用基于角色描述的智能提示词</small>
          </div>
        </a-form-item>
        
        <!-- 预览当前角色信息 -->
        <a-form-item label="当前角色信息预览">
          <div class="character-preview">
            <p><strong>描述：</strong>{{ characterDescription || '暂无描述' }}</p>
            <p><strong>声音类型：</strong>{{ voiceTypeLabel }}</p>
          </div>
        </a-form-item>
      </a-form>
    </div>
  </a-modal>
</template>

<script setup>
import { computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  generating: {
    type: Boolean,
    default: false
  },
  characterName: {
    type: String,
    default: ''
  },
  characterDescription: {
    type: String,
    default: ''
  },
  voiceType: {
    type: String,
    default: ''
  },
  config: {
    type: Object,
    default: () => ({
      style: 'realistic',
      size: '512x512',
      customPrompt: '',
      referenceImageList: [],
      referenceImageFile: null
    })
  }
})

const emit = defineEmits(['generate', 'cancel', 'update:config'])

const voiceTypeLabel = computed(() => {
  const typeMap = {
    'male': '男声',
    'female': '女声', 
    'child': '童声',
    'elder': '老人声',
    'custom': '自定义'
  }
  return typeMap[props.voiceType] || '未知'
})

const beforeReferenceImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    message.error('只能上传图片文件！')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('图片大小不能超过 10MB！')
    return false
  }
  
  // 保存文件引用
  props.config.referenceImageFile = file
  return false // 阻止自动上传
}

const removeReferenceImage = () => {
  props.config.referenceImageFile = null
  props.config.referenceImageList = []
}
</script>

<style scoped>
.avatar-generation-form {
  padding: 16px 0;
}

.style-radio-group {
  display: flex;
  gap: 16px;
}

.tips {
  margin-top: 8px;
  color: #6b7280;
}

.character-preview {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.character-preview p {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.character-preview p:last-child {
  margin-bottom: 0;
}

/* 暗黑模式适配 */
[data-theme='dark'] .character-preview {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme='dark'] .tips {
  color: #8c8c8c !important;
}
</style>