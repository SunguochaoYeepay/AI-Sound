<template>
  <div class="engine-config">
    <a-row :gutter="16">
      <a-col :span="24">
        <a-card class="mb-4">
          <a-alert type="info" show-icon>
            <template #message>
              <div>引擎参数设置可以调整TTS引擎的合成效果，不同引擎支持不同的参数配置</div>
            </template>
          </a-alert>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16">
      <a-col :span="24">
        <a-select 
          v-model:value="currentEngine" 
          style="width: 100%" 
          placeholder="选择TTS引擎" 
          @change="handleEngineChange"
          class="mb-4"
        >
          <a-select-option v-for="engine in engines" :key="engine.id" :value="engine.id">
            {{ engine.name }}
          </a-select-option>
        </a-select>
      </a-col>
    </a-row>

    <div v-if="currentEngine && engineConfig">
      <a-row :gutter="16">
        <a-col :span="24">
          <a-card :title="engineConfig.displayName + ' 参数配置'">
            <a-form 
              :model="formState" 
              :label-col="{ span: 6 }" 
              :wrapper-col="{ span: 14 }"
            >
              <!-- 动态渲染参数表单 -->
              <template v-for="param in engineConfig.params" :key="param.name">
                <!-- 浮点数类型参数 -->
                <a-form-item :label="param.label" v-if="param.type === 'float'">
                  <a-row>
                    <a-col :span="18">
                      <a-slider 
                        v-model:value="formState[param.name]" 
                        :min="param.min" 
                        :max="param.max" 
                        :step="0.01"
                      />
                    </a-col>
                    <a-col :span="6">
                      <a-input-number 
                        v-model:value="formState[param.name]" 
                        :min="param.min" 
                        :max="param.max" 
                        :step="0.01"
                        style="margin-left: 16px"
                      />
                    </a-col>
                  </a-row>
                </a-form-item>

                <!-- 整数类型参数 -->
                <a-form-item :label="param.label" v-else-if="param.type === 'int'">
                  <a-row>
                    <a-col :span="18">
                      <a-slider 
                        v-model:value="formState[param.name]" 
                        :min="param.min" 
                        :max="param.max" 
                        :step="1"
                      />
                    </a-col>
                    <a-col :span="6">
                      <a-input-number 
                        v-model:value="formState[param.name]" 
                        :min="param.min" 
                        :max="param.max" 
                        :step="1"
                        style="margin-left: 16px"
                      />
                    </a-col>
                  </a-row>
                </a-form-item>

                <!-- 选择类型参数 -->
                <a-form-item :label="param.label" v-else-if="param.type === 'select'">
                  <a-select v-model:value="formState[param.name]" style="width: 100%">
                    <a-select-option 
                      v-for="option in param.options" 
                      :key="option" 
                      :value="option"
                    >
                      {{ option }}
                    </a-select-option>
                  </a-select>
                </a-form-item>

                <!-- 布尔类型参数 -->
                <a-form-item :label="param.label" v-else-if="param.type === 'boolean'">
                  <a-switch v-model:checked="formState[param.name]" />
                </a-form-item>

                <!-- 字符串类型参数 -->
                <a-form-item :label="param.label" v-else>
                  <a-input v-model:value="formState[param.name]" />
                </a-form-item>
              </template>

              <a-form-item :wrapper-col="{ span: 14, offset: 6 }">
                <a-button type="primary" @click="saveEngineConfig">
                  保存配置
                </a-button>
                <a-button class="ml-2" @click="resetEngineConfig">
                  重置默认值
                </a-button>
              </a-form-item>
            </a-form>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="16" class="mt-4">
        <a-col :span="24">
          <a-card title="参数效果测试" v-if="engineConfig.params && engineConfig.params.length > 0">
            <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
              <a-form-item label="测试文本">
                <a-textarea v-model:value="testText" :rows="3" placeholder="请输入测试文本..." />
              </a-form-item>
              <a-form-item :wrapper-col="{ span: 18, offset: 4 }">
                <a-button type="primary" @click="testEngineParams" :loading="testing">
                  开始测试
                </a-button>
              </a-form-item>
            </a-form>
            <div v-if="testAudioUrl" class="mt-4">
              <audio controls style="width: 100%" :src="testAudioUrl"></audio>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <div v-else-if="currentEngine && !engineConfig" class="no-config">
      <a-empty description="该引擎暂无可配置参数" />
    </div>

    <div v-else class="no-engine">
      <a-empty description="请选择TTS引擎" />
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, watch } from 'vue';
import { message } from 'ant-design-vue';
import { engineAPI } from '../../services/api';

