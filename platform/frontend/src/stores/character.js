import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useCharacterStore = defineStore('character', () => {
  const matchCharacters = async (bookId, chapterId) => {
    try {
      const response = await axios.post('/api/v1/characters/match', {
        book_id: bookId,
        chapter_id: chapterId
      })
      return response.data
    } catch (error) {
      console.error('匹配角色失败:', error)
      throw error
    }
  }

  const applyMatches = async (matches) => {
    try {
      const response = await axios.post('/api/v1/characters/apply-matches', {
        matches
      })
      return response.data
    } catch (error) {
      console.error('应用匹配结果失败:', error)
      throw error
    }
  }

  const syncCharacters = async (bookId, chapterId) => {
    try {
      const response = await axios.post('/api/v1/characters/sync', {
        book_id: bookId,
        chapter_id: chapterId
      })
      return response.data
    } catch (error) {
      console.error('同步角色记录失败:', error)
      throw error
    }
  }

  return {
    matchCharacters,
    applyMatches,
    syncCharacters
  }
}) 