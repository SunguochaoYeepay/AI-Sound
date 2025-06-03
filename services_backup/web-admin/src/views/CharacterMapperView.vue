<template>
  <div class="character-mapper-container">
    <a-page-header
      title="角色声音映射"
      sub-title="为小说角色分配合适的声音"
    />
    
    <a-row :gutter="24">
      <a-col :span="16">
        <a-card title="角色管理" class="character-card">
          <!-- 角色列表 -->
          <a-table
            :dataSource="characterList"
            :columns="characterColumns"
            :loading="loading"
            rowKey="name"
            :pagination="{ pageSize: 10 }"
          >
            <template #headerCell="{ column }">
              <template v-if="column.key === 'action'">
                <a-button type="primary" size="small" @click="showCreateModal">
                  <template #icon><plus-outlined /></template>
                  添加角色
                </a-button>
              </template>
            </template>
            
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <a @click="selectCharacter(record)">{{ record.name }}</a>
              </template>
              
              <template v-else-if="column.key === 'voice'">
                <a-tag color="blue" v-if="record.voice_name">{{ record.voice_name }}</a-tag>
                <a-tag color="red" v-else>未设置</a-tag>
              </template>
              
              <template v-else-if="column.key === 'attributes'">
                <a-tag v-for="attr in record.attributes || []" :key="attr">{{ attr }}</a-tag>
              </template>
              
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button type="link" size="small" @click="editCharacter(record)">
                    <template #icon><edit-outlined /></template>
                    编辑
                  </a-button>
                  <a-button type="link" size="small" danger @click="confirmDeleteCharacter(record)">
                    <template #icon><delete-outlined /></template>
                    删除
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
      
      <a-col :span="8">
        <a-card title="小说角色分析" class="analyzer-card">
          <p>上传或粘贴小说文本，自动识别其中的角色，并为角色推荐合适的声音。</p>
          
          <a-textarea
            v-model:value="novelText"
            placeholder="在此处粘贴小说文本（段落或章节）"
            :rows="6"
            allow-clear
          />
          
          <div class="analyzer-buttons">
            <a-upload
              :beforeUpload="beforeNovelUpload"
              :showUploadList="false"
              accept=".txt"
            >
              <a-button style="margin-right: 8px">
                <template #icon><upload-outlined /></template>
                上传TXT
              </a-button>
            </a-upload>
            <a-button 
              type="primary" 
              :disabled="!novelText.trim()" 
              :loading="analyzing" 
              @click="analyzeNovel"
            >
              <template #icon><scan-outlined /></template>
              分析角色
            </a-button>
          </div>
          
          <a-divider v-if="analyzedCharacters.length > 0">分析结果</a-divider>
          
          <a-spin :spinning="analyzing">
            <div v-if="analyzedCharacters.length > 0" class="analyzer-results">
              <p>共识别出 {{ analyzedCharacters?.length }} 个角色：</p>
              
              <a-list size="small" bordered>
                <a-list-item v-for="character in analyzedCharacters" :key="character.name">
                  <a-list-item-meta :title="character.name">
                    <template #description>
                      出现次数: {{ character.count }}
                    </template>
                  </a-list-item-meta>
                  <template #actions>
                    <a key="map" @click="mapAnalyzedCharacter(character)">分配声音</a>
                  </template>
                </a-list-item>
              </a-list>
              
              <a-button 
                type="primary" 
                style="margin-top: 16px" 
                @click="mapAllCharacters"
              >
                一键映射全部角色
              </a-button>
            </div>
          </a-spin>
        </a-card>
      </a-col>
    </a-row>
    
    <!-- 创建/编辑角色对话框 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="modalMode === 'create' ? '添加角色' : '编辑角色'"
      @ok="modalMode === 'create' ? createCharacter() : updateCharacter()"
      :confirm-loading="modalLoading"
      width="600px"
    >
      <a-form :model="characterForm" layout="vertical">
        <a-form-item 
          label="角色名称" 
          name="name" 
          :rules="[{ required: true, message: '请输入角色名称' }]"
        >
          <a-input v-model:value="characterForm.name" placeholder="输入角色名称" />
        </a-form-item>
        
        <a-form-item label="选择声音" name="voice_id">
          <a-select
            v-model:value="characterForm.voice_id"
            placeholder="选择声音"
            style="width: 100%"
            :options="voiceOptions"
            :loading="voicesLoading"
            allow-clear
            show-search
            :filter-option="filterVoiceOption"
          />
        </a-form-item>
        
        <a-form-item label="角色属性" name="attributes">
          <a-select
            v-model:value="characterForm.attributes"
            mode="tags"
            placeholder="输入角色属性"
            style="width: 100%"
            :options="attributeOptions"
            allow-clear
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, computed, onMounted } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { characterAPI, voiceAPI } from '../services/api';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  ScanOutlined
} from '@ant-design/icons-vue';

