import BasicTTS from '../views/BasicTTS.vue'
import Characters from '../views/Characters.vue'
import NovelReader from '../views/NovelReader.vue'
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
  {
    path: '/novel-reader',
    name: 'NovelReader',
    component: NovelReader
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