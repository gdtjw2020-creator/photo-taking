<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import { Loading, ZoomIn, Close, Plus, Download, Camera, Picture, Edit, Check } from '@element-plus/icons-vue'
import api from '../api'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { resizeImageIfNeeded } from '../utils/imageResize'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isLoggedIn = computed(() => authStore.isLoggedIn)
const CREDITS_PER_IMAGE = ref(5) // 默认为 5，之后从后端动态同步

// ========== MVP 模式支持 ==========
const currentMode = computed(() => route.query.mode || null)
const oldPhotoStyles = ref([])
const isLoadingStyles = ref(false)
const selectedStyle = ref(null)
const darkroomPackage = ref(3)
const promptMode = ref('similar')
const isAdmin = ref(false)
const previewStyle = ref(null)
const showPreview = ref(false)

// 构图选项定义
const framingOptions = [
  { label: '特写', value: 'portrait', icon: '👤', desc: '头部到肩膀' },
  { label: '上身', value: 'upper_body', icon: '👕', desc: '胸部以上' },
  { label: '半身', value: 'half_body', icon: '👖', desc: '膝盖以上' },
  { label: '七分', value: 'three_quarter', icon: '👢', desc: '小腿以上' },
  { label: '全身', value: 'full_body', icon: '🧍', desc: '从头到脚' }
]
const selectedFraming = ref(null)

// 照片比例选项与响应式状态 (9:16, 3:4, 1:1)
const sizeOptions = [
  { label: '9:16 竖屏', value: '1440x2560', desc: '适合手机壁纸、海报' },
  { label: '3:4 相片', value: '1728x2304', desc: '经典复古冲印比例' },
  { label: '1:1 方形', value: '2048x2048', desc: '社交头像、方形画幅' }
]
const selectedSize = ref('1440x2560')

const pageTitle = computed(() => {
  const m = { classic_style: '时代艺术照', darkroom_random: '暗房盲盒', reference_shoot: '照着样子拍' }
  return m[currentMode.value] || 'AI 写真'
})

const pageSubtitle = computed(() => {
  const m = {
    classic_style: '挑一个年代风格，让唐师傅给您拍张旧时光里的肖像',
    darkroom_random: '交给暗房随机冲洗几张惊喜底片',
    reference_shoot: '上传一张参考图，唐师傅照着样子给您拍'
  }
  return m[currentMode.value] || ''
})

const expectedCount = computed(() => {
  if (currentMode.value === 'darkroom_random') return darkroomPackage.value
  if (currentMode.value === 'reference_shoot') return referenceImages.value.length || 1
  return selectedCount.value
})

const submitButtonText = computed(() => {
  const m = { classic_style: '让唐师傅开拍', darkroom_random: '开启暗房冲洗', reference_shoot: '照着样子拍' }
  return `${m[currentMode.value] || '开始拍摄'} (${expectedCount.value} 张)`
})

const savedFaces = ref([])

const loadStyles = async () => {
  if (currentMode.value === 'classic_style') {
    if (oldPhotoStyles.value.length > 0) return // Already loaded
    
    isLoadingStyles.value = true
    try {
      const stylesRes = await api.get('/api/photoshoot/old_photo_styles')
      oldPhotoStyles.value = stylesRes.data
    } catch (err) {
      console.error('Failed to load old photo styles:', err)
      ElMessage.error('加载年代风格失败，请刷新重试')
    } finally {
      isLoadingStyles.value = false
    }
  }
}

// 监听模式变化，确保在切换到相关模式时加载风格，并进行初始化重置
watch(() => currentMode.value, (newMode) => {
  loadStyles()
  if (newMode === 'darkroom_random') {
    selectedFraming.value = 'default'
    selectedSize.value = '1440x2560'
  } else if (newMode === 'classic_style') {
    selectedFraming.value = null
    selectedSize.value = '1440x2560'
  } else {
    selectedFraming.value = null
    selectedSize.value = '1440x2560'
  }
})

onMounted(async () => {
  try {
    // 同步后端配置（实现环境变量统一）
    const configRes = await api.get('/api/photoshoot/config')
    if (configRes.data?.credits_per_photoshoot) {
        CREDITS_PER_IMAGE.value = configRes.data.credits_per_photoshoot
    }

    // 加载老照片风格
    await loadStyles()
    
    // 加载个人资料及管理员状态
    if (isLoggedIn.value) {
      try {
        const profileRes = await api.get('/api/user/profile')
        if (profileRes.data?.is_admin) {
          isAdmin.value = true
        }
      } catch (err) {
        console.warn('Failed to fetch profile for admin check')
      }
    }
    
    // 加载已存形象 (仅登录用户)
    if (isLoggedIn.value) {
      const faceRes = await api.get('/api/photoshoot/faces')
      savedFaces.value = faceRes.data

      // 新增：检查是否有正在进行的活跃任务，实现“断点续传”
      const activeRes = await api.get('/api/photoshoot/active_task')
      if (activeRes.data) {
          const task = activeRes.data
          let imgCount = 1
          if (task.metadata) {
              let meta = task.metadata
              if (typeof meta === 'string') {
                  try { meta = JSON.parse(meta) } catch (e) {}
              }
              if (meta.selected_prompts) {
                  imgCount = meta.selected_prompts.length || 1
              }
          }
          console.log('[DEBUG] Found active task, resuming polling:', task.id, 'with image count:', imgCount)
          taskId.value = task.id
          taskStatus.value = task.status
          resultImages.value = task.output_urls || []
          const startTime = task.created_at ? new Date(task.created_at).getTime() : null
          // 如果有正在进行的任务，自动切换到结果视图
          isGenerating.value = true
          startPolling(task.id, startTime, imgCount)
      }
    }
    // 处理从“形象存档”跳转过来的情况
    if (route.query.face_url) {
      uploadedImageUrl.value = route.query.face_url
      ElMessage.info('已自动装载形象存档')
    }
  } catch (err) {
    console.error('Failed to init data:', err)
  }
})

const uploadedImageUrl = ref('')
const referenceImages = ref([])
const selectedCount = ref(1)
const isRefUploading = ref(false)
const isUploading = ref(false)
const isGenerating = ref(false)
const autoSaveFace = ref(true)
const taskId = ref('')
const isAgreed = ref(false)
const addWatermark = ref(true)

const selectOldStyle = (style) => {
  selectedStyle.value = style
  // 切换风格时，自动同步该风格推荐的默认景别
  selectedFraming.value = style.default_framing || 'half_body'
  
  if (selectedCount.value > (style.recommended_count || 2)) {
    selectedCount.value = style.recommended_count || 2
  }
}

const goBack = () => {
  router.push('/')
}

