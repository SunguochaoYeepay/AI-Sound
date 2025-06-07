import BasicTTS from '../views/BasicTTS.vue'
import Characters from '../views/Characters.vue'
import Books from '../views/Books.vue'
import BookDetail from '../views/BookDetail.vue'
import BookCreate from '../views/BookCreate.vue'
import NovelReader from '../views/NovelReader.vue'
import NovelProjects from '../views/NovelProjects.vue'
import NovelProjectCreate from '../views/NovelProjectCreate.vue'
import SynthesisCenter from '../views/SynthesisCenter.vue'
import AudioLibrary from '../views/AudioLibrary.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    redirect: '/basic-tts'
  },
  {
    path: '/basic-tts',
    name: 'BasicTTS',
    component: BasicTTS
  },
  {
    path: '/characters',
    name: 'Characters',
    component: Characters
  },
  // 书籍管理路由
  {
    path: '/books',
    name: 'Books',
    component: Books
  },
  {
    path: '/books/create',
    name: 'BookCreate',
    component: BookCreate
  },
  {
    path: '/books/edit/:id',
    name: 'BookEdit',
    component: BookCreate
  },
  {
    path: '/books/detail/:id',
    name: 'BookDetail',
    component: BookDetail
  },
  // 项目管理路由（重构后）
  {
    path: '/novel-reader',
    name: 'NovelProjects',
    component: NovelProjects
  },
  {
    path: '/novel-reader/create',
    name: 'NovelProjectCreate',
    component: NovelProjectCreate
  },
  {
    path: '/novel-reader/edit/:id',
    name: 'NovelProjectEdit',
    component: NovelProjectCreate
  },
  {
    path: '/novel-reader/detail/:id',
    name: 'NovelReaderDetail',
    component: NovelReader
  },
  // 合成中心路由
  {
    path: '/synthesis/:projectId',
    name: 'SynthesisCenter',
    component: SynthesisCenter
  },
  {
    path: '/audio-library',
    name: 'AudioLibrary',
    component: AudioLibrary
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

export default routes