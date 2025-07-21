/**
 * 书籍状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { bookAPI, chapterAPI } from '../api/v2.js'

export const useBookStore = defineStore('book', () => {
  // 书籍列表
  const books = ref([])
  const loading = ref(false)
  const currentBook = ref(null)

  // 章节数据
  const chapters = ref([])
  const chaptersLoading = ref(false)

  // 计算属性
  const bookCount = computed(() => books.value.length)
  const hasBooks = computed(() => bookCount.value > 0)

  // 获取书籍列表
  const fetchBooks = async (params = {}) => {
    loading.value = true
    try {
      const result = await bookAPI.getBooks(params)
      if (result.success) {
        books.value = result.data.items || result.data || []
      }
      return result
    } finally {
      loading.value = false
    }
  }

  // 获取书籍详情
  const fetchBook = async (bookId) => {
    const result = await bookAPI.getBook(bookId)
    if (result.success) {
      currentBook.value = result.data
    }
    return result
  }

  // 获取章节列表
  const fetchChapters = async (bookId, params = {}) => {
    chaptersLoading.value = true
    try {
      const result = await chapterAPI.getChapters(bookId, params)
      if (result.success) {
        chapters.value = result.data.items || result.data || []
      }
      return result
    } finally {
      chaptersLoading.value = false
    }
  }

  // 添加书籍到本地状态
  const addBook = (book) => {
    books.value.unshift(book)
  }

  // 更新书籍
  const updateBook = (bookId, updates) => {
    const index = books.value.findIndex((book) => book.id === bookId)
    if (index > -1) {
      books.value[index] = { ...books.value[index], ...updates }
    }

    if (currentBook.value?.id === bookId) {
      currentBook.value = { ...currentBook.value, ...updates }
    }
  }

  // 删除书籍
  const removeBook = (bookId) => {
    const index = books.value.findIndex((book) => book.id === bookId)
    if (index > -1) {
      books.value.splice(index, 1)
    }

    if (currentBook.value?.id === bookId) {
      currentBook.value = null
    }
  }

  return {
    // 状态
    books,
    loading,
    currentBook,
    chapters,
    chaptersLoading,

    // 计算属性
    bookCount,
    hasBooks,

    // 方法
    fetchBooks,
    fetchBook,
    fetchChapters,
    addBook,
    updateBook,
    removeBook
  }
})