const checkAuth = (msg = '请先登录后开启您的时光留影之旅') => {
  if (!isLoggedIn.value) {
    ElMessageBox.confirm(
      msg,
      '登录提醒',
      {
        confirmButtonText: '立即登录',
        cancelButtonText: '先看看',
        type: 'info',
        center: true,
        roundButton: true
      }
    ).then(() => {
      router.push(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
    }).catch(() => {})
    return false
  }
  return true
}

const cameraInput = ref(null)
const galleryInput = ref(null)

const triggerCamera = () => {
  if (!checkAuth('拍照前需要登录，以便为您保存形象存档')) return
  if (cameraInput.value) cameraInput.value.click()
}

const triggerGallery = () => {
  if (!checkAuth('从相册选取前需要登录，以便为您保存形象存档')) return
  if (galleryInput.value) galleryInput.value.click()
}

const uploadImage = async (rawFile) => {
  if (!checkAuth('上传照片前需要登录，以便为您保存形象存档')) return
  isUploading.value = true
  const formData = new FormData()
  
  try {
    const resizedFile = await resizeImageIfNeeded(rawFile)
    formData.append('file', resizedFile)

    const res = await api.post('/api/photoshoot/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    uploadedImageUrl.value = res.data.url
    ElMessage.success('照片上传成功')

    // 改进：上传成功后立即自动保存到形象存档
    if (autoSaveFace.value) {
      saveCurrentFace()
    }
  } catch (err) {
    const detail = err.response?.data?.detail || '上传失败，请重试'
    ElMessage.error(detail)
  } finally {
    isUploading.value = false
  }
}

const handleUpload = async (file) => {
  await uploadImage(file.raw)
}

const onFileChange = async (e) => {
  const file = e.target.files[0]
  if (file) {
    await uploadImage(file)
    // 重置 input，允许重复上传同一张图
    e.target.value = ''
  }
}

const handleRefUpload = async (file) => {
  if (!checkAuth('上传创作底图前需要登录')) return
  isRefUploading.value = true
  const formData = new FormData()
  const resizedFile = await resizeImageIfNeeded(file.raw)
  formData.append('file', resizedFile)

  try {
    const res = await api.post('/api/photoshoot/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    referenceImages.value.push(res.data.url)
    ElMessage.success('参考图上传成功')
  } catch (err) {
    const detail = err.response?.data?.detail || '上传失败，请重试'
    ElMessage.error(detail)
  } finally {
    isRefUploading.value = false
  }
}

const removeRef = (index) => {
  referenceImages.value.splice(index, 1)
}

const saveCurrentFace = async () => {
  if (!uploadedImageUrl.value) return
  console.log('[DEBUG] Attempting to save face:', uploadedImageUrl.value)
  try {
    const res = await api.post('/api/photoshoot/faces', {
      face_url: uploadedImageUrl.value,
      name: `形象存档 ${savedFaces.value.length + 1}`
    })
    console.log('[DEBUG] Save face success:', res.data)
    savedFaces.value.unshift(res.data)
    ElMessage.success('已永久保存到我的形象库')
  } catch (err) {
    console.error('[DEBUG] Save face error:', err)
    ElMessage.error('保存失败')
  }
}

const selectSavedFace = (face) => {
  uploadedImageUrl.value = face.face_url
}

const submitTask = async () => {
  if (!checkAuth('开启 AI 留影任务需要登录以扣除积分')) return

  // ========== MVP 模式校验 ==========
  if (currentMode.value === 'classic_style') {
    if (!selectedStyle.value) {
      ElMessage.warning('请先选择一个年代风格')
      return
    }
    if (!uploadedImageUrl.value) {
      ElMessage.warning('请先上传您的照片')
      return
    }
  } else if (currentMode.value === 'darkroom_random') {
    if (!uploadedImageUrl.value) {
      ElMessage.warning('请先上传您的照片')
      return
    }
  } else if (currentMode.value === 'reference_shoot') {
    if (referenceImages.value.length === 0) {
      ElMessage.warning('请先上传参考图')
      return
    }
    if (!uploadedImageUrl.value) {
      ElMessage.warning('请先上传您的人脸照片')
      return
    }
  } else {
    if (!uploadedImageUrl.value) {
      ElMessage.warning('请先上传您的照片')
      return
    }
  }

  if (!isAgreed.value) {
    try {
      await ElMessageBox.confirm(
        '开启拍摄前，请确认您上传的照片已获本人授权，且生成的图片仅用于个人娱乐。',
        '合规使用确认',
        { confirmButtonText: '确认', cancelButtonText: '取消', type: 'info', center: true }
      )
      isAgreed.value = true
    } catch (e) { return }
  }

  isGenerating.value = true
  try {
    if (autoSaveFace.value && !savedFaces.value.some(f => f.face_url === uploadedImageUrl.value)) {
        await saveCurrentFace()
    }

    const payloads = {
      classic_style: { 
        module_type: 'classic_style', 
        style_id: selectedStyle.value?.id, 
        image_url: uploadedImageUrl.value, 
        image_count: selectedCount.value, 
        watermark: addWatermark.value,
        framing: selectedFraming.value, // 传递景别参数
        size: selectedSize.value // 传递尺寸参数
      },
      darkroom_random: { 
        module_type: 'darkroom_random', 
        image_url: uploadedImageUrl.value, 
        image_count: darkroomPackage.value, 
        watermark: addWatermark.value,
        framing: selectedFraming.value === 'default' ? null : selectedFraming.value, // 传递暗房盲盒景别参数
        size: selectedSize.value // 传递暗房盲盒尺寸参数
      },
      reference_shoot: { 
        module_type: 'reference_shoot', 
        prompt_mode: promptMode.value, 
        image_url: uploadedImageUrl.value, 
        reference_image_urls: referenceImages.value, 
        image_count: referenceImages.value.length || 1, 
        watermark: addWatermark.value,
        size: 'auto' // 照着样子拍，尺寸固定为 auto 匹配参考图
      }
    }
    const payload = payloads[currentMode.value] || payloads.classic_style

    const res = await api.post('/api/photoshoot/generate', payload)
    taskId.value = res.data.task_id
    resultImages.value = [] // 立即重置旧图片，显示新占位符
    errorMessage.value = '' // 重置错误信息
    ElMessage.success('任务已提交，唐师傅正在准备...')

    let imgCount = 1
    if (currentMode.value === 'classic_style') {
      imgCount = selectedCount.value
    } else if (currentMode.value === 'darkroom_random') {
      imgCount = darkroomPackage.value
    } else if (currentMode.value === 'reference_shoot') {
      imgCount = referenceImages.value.length || 1
    }

    startPolling(res.data.task_id, null, imgCount)
  } catch (err) {
    const msg = err.response?.data?.detail || '开启任务失败，请稍后重试'
    ElMessage.error(msg)
    errorMessage.value = msg
    taskStatus.value = 'failed'
    isGenerating.value = false
  }
}

const pollTimer = ref(null)
const taskStatus = ref('')
const errorMessage = ref('')
const debugMessage = ref('')
const showDebug = ref(false)
const resultImages = ref([])
const taskStartTime = ref(null)     // 任务提交时间 (ms)
const elapsedSeconds = ref(0)       // 已等待秒数
const MAX_WAIT_SECONDS = 900        // 后端硬超时 15 分钟

const formattedElapsed = computed(() => {
  const mins = Math.floor(elapsedSeconds.value / 60)
  const secs = elapsedSeconds.value % 60
  return `${mins} 分 ${secs.toString().padStart(2, '0')} 秒`
})

const loadingText = computed(() => {
  if (resultImages.value.length === 0) {
    if (elapsedSeconds.value < 15) return '唐师傅正在找底片...'
    if (elapsedSeconds.value < 30) return '暗房安全灯亮了...'
    return '显影液开始起作用了...'
  } else {
    return `第 ${resultImages.value.length + 1} 张照片快出来了...`
  }
})

const isLongWait = computed(() => elapsedSeconds.value > 300) // 超过 5 分钟提示离开

const startPolling = (tid, existingStartTime = null, imgCount = 1) => {
  taskStatus.value = 'processing'
  taskStartTime.value = existingStartTime || Date.now()
  elapsedSeconds.value = Math.floor((Date.now() - taskStartTime.value) / 1000)

  const promptsCount = imgCount || 1
  const dynamicMaxSeconds = promptsCount * 7 * 60 // 每张图片最长 7 分钟
  const dynamicMaxMins = promptsCount * 7

  // 如果恢复的任务已经超过最大等待时间，直接标记失败不再轮询
  if (elapsedSeconds.value >= dynamicMaxSeconds) {
    errorMessage.value = `任务已提交超过 ${dynamicMaxMins} 分钟，已自动超时。请到相册查看是否有已生成的结果，或重新提交。`
    taskStatus.value = 'failed'
    isGenerating.value = false
    return
  }

  pollTimer.value = setInterval(async () => {
    try {
      elapsedSeconds.value = Math.floor((Date.now() - taskStartTime.value) / 1000)

      if (elapsedSeconds.value >= dynamicMaxSeconds) {
        errorMessage.value = `已等待超过 ${dynamicMaxMins} 分钟，任务可能已超时。请稍后到相册查看结果。`
        ElMessage.warning(errorMessage.value)
        stopPolling()
        taskStatus.value = 'failed'
        return
      }

      const res = await api.get(`/api/photoshoot/task_status?task_id=${tid}`)
      const data = res.data
      taskStatus.value = data.status

      // 增量更新已生成的图片
      if (data.output_urls && data.output_urls.length > resultImages.value.length) {
          resultImages.value = data.output_urls
          ElMessage({
              message: `第 ${data.output_urls.length} 张留影照已冲洗完成，扣除 1 积分`,
              type: 'success',
              duration: 2000
          })
      }

      if (data.status === 'completed') {
        ElMessage.success('全组照片冲洗完成！')
        stopPolling()
      } else if (data.status === 'failed') {
        const fullMsg = data.error_message || '影艺创作遇到一点小麻烦'
        if (fullMsg.includes(' | [DEBUG] ')) {
          const parts = fullMsg.split(' | [DEBUG] ')
          errorMessage.value = parts[0]
          debugMessage.value = parts[1]
        } else {
          errorMessage.value = fullMsg
          debugMessage.value = ''
        }
        ElMessage.error(errorMessage.value)
        stopPolling()
      }
    } catch (err) {
      console.error('Polling error:', err)
    }
  }, 3000)
}

const stopPolling = () => {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
  isGenerating.value = false
}

const isMobile = ref(/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent))

const downloadImage = (url) => {
  // 使用后端代理下载接口，解决跨域问题并强制触发下载
  // 核心修复：确保使用了完整的 API 基础路径，防止在非同域部署时失效
  const baseUrl = (api.defaults.baseURL || '').replace(/\/$/, '')
  const proxyUrl = `${baseUrl}/api/photoshoot/download?url=${encodeURIComponent(url)}`
  
  if (isMobile.value) {
    // 移动端：直接跳转到下载链接
    // 很多移动浏览器（如 iOS Safari）对 programmatic a.click() 限制较多
    // window.location.href 在后端返回 Content-Disposition: attachment 时能更好地触发系统下载处理器
    window.location.href = proxyUrl
  } else {
    const link = document.createElement('a')
    link.href = proxyUrl
    // 后端已设置 Content-Disposition，浏览器会识别为下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

const downloadAll = async () => {
  if (resultImages.value.length === 0) return
  
  if (isMobile.value) {
    ElMessage.warning('移动端暂不支持批量下载，请点击图片下方的按钮逐张保存')
    return
  }

  ElMessage.info('开始下载照片...')
  for (let i = 0; i < resultImages.value.length; i++) {
    downloadImage(resultImages.value[i])
    // 延迟防止浏览器拦截
    await new Promise(resolve => setTimeout(resolve, 800))
  }
}

// 管理员功能：更新风格封面
const styleCoverInput = ref(null)
const targetStyleId = ref(null)
const updatingStyleId = ref(null) // 用于局部加载状态

const triggerAdminCoverUpload = (styleId) => {
  targetStyleId.value = styleId
  if (styleCoverInput.value) styleCoverInput.value.click()
}

const handleAdminCoverUpload = async (e) => {
  const file = e.target.files[0]
  if (!file || !targetStyleId.value) return
  
  updatingStyleId.value = targetStyleId.value
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await api.post(`/api/photoshoot/styles/${targetStyleId.value}/cover`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    // 更新本地显示
    const style = oldPhotoStyles.value.find(s => s.id === targetStyleId.value)
    if (style) {
      style.preview_url = res.data.preview_url
    }
    ElMessage.success('风格封面更新成功')
  } catch (err) {
    console.error('Update cover error:', err)
    ElMessage.error(err.response?.data?.detail || '更新失败')
  } finally {
    updatingStyleId.value = null
    e.target.value = ''
  }
}

const triggerPreview = (style) => {
  previewStyle.value = style
  showPreview.value = true
}

const openFeedbackDialog = () => {
  if (!checkAuth('请登录后再提交风格建议，以便唐师傅给您答复')) return
  
  ElMessageBox.prompt('告诉唐师傅您期待的年代背景、人像服装或特定摄影风格：', '建议新风格', {
    confirmButtonText: '提交建议',
    cancelButtonText: '我再想想',
    inputPattern: /\S+/,
    inputErrorMessage: '输入内容不能为空',
    inputType: 'textarea',
    inputPlaceholder: '例：希望出一套唐装汉服风格 / 80年代校园怀旧风...',
    customClass: 'feedback-prompt-box'
  }).then(async ({ value }) => {
    try {
      await api.post('/api/user/feedback', {
        content: value,
        type: 'style_request'
      })
      ElMessage.success('收到您的风格建议！唐师傅马上着手开发！')
    } catch (err) {
      ElMessage.error(err.response?.data?.detail || '提交失败，请重试')
    }
  }).catch(() => {})
}

</script>

<template>
  <div class="generate-container">
    <!-- 无模式时：选择拍摄方式 -->
    <template v-if="!currentMode">
      <div class="mode-select-header">
        <p class="mode-kicker">AI OLD PHOTO STUDIO</p>
        <h1 class="mode-title">选择拍摄方式</h1>
      </div>
      <div class="mode-card-grid">
        <button v-for="s in [{mode:'classic_style',title:'时代艺术照',sub:'挑一个年代，拍张旧时光里的肖像',meta:'8 款经典风格',icon:'🎞️'},{mode:'darkroom_random',title:'暗房盲盒',sub:'交给暗房随机冲洗惊喜底片',meta:'3 / 6 / 9 张套餐',icon:'🎰'},{mode:'reference_shoot',title:'照着样子拍',sub:'上传参考图，照着构图气氛重拍',meta:'参考图 + 人脸图',icon:'📸'}]" :key="s.mode" class="mode-card glass-card" @click="$router.push({query:{mode:s.mode}})">
          <span class="mode-card-icon">{{ s.icon }}</span>
          <span class="mode-card-meta">{{ s.meta }}</span>
          <strong>{{ s.title }}</strong>
          <span class="mode-card-sub">{{ s.sub }}</span>
          <span class="mode-card-action">去拍这套 →</span>
        </button>
      </div>
    </template>

    <!-- 有模式时：拍摄流程 -->
    <template v-else>
      <!-- 页头 -->
      <div class="mvp-page-header glass-card">
        <div class="mvp-header-back" @click="goBack">← 换一种拍法</div>
        <p class="mvp-kicker">{{ pageTitle }}</p>
        <h1 class="mvp-title">{{ pageSubtitle }}</h1>
      </div>

      <!-- ===== 时代艺术照 Step 1 ===== -->
      <div v-if="currentMode === 'classic_style'" class="step-card glass-card">
        <h2>1. 选择年代风格</h2>
        
        <!-- 第一阶段：加载风格文本资料 -->
        <div v-if="isLoadingStyles && oldPhotoStyles.length === 0" class="styles-meta-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <p>正在冲洗风格名录...</p>
        </div>

        <div v-else class="old-style-grid">
          <div v-for="style in oldPhotoStyles" :key="style.id" class="old-style-item" 
            :class="{ active: selectedStyle?.id === style.id }" 
            @click="selectOldStyle(style)"
          >
            <div class="old-style-img-container"
              v-loading="updatingStyleId === style.id"
              element-loading-text="更新中..."
              element-loading-background="rgba(0, 0, 0, 0.6)"
            >
              <el-image v-if="style.preview_url" :src="style.preview_url" fit="cover" class="old-style-img" lazy :preview-src-list="[style.preview_url]" preview-teleported hide-on-click-modal>
                <template #placeholder>
                  <div class="old-style-placeholder"><el-icon class="is-loading"><Loading /></el-icon></div>
                </template>
                <template #error>
                  <div class="old-style-placeholder"><span class="placeholder-era-icon">📷</span></div>
                </template>
              </el-image>
              <div v-else class="old-style-placeholder"><span class="placeholder-era-icon">📷</span></div>
              
              <!-- 放大查看按钮 -->
              <div v-if="style.preview_url" class="style-zoom-badge" @click.stop="triggerPreview(style)">
                 <el-icon><ZoomIn /></el-icon>
              </div>
              
              <!-- 管理员快捷编辑 -->
              <div v-if="isAdmin" class="admin-edit-badge" @click.stop="triggerAdminCoverUpload(style.id)">
                <el-icon><Edit /></el-icon> 换封面
              </div>
            </div>
             <div class="old-style-info">
               <span class="old-style-name">{{ style.name }}</span>
               <span class="old-style-desc" :title="style.description">{{ style.description }}</span>
             </div>
           </div>
          
          <!-- 用户建议/反馈风格专属卡片 -->
          <div class="old-style-item feedback-style-card" @click="openFeedbackDialog">
            <div class="old-style-img-container">
              <div class="old-style-placeholder feedback-placeholder">
                <span class="placeholder-era-icon">✨</span>
              </div>
            </div>
            <div class="old-style-info">
              <span class="old-style-name">想要其他风格？</span>
              <span class="old-style-desc">告诉唐师傅您期待的风格，我们将全力为您开发上线！</span>
            </div>
          </div>
        </div>
        <!-- 隐藏的管理员文件输入 -->
        <input type="file" ref="styleCoverInput" style="display: none" accept="image/*" @change="handleAdminCoverUpload">
        
        <!-- 景别选择 (仅在选好风格后显示) -->
        <div v-if="selectedStyle" class="framing-section animate__animated animate__fadeIn">
          <div class="section-divider"></div>
          <h3>2. 选择拍摄景别</h3>
          <p class="section-subtitle">唐师傅已为您推荐最适配当前风格的构图，您也可以手动调整</p>
          <div class="framing-grid">
            <div v-for="opt in framingOptions" :key="opt.value" 
              class="framing-item" 
              :class="{ active: selectedFraming === opt.value, 'is-recommended': selectedStyle.default_framing === opt.value }"
              @click="selectedFraming = opt.value"
            >
              <div class="framing-icon-box">{{ opt.icon }}</div>
              <div class="framing-meta">
                <span class="framing-label">{{ opt.label }}</span>
                <span class="framing-desc">{{ opt.desc }}</span>
              </div>
              <div v-if="selectedStyle.default_framing === opt.value" class="recommend-badge">推荐</div>
              <div class="active-check" v-if="selectedFraming === opt.value">
                <el-icon><Check /></el-icon>
              </div>
            </div>
          </div>
        </div>

        <!-- 比例选择 (仅在选好风格后显示) -->
        <div v-if="selectedStyle" class="aspect-ratio-section animate__animated animate__fadeIn">
          <div class="section-divider"></div>
          <h3>3. 选择照片比例</h3>
          <p class="section-subtitle">选择您期望的输出照片比例（均采用超清 2K 分辨率）</p>
          <div class="aspect-ratio-grid">
            <div v-for="opt in sizeOptions" :key="opt.value" 
              class="aspect-ratio-item" 
              :class="{ active: selectedSize === opt.value }"
              @click="selectedSize = opt.value"
            >
              <div class="aspect-ratio-preview" :class="opt.value === '1440x2560' ? 'portrait' : opt.value === '1728x2304' ? 'photo' : 'square'">
                <div class="aspect-ratio-box"></div>
              </div>
              <div class="aspect-ratio-meta">
                <span class="aspect-ratio-label">{{ opt.label }}</span>
                <span class="aspect-ratio-desc">{{ opt.desc }}</span>
              </div>
              <div class="active-check" v-if="selectedSize === opt.value">
                <el-icon><Check /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 暗房盲盒 Step 1 ===== -->
      <div v-if="currentMode === 'darkroom_random'" class="step-card glass-card">
        <h2>1. 选择胶卷套餐</h2>
        <div class="count-selector film-selector">
          <div class="count-item film-item" :class="{ active: darkroomPackage === 3 }" @click="darkroomPackage = 3">
            <span class="film-count">3</span>
            <span class="film-label">体验盲盒</span>
          </div>
          <div class="count-item film-item" :class="{ active: darkroomPackage === 6 }" @click="darkroomPackage = 6">
            <span class="film-count">6</span>
            <span class="film-label">惊喜盲盒</span>
          </div>
          <div class="count-item film-item" :class="{ active: darkroomPackage === 9 }" @click="darkroomPackage = 9">
            <span class="film-count">9</span>
            <span class="film-label">豪华大满贯</span>
          </div>
        </div>
        <p class="count-hint">唐师傅随机挑选年代风格，为您冲洗 {{ darkroomPackage }} 张惊喜老照片</p>

        <!-- 暗房盲盒比例选择 -->
        <div class="aspect-ratio-section animate__animated animate__fadeIn">
          <div class="section-divider"></div>
          <h3>2. 选择照片比例</h3>
          <p class="section-subtitle">选择您期望的输出照片比例，默认 9:16（采用超清 2K 分辨率）</p>
          <div class="aspect-ratio-grid">
            <div v-for="opt in sizeOptions" :key="opt.value" 
              class="aspect-ratio-item" 
              :class="{ active: selectedSize === opt.value }"
              @click="selectedSize = opt.value"
            >
              <div class="aspect-ratio-preview" :class="opt.value === '1440x2560' ? 'portrait' : opt.value === '1728x2304' ? 'photo' : 'square'">
                <div class="aspect-ratio-box"></div>
              </div>
              <div class="aspect-ratio-meta">
                <span class="aspect-ratio-label">{{ opt.label }}</span>
                <span class="aspect-ratio-desc">{{ opt.desc }}</span>
              </div>
              <div class="active-check" v-if="selectedSize === opt.value">
                <el-icon><Check /></el-icon>
              </div>
            </div>
          </div>
        </div>

        <!-- 暗房盲盒景别选择 -->
        <div class="framing-section animate__animated animate__fadeIn">
          <div class="section-divider"></div>
          <h3>3. 选择拍摄景别</h3>
          <p class="section-subtitle">盲盒模式下，景别可以选择默认随机（跟随风格）或指定统一景别</p>
          <div class="framing-grid">
            <!-- 默认选项 -->
            <div class="framing-item" 
              :class="{ active: selectedFraming === null || selectedFraming === 'default' }"
              @click="selectedFraming = 'default'"
            >
              <div class="framing-icon-box">🎲</div>
              <div class="framing-meta">
                <span class="framing-label">默认随机</span>
                <span class="framing-desc">使用每款风格最适合的景别</span>
              </div>
              <div class="active-check" v-if="selectedFraming === null || selectedFraming === 'default'">
                <el-icon><Check /></el-icon>
              </div>
            </div>
            <!-- 具体选项 -->
            <div v-for="opt in framingOptions" :key="opt.value" 
              class="framing-item" 
              :class="{ active: selectedFraming === opt.value }"
              @click="selectedFraming = opt.value"
            >
              <div class="framing-icon-box">{{ opt.icon }}</div>
              <div class="framing-meta">
                <span class="framing-label">{{ opt.label }}</span>
                <span class="framing-desc">{{ opt.desc }}</span>
              </div>
              <div class="active-check" v-if="selectedFraming === opt.value">
                <el-icon><Check /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 照着样子拍 Step 1 ===== -->
      <div v-if="currentMode === 'reference_shoot'" class="step-card glass-card">
        <h2>1. 上传参考图</h2>
        <p class="sub-hint">上传您心仪的参考图，唐师傅会照着构图和气氛给您重拍。</p>
        <div class="ref-list">
          <div v-for="(img, idx) in referenceImages" :key="idx" class="ref-item">
            <el-image 
              :src="img" 
              fit="cover" 
              class="ref-img"
              :preview-src-list="referenceImages"
              :initial-index="idx"
              preview-teleported
            ></el-image>
            <div class="del-btn" @click.stop="removeRef(idx)"><el-icon><Close /></el-icon></div>
          </div>
          <el-upload v-if="referenceImages.length < 3" class="ref-upload-box" action="#" :auto-upload="false" :show-file-list="false" :on-change="handleRefUpload" accept="image/*">
            <div class="ref-upload-btn" v-loading="isRefUploading"><el-icon><Plus /></el-icon></div>
          </el-upload>
        </div>
      </div>

      <!-- ===== 共享 Step: 上传人脸照 ===== -->
      <div class="step-card glass-card">
        <h2>{{ currentMode === 'reference_shoot' ? '2. 上传您的人脸照' : '2. 上传您的照片' }}</h2>
        <div v-if="savedFaces.length > 0" class="saved-faces-section">
          <p class="sub-hint">常用形象存档：</p>
          <div class="face-list">
            <div v-for="face in savedFaces" :key="face.id" class="face-item" :class="{ active: uploadedImageUrl === face.face_url }" @click="selectSavedFace(face)">
              <img :src="face.face_url">
            </div>
          </div>
        </div>
        <div class="upload-area">
          <!-- 隐藏的原生 Input 用于更精准的控制 -->
          <input type="file" ref="cameraInput" accept="image/*" capture="user" style="display: none" @change="onFileChange">
          <input type="file" ref="galleryInput" accept="image/*" style="display: none" @change="onFileChange">

          <div v-if="!uploadedImageUrl" class="upload-choice-container" v-loading="isUploading">
            <!-- 移动端：双按钮模式 -->
            <template v-if="isMobile">
              <div class="choice-item camera" @click="triggerCamera">
                <div class="choice-icon"><el-icon><Camera /></el-icon></div>
                <span>拍照拍摄</span>
              </div>
              <div class="choice-divider"></div>
              <div class="choice-item gallery" @click="triggerGallery">
                <div class="choice-icon"><el-icon><Picture /></el-icon></div>
                <span>从相册选取</span>
              </div>
            </template>

            <!-- 电脑端：标准上传模式 -->
            <template v-else>
              <el-upload 
                class="desktop-full-upload" 
                drag 
                action="#" 
                :auto-upload="false" 
                :show-file-list="false" 
                :on-change="handleUpload"
                accept="image/*"
              >
                <div class="desktop-upload-content">
                  <el-icon class="upload-icon"><Plus /></el-icon>
                  <div class="upload-text">点击上传 或 将照片拖拽到此处</div>
                  <div class="upload-subtext">支持 JPG, PNG, WebP 格式</div>
                </div>
              </el-upload>
            </template>
          </div>

          <div v-else class="preview-box glass-card" @click="uploadedImageUrl = ''">
            <img :src="uploadedImageUrl" class="uploaded-img">
            <div class="change-hint">点击更换照片</div>
          </div>
        </div>
        <div v-if="uploadedImageUrl" class="save-face-action">
          <el-checkbox v-model="autoSaveFace">自动保存到形象库</el-checkbox>
        </div>
        <p class="hint-text">请确保照片面部清晰、光线充足，尽量上传头肩照</p>
      </div>

      <!-- ===== Step 3: 生成设置 ===== -->
      <div v-if="currentMode === 'classic_style'" class="step-card glass-card">
        <h2>3. 拍摄数量</h2>
        <div class="count-selector">
          <div v-for="n in [1, 2]" :key="n" class="count-item" :class="{ active: selectedCount === n }" @click="selectedCount = n">
            {{ n }} 张
          </div>
        </div>
        <p class="count-hint" v-if="selectedStyle">{{ selectedStyle.name }} 风格，每张使用不同拍摄手法</p>
      </div>

      <div v-if="currentMode === 'reference_shoot'" class="step-card glass-card">
        <h2>3. 模仿强度</h2>
        <div class="count-selector">
          <div class="count-item" :class="{ active: promptMode === 'similar' }" @click="promptMode = 'similar'">
            神似就行
          </div>
          <div class="count-item" :class="{ active: promptMode === 'strict' }" @click="promptMode = 'strict'">
            严丝合缝
          </div>
          <div class="count-item" :class="{ active: promptMode === 'creative' }" @click="promptMode = 'creative'">
            师傅发挥
          </div>
        </div>
      </div>

      <!-- ===== 积分 + 提交 ===== -->
      <div class="total-cost-box glass-card">
        消耗：<span class="cost-value">{{ (expectedCount * CREDITS_PER_IMAGE).toFixed(1) }}</span> 积分
        <span class="cost-unit">({{ CREDITS_PER_IMAGE }} 积分/张)</span>
      </div>
      <div class="action-bar">
        <el-button type="primary" class="primary-button large" :loading="isGenerating" @click="submitTask">{{ submitButtonText }}</el-button>
      </div>

      <!-- ===== 结果展示 ===== -->
      <div v-if="taskStatus" class="result-section glass-card">
        <div v-if="taskStatus === 'failed'" class="error-container">
          <el-alert :title="errorMessage" type="error" show-icon :closable="false">
            <template #default>
              <div class="error-details-wrapper">
                <p>建议：检查图片是否清晰，或稍后重试。</p>
                <div v-if="debugMessage" class="debug-toggle" @click="showDebug = !showDebug">
                  {{ showDebug ? '隐藏技术细节 ↑' : '查看错误详情 ↓' }}
                </div>
                <div v-if="showDebug" class="debug-content">
                  <code>{{ debugMessage }}</code>
                </div>
              </div>
            </template>
          </el-alert>
        </div>
        <div v-if="taskStatus === 'processing'" class="leave-hint">
          <el-alert title="后台冲洗中，可放心离开" type="info" :closable="false" show-icon>
            <template #default>唐师傅的暗房正在加班加点冲洗，稍后到<strong>「相册」</strong>查看。</template>
          </el-alert>
        </div>
        <div v-if="taskStatus === 'processing' && isLongWait" class="leave-hint">
          <el-alert :title="`已等待 ${formattedElapsed}，不如先逛逛？`" type="warning" :closable="false" show-icon />
        </div>
        <h2>取片成果
          <el-tag v-if="taskStatus === 'processing'" type="warning" size="small">冲洗中 ({{ resultImages.length }}/{{ expectedCount }}) {{ formattedElapsed }}</el-tag>
          <el-tag v-else-if="taskStatus === 'failed'" type="danger" size="small">出错</el-tag>
        </h2>
        <div class="result-grid">
          <div v-for="(url, index) in resultImages" :key="url" class="result-item">
            <el-image :src="url" :preview-src-list="resultImages" :initial-index="index" fit="cover" preview-teleported></el-image>
            <div class="result-download-btn" @click.stop="downloadImage(url)"><el-icon><Download /></el-icon></div>
          </div>
          <div v-for="n in Math.max(0, expectedCount - resultImages.length)" :key="'loading-'+n" class="result-item loading-placeholder" v-if="taskStatus === 'processing'">
            <div class="loading-content"><el-icon class="is-loading"><Loading /></el-icon><span>{{ loadingText }}</span></div>
          </div>
        </div>
        <div class="result-actions">
          <el-button type="success" @click="downloadAll">{{ isMobile ? '保存全部照片' : '下载全组照片' }}</el-button>
          <el-button @click="taskStatus = ''">再拍一套</el-button>
        </div>
        <p class="result-hint">提示：点击图片可查看大图{{ isMobile ? '，长按可保存到相册' : '' }}</p>
      </div>

      <!-- ===== 法律声明 ===== -->
      <div class="legal-notice">
        <el-checkbox v-model="isAgreed">我已确认照片为本人或已获授权</el-checkbox>
        <el-checkbox v-model="addWatermark" style="margin-left: 20px">添加"AI生成"水印</el-checkbox>
      </div>
    </template>

    <!-- 全屏预览 -->
    <div v-if="showPreview" class="full-screen-preview" @click="showPreview = false">
      <div class="preview-content" @click.stop>
        <img :src="previewStyle?.preview_url" class="preview-img" alt="预览图">
        
        <!-- 风格详情面板 -->
        <div class="preview-info-panel glass-card">
          <h3 class="preview-style-name">{{ previewStyle?.name }}</h3>
          <p class="preview-style-desc">{{ previewStyle?.description }}</p>
        </div>

        <div class="preview-close" @click="showPreview = false">
          <el-icon><Close /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.generate-container {
  padding: 20px 16px 100px;
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  box-sizing: border-box;
}

.error-details-wrapper {
  margin-top: 8px;
}

.debug-toggle {
  display: inline-block;
  margin-top: 10px;
  font-size: 0.75rem;
  color: #9bd7cb;
  cursor: pointer;
  text-decoration: underline;
  opacity: 0.8;
}

.debug-toggle:hover {
  opacity: 1;
}

.debug-content {
  margin-top: 10px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.7rem;
  color: #fca5a5;
  word-break: break-all;
  max-height: 150px;
  overflow-y: auto;
}

/* 模式选择页 */
.mode-select-header { text-align: center; margin: 28px 0 24px; }
.mode-kicker { margin: 0 0 8px; color: #f7c873; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.12em; }
.mode-title {
  font-size: 1.8rem; font-weight: 800;
  background: linear-gradient(135deg, #fff8e6 0%, #f7c873 48%, #9bd7cb 100%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; color: #fff8e6;
}
.mode-card-grid { display: grid; gap: 14px; }
.mode-card {
  width: 100%; padding: 20px; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px;
  color: #fff; text-align: left; cursor: pointer; display: grid; gap: 6px;
  background: linear-gradient(135deg, rgba(139, 107, 67, 0.3), rgba(26, 22, 20, 0.5));
  transition: all 0.2s;
}
.mode-card:hover { transform: translateY(-2px); border-color: rgba(247,200,115,0.48); }
.mode-card-icon { font-size: 1.8rem; }
.mode-card-meta { color: #f7c873; font-size: 0.78rem; font-weight: 700; }
.mode-card strong { font-size: 1.2rem; }
.mode-card-sub { color: rgba(255,255,255,0.7); font-size: 0.9rem; line-height: 1.5; }
.mode-card-action { color: #9bd7cb; font-weight: 700; font-size: 0.9rem; justify-self: start; }

/* MVP 页头 */
.mvp-page-header {
  text-align: center; padding: 20px; margin-bottom: 20px;
  background: linear-gradient(135deg, rgba(139, 107, 67, 0.15), rgba(26, 22, 20, 0.3));
  border: 1px solid rgba(212, 167, 106, 0.22); position: relative;
}
.mvp-header-back {
  position: absolute; left: 16px; top: 14px; color: #9bd7cb; font-size: 0.82rem;
  cursor: pointer; font-weight: 600; transition: color 0.2s;
}
.mvp-header-back:hover { color: #f7c873; }
.mvp-kicker { margin: 0 0 6px; color: #f7c873; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.1em; }
.mvp-title { font-size: 1.2rem; font-weight: 600; color: rgba(255,255,255,0.88); margin: 0; }

/* Step cards - 老照相馆风格 */
.step-card {
  padding: 20px; margin-bottom: 20px; animation: fadeIn 0.4s ease;
  background:
    linear-gradient(135deg, rgba(139, 107, 67, 0.1), rgba(26, 22, 20, 0.2)),
    repeating-linear-gradient(90deg, rgba(212, 167, 106, 0.03) 0 1px, transparent 1px 20px);
  border: 1px solid rgba(212, 167, 106, 0.18);
}
h2 { color: #f7c873; font-size: 1.1rem; margin-bottom: 16px; font-weight: 700; }

/* 风格选择 */
.old-style-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.old-style-item {
  position: relative;
  border-radius: 12px; overflow: hidden; border: 2px solid transparent; cursor: pointer;
  transition: all 0.3s; background: rgba(255,255,255,0.05); padding-bottom: 10px;
}
.old-style-item.active { border-color: #f7c873; box-shadow: 0 0 16px rgba(247,200,115,0.3); background: rgba(247,200,115,0.08); }
.old-style-item:hover { border-color: rgba(247,200,115,0.4); transform: translateY(-2px); }
.old-style-img-container { width: 100%; aspect-ratio: 4/5; overflow: hidden; background: rgba(0,0,0,0.2); position: relative; }
.old-style-img { width: 100%; height: 100%; transition: transform 0.5s; }
.old-style-item:hover .old-style-img { transform: scale(1.1); }
.old-style-placeholder {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  background:
    linear-gradient(135deg, rgba(139, 107, 67, 0.15), rgba(26, 22, 20, 0.25));
  filter: sepia(0.4) contrast(0.9);
  color: #f7c873;
}

.admin-edit-badge {
  position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.7);
  color: #f7c873; font-size: 0.7rem; padding: 4px 8px; border-radius: 20px;
  display: flex; align-items: center; gap: 4px; backdrop-filter: blur(4px);
  border: 1px solid rgba(247,200,115,0.3); transition: all 0.2s;
}
.admin-edit-badge:hover { background: #f7c873; color: #000; transform: scale(1.05); }

.style-zoom-badge {
  position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.5);
  color: #fff; width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(4px); transition: all 0.2s; cursor: pointer;
}
.style-zoom-badge:hover { background: rgba(247,200,115,0.8); color: #000; }
.placeholder-era-icon { font-size: 2.2rem; opacity: 0.6; }
.old-style-info { padding: 8px 10px 4px; display: flex; flex-direction: column; gap: 3px; }
.old-style-name { font-size: 0.95rem; font-weight: 600; color: #fff; }
.old-style-desc { font-size: 0.78rem; color: var(--text-muted); line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* 暗房胶卷选择 */
.film-selector { justify-content: center; }
.film-item { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 16px 12px; }
.film-count { font-size: 1.8rem; font-weight: 800; color: #f7c873; }
.film-label { font-size: 0.8rem; color: var(--text-muted); }
.film-item.active .film-count { color: #fff; }

/* 上传区 */
.upload-area { margin-bottom: 12px; }
.upload-choice-container {
  display: flex; height: 160px; border-radius: 12px; overflow: hidden;
  background: linear-gradient(135deg, rgba(91,49,36,0.1), rgba(16,38,43,0.15));
  border: 1px solid rgba(212, 167, 106, 0.2); position: relative;
}
.choice-item {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; cursor: pointer; transition: all 0.3s; color: var(--text-muted);
}
.choice-item:hover { background: rgba(212, 167, 106, 0.08); color: #f7c873; }
.choice-icon {
  width: 54px; height: 54px; border-radius: 50%; background: rgba(255,255,255,0.05);
  display: flex; align-items: center; justify-content: center; font-size: 1.8rem;
  border: 1px solid rgba(212, 167, 106, 0.1); transition: all 0.3s;
}
.choice-item:hover .choice-icon { border-color: #f7c873; transform: scale(1.1); box-shadow: 0 0 15px rgba(247,200,115,0.2); }
.choice-item span { font-size: 0.9rem; font-weight: 600; }
.choice-divider { width: 1px; background: rgba(212, 167, 106, 0.15); align-self: stretch; margin: 30px 0; }

/* 电脑端上传样式 */
.desktop-full-upload { width: 100%; height: 100%; }
:deep(.el-upload) { width: 100%; height: 100%; }
:deep(.el-upload-dragger) {
  width: 100%; height: 160px; background: transparent !important;
  border: none !important; display: flex; align-items: center; justify-content: center;
}
.desktop-upload-content {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.upload-icon { font-size: 2.2rem; color: var(--primary-color); opacity: 0.8; }
.upload-text { font-size: 0.95rem; font-weight: 600; color: #fff8e6; }
.upload-subtext { font-size: 0.75rem; color: var(--text-muted); }

@media (min-width: 768px) {
  .upload-choice-container { height: 180px; }
  :deep(.el-upload-dragger) { height: 180px; }
}

.preview-box { position: relative; width: 100%; height: 220px; display: flex; align-items: center; justify-content: center; padding: 10px; border: 2px solid #f7c873; box-sizing: border-box; }
.uploaded-img { max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 4px; }
.change-hint {
  position: absolute; bottom: 0; left: 0; right: 0; text-align: center; padding: 6px;
  background: rgba(0,0,0,0.6); color: #fff; font-size: 0.75rem; border-radius: 0 0 4px 4px;
}
.hint-text { font-size: 0.8rem; color: var(--text-muted); text-align: center; margin-top: 8px; }

/* 人脸存档 */
.saved-faces-section { margin-bottom: 16px; }
.sub-hint { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 12px; }
.face-list { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.face-item {
  flex-shrink: 0; width: 56px; height: 56px; border-radius: 50%; overflow: hidden;
  border: 2px solid transparent; cursor: pointer; transition: all 0.3s;
}
.face-item.active { border-color: #f7c873; box-shadow: 0 0 10px rgba(247,200,115,0.4); }
.face-item img { width: 100%; height: 100%; object-fit: cover; }
.save-face-action { text-align: center; margin-top: 10px; }

/* 数量选择 */
.count-selector { display: flex; gap: 10px; }
.count-item {
  flex: 1; padding: 12px; border-radius: 12px;
  background: linear-gradient(135deg, rgba(91,49,36,0.18), rgba(16,38,43,0.22));
  border: 2px solid rgba(247,200,115,0.12); cursor: pointer; text-align: center;
  transition: all 0.3s; font-weight: bold; color: rgba(255,255,255,0.7);
}
.count-item.active {
  border-color: #f7c873; background: rgba(247,200,115,0.18); color: #fff;
  box-shadow: 0 0 12px rgba(247,200,115,0.2);
}
.count-hint { font-size: 0.78rem; color: var(--text-muted); margin-top: 12px; text-align: center; }

/* 积分 */
.total-cost-box {
  text-align: center; padding: 14px; font-size: 0.9rem; color: var(--text-muted); margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(91,49,36,0.15), rgba(16,38,43,0.2));
  border: 1px solid rgba(247,200,115,0.12);
}
.cost-value { color: #f7c873; font-size: 1.2rem; font-weight: bold; margin: 0 4px; }
.cost-unit { font-size: 0.75rem; margin-left: 4px; }

/* 提交 */
.action-bar { margin-bottom: 20px; }
.primary-button.large { width: 100%; height: 50px; font-size: 1.05rem; border-radius: 12px; }

/* 结果 */
.result-section {
  padding: 20px; margin-bottom: 20px; animation: fadeIn 0.5s ease;
  background:
    linear-gradient(135deg, rgba(139, 107, 67, 0.15), rgba(26, 22, 20, 0.25)),
    repeating-linear-gradient(90deg, rgba(212, 167, 106, 0.03) 0 1px, transparent 1px 20px);
  border: 1px solid rgba(212, 167, 106, 0.18);
}
.error-container { margin-bottom: 16px; }
.leave-hint { margin-bottom: 12px; }
.result-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; margin-bottom: 16px; }
.result-item { border-radius: 12px; overflow: hidden; height: 240px; position: relative; }
.result-item :deep(.el-image) {
  width: 100%;
  height: 100%;
  cursor: pointer;
  transition: transform 0.3s;
}
.result-item :deep(.el-image):hover {
  transform: scale(1.02);
}
.result-download-btn {
  position: absolute; bottom: 8px; right: 8px; width: 32px; height: 32px;
  background: rgba(0,0,0,0.6); border-radius: 50%; display: flex; align-items: center;
  justify-content: center; color: #fff; cursor: pointer; backdrop-filter: blur(4px);
  transition: all 0.2s; z-index: 2;
}
.result-download-btn:hover { background: var(--primary-color); transform: scale(1.1); }
.result-actions { display: flex; gap: 12px; }
.result-actions .el-button { flex: 1; }
.loading-placeholder {
  background: rgba(255,255,255,0.03); border: 1px dashed rgba(255,255,255,0.1);
  display: flex; align-items: center; justify-content: center; animation: pulse 2s infinite;
}
.loading-content { display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--text-muted); }
.loading-content i { font-size: 2rem; }
.result-hint {
  margin-top: 12px;
  font-size: 0.8rem;
  color: #f7c873;
  text-align: center;
  background: rgba(247, 200, 115, 0.1);
  padding: 8px;
  border-radius: 8px;
  opacity: 0.9;
}

.mobile-hint { margin-top: 12px; font-size: 0.8rem; color: var(--primary-color); text-align: center; }

/* 参考图 */
.ref-list { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px; }
.ref-item { width: 80px; height: 120px; position: relative; border-radius: 8px; overflow: hidden; border: 2px solid rgba(247,200,115,0.4); }
.ref-img { width: 100%; height: 100%; }
.del-btn {
  position: absolute; top: 4px; right: 4px; width: 20px; height: 20px;
  background: rgba(0,0,0,0.6); border-radius: 50%; display: flex; align-items: center;
  justify-content: center; color: #fff; cursor: pointer;
}
.del-btn:hover { background: var(--danger-color, #f56c6c); }
.ref-upload-box { width: 80px; height: 120px; }
.ref-upload-btn {
  width: 80px; height: 120px; border: 2px dashed rgba(255,255,255,0.2); border-radius: 8px;
  display: flex; align-items: center; justify-content: center; font-size: 1.5rem;
  color: var(--text-muted); cursor: pointer; transition: all 0.3s;
}
.ref-upload-btn:hover { border-color: #f7c873; color: #f7c873; }

/* 法律 */
.legal-notice { margin-top: 16px; text-align: center; }
:deep(.el-checkbox__label) { color: var(--text-muted); font-size: 0.8rem; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }

@media (min-width: 768px) {
  .result-grid { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
  .result-item { height: 300px; }
  .mode-card-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 480px) {
  .old-style-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .mvp-title { font-size: 1.05rem; }
  .mode-title { font-size: 1.5rem; }
}

/* 全屏预览 */
.full-screen-preview {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.9); z-index: 3000;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(10px);
}
.preview-content { position: relative; max-width: 90%; max-height: 90%; }
.preview-img { max-width: 100%; max-height: 90vh; border-radius: 8px; border: 2px solid rgba(247,200,115,0.3); box-shadow: 0 0 30px rgba(0,0,0,0.5); }
.preview-close {
  position: absolute; top: -40px; right: 0; color: #fff; font-size: 1.5rem;
  cursor: pointer; background: rgba(255,255,255,0.1); width: 32px; height: 32px;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.preview-close:hover { background: #f7c873; color: #000; transform: rotate(90deg); }

/* 预览信息面板 */
.preview-info-panel {
  position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
  width: 90%; max-width: 400px; padding: 16px;
  background: rgba(26, 22, 20, 0.85); border: 1px solid rgba(212, 167, 106, 0.3);
  box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center;
  animation: slideUp 0.3s ease-out;
}
.preview-style-name { margin: 0 0 6px; color: #f7c873; font-size: 1.1rem; font-weight: 700; }
.preview-style-desc { margin: 0; color: rgba(255,255,255,0.8); font-size: 0.85rem; line-height: 1.5; }

@keyframes slideUp { from { opacity: 0; transform: translate(-50%, 20px); } to { opacity: 1; transform: translate(-50%, 0); } }

@media (max-width: 480px) {
  .old-style-desc { white-space: normal; height: auto; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
  .old-style-item { height: auto; }
}

.framing-section {
  margin-top: 32px;
  text-align: left;
}

.section-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.3), transparent);
  margin-bottom: 24px;
}

.section-subtitle {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: -8px;
  margin-bottom: 20px;
}

.framing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.framing-item {
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  border: 1.5px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.framing-item:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(212, 175, 55, 0.4);
  transform: translateY(-2px);
}

.framing-item.active {
  background: rgba(212, 175, 55, 0.15);
  border-color: #d4af37;
  box-shadow: 0 0 15px rgba(212, 175, 55, 0.2);
}

.framing-icon-box {
  font-size: 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.framing-meta {
  display: flex;
  flex-direction: column;
}

.framing-label {
  font-weight: 600;
  font-size: 0.95rem;
  color: #fff;
}

.framing-desc {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.recommend-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #d4af37;
  color: #000;
  font-size: 10px;
  padding: 2px 8px;
  border-bottom-left-radius: 8px;
  font-weight: bold;
  transform: scale(0.9);
}

.active-check {
  position: absolute;
  bottom: 8px;
  right: 8px;
  color: #d4af37;
  font-size: 1.2rem;
}

@media (max-width: 768px) {
  .framing-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 照片比例选择区域样式 */
.aspect-ratio-section {
  margin-top: 32px;
  text-align: left;
}

.aspect-ratio-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.aspect-ratio-item {
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  border: 1.5px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.aspect-ratio-item:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(212, 175, 55, 0.4);
  transform: translateY(-2px);
}

.aspect-ratio-item.active {
  background: rgba(212, 175, 55, 0.15);
  border-color: #d4af37;
  box-shadow: 0 0 15px rgba(212, 175, 55, 0.2);
}

.aspect-ratio-preview {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.aspect-ratio-item.active .aspect-ratio-preview {
  border-color: rgba(212, 175, 55, 0.4);
  background: rgba(212, 175, 55, 0.08);
}

.aspect-ratio-box {
  border: 2px solid rgba(255, 255, 255, 0.6);
  border-radius: 3px;
  transition: all 0.3s;
}

.aspect-ratio-item.active .aspect-ratio-box {
  border-color: #d4af37;
}

/* 9:16 portrait */
.aspect-ratio-preview.portrait .aspect-ratio-box {
  width: 16px;
  height: 28px;
}

/* 3:4 photo */
.aspect-ratio-preview.photo .aspect-ratio-box {
  width: 22px;
  height: 28px;
}

/* 1:1 square */
.aspect-ratio-preview.square .aspect-ratio-box {
  width: 24px;
  height: 24px;
}

.aspect-ratio-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.aspect-ratio-label {
  font-weight: 600;
  font-size: 0.95rem;
  color: #fff;
}

.aspect-ratio-desc {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
}

@media (max-width: 576px) {
  .aspect-ratio-grid {
    grid-template-columns: 1fr;
  }
  .aspect-ratio-item {
    flex-direction: row;
    align-items: center;
    justify-content: flex-start;
    padding: 10px 14px;
    gap: 14px;
  }
  .aspect-ratio-meta {
    align-items: flex-start;
    text-align: left;
  }
}

/* 自定义反馈风格卡片样式 */
.feedback-style-card {
  border: 2px dashed rgba(247, 200, 115, 0.3) !important;
  background: rgba(247, 200, 115, 0.02) !important;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.feedback-style-card:hover {
  border-color: #f7c873 !important;
  box-shadow: 0 0 15px rgba(247, 200, 115, 0.15) !important;
  background: rgba(247, 200, 115, 0.06) !important;
  transform: translateY(-4px);
}

.feedback-placeholder {
  background: linear-gradient(135deg, rgba(247, 200, 115, 0.12), rgba(155, 215, 203, 0.12)) !important;
  color: #f7c873 !important;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>

