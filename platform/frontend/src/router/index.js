import BasicTTS from '../views/BasicTTS.vue'
import Characters from '../views/Characters.vue'
import NovelReader from '../views/NovelReader.vue'

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
  {
    path: '/novel-reader',
    name: 'NovelReader',
    component: NovelReader
  }
]

export default routes