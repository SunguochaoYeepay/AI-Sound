<template>
  <div class="novel-manage">
    <a-row :gutter="16" class="mb-16">
      <a-col :span="24">
        <a-card title="小说管理" :bordered="false">
          <p>上传、配置与处理小说</p>
        </a-card>
      </a-col>
    </a-row>
    
    <a-row :gutter="16" class="mb-16">
      <a-col :span="12">
        <a-card title="小说上传">
          <a-upload-dragger
            name="file"
            :multiple="false"
            :before-upload="beforeUpload"
            :show-upload-list="false"
            accept=".txt,.epub,.pdf"
          >
            <p class="ant-upload-drag-icon">
              <inbox-outlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持单个TXT、EPUB或PDF文件，最大100MB
            </p>
          </a-upload-dragger>
          
          <div v-if="currentFile" class="mt-16">
            <a-alert 
              :message="`已选择文件: ${currentFile.name}`" 
              type="info" 
              show-icon 
              class="mb-16"
            />
            
            <a-button type="primary" @click="uploadNovel" :loading="uploading">
              开始上传
            </a-button>
            <a-button @click="cancelUpload" class="ml-2">
              取消
            </a-button>
          </div>
        </a-card>
      </a-col>
      
      <a-col :span="12">
        <a-card title="从URL导入">
          <a-form layout="vertical">
            <a-form-item label="小说URL" :rules="[{ required: true, message: '请输入URL' }]">
              <a-input
                v-model:value="importUrl"
                placeholder="输入小说URL（支持常见小说网站）"
                :disabled="importing"
              />
            </a-form-item>
            
            <a-form-item label="小说标题（可选）">
              <a-input
                v-model:value="importTitle"
                placeholder="指定标题（留空则自动获取）"
                :disabled="importing"
              />
            </a-form-item>
            
            <a-form-item>
              <a-button 
                type="primary" 
                @click="importFromUrl" 
                :loading="importing"
                :disabled="!importUrl"
              >
                <template #icon><link-outlined /></template>
                开始导入
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>
    </a-row>
    
    <a-row :gutter="16">
      <a-col :span="24">
        <a-card title="小说列表">
          <a-table
            :dataSource="novels"
            :columns="columns"
            :pagination="{ pageSize: 10 }"
            :loading="loading"
            rowKey="id"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'action'">
                <a-space>
                  <a-button type="link" @click="viewNovel(record)">查看</a-button>
                  <a-button type="link" @click="processNovel(record)">生成有声书</a-button>
                  <a-dropdown>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item key="1" @click="editConfig(record)">编辑配置</a-menu-item>
                        <a-menu-item key="2" @click="confirmDeleteNovel(record)">删除</a-menu-item>
                      </a-menu>
                    </template>
                    <a-button type="link">
                      更多 <down-outlined />
                    </a-button>
                  </a-dropdown>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
    
    <a-modal
      v-model:visible="previewVisible"
      title="小说预览"
      width="800px"
      :footer="null"
    >
      <a-spin :spinning="previewLoading">
        <div v-if="currentNovel">
          <a-descriptions bordered :column="2" size="small" class="mb-16">
            <a-descriptions-item label="标题" span="2">{{ currentNovel.name }}</a-descriptions-item>
            <a-descriptions-item label="文件大小">{{ formatFileSize(currentNovel.size) }}</a-descriptions-item>
            <a-descriptions-item label="上传时间">{{ currentNovel.uploadTime }}</a-descriptions-item>
            <a-descriptions-item label="章节数">{{ novelChapters.length }}</a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="getStatusColor(currentNovel.status)">
                {{ getStatusText(currentNovel.status) }}
              </a-tag>
            </a-descriptions-item>
          </a-descriptions>
          
          <a-divider orientation="left">章节列表</a-divider>
          
          <a-row>
            <a-col :span="8">
              <a-list
                size="small"
                bordered
                class="chapter-list"
                :data-source="novelChapters"
              >
                <template #renderItem="{ item }">
                  <a-list-item 
                    :class="{ 'active-chapter': selectedChapter?.id === item.id }"
                    @click="selectChapter(item)"
                  >
                    <span class="chapter-title">{{ item.title }}</span>
                  </a-list-item>
                </template>
              </a-list>
            </a-col>
            
            <a-col :span="16" class="chapter-content">
              <div v-if="selectedChapter" class="content-panel">
                <div class="chapter-header">
                  <h3>{{ selectedChapter.title }}</h3>
                </div>
                
                <a-divider />
                
                <div class="chapter-text">
                  <p v-for="(paragraph, index) in chapterParagraphs" :key="index">
                    {{ paragraph }}
                  </p>
                </div>
              </div>
              
              <a-empty v-else description="选择章节查看内容" />
            </a-col>
          </a-row>
        </div>
      </a-spin>
    </a-modal>
    
    <a-modal
      v-model:visible="configVisible"
      title="小说处理配置"
      @ok="saveConfig"
      :confirmLoading="savingConfig"
    >
      <a-form :model="configForm" layout="vertical">
        <a-form-item label="默认音色">
          <a-select v-model:value="configForm.defaultVoice">
            <a-select-option value="female_young">年轻女声</a-select-option>
            <a-select-option value="female_mature">成熟女声</a-select-option>
            <a-select-option value="male_young">年轻男声</a-select-option>
            <a-select-option value="male_middle">中年男声</a-select-option>
            <a-select-option value="male_elder">老年男声</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="章节识别模式">
          <a-radio-group v-model:value="configForm.chapterMode">
            <a-radio value="auto">自动识别</a-radio>
            <a-radio value="custom">自定义模式</a-radio>
          </a-radio-group>
        </a-form-item>
        
        <a-form-item label="自定义章节模式" v-if="configForm.chapterMode === 'custom'">
          <a-input 
            v-model:value="configForm.chapterPattern" 
            placeholder="输入正则表达式，如: ^第.{1,10}[章节]"
          />
        </a-form-item>
        
        <a-form-item label="处理选项">
          <a-checkbox v-model:checked="configForm.splitByChapter">按章节拆分</a-checkbox>
          <a-checkbox v-model:checked="configForm.useVoiceMapping">使用角色声音映射</a-checkbox>
          <a-checkbox v-model:checked="configForm.detectEmotion">情感检测</a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted, computed, h, resolveComponent } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { useRouter } from 'vue-router';
