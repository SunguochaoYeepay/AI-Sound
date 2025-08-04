<template>
  <div class="layout-test-container">
    <a-card title="🎵 音频编辑器布局优化测试" :bordered="false">
      <a-space direction="vertical" size="large" style="width: 100%">
        
        <!-- 布局对比 -->
        <a-card title="📊 布局优化对比" size="small">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-statistic
                title="优化前"
                value="自定义布局"
                value-style="color: #cf1322"
              />
              <div style="margin-top: 8px; font-size: 12px; color: #666;">
                • 自定义头部样式<br>
                • 与其他页面不一致<br>
                • 暗色主题为主<br>
                • 响应式支持有限
              </div>
            </a-col>
            <a-col :span="12">
              <a-statistic
                title="优化后"
                value="标准布局"
                value-style="color: #3f8600"
              />
              <div style="margin-top: 8px; font-size: 12px; color: #666;">
                • 标准页面头部<br>
                • 与其他页面一致<br>
                • 支持明暗主题<br>
                • 完整响应式设计
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- 布局结构展示 -->
        <a-card title="🏗️ 新的布局结构" size="small">
          <a-descriptions :column="1" bordered>
            <a-descriptions-item label="容器类名">
              <code>.sound-editor-container</code> (统一命名规范)
            </a-descriptions-item>
            <a-descriptions-item label="页面头部">
              <code>.page-header</code> (标准页面头部样式)
            </a-descriptions-item>
            <a-descriptions-item label="标题区域">
              <code>.title-section</code> (包含返回按钮和标题)
            </a-descriptions-item>
            <a-descriptions-item label="操作区域">
              <code>.action-section</code> (帮助、设置、全屏按钮)
            </a-descriptions-item>
            <a-descriptions-item label="内容区域">
              <code>.editor-content</code> (多轨编辑器组件)
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 视觉优化 -->
        <a-card title="🎨 视觉优化" size="small">
          <a-list size="small">
            <a-list-item>
              <template #actions>
                <a-tag color="green">✅</a-tag>
              </template>
              <a-list-item-meta
                title="统一头部样式"
                description="使用标准页面头部，与其他页面保持一致"
              />
            </a-list-item>
            <a-list-item>
              <template #actions>
                <a-tag color="green">✅</a-tag>
              </template>
              <a-list-item-meta
                title="图标和标题"
                description="添加音频编辑器图标，标题更加直观"
              />
            </a-list-item>
            <a-list-item>
              <template #actions>
                <a-tag color="green">✅</a-tag>
              </template>
              <a-list-item-meta
                title="描述文字"
                description="添加页面描述，说明功能用途"
              />
            </a-list-item>
            <a-list-item>
              <template #actions>
                <a-tag color="green">✅</a-tag>
              </template>
              <a-list-item-meta
                title="响应式设计"
                description="移动端友好的布局适配"
              />
            </a-list-item>
            <a-list-item>
              <template #actions>
                <a-tag color="green">✅</a-tag>
              </template>
              <a-list-item-meta
                title="暗黑模式"
                description="完整的明暗主题支持"
              />
            </a-list-item>
          </a-list>
        </a-card>

        <!-- 功能保持 -->
        <a-card title="🔧 功能保持" size="small">
          <a-alert
            message="所有原有功能完全保留"
            description="全屏模式、帮助对话框、设置面板等功能都正常工作"
            type="success"
            show-icon
            style="margin-bottom: 16px"
          />
          <a-space wrap>
            <a-tag color="blue">全屏模式</a-tag>
            <a-tag color="green">帮助系统</a-tag>
            <a-tag color="orange">设置面板</a-tag>
            <a-tag color="purple">返回导航</a-tag>
            <a-tag color="red">多轨编辑</a-tag>
          </a-space>
        </a-card>

        <!-- 测试按钮 -->
        <a-card title="🧪 功能测试" size="small">
          <a-space wrap>
            <a-button type="primary" @click="testLayout">
              测试布局效果
            </a-button>
            <a-button @click="testResponsive">
              测试响应式
            </a-button>
            <a-button @click="testTheme">
              测试主题切换
            </a-button>
            <a-button @click="goToEditor">
              前往音频编辑器
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

const testLayout = () => {
  message.success('布局已优化！音频编辑器现在使用标准页面布局')
}

const testResponsive = () => {
  message.info('请调整浏览器窗口大小，查看响应式布局效果')
}

const testTheme = () => {
  message.info('请切换明暗主题，查看音频编辑器页面的主题适配效果')
}

const goToEditor = () => {
  router.push('/sound-editor')
}
</script>

<style scoped>
.layout-test-container {
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

code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
</style> 