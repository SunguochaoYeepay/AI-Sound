/**
 * 音频处理WebWorker
 * 支持后台音频解码、波形数据计算、音频效果处理
 */

// Worker消息类型
const MessageTypes = {
  DECODE_AUDIO: 'decode_audio',
  GENERATE_WAVEFORM: 'generate_waveform',
  APPLY_EFFECTS: 'apply_effects',
  PROCESS_BATCH: 'process_batch',
  CALCULATE_PEAKS: 'calculate_peaks',
  NORMALIZE_AUDIO: 'normalize_audio',
  APPLY_FADE: 'apply_fade',
  MIX_TRACKS: 'mix_tracks'
}

// 全局变量
let audioContext = null
let sampleRate = 44100

// 初始化AudioContext
const initAudioContext = () => {
  if (!audioContext) {
    audioContext = new (self.AudioContext || self.webkitAudioContext)({
      sampleRate: sampleRate
    })
  }
  return audioContext
}

// 音频解码
const decodeAudio = async (arrayBuffer, taskId) => {
  try {
    const ctx = initAudioContext()
    const audioBuffer = await ctx.decodeAudioData(arrayBuffer)

    const result = {
      taskId,
      success: true,
      data: {
        sampleRate: audioBuffer.sampleRate,
        length: audioBuffer.length,
        duration: audioBuffer.duration,
        numberOfChannels: audioBuffer.numberOfChannels,
        channelData: []
      }
    }

    // 提取每个声道的数据
    for (let i = 0; i < audioBuffer.numberOfChannels; i++) {
      result.data.channelData.push(audioBuffer.getChannelData(i))
    }

    self.postMessage({
      type: MessageTypes.DECODE_AUDIO,
      result
    })
  } catch (error) {
    self.postMessage({
      type: MessageTypes.DECODE_AUDIO,
      result: {
        taskId,
        success: false,
        error: error.message
      }
    })
  }
}

// 生成波形数据
const generateWaveform = (channelData, options = {}, taskId) => {
  try {
    const { width = 1000, height = 100, samplesPerPixel = 512, normalize = true } = options

    const samples = channelData.length
    const blockSize = Math.floor(samples / width)
    const peaks = []

    for (let i = 0; i < width; i++) {
      const start = i * blockSize
      const end = Math.min(start + blockSize, samples)

      let min = 0
      let max = 0

      for (let j = start; j < end; j++) {
        const sample = channelData[j]
        if (sample > max) max = sample
        if (sample < min) min = sample
      }

      peaks.push({
        min: normalize ? min * height : min,
        max: normalize ? max * height : max
      })
    }

    self.postMessage({
      type: MessageTypes.GENERATE_WAVEFORM,
      result: {
        taskId,
        success: true,
        data: {
          peaks,
          width,
          height,
          duration: samples / sampleRate
        }
      }
    })
  } catch (error) {
    self.postMessage({
      type: MessageTypes.GENERATE_WAVEFORM,
      result: {
        taskId,
        success: false,
        error: error.message
      }
    })
  }
}

// 计算音频峰值
const calculatePeaks = (channelData, options = {}, taskId) => {
  try {
    const {
      threshold = -20, // dB
      windowSize = 1024
    } = options

    const peaks = []
    const linearThreshold = Math.pow(10, threshold / 20)

    for (let i = 0; i < channelData.length; i += windowSize) {
      const window = channelData.slice(i, i + windowSize)
      let rms = 0

      for (let j = 0; j < window.length; j++) {
        rms += window[j] * window[j]
      }

      rms = Math.sqrt(rms / window.length)

      if (rms > linearThreshold) {
        peaks.push({
          time: i / sampleRate,
          amplitude: rms,
          db: 20 * Math.log10(rms)
        })
      }
    }

    self.postMessage({
      type: MessageTypes.CALCULATE_PEAKS,
      result: {
        taskId,
        success: true,
        data: peaks
      }
    })
  } catch (error) {
    self.postMessage({
      type: MessageTypes.CALCULATE_PEAKS,
      result: {
        taskId,
        success: false,
        error: error.message
      }
    })
  }
}

// 音频标准化
const normalizeAudio = (channelData, targetLevel = -3, taskId) => {
  try {
    // 找到最大振幅
    let maxAmplitude = 0
    for (let i = 0; i < channelData.length; i++) {
      const abs = Math.abs(channelData[i])
      if (abs > maxAmplitude) {
        maxAmplitude = abs
      }
    }

    // 计算增益
    const targetLinear = Math.pow(10, targetLevel / 20)
    const gain = maxAmplitude > 0 ? targetLinear / maxAmplitude : 1

    // 应用增益
    const normalizedData = new Float32Array(channelData.length)
    for (let i = 0; i < channelData.length; i++) {
      normalizedData[i] = channelData[i] * gain
    }

    self.postMessage({
      type: MessageTypes.NORMALIZE_AUDIO,
      result: {
        taskId,
        success: true,
        data: {
          normalizedData,
          appliedGain: gain,
          gainDb: 20 * Math.log10(gain)
        }
      }
    })
  } catch (error) {
    self.postMessage({
      type: MessageTypes.NORMALIZE_AUDIO,
      result: {
        taskId,
        success: false,
        error: error.message
      }
    })
  }
}

