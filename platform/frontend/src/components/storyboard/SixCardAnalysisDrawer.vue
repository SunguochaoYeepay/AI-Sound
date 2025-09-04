<template>
  <a-drawer
    :open="open"
    :title="`🎯 段落 ${selectedResult?._metadata?.segment_index || ''} 的6卡分析`"
    placement="right"
    width="800"
    :closable="true"
    @close="$emit('close')"
  >
    <div v-if="selectedResult" class="six-card-drawer-content">
      <!-- 横向tabs导航 -->
      <a-tabs 
        v-model:activeKey="activeTabKey" 
        type="card" 
        size="small"
        class="six-card-tabs"
      >
        <!-- 故事卡 -->
        <a-tab-pane key="story" tab="📖 故事卡">
          <div class="tab-content">
            <div class="card-content">
              <p><strong>主题:</strong> {{ selectedResult.story_card?.theme || '暂无数据' }}</p>
              <p><strong>情节要点:</strong> {{ selectedResult.story_card?.plot_point || '暂无数据' }}</p>
              <p><strong>叙述目的:</strong> {{ selectedResult.story_card?.narrative_purpose || '暂无数据' }}</p>
            </div>
          </div>
        </a-tab-pane>
        
        <!-- 角色卡 -->
        <a-tab-pane key="character" tab="🎭 角色卡">
          <div class="tab-content">
            <div class="card-content">
              <div v-if="selectedResult.character_card?.characters && selectedResult.character_card.characters.length > 0">
                <div v-for="(character, charIndex) in selectedResult.character_card.characters" :key="charIndex" class="character-item">
                  <div class="character-header">
                    <span class="character-name">{{ character.name }}</span>
                    <a-tag color="blue" size="small">角色</a-tag>
                  </div>
                  <p><strong>动作:</strong> {{ character.actions || '无' }}</p>
                  <p><strong>情绪:</strong> {{ Array.isArray(character.emotions) ? character.emotions.join(', ') : character.emotions || '无' }}</p>
                </div>
              </div>
              <div v-else class="empty-data">
                <a-empty description="暂无角色数据" :image="false" />
              </div>
            </div>
          </div>
        </a-tab-pane>
        
        <!-- 场景卡 -->
        <a-tab-pane key="scene" tab="🎬 场景卡">
          <div class="tab-content">
            <div class="card-content">
              <p><strong>地点:</strong> {{ selectedResult.scene_card?.location || '暂无数据' }}</p>
              <p><strong>时间:</strong> {{ selectedResult.scene_card?.time || '暂无数据' }}</p>
              <p><strong>氛围:</strong> {{ selectedResult.scene_card?.atmosphere || '暂无数据' }}</p>
              <p><strong>环境音:</strong> {{ Array.isArray(selectedResult.scene_card?.environment_sounds) ? selectedResult.scene_card.environment_sounds.join(', ') : selectedResult.scene_card?.environment_sounds || '无' }}</p>
            </div>
          </div>
        </a-tab-pane>
        
        <!-- 事件卡 -->
        <a-tab-pane key="event" tab="📝 事件卡">
          <div class="tab-content">
            <div class="card-content">
              <p><strong>主要事件:</strong> {{ selectedResult.event_card?.main_event || '暂无数据' }}</p>
              <p><strong>子事件:</strong> {{ Array.isArray(selectedResult.event_card?.sub_events) ? selectedResult.event_card.sub_events.join(', ') : selectedResult.event_card.sub_events || '无' }}</p>
              <p><strong>意义:</strong> {{ selectedResult.event_card?.significance || '暂无数据' }}</p>
            </div>
          </div>
        </a-tab-pane>
        
        <!-- 情绪卡 -->
        <a-tab-pane key="emotion" tab="💝 情绪卡">
          <div class="tab-content">
            <div class="card-content">
              <p><strong>整体基调:</strong> {{ selectedResult.emotion_card?.overall_tone || '暂无数据' }}</p>
              <div v-if="selectedResult.emotion_card?.emotion_changes && selectedResult.emotion_card.emotion_changes.length > 0">
                <p><strong>情绪变化:</strong></p>
                <div v-for="(change, changeIndex) in selectedResult.emotion_card.emotion_changes" :key="changeIndex" class="emotion-change">
                  <a-tag color="orange" size="small">{{ change.from }}</a-tag>
                  <span class="arrow">→</span>
                  <a-tag color="green" size="small">{{ change.to }}</a-tag>
                  <span class="trigger">(触发: {{ change.trigger }})</span>
                </div>
              </div>
              <div v-else class="empty-data">
                <a-empty description="暂无情绪变化数据" :image="false" />
              </div>
            </div>
          </div>
        </a-tab-pane>
        
        <!-- 音频剧本卡 -->
        <a-tab-pane key="audio_script" tab="🎵 音频剧本卡">
          <div class="tab-content">
            <div class="card-content">
              <p><strong>配音指导:</strong> {{ selectedResult.audio_script_card?.voice_direction || '暂无数据' }}</p>
              <p><strong>节奏:</strong> {{ selectedResult.audio_script_card?.pacing || '暂无数据' }}</p>
              <p><strong>背景音乐:</strong> {{ selectedResult.audio_script_card?.background_music || '暂无数据' }}</p>
              <p><strong>音效:</strong> {{ Array.isArray(selectedResult.audio_script_card?.sound_effects) ? selectedResult.audio_script_card.sound_effects.join(', ') : selectedResult.audio_script_card?.sound_effects || '无' }}</p>
            </div>
          </div>
        </a-tab-pane>
        
        <!-- 音频分镜卡 -->
        <a-tab-pane key="audio_storyboard" tab="🎬 音频分镜卡">
          <div class="tab-content">
            <div class="card-content">
              <!-- 时间轴信息 -->
              <div v-if="selectedResult.audio_storyboard_card?.timeline" class="timeline-info">
                <div class="info-header">
                  <a-tag color="purple" size="small">⏱️ 时间轴</a-tag>
                </div>
                <p><strong>总时长:</strong> {{ selectedResult.audio_storyboard_card.timeline.total_duration }} 秒</p>
                <p><strong>分段数:</strong> {{ selectedResult.audio_storyboard_card.timeline.segments?.length || 0 }}</p>
                <div v-if="selectedResult.audio_storyboard_card.timeline.segments" class="timeline-segments">
                  <p><strong>时间轴详情:</strong></p>
                  <div v-for="(segment, segIndex) in selectedResult.audio_storyboard_card.timeline.segments" :key="segIndex" class="timeline-segment">
                    <span class="segment-time">{{ segment.start_time }}-{{ segment.end_time }}s</span>
                    <span class="segment-speaker">{{ segment.speaker }}</span>
                    <span class="segment-emotion">{{ segment.emotion }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 音轨配置 -->
              <div v-if="selectedResult.audio_storyboard_card?.audio_tracks" class="audio-tracks-info">
                <div class="info-header">
                  <a-tag color="cyan" size="small">🎵 音轨配置</a-tag>
                </div>
                <div v-for="(track, trackName) in selectedResult.audio_storyboard_card.audio_tracks" :key="trackName" class="audio-track">
                  <span class="track-name">{{ track.name }}</span>
                  <span class="track-priority">优先级: {{ track.priority }}</span>
                  <span class="track-volume">音量: {{ track.volume }}%</span>
                </div>
              </div>
              
              <!-- 角色语音配置 -->
              <div v-if="selectedResult.audio_storyboard_card?.voice_assignments?.characters" class="voice-assignments-info">
                <div class="info-header">
                  <a-tag color="magenta" size="small">🎤 角色语音</a-tag>
                </div>
                <div v-for="(char, charIndex) in selectedResult.audio_storyboard_card.voice_assignments.characters" :key="charIndex" class="voice-character">
                  <span class="char-name">{{ char.name }}</span>
                  <span class="char-role">{{ char.role_type }}</span>
                  <span class="char-voice">{{ char.voice_name }}</span>
                </div>
              </div>
              
              <!-- 背景音乐 -->
              <div v-if="selectedResult.audio_storyboard_card?.background_music" class="background-music-info">
                <div class="info-header">
                  <a-tag color="gold" size="small">🎼 背景音乐</a-tag>
                </div>
                <p>类型: {{ selectedResult.audio_storyboard_card.background_music.type }}</p>
                <p>情绪: {{ selectedResult.audio_storyboard_card.background_music.mood }}</p>
                <p>节奏: {{ selectedResult.audio_storyboard_card.background_music.tempo }}</p>
                <p>音量: {{ selectedResult.audio_storyboard_card.background_music.volume }}%</p>
              </div>
              
              <!-- 混音参数 -->
              <div v-if="selectedResult.audio_storyboard_card?.mixing_parameters" class="mixing-params-info">
                <div class="info-header">
                  <a-tag color="volcano" size="small">🎚️ 混音参数</a-tag>
                </div>
                <p>主音量: {{ selectedResult.audio_storyboard_card.mixing_parameters.main_volume }}%</p>
                <p>背景音量: {{ selectedResult.audio_storyboard_card.mixing_parameters.background_volume }}%</p>
                <p>环境音量: {{ selectedResult.audio_storyboard_card.mixing_parameters.environment_volume }}%</p>
              </div>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref } from 'vue'

// Props
const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  selectedResult: {
    type: Object,
    default: () => null
  }
})

// Emits
const emit = defineEmits(['close'])

// Reactive data
const activeTabKey = ref('story') // 默认激活第一个tab
</script>

<style scoped>
@import '@/assets/styles/storyboard.css';
</style>
