<template>
  <div class="intelligent-detector">
    <!-- 检测控制区域 -->
    <div class="detector-header">
      <div class="detector-controls">
        <a-button 
          type="primary" 
          :loading="detecting" 
          @click="runDetection"
          size="small"
        >
          <template #icon><SearchOutlined /></template>
          {{ detecting ? '检测中...' : '智能检测' }}
        </a-button>
        
        <a-button 
          v-if="detectionResult && detectionResult.issues.length > 0"
          type="text" 
          size="small"
          @click="clearDetectionResult"
        >
          <template #icon><ClearOutlined /></template>
          清除结果
        </a-button>
        
        <a-button 
          v-if="ignoredIssues.size > 0" 
          @click="resetIgnoredIssues"
          type="dashed"
          size="small"
        >
          <template #icon><EyeInvisibleOutlined /></template>
          重置忽略状态 ({{ ignoredIssues.size }})
        </a-button>
        
       
      </div>
    </div>

    <!-- 检测结果展示区域 -->
    <div v-if="detectionResult" class="detection-results">
      <!-- 成功状态 -->
      <a-alert
        v-if="detectionResult.issues.length === 0"
        message="检测完成，未发现问题"
        description="所有片段的角色配置和文本内容都正常"
        type="success"
        show-icon
        closable
        @close="clearDetectionResult"
      />
      
      <!-- 发现问题 -->
      <a-alert
        v-else
        :message="`发现 ${detectionResult.issues.length} 个问题`"
        :description="`严重: ${detectionResult.stats?.critical_count || 0}, 警告: ${detectionResult.stats?.warning_count || 0}, 信息: ${detectionResult.stats?.info_count || 0}`"
        type="warning"
        show-icon
        closable
        @close="clearDetectionResult"
      >
        <template #action>
          <a-space>
            <a-button 
              size="small" 
              @click="showDetails = !showDetails"
            >
              {{ showDetails ? '隐藏详情' : '查看详情' }}
            </a-button>
            <a-button
              v-if="detectionResult.fixable_count > 0"
              size="small"
              type="primary"
              @click="applyAutoFix"
              :loading="applyingFix"
            >
              自动修复 ({{ detectionResult.fixable_count }})
            </a-button>
          </a-space>
        </template>
      </a-alert>

      <!-- 问题详情 -->
      <div v-if="showDetails && detectionResult.issues.length > 0" class="issues-detail">
        <a-list 
          :data-source="detectionResult.issues" 
          size="small"
          :pagination="detectionResult.issues.length > 10 ? { pageSize: 10 } : false"
        >
          <template #renderItem="{ item: issue }">
            <a-list-item>
              <a-list-item-meta>
                <template #avatar>
                  <a-tag 
                    :color="getIssueColor(issue.severity)"
                    size="small"
                  >
                    {{ getIssueSeverityText(issue.severity) }}
                  </a-tag>
                </template>
                <template #title>
                  <span class="issue-title">
                    {{ issue.message }}
                  </span>
                  <a-tag v-if="issue.fixable" color="blue" size="small">
                    可修复
                  </a-tag>
                </template>
                <template #description>
                  <div class="issue-details">
                    <div v-if="issue.segment_index !== undefined" class="detail-item">
                      <strong>片段位置:</strong> 第 {{ issue.segment_index + 1 }} 个片段
                    </div>
                    <div v-if="issue.character_name" class="detail-item">
                      <strong>相关角色:</strong> {{ issue.character_name }}
                    </div>
                    <div v-if="issue.issue_type" class="detail-item">
                      <strong>问题类型:</strong> {{ getIssueTypeText(issue.issue_type) }}
                    </div>
                    <div v-if="issue.context" class="detail-item">
                      <strong>问题内容:</strong> 
                      <div class="context-content">{{ issue.context }}</div>
                    </div>
                    <div v-if="issue.description" class="detail-item">
                      <strong>详细描述:</strong> {{ issue.description }}
                    </div>
                    <div v-if="issue.suggestion" class="detail-item suggestion">
                      <strong>修复建议:</strong> {{ issue.suggestion }}
                    </div>
                    <div v-if="issue.fix_data" class="detail-item">
                      <strong>修复方案:</strong> {{ getFixDataText(issue.fix_data) }}
                    </div>
                  </div>
                </template>
              </a-list-item-meta>
              <template #actions>
                <a-button 
                  v-if="issue.fixable"
                  type="link" 
                  size="small"
                  @click="fixSingleIssue(issue)"
                  :loading="fixingIssues.has(issue.id)"
                >
                  修复此问题
                </a-button>
                
                <a-button 
                  type="link" 
                  size="small"
                  @click="ignoreIssue(issue)"
                >
                  忽略
                </a-button>

              </template>
            </a-list-item>
          </template>
        </a-list>
      </div>
    </div>

    <!-- 修复进度 -->
    <div v-if="applyingFix" class="fixing-progress">
      <a-progress 
        :percent="fixProgress" 
        :status="fixProgress === 100 ? 'success' : 'active'"
        :show-info="true"
      />
      <div class="progress-text">正在修复问题... {{ fixedCount }}/{{ totalFixableCount }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, readonly } from 'vue'
