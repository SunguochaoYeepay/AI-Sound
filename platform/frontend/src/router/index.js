import BasicTTS from '../views/BasicTTS.vue'
import Characters from '../views/Characters.vue'
import NovelReader from '../views/NovelReader.vue'
import NovelProjects from '../views/NovelProjects.vue'
import NovelProjectCreate from '../views/NovelProjectCreate.vue'
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