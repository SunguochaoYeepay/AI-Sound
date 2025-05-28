<template>
  <div class="system-settings">
    <a-page-header
      title="系统设置"
      sub-title="配置系统参数和偏好设置"
    />
    
    <a-row :gutter="24">
      <a-col :span="16">
        <a-card title="基本设置" class="settings-card">
          <a-form
            :model="basicSettings"
            layout="vertical"
            @finish="saveBasicSettings"
          >
            <a-form-item label="系统名称" name="system_name">
              <a-input 
                v-model:value="basicSettings.system_name" 
                placeholder="AI-Sound 语音合成系统"
              />
            </a-form-item>
            
            <a-form-item label="默认语言" name="default_language">
              <a-select 
                v-model:value="basicSettings.default_language"
                placeholder="选择默认语言"
                style="width: 200px"
              >
                <a-select-option value="zh-CN">中文（简体）</a-select-option>
                <a-select-option value="zh-TW">中文（繁体）</a-select-option>
                <a-select-option value="en-US">English</a-select-option>
                <a-select-option value="ja-JP">日本語</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item label="时区设置" name="timezone">
              <a-select 
                v-model:value="basicSettings.timezone"
                placeholder="选择时区"
                style="width: 300px"
                show-search
              >
                <a-select-option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</a-select-option>
                <a-select-option value="Asia/Tokyo">Asia/Tokyo (UTC+9)</a-select-option>
                <a-select-option value="America/New_York">America/New_York (UTC-5)</a-select-option>
                <a-select-option value="Europe/London">Europe/London (UTC+0)</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="basicLoading">
                保存基本设置
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
        
        <a-card title="TTS 设置" class="settings-card">
          <a-form
            :model="ttsSettings"
            layout="vertical"
            @finish="saveTtsSettings"
          >
            <a-form-item label="默认音频格式" name="default_format">
              <a-select 
                v-model:value="ttsSettings.default_format"
                placeholder="选择默认音频格式"
                style="width: 200px"
              >
                <a-select-option value="wav">WAV</a-select-option>
                <a-select-option value="mp3">MP3</a-select-option>
                <a-select-option value="flac">FLAC</a-select-option>
                <a-select-option value="ogg">OGG</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item label="默认采样率" name="default_sample_rate">
              <a-select 
                v-model:value="ttsSettings.default_sample_rate"
                placeholder="选择默认采样率"
                style="width: 200px"
              >
                <a-select-option :value="16000">16000 Hz</a-select-option>
                <a-select-option :value="22050">22050 Hz</a-select-option>
                <a-select-option :value="44100">44100 Hz</a-select-option>
                <a-select-option :value="48000">48000 Hz</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item label="最大并发任务数" name="max_concurrent_tasks">
              <a-input-number 
                v-model:value="ttsSettings.max_concurrent_tasks"
                :min="1"
                :max="10"
                style="width: 200px"
              />
            </a-form-item>
            
            <a-form-item label="任务超时时间（分钟）" name="task_timeout">
              <a-input-number 
                v-model:value="ttsSettings.task_timeout"
                :min="5"
                :max="120"
                style="width: 200px"
              />
            </a-form-item>
            
            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="ttsLoading">
                保存TTS设置
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
        
        <a-card title="存储设置" class="settings-card">
          <a-form
            :model="storageSettings"
            layout="vertical"
            @finish="saveStorageSettings"
          >
            <a-form-item label="输出目录" name="output_directory">
              <a-input 
                v-model:value="storageSettings.output_directory" 
                placeholder="/app/output"
                addon-before="路径"
              />
            </a-form-item>
            
            <a-form-item label="临时目录" name="temp_directory">
              <a-input 
                v-model:value="storageSettings.temp_directory" 
                placeholder="/app/temp"
                addon-before="路径"
              />
            </a-form-item>
            
            <a-form-item label="最大存储空间（GB）" name="max_storage_size">
              <a-input-number 
                v-model:value="storageSettings.max_storage_size"
                :min="1"
                :max="1000"
                style="width: 200px"
              />
            </a-form-item>
            
            <a-form-item label="自动清理" name="auto_cleanup">
              <a-switch 
                v-model:checked="storageSettings.auto_cleanup"
                checked-children="开启"
                un-checked-children="关闭"
              />
              <div class="setting-description">
                自动清理超过30天的临时文件和已完成任务
              </div>
            </a-form-item>
            
            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="storageLoading">
                保存存储设置
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>
      
      <a-col :span="8">
        <a-card title="系统信息" class="info-card">
          <a-spin :spinning="infoLoading">
            <a-descriptions bordered :column="1">
              <a-descriptions-item label="系统版本">
                {{ systemInfo.version || 'v1.0.0' }}
              </a-descriptions-item>
              <a-descriptions-item label="运行时间">
                {{ formatUptime(systemInfo.uptime) }}
              </a-descriptions-item>
              <a-descriptions-item label="CPU使用率">
                <a-progress 
                  :percent="Math.round(systemInfo.cpu_usage || 0)" 
                  size="small"
                  :status="systemInfo.cpu_usage > 80 ? 'exception' : 'normal'"
                />
              </a-descriptions-item>
              <a-descriptions-item label="内存使用">
                <a-progress 
                  :percent="Math.round(systemInfo.memory_usage || 0)" 
                  size="small"
                  :status="systemInfo.memory_usage > 80 ? 'exception' : 'normal'"
                />
              </a-descriptions-item>
              <a-descriptions-item label="磁盘使用">
                <a-progress 
                  :percent="Math.round(systemInfo.disk_usage || 0)" 
                  size="small"
                  :status="systemInfo.disk_usage > 90 ? 'exception' : 'normal'"
                />
              </a-descriptions-item>
              <a-descriptions-item label="活跃引擎">
                {{ systemInfo.active_engines || 0 }}
              </a-descriptions-item>
              <a-descriptions-item label="运行任务">
                {{ systemInfo.running_tasks || 0 }}
              </a-descriptions-item>
            </a-descriptions>
          </a-spin>
          
          <a-divider />
          
          <a-space direction="vertical" style="width: 100%">
            <a-button block @click="refreshSystemInfo" :loading="infoLoading">
              <template #icon><reload-outlined /></template>
              刷新系统信息
            </a-button>
            
            <a-button block type="primary" @click="exportSettings">
              <template #icon><download-outlined /></template>
              导出配置
            </a-button>
            
            <a-upload
              :before-upload="importSettings"
              :show-upload-list="false"
              accept=".json"
            >
              <a-button block>
                <template #icon><upload-outlined /></template>
                导入配置
              </a-button>
            </a-upload>
          </a-space>
        </a-card>
        
        <a-card title="日志管理" class="info-card">
          <a-space direction="vertical" style="width: 100%">
            <a-select 
              v-model:value="logLevel"
              placeholder="选择日志级别"
              style="width: 100%"
              @change="changeLogLevel"
            >
              <a-select-option value="DEBUG">DEBUG</a-select-option>
              <a-select-option value="INFO">INFO</a-select-option>
              <a-select-option value="WARNING">WARNING</a-select-option>
              <a-select-option value="ERROR">ERROR</a-select-option>
            </a-select>
            
            <a-button block @click="downloadLogs">
              <template #icon><download-outlined /></template>
              下载日志文件
            </a-button>
            
            <a-button block danger @click="clearLogs">
              <template #icon><delete-outlined /></template>
              清空日志
            </a-button>
          </a-space>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { systemAPI } from '../services/api';