export default defineComponent({
  name: 'CharacterMapperView',
  components: {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    UploadOutlined,
    ScanOutlined
  },
  setup() {
    const loading = ref(false);
    const voicesLoading = ref(false);
    
    // 角色列表
    const characterList = ref([]);
    
    // 声音列表
    const voiceList = ref([]);
    
    // 表格列定义
    const characterColumns = [
      {
        title: '角色名称',
        dataIndex: 'name',
        key: 'name',
        sorter: (a, b) => a.name.localeCompare(b.name),
      },
      {
        title: '声音',
        dataIndex: 'voice_name',
        key: 'voice',
        sorter: (a, b) => (a.voice_name || '').localeCompare(b.voice_name || '')
      },
      {
        title: '属性',
        dataIndex: 'attributes',
        key: 'attributes'
      },
      {
        title: '操作',
        key: 'action',
        width: 150,
      },
    ];
    
    // 角色表单
    const characterForm = reactive({
      name: '',
      voice_id: undefined,
      attributes: []
    });
    
    // 模态框控制
    const modalVisible = ref(false);
    const modalLoading = ref(false);
    const modalMode = ref('create'); // 'create' 或 'edit'
    const editingCharacterName = ref('');
    
    // 角色分析
    const novelText = ref('');
    const analyzing = ref(false);
    const analyzedCharacters = ref([]);
    
    // 声音选项
    const voiceOptions = computed(() => {
      return voiceList.value?.map(voice => ({
        value: voice.id,
        label: voice.name,
        gender: voice.attributes?.gender,
        age: voice.attributes?.age_group
      }));
    });
    
    // 角色属性选项
    const attributeOptions = [
      { value: 'protagonist', label: '主角' },
      { value: 'antagonist', label: '反派' },
      { value: 'supporting', label: '配角' },
      { value: 'male', label: '男性' },
      { value: 'female', label: '女性' },
      { value: 'child', label: '儿童' },
      { value: 'young', label: '青年' },
      { value: 'middle', label: '中年' },
      { value: 'old', label: '老年' }
    ];
    
    // 加载角色列表
    const fetchCharacters = async () => {
      loading.value = true;
      try {
        const response = await characterAPI.getCharacters();
        characterList.value = response.data?.characters || [];
      } catch (error) {
        console.error('获取角色列表失败:', error);
        message.error('获取角色列表失败: ' + (error.response?.data?.message || error.message));
      } finally {
        loading.value = false;
      }
    };
    
    // 加载声音列表
    const fetchVoices = async () => {
      voicesLoading.value = true;
      try {
        const response = await voiceAPI.getVoices();
        voiceList.value = response.voices || [];
      } catch (error) {
        console.error('获取声音列表失败:', error);
        message.error('获取声音列表失败: ' + (error.response?.data?.message || error.message));
      } finally {
        voicesLoading.value = false;
      }
    };
    
    // 显示创建角色对话框
    const showCreateModal = () => {
      // 重置表单
      characterForm.name = '';
      characterForm.voice_id = undefined;
      characterForm.attributes = [];
      
      modalMode.value = 'create';
      modalVisible.value = true;
    };
    
    // 创建角色
    const createCharacter = async () => {
      // 验证表单
      if (!characterForm.name.trim()) {
        message.warning('请输入角色名称');
        return;
      }
      
      modalLoading.value = true;
      
      try {
        // 调用API创建角色
        await characterAPI.createCharacter({
          name: characterForm.name,
          voice_id: characterForm.voice_id,
          attributes: characterForm.attributes
        });
        
        message.success('角色创建成功');
        modalVisible.value = false;
        
        // 刷新角色列表
        fetchCharacters();
      } catch (error) {
        console.error('创建角色失败:', error);
        message.error('创建角色失败: ' + (error.response?.data?.message || error.message));
      } finally {
        modalLoading.value = false;
      }
    };
    
    // 选择角色
    const selectCharacter = (character) => {
      // 获取角色详情或执行其他操作
      message.info(`已选择角色: ${character.name}`);
    };
    
    // 编辑角色
    const editCharacter = (character) => {
      // 设置表单数据
      characterForm.name = character.name;
      characterForm.voice_id = character.voice_id;
      characterForm.attributes = character.attributes || [];
      
      editingCharacterName.value = character.name;
      modalMode.value = 'edit';
      modalVisible.value = true;
    };
    
    // 更新角色
    const updateCharacter = async () => {
      // 验证表单
      if (!characterForm.name.trim()) {
        message.warning('请输入角色名称');
        return;
      }
      
      modalLoading.value = true;
      
      try {
        // 调用API更新角色
        await characterAPI.updateCharacter(editingCharacterName.value, {
          name: characterForm.name,
          voice_id: characterForm.voice_id,
          attributes: characterForm.attributes
        });
        
        message.success('角色更新成功');
        modalVisible.value = false;
        
        // 刷新角色列表
        fetchCharacters();
      } catch (error) {
        console.error('更新角色失败:', error);
        message.error('更新角色失败: ' + (error.response?.data?.message || error.message));
      } finally {
        modalLoading.value = false;
      }
    };
    
    // 确认删除角色
    const confirmDeleteCharacter = (character) => {
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除角色"${character.name}"吗？此操作不可恢复。`,
        okText: '删除',
        okType: 'danger',
        cancelText: '取消',
        async onOk() {
          try {
            // 调用API删除角色
            await characterAPI.deleteCharacter(character.id || character.name);
            message.success('角色已删除');
            
            // 从列表中移除
            characterList.value = characterList.value?.filter(item => item.name !== character.name);
          } catch (error) {
            console.error('删除角色失败:', error);
            message.error('删除角色失败: ' + (error.response?.data?.message || error.message));
          }
        }
      });
    };
    
    // 上传小说文件前处理
    const beforeNovelUpload = (file) => {
      // 验证文件类型
      const isText = file.type === 'text/plain' || /\.txt$/i.test(file.name);
      if (!isText) {
        message.error('只能上传TXT文本文件！');
        return false;
      }
      
      // 读取文件内容
      const reader = new FileReader();
      reader.onload = (e) => {
        novelText.value = e.target.result;
      };
      reader.readAsText(file);
      
      // 阻止默认上传行为
      return false;
    };
    
    // 分析小说角色
    const analyzeNovel = async () => {
      if (!novelText.value.trim()) {
        message.warning('请输入小说文本');
        return;
      }
      
      analyzing.value = true;
      analyzedCharacters.value = [];
      
      try {
        // 简单的本地角色识别（正则匹配）
        const text = novelText.value;
        const characterPattern = /[""「」'']([^""「」''。，！？]{1,10})[""「」'']/g;
        const characters = new Map();
        
        let match;
        while ((match = characterPattern.exec(text)) !== null) {
          const name = match[1].trim();
          if (name.length > 0 && name?.length <= 10) {
            characters.set(name, (characters.get(name) || 0) + 1);
          }
        }
        
        // 转换为数组并按出现频率排序
        const characterArray = Array.from(characters.entries())
          .map(([name, count]) => ({ name, count }))
          .filter(char => char.count >= 2) // 过滤出现次数太少的
          .sort((a, b) => b.count - a.count)
          .slice(0, 20); // 最多显示20个角色
        
        analyzedCharacters.value = characterArray;
        
        if (characterArray?.length === 0) {
          message.info('未识别出任何角色，请检查文本格式');
        } else {
          message.success(`成功识别出 ${characterArray?.length} 个角色`);
        }
      } catch (error) {
        console.error('分析角色失败:', error);
        message.error('分析角色失败: ' + error.message);
      } finally {
        analyzing.value = false;
      }
    };
    
    // 为分析出的角色分配声音
    const mapAnalyzedCharacter = (character) => {
      // 设置表单数据
      characterForm.name = character.name;
      characterForm.voice_id = undefined;
      characterForm.attributes = [];
      
      modalMode.value = 'create';
      modalVisible.value = true;
    };
    
    // 一键映射所有角色
    const mapAllCharacters = async () => {
      if (analyzedCharacters.value?.length === 0) {
        message.warning('没有可映射的角色');
        return;
      }
      
      if (voiceList.value?.length === 0) {
        message.warning('没有可用的声音，请先添加声音');
        return;
      }
      
      try {
        message.loading('正在为角色分配声音...', 0);
        
        // 逐个映射角色
        let successCount = 0;
        
        for (const character of analyzedCharacters.value) {
          // 根据角色名称推测性别
          const nameHint = character.name;
          const isMale = /先生|男|爸|哥|弟|叔|爷|王|李|张|刘/.test(nameHint);
          const isFemale = /女士|女|妈|姐|妹|婶|奶|娜|莉|琳|玉/.test(nameHint);
          
          // 筛选声音
          let voices = voiceList.value;
          if (isMale) {
            voices = voiceList.value?.filter(v => v.attributes?.gender === 'male');
          } else if (isFemale) {
            voices = voiceList.value?.filter(v => v.attributes?.gender === 'female');
          }
          
          if (voices?.length === 0) {
            voices = voiceList.value; // 如果没有匹配的，使用所有声音
          }
          
          // 随机选择一个声音
          const voiceId = voices[Math.floor(Math.random() * voices?.length)].id;
          
          // 创建角色映射
          try {
            await characterAPI.createCharacter({
              name: character.name,
              voice_id: voiceId,
              attributes: isMale ? ['male'] : isFemale ? ['female'] : []
            });
            
            successCount++;
          } catch (error) {
            console.error(`映射角色 ${character.name} 失败:`, error);
          }
        }
        
        message.destroy();
        if (successCount > 0) {
          message.success(`成功映射 ${successCount} 个角色`);
          fetchCharacters(); // 刷新角色列表
        } else {
          message.warning('没有成功映射任何角色');
        }
      } catch (error) {
        message.destroy();
        console.error('角色映射失败:', error);
        message.error('角色映射失败: ' + (error.response?.data?.message || error.message));
      }
    };
    
    // 声音选择过滤
    const filterVoiceOption = (input, option) => {
      return (option?.label ?? '').toLowerCase().includes(input.toLowerCase());
    };
    
    // 组件加载时获取角色和声音列表
    onMounted(() => {
      fetchCharacters();
      fetchVoices();
    });
    
    return {
      // 数据
      loading,
      voicesLoading,
      characterList,
      characterColumns,
      characterForm,
      modalVisible,
      modalLoading,
      modalMode,
      novelText,
      analyzing,
      analyzedCharacters,
      voiceOptions,
      attributeOptions,
      
      // 方法
      showCreateModal,
      createCharacter,
      selectCharacter,
      editCharacter,
      updateCharacter,
      confirmDeleteCharacter,
      beforeNovelUpload,
      analyzeNovel,
      mapAnalyzedCharacter,
      mapAllCharacters,
      filterVoiceOption
    };
  }
});
</script>

<style scoped>
.character-mapper-container {
  max-width: 100%;
}

.character-card,
.analyzer-card {
  margin-bottom: 24px;
}

.analyzer-buttons {
  margin-top: 16px;
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}

.analyzer-results {
  margin-top: 16px;
}
</style> 