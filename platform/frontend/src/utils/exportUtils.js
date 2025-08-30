/**
 * 数据导出工具
 * 支持导出审核报告、卡片数据等
 */

/**
 * 导出审核报告为JSON文件
 * @param {Object} reviewData - 审核数据
 * @param {string} sessionName - 会话名称
 * @param {string} chapterTitle - 章节标题
 */
export const exportReviewReport = (reviewData, sessionName, chapterTitle) => {
  const exportData = {
    session_name: sessionName,
    chapter_title: chapterTitle,
    export_time: new Date().toISOString(),
    chapter_info: reviewData.chapter,
    cards_summary: {
      total_cards: Object.values(reviewData.cards).flat().length,
      confirmed_cards: Object.values(reviewData.cards).flat().filter(card => card.is_confirmed).length,
      pending_cards: Object.values(reviewData.cards).flat().filter(card => !card.is_confirmed).length,
      card_types: Object.keys(reviewData.cards).map(type => ({
        type,
        count: reviewData.cards[type].length,
        confirmed: reviewData.cards[type].filter(card => card.is_confirmed).length
      }))
    },
    book_cards_summary: {
      total_cards: Object.values(reviewData.book_cards).flat().length,
      confirmed_cards: Object.values(reviewData.book_cards).flat().filter(card => card.is_confirmed).length,
      pending_cards: Object.values(reviewData.book_cards).flat().filter(card => !card.is_confirmed).length,
      card_types: Object.keys(reviewData.book_cards).map(type => ({
        type,
        count: reviewData.book_cards[type].length,
        confirmed: reviewData.book_cards[type].filter(card => card.is_confirmed).length
      }))
    },
    cards: reviewData.cards,
    book_cards: reviewData.book_cards
  }

  downloadJSON(exportData, `审核报告_${sessionName}_${chapterTitle}_${new Date().toISOString().split('T')[0]}.json`)
}

/**
 * 导出会话卡片数据为JSON文件
 * @param {Array} cards - 卡片列表
 * @param {string} sessionName - 会话名称
 */
export const exportSessionCards = (cards, sessionName) => {
  const exportData = {
    session_name: sessionName,
    export_time: new Date().toISOString(),
    total_cards: cards.length,
    confirmed_cards: cards.filter(card => card.is_confirmed).length,
    pending_cards: cards.filter(card => !card.is_confirmed).length,
    card_types: Object.entries(
      cards.reduce((acc, card) => {
        acc[card.card_type] = (acc[card.card_type] || 0) + 1
        return acc
      }, {})
    ).map(([type, count]) => ({
      type,
      count,
      confirmed: cards.filter(card => card.card_type === type && card.is_confirmed).length
    })),
    cards: cards
  }

  downloadJSON(exportData, `会话卡片_${sessionName}_${new Date().toISOString().split('T')[0]}.json`)
}

/**
 * 导出会话统计报告为CSV文件
 * @param {Object} session - 会话信息
 * @param {Array} cards - 卡片列表
 * @param {Array} chapters - 章节列表
 */
export const exportSessionReport = (session, cards, chapters) => {
  const csvData = [
    ['会话信息'],
    ['会话ID', session.id],
    ['会话名称', session.session_name],
    ['书籍ID', session.book_id],
    ['状态', session.status],
    ['进度', `${session.progress}%`],
    ['总章节数', session.total_chapters],
    ['已分析章节', session.analyzed_chapters],
    ['失败章节', session.failed_chapters],
    ['创建时间', session.created_at],
    [''],
    ['卡片统计'],
    ['卡片类型', '总数', '已确认', '待确认', '确认率'],
    ...Object.entries(
      cards.reduce((acc, card) => {
        acc[card.card_type] = (acc[card.card_type] || 0) + 1
        return acc
      }, {})
    ).map(([type, count]) => {
      const confirmed = cards.filter(card => card.card_type === type && card.is_confirmed).length
      const pending = count - confirmed
      const rate = count > 0 ? `${((confirmed / count) * 100).toFixed(1)}%` : '0%'
      return [type, count, confirmed, pending, rate]
    }),
    [''],
    ['章节统计'],
    ['章节编号', '章节标题', '字数', '分析状态', '卡片数'],
    ...chapters.map(chapter => [
      chapter.chapter_number,
      chapter.chapter_title,
      chapter.word_count,
      chapter.analysis_status,
      chapter.card_count
    ])
  ]

  downloadCSV(csvData, `会话报告_${session.session_name}_${new Date().toISOString().split('T')[0]}.csv`)
}

/**
 * 下载JSON文件
 * @param {Object} data - 要导出的数据
 * @param {string} filename - 文件名
 */
const downloadJSON = (data, filename) => {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 下载CSV文件
 * @param {Array} data - 要导出的数据
 * @param {string} filename - 文件名
 */
const downloadCSV = (data, filename) => {
  const csvContent = data.map(row => 
    row.map(cell => {
      if (typeof cell === 'string' && cell.includes(',')) {
        return `"${cell}"`
      }
      return cell
    }).join(',')
  ).join('\n')

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 格式化卡片内容为可读文本
 * @param {Object} card - 卡片对象
 * @returns {string} 格式化后的文本
 */
export const formatCardContent = (card) => {
  const content = card.content || {}
  
  switch (card.card_type) {
    case 'story':
      return `故事概要：${content.story_summary || ''}\n主题：${(content.themes || []).join(', ')}\n类型：${content.genre || ''}`
    
    case 'character':
      return `角色名称：${content.character_name || ''}\n角色类型：${content.character_type || ''}\n性格：${(content.personality || []).join(', ')}\n背景：${content.background || ''}`
    
    case 'scene':
      return `场景名称：${content.scene_name || ''}\n场景类型：${content.scene_type || ''}\n位置：${content.location?.description || ''}\n氛围：${content.atmosphere?.mood || ''}`
    
    case 'event':
      return `事件名称：${content.event_name || ''}\n事件类型：${content.event_type || ''}\n参与者：${(content.participants || []).join(', ')}\n描述：${content.action_description || ''}`
    
    case 'emotion':
      return `情绪类型：${content.emotion_type || ''}\n强度：${content.intensity || ''}\n触发因素：${(content.triggers || []).join(', ')}\n表达方式：${(content.expression || []).join(', ')}`
    
    case 'audio_storyboard':
      return `时间轴：${(content.timeline || []).map(item => `${item.time_range}: ${item.content}`).join('\n')}\n音频轨道：${Object.keys(content.audio_tracks || {}).join(', ')}`
    
    default:
      return JSON.stringify(content, null, 2)
  }
}