import {
  ReloadOutlined,
  DownloadOutlined,
  UploadOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue';

export default defineComponent({
  name: 'SystemSettingsView',
  components: {
    ReloadOutlined,
    DownloadOutlined,
    UploadOutlined,
    DeleteOutlined
  },
  setup() {
    // 加载状态
    const basicLoading = ref(false);
    const ttsLoading = ref(false);
    const storageLoading = ref(false);
    const infoLoading = ref(false);
    
    // 基本设置
    const basicSettings = reactive({
      system_name: 'AI-Sound 语音合成系统',
      default_language: 'zh-CN',
      timezone: 'Asia/Shanghai'
    });
    
    // TTS设置
    const ttsSettings = reactive({
      default_format: 'wav',
      default_sample_rate: 22050,
      max_concurrent_tasks: 3,
      task_timeout: 30
    });
    
    // 存储设置
    const storageSettings = reactive({
      output_directory: '/app/output',
      temp_directory: '/app/temp',
      max_storage_size: 100,
      auto_cleanup: true
    });
    
    // 系统信息
    const systemInfo = ref({
      version: 'v1.0.0',
      uptime: 0,
      cpu_usage: 0,
      memory_usage: 0,
      disk_usage: 0,
      active_engines: 0,
      running_tasks: 0
    });
    
    // 日志级别
    const logLevel = ref('INFO');
    
    // 格式化运行时间
    const formatUptime = (seconds) => {
      if (!seconds) return '0秒';
      
      const days = Math.floor(seconds / 86400);
      const hours = Math.floor((seconds % 86400) / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      
      let result = '';
      if (days > 0) result += `${days}天`;
      if (hours > 0) result += `${hours}小时`;
      if (minutes > 0) result += `${minutes}分钟`;
      
      return result || '不到1分钟';
    };
    
    // 加载系统设置
    const loadSettings = async () => {
      try {
        const response = await systemAPI.getSettings();
        const settings = response.data || {};
        
        // 更新各个设置对象
        if (settings.basic) {
          Object.assign(basicSettings, settings.basic);
        }
        if (settings.tts) {
          Object.assign(ttsSettings, settings.tts);
        }
        if (settings.storage) {
          Object.assign(storageSettings, settings.storage);
        }
        if (settings.log_level) {
          logLevel.value = settings.log_level;
        }
      } catch (error) {
        console.error('加载系统设置失败:', error);
        message.error('加载系统设置失败: ' + (error.response?.data?.message || error.message));
      }
    };
    
    // 加载系统信息
    const loadSystemInfo = async () => {
      infoLoading.value = true;
      try {
        const response = await systemAPI.getSystemInfo();
        systemInfo.value = response.data || {};
      } catch (error) {
        console.error('加载系统信息失败:', error);
        message.error('加载系统信息失败: ' + (error.response?.data?.message || error.message));
      } finally {
        infoLoading.value = false;
      }
    };
    
    // 保存基本设置
    const saveBasicSettings = async () => {
      basicLoading.value = true;
      try {
        await systemAPI.updateSettings({
          basic: basicSettings
        });
        message.success('基本设置保存成功');
      } catch (error) {
        console.error('保存基本设置失败:', error);
        message.error('保存基本设置失败: ' + (error.response?.data?.message || error.message));
      } finally {
        basicLoading.value = false;
      }
    };
    
    // 保存TTS设置
    const saveTtsSettings = async () => {
      ttsLoading.value = true;
      try {
        await systemAPI.updateSettings({
          tts: ttsSettings
        });
        message.success('TTS设置保存成功');
      } catch (error) {
        console.error('保存TTS设置失败:', error);
        message.error('保存TTS设置失败: ' + (error.response?.data?.message || error.message));
      } finally {
        ttsLoading.value = false;
      }
    };
    
    // 保存存储设置
    const saveStorageSettings = async () => {
      storageLoading.value = true;
      try {
        await systemAPI.updateSettings({
          storage: storageSettings
        });
        message.success('存储设置保存成功');
      } catch (error) {
        console.error('保存存储设置失败:', error);
        message.error('保存存储设置失败: ' + (error.response?.data?.message || error.message));
      } finally {
        storageLoading.value = false;
      }
    };
    
    // 刷新系统信息
    const refreshSystemInfo = () => {
      loadSystemInfo();
    };
    
    // 更改日志级别
    const changeLogLevel = async (level) => {
      try {
        await systemAPI.updateSettings({
          log_level: level
        });
        message.success('日志级别已更新');
      } catch (error) {
        console.error('更新日志级别失败:', error);
        message.error('更新日志级别失败: ' + (error.response?.data?.message || error.message));
      }
    };
    
    // 导出配置
    const exportSettings = async () => {
      try {
        const response = await systemAPI.exportSettings();
        
        // 创建下载链接
        const blob = new Blob([JSON.stringify(response.data, null, 2)], {
          type: 'application/json'
        });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `ai-sound-settings-${new Date().toISOString().split('T')[0]}.json`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        message.success('配置导出成功');
      } catch (error) {
        console.error('导出配置失败:', error);
        message.error('导出配置失败: ' + (error.response?.data?.message || error.message));
      }
    };
    
    // 导入配置
    const importSettings = (file) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const settings = JSON.parse(e.target.result);
          
          await systemAPI.importSettings(settings);
          message.success('配置导入成功，正在重新加载...');
          
          // 重新加载设置
          setTimeout(() => {
            loadSettings();
            loadSystemInfo();
          }, 1000);
        } catch (error) {
          console.error('导入配置失败:', error);
          message.error('导入配置失败: ' + (error.response?.data?.message || error.message));
        }
      };
      reader.readAsText(file);
      
      // 阻止默认上传行为
      return false;
    };
    
    // 下载日志文件
    const downloadLogs = async () => {
      try {
        const response = await systemAPI.downloadLogs();
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `ai-sound-logs-${new Date().toISOString().split('T')[0]}.log`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        message.success('日志文件下载成功');
      } catch (error) {
        console.error('下载日志失败:', error);
        message.error('下载日志失败: ' + (error.response?.data?.message || error.message));
      }
    };
    
    // 清空日志
    const clearLogs = async () => {
      try {
        await systemAPI.clearLogs();
        message.success('日志已清空');
      } catch (error) {
        console.error('清空日志失败:', error);
        message.error('清空日志失败: ' + (error.response?.data?.message || error.message));
      }
    };
    
    // 组件挂载时加载数据
    onMounted(() => {
      loadSettings();
      loadSystemInfo();
      
      // 定时刷新系统信息（每30秒）
      const refreshInterval = setInterval(loadSystemInfo, 30000);
      
      // 组件卸载时清理定时器
      return () => {
        clearInterval(refreshInterval);
      };
    });
    
    return {
      // 加载状态
      basicLoading,
      ttsLoading,
      storageLoading,
      infoLoading,
      
      // 设置数据
      basicSettings,
      ttsSettings,
      storageSettings,
      systemInfo,
      logLevel,
      
      // 方法
      formatUptime,
      saveBasicSettings,
      saveTtsSettings,
      saveStorageSettings,
      refreshSystemInfo,
      changeLogLevel,
      exportSettings,
      importSettings,
      downloadLogs,
      clearLogs
    };
  }
});
</script>

<style scoped>
.system-settings {
  max-width: 100%;
}

.settings-card,
.info-card {
  margin-bottom: 24px;
}

.setting-description {
  margin-top: 8px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}
</style>