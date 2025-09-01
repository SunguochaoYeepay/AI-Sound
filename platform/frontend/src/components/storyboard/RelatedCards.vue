<template>
  <div class="related-cards" v-if="cards.length > 0">
    <div class="cards-header">
      <span class="cards-title">📋 关联卡片</span>
      <span class="cards-count">({{ cards.length }})</span>
    </div>
    <div class="cards-list">
      <div 
        v-for="card in cards" 
        :key="card.type"
        class="card-mini"
        :class="`${card.type}-card`"
        @click="handleCardClick(card)"
      >
        {{ card.icon }} {{ card.name }}
      </div>
    </div>
  </div>
</template>

<script setup>
// Props
const props = defineProps({
  cards: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['card-click'])

// Methods
const handleCardClick = (card) => {
  emit('card-click', card)
}
</script>

<style scoped>
.related-cards {
  margin-top: 12px;
  padding: 12px;
  background: var(--card-bg, #f8f9fa);
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 6px;
}

.cards-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.cards-title {
  font-weight: 500;
  margin-right: 4px;
}

.cards-count {
  color: var(--primary-color, #1890ff);
  font-weight: 500;
}

.cards-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.card-mini {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color, #e8e8e8);
  background: var(--card-bg, white);
  color: var(--text-color, #333);
}

.card-mini:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px var(--shadow-color, rgba(0,0,0,0.1));
}

.card-mini.story-card {
  background: #fff2e8;
  color: #fa8c16;
  border-color: #fa8c16;
}

.card-mini.character-card {
  background: #e6f7ff;
  color: #1890ff;
  border-color: #1890ff;
}

.card-mini.scene-card {
  background: #f6ffed;
  color: #52c41a;
  border-color: #52c41a;
}

.card-mini.event-card {
  background: #f9f0ff;
  color: #722ed1;
  border-color: #722ed1;
}

.card-mini.emotion-card {
  background: #fff0f6;
  color: #eb2f96;
  border-color: #eb2f96;
}

.card-mini.audio_storyboard-card {
  background: #e6fffb;
  color: #13c2c2;
  border-color: #13c2c2;
}

.card-mini.audio_script-card {
  background: #fffbe6;
  color: #faad14;
  border-color: #faad14;
}

/* 深色主题下的卡片颜色 */
[data-theme="dark"] .card-mini.story-card {
  background: rgba(250, 140, 22, 0.15);
  color: #ffa940;
  border-color: #ffa940;
}

[data-theme="dark"] .card-mini.character-card {
  background: rgba(24, 144, 255, 0.15);
  color: #69c0ff;
  border-color: #69c0ff;
}

[data-theme="dark"] .card-mini.scene-card {
  background: rgba(82, 196, 26, 0.15);
  color: #95de64;
  border-color: #95de64;
}

[data-theme="dark"] .card-mini.event-card {
  background: rgba(114, 46, 209, 0.15);
  color: #b37feb;
  border-color: #b37feb;
}

[data-theme="dark"] .card-mini.emotion-card {
  background: rgba(235, 47, 150, 0.15);
  color: #ff85c0;
  border-color: #ff85c0;
}

[data-theme="dark"] .card-mini.audio_storyboard-card {
  background: rgba(19, 194, 194, 0.15);
  color: #5cdbd3;
  border-color: #5cdbd3;
}

[data-theme="dark"] .card-mini.audio_script-card {
  background: rgba(250, 173, 20, 0.15);
  color: #ffd666;
  border-color: #ffd666;
}

/* 深色主题下的关联卡片样式 */
[data-theme="dark"] .related-cards {
  background: var(--card-bg, #1a1a1a) !important;
  border-color: var(--border-color, #333333) !important;
}

[data-theme="dark"] .cards-header {
  color: var(--text-secondary, #999999) !important;
}

[data-theme="dark"] .cards-count {
  color: var(--primary-color, #4a9eff) !important;
}
</style>