export default defineComponent({
  name: 'EngineConfigTab',
  setup() {
    // 移除 apiStore 引用;
    const engines = ref([]);
    const currentEngine = ref(null);
    const engineConfig = ref(null);
    const formState = reactive({});
    const testText = ref('你好，这是一段测试文本，用于测试TTS引擎参数设置的效果。');
    const testAudioUrl = ref('');
    const testing = ref(false);

    // 加载引擎列表
    const loadEngines = async () => {
      try {
        // 尝试从 API 获取引擎列表
        // 先直接使用默认列表，避免404错误
        engines.value = [
          { id: 'megatts3', name: 'MegaTTS3 引擎' },
          { id: 'espnet', name: 'ESPnet 引擎' },
          { id: 'bert-vits2', name: 'Bert-VITS2 引擎' }
        ];
        
        // 尝试获取引擎列表，但不阻塞界面加载
        try {
          const response = await apiStore.request('get', '/api/engines');
          if (response && response.engines) {
            // 如果获取成功，更新引擎列表
            const apiEngines = [];
            for (const [id, info] of Object.entries(response.engines)) {
              apiEngines.push({ id, name: info.name || id });
            }
            if (apiEngines.length > 0) {
              engines.value = apiEngines;
            }
          }
        } catch (e) {
          console.log('引擎列表获取失败，使用默认列表');
        }
      } catch (error) {
        message.error('加载引擎列表失败: ' + (error.message || '未知错误'));
      }
    };

    // 加载引擎配置
    const loadEngineConfig = async (engineId) => {
      try {
        // 从 API 获取引擎配置
        const config = await apiStore.request('get', `/api/engines/${engineId}/config`);
        if (config) {
          engineConfig.value = config;
          
          // 初始化表单状态
          if (engineConfig.value && engineConfig.value.params) {
            engineConfig.value.params.forEach(param => {
              formState[param.name] = param.default;
            });
          }
          return;
        }
        
        // 如果 API 没有返回数据，使用默认配置
        if (engineId === 'megatts3') {
          engineConfig.value = {
            displayName: 'MegaTTS3 引擎',
            params: [
              { name: 'speed', type: 'float', default: 1.0, min: 0.5, max: 2.0, label: '语速' },
              { name: 'pitch', type: 'float', default: 0.0, min: -12, max: 12, label: '音调' },
              { name: 'volume', type: 'float', default: 1.0, min: 0.0, max: 2.0, label: '音量' },
              { name: 'emotion', type: 'select', default: 'neutral', options: ['neutral', 'happy', 'sad', 'angry'], label: '情感' },
              { name: 'sdp_ratio', type: 'float', default: 0.2, min: 0.0, max: 1.0, label: '韵律多样性' }
            ]
          };
        } else if (engineId === 'espnet') {
          engineConfig.value = {
            displayName: 'ESPnet 引擎',
            params: [
              { name: 'speed', type: 'float', default: 1.0, min: 0.5, max: 2.0, label: '语速' },
              { name: 'pitch', type: 'float', default: 0.0, min: -12, max: 12, label: '音调' },
              { name: 'volume', type: 'float', default: 1.0, min: 0.0, max: 2.0, label: '音量' }
            ]
          };
        } else if (engineId === 'bert-vits2') {
          engineConfig.value = {
            displayName: 'Bert-VITS2 引擎',
            params: [
              { name: 'noise', type: 'float', default: 0.667, min: 0.0, max: 1.0, label: '音频噪声' },
              { name: 'noisew', type: 'float', default: 0.8, min: 0.0, max: 1.0, label: '音长噪声' },
              { name: 'length', type: 'float', default: 1.0, min: 0.1, max: 2.0, label: '语速控制' },
              { name: 'sdp_ratio', type: 'float', default: 0.2, min: 0.0, max: 1.0, label: 'SDP混合比' },
              { name: 'style_weight', type: 'float', default: 0.7, min: 0.0, max: 1.0, label: '风格强度' }
            ]
          };
        } else {
          engineConfig.value = null;
        }

        // 初始化表单状态
        if (engineConfig.value && engineConfig.value.params) {
          engineConfig.value.params.forEach(param => {
            formState[param.name] = param.default;
          });
        }
      } catch (error) {
        message.error('加载引擎配置失败: ' + (error.message || '未知错误'));
        
        // 如果发生错误，使用默认配置
        if (engineId === 'megatts3') {
          engineConfig.value = {
            displayName: 'MegaTTS3 引擎',
            params: [
              { name: 'speed', type: 'float', default: 1.0, min: 0.5, max: 2.0, label: '语速' },
              { name: 'pitch', type: 'float', default: 0.0, min: -12, max: 12, label: '音调' },
              { name: 'volume', type: 'float', default: 1.0, min: 0.0, max: 2.0, label: '音量' }
            ]
          };
          
          // 初始化表单状态
          engineConfig.value.params.forEach(param => {
            formState[param.name] = param.default;
          });
        }
      }
    };

    // 处理引擎变更
    const handleEngineChange = (value) => {
      loadEngineConfig(value);
    };

    // 保存引擎配置
    const saveEngineConfig = async () => {
      try {
        // 调用 API 保存引擎配置
        const response = await apiStore.request('post', `/api/engines/${currentEngine.value}/config`, formState);
        
        if (response && response.status === 'success') {
          message.success('引擎参数配置保存成功');
        } else {
          message.warning('保存引擎参数配置可能失败');
        }
      } catch (error) {
        message.error('保存引擎参数配置失败: ' + (error.message || '未知错误'));
      }
    };

    // 重置引擎配置为默认值
    const resetEngineConfig = () => {
      if (engineConfig.value && engineConfig.value.params) {
        engineConfig.value.params.forEach(param => {
          formState[param.name] = param.default;
        });
        message.info('已重置为默认参数');
      }
    };

    // 测试引擎参数
    const testEngineParams = async () => {
      if (!testText.value.trim()) {
        message.warning('请输入测试文本');
        return;
      }

      testing.value = true;
      try {
        // 调用 API 测试引擎参数
        const response = await apiStore.request('post', `/api/engines/${currentEngine.value}/test`, {
          text: testText.value,
          params: formState
        });
        
        if (response && response.audioUrl) {
          // 使用返回的音频URL
          testAudioUrl.value = response.audioUrl;
          message.success('参数测试完成');
        } else {
          // 如果没有音频URL，使用空音频
          testAudioUrl.value = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=';
          message.warning('参数测试可能失败，返回空音频');
        }
      } catch (error) {
        message.error('测试引擎参数失败: ' + (error.message || '未知错误'));
        // 返回空音频
        testAudioUrl.value = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=';
      } finally {
        testing.value = false;
      }
    };

    // 初始化
    loadEngines();

    return {
      engines,
      currentEngine,
      engineConfig,
      formState,
      testText,
      testAudioUrl,
      testing,
      handleEngineChange,
      saveEngineConfig,
      resetEngineConfig,
      testEngineParams
    };
  }
});
</script>

<style scoped>
.engine-config {
  width: 100%;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.ml-2 {
  margin-left: 8px;
}

.no-config, .no-engine {
  padding: 48px 0;
}
</style>