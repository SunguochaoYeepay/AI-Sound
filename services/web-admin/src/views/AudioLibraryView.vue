<template>
  <div class="audio-library">
    <a-row :gutter="16" class="mb-16">
      <a-col :span="24">
        <a-card title="音频库" :bordered="false">
          <p>管理和预览生成的音频文件</p>
        </a-card>
      </a-col>
    </a-row>
    
    <a-row :gutter="16">
      <a-col :span="24">
        <a-card title="音频文件列表">
          <a-table
            :dataSource="audioFiles"
            :columns="columns"
            :pagination="{ pageSize: 10 }"
            :loading="loading"
            rowKey="id"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'action'">
                <a-button type="link" @click="playAudio(record)">
                  <sound-outlined /> 播放
                </a-button>
                <a-button type="link" @click="downloadAudio(record)">
                  <download-outlined /> 下载
                </a-button>
                <a-button type="link" danger @click="deleteAudio(record)">
                  <delete-outlined /> 删除
                </a-button>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
    
    <!-- 音频播放器 -->
    <a-modal
      v-model:visible="playerVisible"
      title="音频播放器"
      :footer="null"
      width="500px"
    >
      <div class="audio-player">
        <h3>{{ currentAudio?.name || '未知音频' }}</h3>
        <audio
          v-if="currentAudio?.url"
          ref="audioPlayer"
          controls
          style="width: 100%"
          :src="currentAudio.url"
        ></audio>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { useApiStore } from '@/store/api';
import { SoundOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons-vue';

export default defineComponent({
  name: 'AudioLibraryView',
  components: {
    SoundOutlined,
    DownloadOutlined,
    DeleteOutlined
  },
  setup() {
    const apiStore = useApiStore();
    const audioFiles = ref([]);
    const loading = ref(true);
    const playerVisible = ref(false);
    const currentAudio = ref(null);
    const audioPlayer = ref(null);
    
    // 表格列定义
    const columns = [
      {
        title: '文件名',
        dataIndex: 'name',
        key: 'name',
      },
      {
        title: '创建时间',
        dataIndex: 'createTime',
        key: 'createTime',
      },
      {
        title: '时长',
        dataIndex: 'duration',
        key: 'duration',
      },
      {
        title: '文件大小',
        dataIndex: 'size',
        key: 'size',
        customRender: ({ text }) => `${(text / 1024 / 1024).toFixed(2)} MB`
      },
      {
        title: '来源',
        dataIndex: 'source',
        key: 'source',
      },
      {
        title: '操作',
        key: 'action',
      },
    ];
    
    // 播放音频
    const playAudio = (audio) => {
      currentAudio.value = audio;
      playerVisible.value = true;
      // 在模态框打开后，让音频自动播放
      setTimeout(() => {
        if (audioPlayer.value) {
          audioPlayer.value.play().catch(err => {
            console.error('音频自动播放失败:', err);
          });
        }
      }, 300);
    };
    
    // 下载音频
    const downloadAudio = (audio) => {
      if (!audio.url) {
        message.error('下载链接不可用');
        return;
      }
      
      // 创建临时下载链接
      const link = document.createElement('a');
      link.href = audio.url;
      link.download = audio.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      message.success('已开始下载');
    };
    
    // 删除音频
    const deleteAudio = (audio) => {
      // 实际项目中应该有确认对话框和API调用
      message.info(`删除音频: ${audio.name} - 功能开发中`);
    };
    
    // 加载音频文件列表
    const loadAudioFiles = async () => {
      loading.value = true;
      try {
        // 实际集成时，这里将调用API获取音频文件列表
        // const data = await apiStore.getAudioFiles();
        // 模拟数据
        setTimeout(() => {
          audioFiles.value = [
            {
              id: 'audio_1',
              name: '三体-第一章.mp3',
              createTime: '2025-05-18 16:45:12',
              duration: '15:30',
              size: 12345678,
              source: '小说批量生成',
              url: 'https://example.com/audio/1.mp3'
            },
            {
              id: 'audio_2',
              name: '三体-第二章.mp3',
              createTime: '2025-05-18 16:50:33',
              duration: '18:22',
              size: 15678901,
              source: '小说批量生成',
              url: 'https://example.com/audio/2.mp3'
            },
            {
              id: 'audio_3',
              name: '测试单句.wav',
              createTime: '2025-05-17 10:12:55',
              duration: '0:12',
              size: 1234567,
              source: '单句合成',
              url: 'https://example.com/audio/3.wav'
            }
          ];
          loading.value = false;
        }, 1000);
      } catch (error) {
        message.error('加载音频列表失败');
        loading.value = false;
      }
    };
    
    onMounted(() => {
      loadAudioFiles();
    });
    
    return {
      audioFiles,
      columns,
      loading,
      playerVisible,
      currentAudio,
      audioPlayer,
      playAudio,
      downloadAudio,
      deleteAudio
    };
  }
});
</script>

<style scoped>
.audio-library {
  width: 100%;
}

.audio-player {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
}
</style>