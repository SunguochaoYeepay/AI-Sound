<template>
  <div class="navigation-test">
    <a-card title="导航优化测试" :bordered="false">
      <a-space direction="vertical" size="large" style="width: 100%">
        
        <!-- 导航结构展示 -->
        <a-card title="📋 新的导航结构" size="small">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="📚 内容管理">
              首页、书籍管理
            </a-descriptions-item>
            <a-descriptions-item label="🎵 音频制作">
              声音克隆、角色配音、语音合成
            </a-descriptions-item>
            <a-descriptions-item label="🎬 创作工具">
              环境音效、背景音乐、环境混音、音频编辑器
            </a-descriptions-item>
            <a-descriptions-item label="📦 资源库">
              音频库、图片生成、图片库
            </a-descriptions-item>
            <a-descriptions-item label="⚙️ 系统管理">
              用户管理、角色权限、日志监控、数据备份、系统配置
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 快速访问功能 -->
        <a-card title="🚀 快速访问功能" size="small">
          <a-alert
            message="快速访问栏已添加到顶部"
            description="包含最常用的5个功能：首页、书籍管理、语音合成、声音克隆、音频编辑器"
            type="success"
            show-icon
            style="margin-bottom: 16px"
          />
          <a-space wrap>
            <a-tag color="blue">🏠 首页</a-tag>
            <a-tag color="green">📚 书籍管理</a-tag>
            <a-tag color="orange">🎵 语音合成</a-tag>
            <a-tag color="purple">🎤 声音克隆</a-tag>
            <a-tag color="red">🎛️ 音频编辑器</a-tag>
          </a-space>
        </a-card>

        <!-- 优化效果对比 -->
        <a-card title="📊 优化效果对比" size="small">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-statistic
                title="优化前"
                :value="6"
                suffix="个分组"
                value-style="color: #cf1322"
              />
              <div style="margin-top: 8px; font-size: 12px; color: #666;">
                • 导航层级过深<br>
                • 功能分散<br>
                • 视觉冗余
              </div>
            </a-col>
            <a-col :span="12">
              <a-statistic
                title="优化后"
                :value="5"
                suffix="个分组"
                value-style="color: #3f8600"
              />
              <div style="margin-top: 8px; font-size: 12px; color: #666;">
                • 智能分组<br>
                • 快速访问<br>
                • 响应式设计
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- 交互优化 -->
        <a-card title="🎨 交互优化" size="small">
          <a-list size="small">
            <a-list-item>
              <template #actions>
                <a-tag color="green">✅</a-tag>
              </template>
              <a-list-item-meta
                title="智能展开"
                description="根据用户使用习惯自动展开常用分组"
              />
            </a-list-item>
            <a-list-item>
              <template #actions>
                <a-tag color="green">✅</a-tag>
              </template>
              <a-list-item-meta
                title="快速访问"
                description="顶部快速访问栏，一键跳转常用功能"
              />
            </a-list-item>
            <a-list-item>
              <template #actions>
                <a-tag color="green">✅</a-tag>
              </template>
              <a-list-item-meta
                title="响应式设计"
                description="移动端友好的导航体验"
              />
            </a-list-item>
            <a-list-item>
              <template #actions>
                <a-tag color="green">✅</a-tag>
              </template>
              <a-list-item-meta
                title="视觉优化"
                description="减少视觉冗余，提升用户体验"
              />
            </a-list-item>
          </a-list>
        </a-card>

        <!-- 测试按钮 -->
        <a-card title="🧪 功能测试" size="small">
          <a-space wrap>
            <a-button type="primary" @click="testQuickAccess">
              测试快速访问
            </a-button>
            <a-button @click="testNavigation">
              测试导航跳转
            </a-button>
            <a-button @click="testResponsive">
              测试响应式
            </a-button>
          </a-space>
        </a-card>

      </a-space>
    </a-card>
  </div>
</template>

<script setup>
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const testQuickAccess = () => {
  message.success('快速访问栏已启用！点击顶部快速访问按钮测试功能')
}

const testNavigation = () => {
  message.info('导航分组已重新组织，请尝试点击不同分组查看效果')
}

const testResponsive = () => {
  message.info('请调整浏览器窗口大小，查看响应式导航效果')
}
</script>

<style scoped>
.navigation-test {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.ant-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.ant-statistic {
  text-align: center;
}

.ant-list-item {
  padding: 12px 0;
}

.ant-list-item-meta-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.ant-list-item-meta-description {
  font-size: 12px;
  color: #666;
}
</style> 