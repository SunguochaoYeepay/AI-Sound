<template>
  <div class="settings">
    <a-row :gutter="16" class="mb-16">
      <a-col :span="24">
        <a-card title="系统设置" :bordered="false">
          <p>配置系统参数和资源</p>
        </a-card>
      </a-col>
    </a-row>
    
    <a-row :gutter="16">
      <a-col :span="24">
        <a-card>
          <a-tabs default-active-key="1">
            <a-tab-pane key="1" tab="基本设置">
              <a-form 
                :model="basicSettings" 
                :label-col="{ span: 6 }" 
                :wrapper-col="{ span: 14 }"
              >
                <a-form-item label="系统名称">
                  <a-input v-model:value="basicSettings.systemName" />
                </a-form-item>
                
                <a-form-item label="TTS引擎模型">
                  <a-select v-model:value="basicSettings.ttsModel">
                    <a-select-option value="MegaTTS3-zh-en-v1.0">MegaTTS3-zh-en-v1.0</a-select-option>
                    <a-select-option value="MegaTTS3-zh-en-v2.0">MegaTTS3-zh-en-v2.0</a-select-option>
                  </a-select>
                </a-form-item>
                
                <a-form-item label="显存占用限制">
                  <a-slider 
                    v-model:value="basicSettings.vramLimit"
                    :min="1"
                    :max="48"
                    :marks="{ 1: '1GB', 8: '8GB', 16: '16GB', 24: '24GB', 32: '32GB', 48: '48GB' }"
                  />
                </a-form-item>
                
                <a-form-item label="最大并行任务数">
                  <a-input-number 
                    v-model:value="basicSettings.maxTasks" 
                    :min="1" 
                    :max="16"
                  />
                </a-form-item>
                
                <a-form-item label="音频输出格式">
                  <a-radio-group v-model:value="basicSettings.audioFormat">
                    <a-radio value="wav">WAV (无损)</a-radio>
                    <a-radio value="mp3">MP3 (压缩)</a-radio>
                  </a-radio-group>
                </a-form-item>
                
                <a-form-item label="音频采样率">
                  <a-select v-model:value="basicSettings.sampleRate">
                    <a-select-option value="22050">22.05kHz</a-select-option>
                    <a-select-option value="24000">24kHz</a-select-option>
                    <a-select-option value="44100">44.1kHz</a-select-option>
                    <a-select-option value="48000">48kHz</a-select-option>
                  </a-select>
                </a-form-item>
                
                <a-form-item :wrapper-col="{ span: 14, offset: 6 }">
                  <a-button type="primary" @click="saveBasicSettings">
                    保存设置
                  </a-button>
                  <a-button class="ml-2" @click="resetBasicSettings">
                    重置
                  </a-button>
                </a-form-item>
              </a-form>
            </a-tab-pane>
            
            <a-tab-pane key="2" tab="高级设置">
              <a-form 
                :model="advancedSettings" 
                :label-col="{ span: 6 }" 
                :wrapper-col="{ span: 14 }"
              >
                <a-form-item label="API密钥">
                  <a-input-password v-model:value="advancedSettings.apiKey" />
                  <a-button size="small" type="link" @click="generateApiKey">
                    重新生成
                  </a-button>
                </a-form-item>
                
                <a-form-item label="允许远程访问">
                  <a-switch v-model:checked="advancedSettings.allowRemoteAccess" />
                </a-form-item>
                
                <a-form-item label="日志级别">
                  <a-select v-model:value="advancedSettings.logLevel">
                    <a-select-option value="debug">调试</a-select-option>
                    <a-select-option value="info">信息</a-select-option>
                    <a-select-option value="warning">警告</a-select-option>
                    <a-select-option value="error">错误</a-select-option>
                  </a-select>
                </a-form-item>
                
                <a-form-item label="缓存目录">
                  <a-input v-model:value="advancedSettings.cacheDir" />
                  <a-button size="small" type="link" @click="cleanCache">
                    清理缓存
                  </a-button>
                </a-form-item>
                
                <a-form-item :wrapper-col="{ span: 14, offset: 6 }">
                  <a-button type="primary" @click="saveAdvancedSettings">
                    保存设置
                  </a-button>
                </a-form-item>
              </a-form>
            </a-tab-pane>
            
            <a-tab-pane key="3" tab="资源管理">
              <a-list item-layout="horizontal" :data-source="resources">
                <template #header>
                  <div>模型资源</div>
                </template>
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-list-item-meta
                      :title="item.name"
                      :description="item.description"
                    >
                      <template #avatar>
                        <a-avatar :style="{ backgroundColor: item.installed ? '#52c41a' : '#ff4d4f' }">
                          {{ item.installed ? '已' : '缺' }}
                        </a-avatar>
                      </template>
                    </a-list-item-meta>
                    <template #actions>
                      <a-button 
                        v-if="!item.installed" 
                        type="primary" 
                        @click="downloadResource(item)"
                        :loading="item.downloading"
                      >
                        下载
                      </a-button>
                      <a-button 
                        v-else 
                        type="default" 
                        @click="checkResource(item)"
                      >
                        校验
                      </a-button>
                    </template>
                  </a-list-item>
                </template>
              </a-list>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { useApiStore } from '@/store/api';