// 移除旧的 store 引用
import { 
  InboxOutlined, 
  DownOutlined, 
  LinkOutlined
} from '@ant-design/icons-vue';

export default defineComponent({
  name: 'NovelManageView',
  components: {
    InboxOutlined,
    DownOutlined,
    LinkOutlined
  },
  setup() {
    const router = useRouter();
    // 移除 apiStore 引用
    const novels = ref([]);
    const loading = ref(true);
    const currentFile = ref(null);
    const uploading = ref(false);
    
    // URL导入相关
    const importUrl = ref('');
    const importTitle = ref('');
    const importing = ref(false);
    
    // 小说预览相关
    const previewVisible = ref(false);
    const previewLoading = ref(false);
    const currentNovel = ref(null);
    const novelChapters = ref([]);
    const selectedChapter = ref(null);
    const chapterContent = ref('');
    
    // 配置相关
    const configVisible = ref(false);
    const savingConfig = ref(false);
    const configForm = reactive({
      defaultVoice: 'female_young',
      chapterMode: 'auto',
      chapterPattern: '^第.{1,10}[章节]',
      splitByChapter: true,
      useVoiceMapping: true,
      detectEmotion: true
    });
    const configNovelId = ref(null);
    
    // 章节内容按段落拆分
    const chapterParagraphs = computed(() => {
      if (!chapterContent.value) return [];
      return chapterContent.value.split(/\n+/).filter(p => p.trim());
    });
    
    // 表格列定义
    const columns = [
      {
        title: '小说名称',
        dataIndex: 'name',
        key: 'name',
        ellipsis: true
      },
      {
        title: '上传时间',
        dataIndex: 'uploadTime',
        key: 'uploadTime',
      },
      {
        title: '文件大小',
        dataIndex: 'size',
        key: 'size',
        customRender: ({ text }) => formatFileSize(text)
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        customRender: ({ text }) => {
          return h(resolveComponent('a-tag'), { color: getStatusColor(text) }, () => getStatusText(text));
        }
      },
      {
        title: '操作',
        key: 'action',
      },
    ];
    
    // 上传前检查
    const beforeUpload = (file) => {
      const isAllowedType = file.type === 'text/plain' || 
                            file.type === 'application/epub+zip' || 
                            file.type === 'application/pdf';
      if (!isAllowedType) {
        message.error('只支持TXT、EPUB或PDF文件!');
        return false;
      }
      
      const isLessThan100MB = file.size / 1024 / 1024 < 100;
      if (!isLessThan100MB) {
        message.error('文件必须小于100MB!');
        return false;
      }
      
      currentFile.value = file;
      return false; // 阻止自动上传
    };
    
    // 上传小说
    const uploadNovel = async () => {
      if (!currentFile.value) {
        message.warning('请先选择一个文件');
        return;
      }
      
      uploading.value = true;
      try {
        const response = await apiStore.uploadNovel(currentFile.value);
        
        if (response && response.success) {
          message.success('小说上传成功!');
          currentFile.value = null;
          // 刷新小说列表
          loadNovels();
        } else {
          message.error('上传失败: ' + (response?.message || '未知错误'));
        }
      } catch (error) {
        message.error('上传失败: ' + (error.message || '未知错误'));
      } finally {
        uploading.value = false;
      }
    };
    
    // 取消上传
    const cancelUpload = () => {
      currentFile.value = null;
    };
    
    // 从URL导入小说
    const importFromUrl = async () => {
      if (!importUrl.value) {
        message.warning('请输入URL');
        return;
      }
      
      importing.value = true;
      try {
        const response = await apiStore.importNovelFromUrl(importUrl.value, {
          title: importTitle.value || undefined
        });
        
        if (response && response.success) {
          message.success('小说导入成功!');
          importUrl.value = '';
          importTitle.value = '';
          // 刷新小说列表
          loadNovels();
        } else {
          message.error('导入失败: ' + (response?.message || '未知错误'));
        }
      } catch (error) {
        message.error('导入失败: ' + (error.message || '未知错误'));
      } finally {
        importing.value = false;
      }
    };
    
    // 查看小说
    const viewNovel = async (novel) => {
      currentNovel.value = novel;
      previewVisible.value = true;
      previewLoading.value = true;
      
      try {
        // 获取章节列表
        const chapters = await apiStore.getNovelChapters(novel.id);
        novelChapters.value = chapters;
        
        // 如果有章节，默认选中第一章
        if (chapters.length > 0) {
          selectChapter(chapters[0]);
        }
      } catch (error) {
        message.error('获取小说章节失败: ' + (error.message || '未知错误'));
      } finally {
        previewLoading.value = false;
      }
    };
    
    // 选择章节
    const selectChapter = async (chapter) => {
      selectedChapter.value = chapter;
      previewLoading.value = true;
      
      try {
        // 获取章节内容
        const content = await apiStore.getChapterContent(currentNovel.value.id, chapter.id);
        if (content) {
          chapterContent.value = content.text || '';
        } else {
          chapterContent.value = '无法加载章节内容';
        }
      } catch (error) {
        chapterContent.value = '加载失败: ' + (error.message || '未知错误');
      } finally {
        previewLoading.value = false;
      }
    };
    
    // 处理小说
    const processNovel = (novel) => {
      // 跳转到小说处理页面，并携带小说ID
      router.push({
        path: '/novel',
        query: { id: novel.id }
      });
    };
    
    // 编辑配置
    const editConfig = async (novel) => {
      configNovelId.value = novel.id;
      previewLoading.value = true;
      
      try {
        // 获取小说配置
        const config = await apiStore.getNovelDetails(novel.id);
        
        if (config && config.config) {
          // 填充配置表单
          configForm.defaultVoice = config.config.defaultVoice || 'female_young';
          configForm.chapterMode = config.config.chapterMode || 'auto';
          configForm.chapterPattern = config.config.chapterPattern || '^第.{1,10}[章节]';
          configForm.splitByChapter = config.config.splitByChapter !== false;
          configForm.useVoiceMapping = config.config.useVoiceMapping !== false;
          configForm.detectEmotion = config.config.detectEmotion !== false;
        }
        
        configVisible.value = true;
      } catch (error) {
        message.error('获取小说配置失败: ' + (error.message || '未知错误'));
      } finally {
        previewLoading.value = false;
      }
    };
    
    // 保存配置
    const saveConfig = async () => {
      if (!configNovelId.value) return;
      
      savingConfig.value = true;
      
      try {
        const result = await apiStore.updateNovelConfig(configNovelId.value, configForm);
        
        if (result && result.success) {
          message.success('配置保存成功');
          configVisible.value = false;
        } else {
          message.error('配置保存失败: ' + (result?.message || '未知错误'));
        }
      } catch (error) {
        message.error('配置保存失败: ' + (error.message || '未知错误'));
      } finally {
        savingConfig.value = false;
      }
    };
    
    // 确认删除小说
    const confirmDeleteNovel = (novel) => {
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除小说"${novel.name}"吗？此操作不可恢复。`,
        okText: '删除',
        okType: 'danger',
        cancelText: '取消',
        onOk: async () => {
          try {
            const result = await apiStore.deleteNovel(novel.id);
            
            if (result && result.success) {
              message.success('小说已删除');
              loadNovels();
            } else {
              message.error('删除失败: ' + (result?.message || '未知错误'));
            }
          } catch (error) {
            message.error('删除失败: ' + (error.message || '未知错误'));
          }
        }
      });
    };
    
    // 格式化文件大小
    const formatFileSize = (bytes) => {
      if (!bytes || bytes === 0) return '0 B';
      
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    // 获取状态颜色
    const getStatusColor = (status) => {
      const colors = {
        'pending': 'blue',
        'processing': 'orange',
        'completed': 'green',
        'failed': 'red'
      };
      return colors[status] || 'default';
    };
    
    // 获取状态文本
    const getStatusText = (status) => {
      const texts = {
        'pending': '待处理',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败'
      };
      return texts[status] || '未知';
    };
    
    // 加载小说列表
    const loadNovels = async () => {
      loading.value = true;
      try {
        const data = await apiStore.getNovels();
        novels.value = data || [];
      } catch (error) {
        message.error('加载小说列表失败: ' + (error.message || '未知错误'));
        novels.value = [];
      } finally {
        loading.value = false;
      }
    };
    
    onMounted(() => {
      loadNovels();
    });
    
    return {
      novels,
      columns,
      loading,
      currentFile,
      uploading,
      beforeUpload,
      uploadNovel,
      cancelUpload,
      viewNovel,
      processNovel,
      editConfig,
      confirmDeleteNovel,
      formatFileSize,
      getStatusColor,
      getStatusText,
      
      // URL导入相关
      importUrl,
      importTitle,
      importing,
      importFromUrl,
      
      // 小说预览相关
      previewVisible,
      previewLoading,
      currentNovel,
      novelChapters,
      selectedChapter,
      chapterParagraphs,
      selectChapter,
      
      // 配置相关
      configVisible,
      configForm,
      savingConfig,
      saveConfig
    };
  }
});
</script>

<style scoped>
.novel-manage {
  width: 100%;
}

.mb-16 {
  margin-bottom: 16px;
}

.mt-16 {
  margin-top: 16px;
}

.ml-2 {
  margin-left: 8px;
}

.chapter-list {
  height: 400px;
  overflow-y: auto;
}

.active-chapter {
  background-color: #e6f7ff;
}

.chapter-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
  display: block;
}

.chapter-content {
  padding-left: 24px;
}

.content-panel {
  height: 400px;
  overflow-y: auto;
}

.chapter-header {
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.chapter-text {
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>