// 应用淡入淡出
const applyFade = (channelData, options = {}, taskId) => {
  try {
    const {
      fadeInDuration = 0,
      fadeOutDuration = 0,
      fadeType = 'linear' // linear, exponential, logarithmic
    } = options

    const fadeInSamples = Math.floor(fadeInDuration * sampleRate)
    const fadeOutSamples = Math.floor(fadeOutDuration * sampleRate)
    const totalSamples = channelData.length

    const processedData = new Float32Array(channelData)

    // 淡入处理
    for (let i = 0; i < Math.min(fadeInSamples, totalSamples); i++) {
      let factor = i / fadeInSamples

      switch (fadeType) {
        case 'exponential':
          factor = factor * factor
          break
        case 'logarithmic':
          factor = Math.sqrt(factor)
          break
        default: // linear
          break
      }

      processedData[i] *= factor
    }

    // 淡出处理
    const fadeOutStart = totalSamples - fadeOutSamples
    for (let i = Math.max(0, fadeOutStart); i < totalSamples; i++) {
      let factor = (totalSamples - i) / fadeOutSamples

      switch (fadeType) {
        case 'exponential':
          factor = factor * factor
          break
        case 'logarithmic':
          factor = Math.sqrt(factor)
          break
        default: // linear
          break
      }

      processedData[i] *= factor
    }

    self.postMessage({
      type: MessageTypes.APPLY_FADE,
      result: {
        taskId,
        success: true,
        data: processedData
      }
    })
  } catch (error) {
    self.postMessage({
      type: MessageTypes.APPLY_FADE,
      result: {
        taskId,
        success: false,
        error: error.message
      }
    })
  }
}

// 混合多个音频轨道
const mixTracks = (tracks, options = {}, taskId) => {
  try {
    const { outputLength = Math.max(...tracks.map((t) => t.data.length)), masterVolume = 1.0 } =
      options

    const mixedData = new Float32Array(outputLength)

    tracks.forEach((track) => {
      const { data, volume = 1.0, startTime = 0, pan = 0 } = track
      const startSample = Math.floor(startTime * sampleRate)

      for (let i = 0; i < data.length && startSample + i < outputLength; i++) {
        const outputIndex = startSample + i
        if (outputIndex >= 0) {
          // 应用音量和声像
          let sample = data[i] * volume

          // 简单的声像处理（这里可以扩展为更复杂的算法）
          if (pan !== 0) {
            sample *= 1 - Math.abs(pan)
          }

          mixedData[outputIndex] += sample
        }
      }
    })

    // 应用主音量
    for (let i = 0; i < mixedData.length; i++) {
      mixedData[i] *= masterVolume
    }

    self.postMessage({
      type: MessageTypes.MIX_TRACKS,
      result: {
        taskId,
        success: true,
        data: mixedData
      }
    })
  } catch (error) {
    self.postMessage({
      type: MessageTypes.MIX_TRACKS,
      result: {
        taskId,
        success: false,
        error: error.message
      }
    })
  }
}

// 批量处理
const processBatch = async (tasks, taskId) => {
  try {
    const results = []

    for (const task of tasks) {
      switch (task.type) {
        case 'normalize':
          // 这里会调用相应的处理函数，但需要同步等待结果
          break
        case 'fade':
          // 淡入淡出处理
          break
        case 'volume':
          // 音量调整
          const volumeData = new Float32Array(task.data.length)
          for (let i = 0; i < task.data.length; i++) {
            volumeData[i] = task.data[i] * task.options.gain
          }
          results.push({
            taskType: task.type,
            data: volumeData
          })
          break
        default:
          results.push({
            taskType: task.type,
            error: `Unknown task type: ${task.type}`
          })
      }
    }

    self.postMessage({
      type: MessageTypes.PROCESS_BATCH,
      result: {
        taskId,
        success: true,
        data: results
      }
    })
  } catch (error) {
    self.postMessage({
      type: MessageTypes.PROCESS_BATCH,
      result: {
        taskId,
        success: false,
        error: error.message
      }
    })
  }
}

// 消息处理
self.onmessage = function (e) {
  const { type, data, taskId } = e.data

  switch (type) {
    case MessageTypes.DECODE_AUDIO:
      decodeAudio(data.arrayBuffer, taskId)
      break

    case MessageTypes.GENERATE_WAVEFORM:
      generateWaveform(data.channelData, data.options, taskId)
      break

    case MessageTypes.CALCULATE_PEAKS:
      calculatePeaks(data.channelData, data.options, taskId)
      break

    case MessageTypes.NORMALIZE_AUDIO:
      normalizeAudio(data.channelData, data.targetLevel, taskId)
      break

    case MessageTypes.APPLY_FADE:
      applyFade(data.channelData, data.options, taskId)
      break

    case MessageTypes.MIX_TRACKS:
      mixTracks(data.tracks, data.options, taskId)
      break

    case MessageTypes.PROCESS_BATCH:
      processBatch(data.tasks, taskId)
      break

    default:
      self.postMessage({
        type: 'error',
        result: {
          taskId,
          success: false,
          error: `Unknown message type: ${type}`
        }
      })
  }
}