export default defineComponent({
  name: 'SettingsView',
  setup() {
    const apiStore = useApiStore();
    const basicSettings = reactive({
      systemName: 'MegaTTS3管理系统',
      ttsModel: 'MegaTTS3-zh-en-v1.0',
      vramLimit: 8,
      maxTasks: 4,
      audioFormat: 'wav',
      sampleRate: 24000
    });
    
    const advancedSettings = reactive({
      apiKey: '****************************************',
      allowRemoteAccess: false,
      logLevel: 'info',
      cacheDir: '/tmp/megatts3/cache'
    });
    
    const resources = ref([
      {
        id: 1,
        name: 'MegaTTS3-zh-en-v1.0',
        description: '基础中英文双语语音合成模型',
        installed: true,
        downloading: false
      },
      {
        id: 2,
        name: 'MegaTTS3-style-transfer-v2',
        description: '语音风格迁移模型',
        installed: false,
        downloading: false
      },
      {
        id: 3,
        name: 'MegaTTS3-soundfield-v1',
        description: '声场处理增强模型',
        installed: false,
        downloading: false
      }
    ]);
    
    // 加载设置
    const loadSettings = async () => {
      try {
        // 实际项目中，这里会从API获取设置
        // const settings = await apiStore.getSystemSettings();
        // Object.assign(basicSettings, settings.basic);
        // Object.assign(advancedSettings, settings.advanced);
        
        // 模拟加载
        setTimeout(() => {
          message.success('设置加载成功');
        }, 500);
      } catch (error) {
        message.error('加载设置失败: ' + (error.message || '未知错误'));
      }
    };
    
    // 保存基本设置
    const saveBasicSettings = async () => {
      try {
        // 实际项目中，这里会调用API保存设置
        // await apiStore.saveSystemSettings({ basic: basicSettings });
        
        // 模拟保存
        setTimeout(() => {
          message.success('基本设置保存成功');
        }, 500);
      } catch (error) {
        message.error('保存失败: ' + (error.message || '未知错误'));
      }
    };
    
    // 重置基本设置
    const resetBasicSettings = () => {
      Object.assign(basicSettings, {
        systemName: 'MegaTTS3管理系统',
        ttsModel: 'MegaTTS3-zh-en-v1.0',
        vramLimit: 8,
        maxTasks: 4,
        audioFormat: 'wav',
        sampleRate: 24000
      });
      message.info('已重置为默认设置');
    };
    
    // 保存高级设置
    const saveAdvancedSettings = async () => {
      try {
        // 实际项目中，这里会调用API保存设置
        // await apiStore.saveSystemSettings({ advanced: advancedSettings });
        
        // 模拟保存
        setTimeout(() => {
          message.success('高级设置保存成功');
        }, 500);
      } catch (error) {
        message.error('保存失败: ' + (error.message || '未知错误'));
      }
    };
    
    // 生成API密钥
    const generateApiKey = () => {
      // 模拟生成API密钥
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
      let key = '';
      for (let i = 0; i < 40; i++) {
        key += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      advancedSettings.apiKey = key;
      message.success('已生成新的API密钥');
    };
    
    // 清理缓存
    const cleanCache = async () => {
      try {
        // 实际项目中，这里会调用API清理缓存
        // await apiStore.cleanCache();
        
        // 模拟操作
        setTimeout(() => {
          message.success('缓存清理成功');
        }, 800);
      } catch (error) {
        message.error('清理缓存失败: ' + (error.message || '未知错误'));
      }
    };
    
    // 下载资源
    const downloadResource = async (resource) => {
      const targetResource = resources.value.find(r => r.id === resource.id);
      if (targetResource) {
        targetResource.downloading = true;
        
        try {
          // 实际项目中，这里会调用API下载资源
          // await apiStore.downloadResource(resource.id);
          
          // 模拟下载
          setTimeout(() => {
            targetResource.installed = true;
            targetResource.downloading = false;
            message.success(`资源 ${resource.name} 下载成功`);
          }, 3000);
        } catch (error) {
          targetResource.downloading = false;
          message.error('下载失败: ' + (error.message || '未知错误'));
        }
      }
    };
    
    // 校验资源
    const checkResource = async (resource) => {
      try {
        // 实际项目中，这里会调用API校验资源
        // const result = await apiStore.checkResource(resource.id);
        
        // 模拟校验
        setTimeout(() => {
          message.success(`资源 ${resource.name} 校验通过`);
        }, 1000);
      } catch (error) {
        message.error('校验失败: ' + (error.message || '未知错误'));
      }
    };
    
    onMounted(() => {
      loadSettings();
    });
    
    return {
      basicSettings,
      advancedSettings,
      resources,
      saveBasicSettings,
      resetBasicSettings,
      saveAdvancedSettings,
      generateApiKey,
      cleanCache,
      downloadResource,
      checkResource
    };
  }
});
</script>

<style scoped>
.settings {
  width: 100%;
}

.ml-2 {
  margin-left: 8px;
}
</style>