import { message } from 'ant-design-vue'
import { 
  SearchOutlined, 
  ClearOutlined,
  EyeInvisibleOutlined
} from '@ant-design/icons-vue'
import { intelligentDetection, applyDetectionFixes } from '@/api'

// Props
const props = defineProps({
  bookId: {
    type: Number,
    required: true
  },
  chapterId: {
    type: Number,
    required: true
  },
  segments: {
    type: Array,
    default: () => []
  },
  characters: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['segments-updated', 'auto-save-fixes', 'refresh-chapter-data'])

// 响应式数据
const detecting = ref(false)
const detectionResult = ref(null)
const showDetails = ref(false)
const applyingFix = ref(false)
const fixingIssues = ref(new Set())
const ignoredIssues = ref(new Set()) // 存储被忽略的问题ID
const fixProgress = ref(0)
const fixedCount = ref(0)
const totalFixableCount = ref(0)

// 计算属性
const hasIssues = computed(() => {
  return detectionResult.value && detectionResult.value.issues.length > 0
})

// 获取问题严重程度颜色
const getIssueColor = (severity) => {
  switch (severity) {
    case 'critical': return 'red'
    case 'warning': return 'orange'
    case 'info': return 'blue'
    default: return 'default'
  }
}

// 获取问题严重程度文本
const getIssueSeverityText = (severity) => {
  switch (severity) {
    case 'critical': return '严重'
    case 'warning': return '警告'
    case 'info': return '信息'
    default: return '未知'
  }
}

// 获取问题类型文本
const getIssueTypeText = (issueType) => {
  const typeMap = {
    'character_mismatch': '角色配置不匹配',
    'empty_content': '内容为空',
    'long_segment': '片段过长',
    'special_characters': '特殊字符',
    'quoted_content_as_narration': '对话标记为旁白',
    'narration_as_dialogue': '旁白标记为对话',
    'inconsistent_voice_type': '语音类型不一致'
  }
  return typeMap[issueType] || issueType
}

// 获取修复数据文本
const getFixDataText = (fixData) => {
  if (!fixData) return '无'
  
  if (typeof fixData === 'string') {
    return fixData
  }
  
  if (typeof fixData === 'object') {
    const parts = []
    if (fixData.new_speaker) {
      parts.push(`角色: ${fixData.new_speaker}`)
    }
    if (fixData.new_text_type) {
      parts.push(`类型: ${fixData.new_text_type === 'dialogue' ? '对话' : '旁白'}`)
    }
    if (fixData.new_text) {
      parts.push(`内容: ${fixData.new_text.substring(0, 50)}${fixData.new_text.length > 50 ? '...' : ''}`)
    }
    return parts.join(', ') || '自动修复'
  }
  
  return '自动修复'
}

// 运行智能检测
const runDetection = async () => {
  if (!props.bookId || !props.chapterId) {
    message.error('缺少必要参数')
    return
  }

  detecting.value = true
  showDetails.value = false
  
  try {
    console.log('[智能检测] 开始检测:', {
      bookId: props.bookId,
      chapterId: props.chapterId,
      segmentsCount: props.segments.length,
      charactersCount: props.characters.length
    })

    const response = await intelligentDetection(props.chapterId, true)
    console.log('[智能检测] 收到响应:', response)

    // 从 Axios 响应中提取实际数据
    const responseData = response.data || response
    console.log('[智能检测] 处理后的响应数据:', responseData)

    // 检查响应是否成功
    if (responseData.success) {
      const result = responseData.detection_result
      detectionResult.value = {
        ...result,
        // 确保issues数组存在
        issues: result.issues || [],
        // 确保统计信息存在
        stats: result.stats || {
          critical_count: 0,
          warning_count: 0,
          info_count: 0,
          total_count: 0
        }
      }

      // 🔥 新增：过滤掉已忽略的问题
      if (detectionResult.value.issues && detectionResult.value.issues.length > 0) {
        const originalCount = detectionResult.value.issues.length
        detectionResult.value.issues = detectionResult.value.issues.filter(issue => 
          !ignoredIssues.value.has(issue.id)
        )
        const filteredCount = detectionResult.value.issues.length
        
        if (originalCount > filteredCount) {
          console.log(`[智能检测] 已过滤 ${originalCount - filteredCount} 个被忽略的问题`)
        }
      }

      console.log('[智能检测] 处理后的结果:', detectionResult.value)
      
      if (detectionResult.value.issues.length === 0) {
        message.success(responseData.message || '检测完成，未发现问题')
      } else {
        message.warning(responseData.message || `发现 ${detectionResult.value.issues.length} 个问题`)
        showDetails.value = true // 自动展开详情
      }
    } else {
      message.error(responseData.message || '检测失败')
    }
  } catch (error) {
    console.error('[智能检测] 检测失败:', error)
    message.error('检测过程中发生错误')
  } finally {
    detecting.value = false
  }
}

// 清空检测结果
const clearDetectionResult = () => {
  detectionResult.value = null
  showDetails.value = false
}

// 忽略问题
const ignoreIssue = (issue) => {
  ignoredIssues.value.add(issue.id)
  message.success('已忽略该问题，下次检测时将跳过')
  
  // 从当前检测结果中移除该问题
  if (detectionResult.value && detectionResult.value.issues) {
    detectionResult.value.issues = detectionResult.value.issues.filter(item => item.id !== issue.id)
    
    // 如果没有问题了，隐藏详情
    if (detectionResult.value.issues.length === 0) {
      showDetails.value = false
      message.info('所有问题已处理完毕')
    }
  }
}

// 重置忽略状态（重新智能准备时调用）
 const resetIgnoredIssues = () => {
   const ignoredCount = ignoredIssues.value.size
   ignoredIssues.value.clear()
   if (ignoredCount > 0) {
     message.info(`已重置 ${ignoredCount} 个被忽略的问题状态`)
   }
 }

 // 清空进度相关数据
 const clearProgress = () => {
   fixProgress.value = 0
   fixedCount.value = 0
   totalFixableCount.value = 0
 }

// 应用自动修复
const applyAutoFix = async () => {
  if (!detectionResult.value || detectionResult.value.fixable_count === 0) {
    return
  }

  applyingFix.value = true
  fixProgress.value = 0
  fixedCount.value = 0
  totalFixableCount.value = detectionResult.value.fixable_count

  try {
    const fixableIssues = detectionResult.value.issues.filter(issue => issue.fixable)
    
    if (fixableIssues.length === 0) {
      message.warning('没有可自动修复的问题')
      return
    }

    // 调用后端API应用修复
    const fixData = {
      issues: fixableIssues
    }
    
    const response = await applyDetectionFixes(props.chapterId, fixData)
    
    if (response.data.success) {
      message.success(`已自动修复 ${response.data.data.fixed_count} 个问题，正在刷新数据...`)
      
      // 🔥 修复：自动修复后重新获取最新数据
      setTimeout(async () => {
        try {
          // 1. 触发父组件保存
          emit('auto-save-fixes')
          
          // 2. 🔥 关键修复：重新获取最新的章节数据来刷新界面
          emit('refresh-chapter-data')
          
          // 3. 清空检测结果，让用户重新点击检测按钮
          detectionResult.value = null
          showDetails.value = false
          
          message.success('修复完成并已刷新数据，请重新点击智能检测查看结果')
          
        } catch (error) {
          console.error('[智能检测] 修复后刷新失败:', error)
          message.warning('修复完成，但数据刷新失败，请手动刷新页面')
        }
      }, 1000) // 延长等待时间确保后端数据保存完成
    } else {
      message.error(response.data.message || '自动修复失败')
    }
    
  } catch (error) {
    console.error('[智能检测] 自动修复失败:', error)
    message.error('自动修复过程中发生错误')
  } finally {
    applyingFix.value = false
  }
}

// 🔥 移除未使用的批量修复函数（fixSingleIssueInBatch）
// 简化逻辑：只保留必要的单个问题修复功能

// 修复单个问题
const fixSingleIssue = async (issue, showMessage = true) => {
  fixingIssues.value.add(issue.id)
  
  try {
    console.log('[智能检测] 修复问题:', issue)
    
    // 根据问题类型应用修复
    const updatedSegments = [...props.segments]
    let fixed = false
    
    const issueType = issue.issue_type || issue.type
    switch (issueType) {
      case 'missing_speaker':
        // 为缺失说话人的片段设置默认说话人
        if (issue.segment_index !== undefined) {
          updatedSegments[issue.segment_index].speaker = issue.suggested_speaker || '旁白'
          fixed = true
        }
        break
        
      case 'character_mismatch':
        // 处理角色相关问题（可能是角色缺失或语音类型缺失）
        if (issue.segment_index !== undefined) {
          const segment = updatedSegments[issue.segment_index]
          
          // 检查问题类型：是角色缺失还是语音类型缺失
          if (issue.description && issue.description.includes('未配置语音类型')) {
            // 语音类型缺失 - 为角色配置默认语音类型
            // 🔥 优先使用真实角色名，而不是"未知角色"
            const realSpeaker = segment.voice_name || segment.speaker || '旁白'
            
            // 确保speaker和voice_name同步
            if (segment.voice_name && segment.speaker === '未知角色') {
              segment.speaker = segment.voice_name
            }
            
            if (realSpeaker === '旁白') {
              segment.voice_type = 'narrator'
            } else if (realSpeaker.includes('女') || realSpeaker.includes('妹') || realSpeaker.includes('姐')) {
              segment.voice_type = 'female'
            } else if (realSpeaker.includes('男') || realSpeaker.includes('哥') || realSpeaker.includes('兄')) {
              segment.voice_type = 'male'
            } else if (realSpeaker.includes('帝') || realSpeaker.includes('王') || realSpeaker.includes('君')) {
              segment.voice_type = 'male'  // 帝王类角色通常是男性
            } else {
              segment.voice_type = 'neutral'  // 默认中性语音
            }
            
            // 如果有character_id但没有voice_id，设置voice_id
            if (segment.character_id && !segment.voice_id) {
              segment.voice_id = segment.character_id.toString()
            }
            
            fixed = true
          } else {
            // 角色缺失 - 根据文本内容推断说话人
            if (issue.suggested_speaker) {
              segment.speaker = issue.suggested_speaker
              segment.voice_name = issue.suggested_speaker
            } else if (segment.voice_name) {
              // 如果有voice_name但speaker是未知角色，使用voice_name
              segment.speaker = segment.voice_name
            } else if (segment.text_type === 'dialogue') {
              segment.speaker = '未知角色'
            } else {
              segment.speaker = '旁白'
            }
            fixed = true
          }
        }
        break
        
      case 'invalid_character':
        // 将无效角色替换为有效角色
        if (issue.segment_index !== undefined && issue.suggested_speaker) {
          updatedSegments[issue.segment_index].speaker = issue.suggested_speaker
          fixed = true
        }
        break
        
      case 'empty_text':
        // 为空文本片段设置占位文本
        if (issue.segment_index !== undefined) {
          updatedSegments[issue.segment_index].text = issue.suggested_text || '[请补充文本内容]'
          fixed = true
        }
        break
        
      case 'duplicate_segment':
        // 删除重复片段
        if (issue.segment_index !== undefined && issue.segment_index > 0) {
          updatedSegments.splice(issue.segment_index, 1)
          fixed = true
        }
        break
        
      case 'special_characters':
        // 清理特殊字符（如"——"符号）
        if (issue.segment_index !== undefined) {
          const segment = updatedSegments[issue.segment_index]
          // 移除"——"符号和其他特殊字符
          segment.text = segment.text.replace(/[———]/g, '')
          fixed = true
        }
        break
        
      case 'character_detection_issue':
        // 处理角色检测问题
        if (issue.segment_index !== undefined && issue.fix_data && issue.fix_data.action) {
          const segment = updatedSegments[issue.segment_index]
          
          switch (issue.fix_data.action) {
            case 'set_character':
              // 设置角色和文本类型
              if (issue.fix_data.character) {
                segment.speaker = issue.fix_data.character
                segment.character = issue.fix_data.character
              }
              if (issue.fix_data.text_type) {
                segment.text_type = issue.fix_data.text_type
                // 为对话类型设置默认语音类型
                if (issue.fix_data.text_type === 'dialogue' && !segment.voice_type) {
                  segment.voice_type = 'neutral'
                }
              }
              fixed = true
              break
              
            case 'set_narration':
              // 设置为旁白
              segment.text_type = 'narration'
              segment.speaker = '旁白'
              segment.character = null
              segment.voice_type = null
              fixed = true
              break
              
            default:
              console.warn('[智能检测] 未知的角色检测修复类型:', issue.fix_data.action)
              break
          }
        }
        break
        
      // 🔥 新增：旁白内容被标记为对话的修复
      case 'narration_as_dialogue':
        if (issue.segment_index !== undefined && issue.fix_data?.action === 'change_to_narration') {
          const segment = updatedSegments[issue.segment_index]
          segment.text_type = 'narration'
          segment.speaker = '旁白'
          segment.character = null
          segment.voice_type = null
          fixed = true
          console.log(`[智能检测] 已将段落 ${issue.segment_index + 1} 从对话改为旁白`)
        }
        break
        
      // 🔥 新增：对话内容被标记为旁白的修复
      case 'dialogue_as_narration':
        if (issue.segment_index !== undefined && issue.fix_data?.action === 'change_to_dialogue') {
          const segment = updatedSegments[issue.segment_index]
          segment.text_type = 'dialogue'
          segment.speaker = '未知角色'
          segment.voice_type = 'neutral'
          fixed = true
          console.log(`[智能检测] 已将段落 ${issue.segment_index + 1} 从旁白改为对话`)
        }
        break
        
      // 🔥 新增：混合文本拆分处理
      case 'segment_split_needed':
        if (issue.segment_index !== undefined && issue.fix_data?.suggested_segments) {
          const originalSegment = updatedSegments[issue.segment_index]
          const suggestedSegments = issue.fix_data.suggested_segments
          
          // 创建新的段落数组
          const newSegments = suggestedSegments.map((suggested, subIndex) => {
            const speaker = suggested.speaker || '旁白'
            const newSegment = {
              ...originalSegment, // 继承原段落的其他属性
              id: `segment_${Date.now()}_${subIndex}`,
              segment_id: originalSegment.segment_id + subIndex,
              text: suggested.text || '',
              speaker: speaker,
              voice_name: speaker, // 🔥 修复：确保voice_name与speaker一致
              text_type: suggested.text_type || 'narration',
              confidence: suggested.confidence || 0.9,
              detection_rule: 'ai_split_detection',
              _forceUpdate: Date.now()
            }
            
            // 🔥 关键修复：旁白段落不应该有character_id或voice_id
            if (speaker === '旁白') {
              delete newSegment.character_id
              delete newSegment.voice_id
            }
            
            return newSegment
          })
          
          // 替换原段落
          updatedSegments.splice(issue.segment_index, 1, ...newSegments)
          
          // 重新编号所有段落
          updatedSegments.forEach((segment, index) => {
            segment.segment_id = index + 1
          })
          
          fixed = true
          console.log(`[智能检测] 已拆分段落 ${issue.segment_index + 1} 为 ${newSegments.length} 个子段落`)
        }
        break
      
      default:
        // 对于未知的问题类型，尝试通用修复
        console.warn('[智能检测] 未知问题类型:', issueType, issue)
        if (issue.segment_index !== undefined && issue.suggested_speaker) {
          updatedSegments[issue.segment_index].speaker = issue.suggested_speaker
          fixed = true
        } else if (issue.segment_index !== undefined && !updatedSegments[issue.segment_index].speaker) {
          updatedSegments[issue.segment_index].speaker = '旁白'
          fixed = true
        }
        break
    }
    
    if (fixed) {
      console.log(`[智能检测] 问题修复成功: ${issueType} (片段 ${issue.segment_index})`)
      emit('segments-updated', updatedSegments)
      
      // 🔥 新增：单条修复也要自动保存
      setTimeout(async () => {
        try {
          emit('auto-save-fixes') // 触发父组件保存
          if (showMessage) {
            message.success(`问题修复成功并已保存: ${issue.description || issueType}`)
          }
          // 🔥 移除自动检测：改为手工检测
          // 修复完成，用户可手动点击检测按钮重新检测
        } catch (error) {
          console.error('[智能检测] 单条修复自动保存失败:', error)
          if (showMessage) {
            message.warning(`修复成功，但保存失败，请手动点击保存按钮`)
          }
        }
      }, 500)
      
    } else {
      console.warn(`[智能检测] 无法修复问题: ${issueType}`, issue)
      if (showMessage) {
        message.warning(`此问题无法自动修复，请手动处理: ${issue.description || issueType}`)
      }
    }
    
  } catch (error) {
    console.error('[智能检测] 修复问题失败:', error)
    if (showMessage) {
      message.error('修复失败')
    }
  } finally {
    fixingIssues.value.delete(issue.id)
  }
}



// 暴露方法给父组件
defineExpose({
  runDetection,
  clearDetectionResult,
  hasIssues,
  ignoreIssue,
  resetIgnoredIssues,
  ignoredIssues: readonly(ignoredIssues)
})
</script>

<style scoped>




.detector-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.help-icon {
  color: var(--ant-text-color-secondary);
  cursor: help;
}

.detection-results {
  margin-bottom: 16px;
}

.issues-detail {
  margin-top: 12px;
  padding: 12px;
}

.detail-item {
  margin-bottom: 8px;
  padding: 4px 0;
  border-bottom: 1px solid var(--ant-border-color);
}

.detail-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.detail-item strong {
  color: var(--ant-primary-color);
  margin-right: 8px;
  min-width: 80px;
  display: inline-block;
}

.context-content {
  background: var(--ant-color-bg-layout);
  padding: 8px 12px;
  border-radius: 4px;
  margin-top: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  max-height: 100px;
  overflow-y: auto;
  border-left: 3px solid var(--ant-primary-color);
}

.suggestion {
  background: var(--ant-success-color-bg);
  border-left: 3px solid var(--ant-success-color);
  padding: 8px 12px;
  border-radius: 4px;
}

.suggestion strong {
  color: var(--ant-success-color);
}

.issue-title {
  font-weight: 500;
  color: var(--ant-text-color);
}

.issue-details {
  margin-top: 8px;
  padding: 8px;
  background: var(--ant-color-bg-layout);
  border-radius: 6px;
  border: 1px solid var(--ant-border-color);
}

.issue-title {
  font-weight: 500;
}

.issue-details {
  font-size: 12px;
  color: var(--ant-text-color-secondary);
}

.suggestion {
  margin-top: 4px;
  padding: 4px 8px;
  background: var(--ant-primary-1);
  border-left: 3px solid var(--ant-primary-color);
  border-radius: 2px;
}

.fixing-progress {
  padding: 12px;
  background: var(--ant-color-bg-container);
  border-radius: 6px;
  margin-top: 12px;
}

.progress-text {
  margin-top: 8px;
  text-align: center;
  color: var(--ant-text-color-secondary);
  font-size: 12px;
}
</style>