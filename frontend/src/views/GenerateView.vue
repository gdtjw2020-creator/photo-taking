<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import { Loading, ZoomIn, Close, Plus, Download } from '@element-plus/icons-vue'
import api from '../api'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { resizeImageIfNeeded } from '../utils/imageResize'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isLoggedIn = computed(() => authStore.isLoggedIn)
const CREDITS_PER_IMAGE = ref(5) // 默认为 5，之后从后端动态同步

const templates = ref([])
const savedFaces = ref([])

onMounted(async () => {
  try {
    // 同步后端配置（实现环境变量统一）
    const configRes = await api.get('/api/photoshoot/config')
    if (configRes.data?.credits_per_photoshoot) {
        CREDITS_PER_IMAGE.value = configRes.data.credits_per_photoshoot
    }

    // 加载模板
    const tplRes = await api.get('/api/photoshoot/templates')
    templates.value = tplRes.data
    if (templates.value.length > 0) {
      selectedTemplate.value = templates.value[0]
    }
    
    // 加载已存人脸 (仅登录用户)
    if (isLoggedIn.value) {
      const faceRes = await api.get('/api/photoshoot/faces')
      savedFaces.value = faceRes.data

      // 新增：检查是否有正在进行的活跃任务，实现“断点续传”
      const activeRes = await api.get('/api/photoshoot/active_task')
      if (activeRes.data) {
          const task = activeRes.data
          console.log('[DEBUG] Found active task, resuming polling:', task.id)
          taskId.value = task.id
          taskStatus.value = task.status
          resultImages.value = task.output_urls || []
          const startTime = task.created_at ? new Date(task.created_at).getTime() : null
          // 如果有正在进行的任务，自动切换到结果视图
          isGenerating.value = true
          startPolling(task.id, startTime)
      }
    }
    // 处理从“人脸存档”跳转过来的情况
    if (route.query.face_url) {
      uploadedImageUrl.value = route.query.face_url
      ElMessage.info('已自动装载形象存档')
    }
  } catch (err) {
    console.error('Failed to init data:', err)
  }
})

const selectedTemplate = ref(null)
const uploadedImageUrl = ref('')
const referenceImages = ref([]) // 新增：参考图数组
const isRefUploading = ref(false) // 新增：参考图上传状态
const activeTab = ref(route.query.tab || 'template') // 从 URL 初始化当前激活模式
const imageCount = ref(1) // 默认 1 张
const isUploading = ref(false)
const isGenerating = ref(false)
const autoSaveFace = ref(true) // 默认开启自动保存
const taskId = ref('')
const isAgreed = ref(false)
const addWatermark = ref(true) // 默认添加"AI生成"水印
const photoshootCounts = [1, 2, 3, 4, 5]
const previewList = ref([])
const showViewer = ref(false)

const showPreview = (url) => {
  previewList.value = [url]
  showViewer.value = true
}

const selectTemplate = (template) => {
  selectedTemplate.value = template
}

const handleTabChange = (tab) => {
  activeTab.value = tab
  // 同步到 URL，但不产生历史记录
  router.replace({ query: { ...route.query, tab } })
}

const checkAuth = (msg = '请先登录后开启您的约拍之旅') => {
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

const handleUpload = async (file) => {
  if (!checkAuth('上传照片前需要登录，以便为您保存形象存档')) return
  isUploading.value = true
  const formData = new FormData()
  const resizedFile = await resizeImageIfNeeded(file.raw)
  formData.append('file', resizedFile)

  try {
    const res = await api.post('/api/photoshoot/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    uploadedImageUrl.value = res.data.url
    ElMessage.success('照片上传成功')

    // 改进：上传成功后立即自动保存到人脸存档
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
  if (!checkAuth('开启 AI 约拍任务需要登录以扣除积分')) return
  
  if (activeTab.value === 'custom') {
    // 自定义参考图模式
    if (referenceImages.value.length === 0) {
      ElMessage.warning('请先上传至少一张创作底图')
      return
    }
    if (!uploadedImageUrl.value) {
      ElMessage.warning('请先上传您的形象照片')
      return
    }
  } else {
    // 模板模式
    if (!selectedTemplate.value || !uploadedImageUrl.value) {
      ElMessage.warning('请先选择模板并上传照片')
      return
    }
  }

  // 新增：法律声明强制校验
  if (!isAgreed.value) {
    try {
      await ElMessageBox.confirm(
        '开启 AI 约拍前，请确认您上传的照片已获本人授权，且生成的图片仅用于个人娱乐。系统严禁生成违规、不雅或侵犯他人隐私的内容。确认开启吗？',
        '合规使用与隐私保护确认',
        {
          confirmButtonText: '确认并自动勾选',
          cancelButtonText: '暂不开启',
          type: 'info',
          center: true
        }
      )
      isAgreed.value = true
    } catch (e) {
      return // 用户取消
    }
  }

  isGenerating.value = true
  try {
    // 如果开启了自动保存，且该人脸尚未在存档中
    if (autoSaveFace.value && !savedFaces.value.some(f => f.face_url === uploadedImageUrl.value)) {
        await saveCurrentFace()
    }

    const payload = {
      template_id: activeTab.value === 'template' ? selectedTemplate.value.id : null,
      image_url: uploadedImageUrl.value,
      reference_image_urls: activeTab.value === 'custom' ? referenceImages.value : undefined,
      image_count: activeTab.value === 'custom' ? referenceImages.value.length : imageCount.value,
      watermark: addWatermark.value
    }

    const res = await api.post('/api/photoshoot/generate', payload)
    taskId.value = res.data.task_id
    resultImages.value = [] // 立即重置旧图片，显示新占位符
    errorMessage.value = '' // 重置错误信息
    ElMessage.success('任务已提交，正在修图中...')
    startPolling(res.data.task_id)
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
const resultImages = ref([])
const taskStartTime = ref(null)     // 任务提交时间 (ms)
const elapsedSeconds = ref(0)       // 已等待秒数
const MAX_WAIT_SECONDS = 900        // 后端硬超时 15 分钟

const formattedElapsed = computed(() => {
  const mins = Math.floor(elapsedSeconds.value / 60)
  const secs = elapsedSeconds.value % 60
  return `${mins} 分 ${secs.toString().padStart(2, '0')} 秒`
})

const isLongWait = computed(() => elapsedSeconds.value > 300) // 超过 5 分钟提示离开

const startPolling = (tid, existingStartTime = null) => {
  taskStatus.value = 'processing'
  taskStartTime.value = existingStartTime || Date.now()
  elapsedSeconds.value = Math.floor((Date.now() - taskStartTime.value) / 1000)

  // 如果恢复的任务已经超过最大等待时间，直接标记失败不再轮询
  if (elapsedSeconds.value >= MAX_WAIT_SECONDS) {
    errorMessage.value = `任务已提交超过 ${MAX_WAIT_SECONDS} 秒（15 分钟），已自动超时。请到相册查看是否有已生成的结果，或重新提交。`
    taskStatus.value = 'failed'
    isGenerating.value = false
    return
  }

  pollTimer.value = setInterval(async () => {
    try {
      elapsedSeconds.value = Math.floor((Date.now() - taskStartTime.value) / 1000)

      if (elapsedSeconds.value >= MAX_WAIT_SECONDS) {
        errorMessage.value = `已等待超过 ${MAX_WAIT_SECONDS} 秒（15 分钟），任务可能已超时。请稍后到相册查看结果。`
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
              message: `第 ${data.output_urls.length} 张约拍照已冲洗完成，扣除 1 积分`,
              type: 'success',
              duration: 2000
          })
      }

      if (data.status === 'completed') {
        ElMessage.success('全组照片约拍完成！')
        stopPolling()
      } else if (data.status === 'failed') {
        errorMessage.value = data.error_message || '任务生成失败，请重试'
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

const downloadImage = (url, index) => {
  // 使用后端代理下载接口，解决跨域问题并强制触发下载
  const proxyUrl = `/api/photoshoot/download?url=${encodeURIComponent(url)}`
  const link = document.createElement('a')
  link.href = proxyUrl
  // 后端已设置 Content-Disposition，浏览器会识别为下载
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const downloadAll = async () => {
  if (resultImages.value.length === 0) return
  
  ElMessage.info('开始下载照片...')
  for (let i = 0; i < resultImages.value.length; i++) {
    await downloadImage(resultImages.value[i], i)
    // 延迟防止浏览器拦截
    await new Promise(resolve => setTimeout(resolve, 800))
  }
}

const handleSuggest = () => {
    if (!checkAuth('提交愿望前请先登录')) return
    
    ElMessageBox.prompt('告诉我们您想要什么样的写真风格（如：动漫风、油画质感、赛博猫咪...）', '风格许愿池', {
        confirmButtonText: '提交愿望',
        cancelButtonText: '再想想',
        inputPlaceholder: '请输入您期待的风格名称或描述',
        inputValidator: (value) => {
            if (!value || value.trim().length < 2) return '愿望写得详细一点哦（至少2个字）'
            return true
        }
    }).then(async ({ value }) => {
        try {
            await api.post('/api/user/feedback', { content: value, type: 'style_request' })
            ElMessage.success('愿望已收到！我们会尽快安排研发该风格~')
        } catch (err) {
            ElMessage.error('提交失败，请稍后重试')
        }
    }).catch(() => {})
}
</script>

<template>
  <div class="generate-container">
    <div class="step-card glass-card">
      <div class="mode-tabs">
        <div class="mode-tab" :class="{ active: activeTab === 'template' }" @click="handleTabChange('template')">预设写真风格</div>
        <div class="mode-tab" :class="{ active: activeTab === 'custom' }" @click="handleTabChange('custom')">AI 写真定制</div>
      </div>

      <div v-show="activeTab === 'template'">
        <div class="template-grid">
          <div 
            v-for="tpl in templates" 
            :key="tpl.id" 
            class="template-item" 
            :class="{ active: selectedTemplate?.id === tpl.id }"
            @click="selectTemplate(tpl)"
          >
            <div class="template-img-container">
              <el-image 
                :src="tpl.preview" 
                :alt="tpl.name" 
                fit="cover"
                class="template-img"
              ></el-image>
              <div class="zoom-btn" @click.stop="showPreview(tpl.preview)">
                  <el-icon><ZoomIn /></el-icon>
              </div>
            </div>
            <span>{{ tpl.name }}</span>
          </div>

          <!-- 独立的图片预览器 -->
          <el-image-viewer 
              v-if="showViewer" 
              @close="showViewer = false" 
              :url-list="previewList" 
              teleported
          />

          
          <!-- 新增：许愿卡片 -->
          <div class="template-item suggest-item" @click="handleSuggest">
            <div class="suggest-content">
              <div class="plus-icon">+</div>
              <span>想要更多风格？</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 自定义参考图上传区 -->
      <div v-show="activeTab === 'custom'" class="custom-ref-area">
        <p class="sub-hint">上传您心仪的创作底图（最多 5 张，请确保内容合规。如生成效果不佳，建议尝试更换底图）。</p>
        <div class="ref-list">
          <div v-for="(img, idx) in referenceImages" :key="idx" class="ref-item">
            <el-image :src="img" fit="cover" class="ref-img"></el-image>
            <div class="del-btn" @click.stop="removeRef(idx)">
              <el-icon><Close /></el-icon>
            </div>
          </div>
          
          <el-upload
            v-if="referenceImages.length < 5"
            class="ref-upload-box"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleRefUpload"
            accept="image/*"
          >
            <div class="ref-upload-btn" v-loading="isRefUploading">
              <el-icon><Plus /></el-icon>
            </div>
          </el-upload>
        </div>
      </div>
    </div>

    <div class="step-card glass-card">
      <h2>2. 录入您的数字形象</h2>
      
      <!-- 已存人脸存档 -->
      <div v-if="savedFaces.length > 0" class="saved-faces-section">
        <p class="sub-hint">常用形象存档：</p>
        <div class="face-list">
          <div 
            v-for="face in savedFaces" 
            :key="face.id" 
            class="face-item"
            :class="{ active: uploadedImageUrl === face.face_url }"
            @click="selectSavedFace(face)"
          >
            <img :src="face.face_url">
          </div>
        </div>
      </div>

      <div class="upload-area">
        <el-upload
          class="upload-box"
          drag
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleUpload"
        >
          <div v-if="!uploadedImageUrl" class="upload-placeholder">
            <i class="el-icon-upload"></i>
            <div class="el-upload__text">点击或将照片拖拽到此处</div>
          </div>
          <div v-else class="preview-box">
            <img :src="uploadedImageUrl" class="uploaded-img">
            <div class="change-hint">点击更换照片</div>
          </div>
        </el-upload>
      </div>
      <div v-if="uploadedImageUrl" class="save-face-action">
        <el-checkbox v-model="autoSaveFace" class="auto-save-cb">自动保存此形象到我的形象库</el-checkbox>
        <el-button 
            v-if="!autoSaveFace && !savedFaces.some(f => f.face_url === uploadedImageUrl)"
            size="small" 
            type="info" 
            plain 
            @click="saveCurrentFace"
            style="margin-left: 10px"
        >
          立即保存
        </el-button>
      </div>
      <p class="hint-text">请确保照片面部清晰、光线充足，尽量上传头肩照</p>
    </div>

    <div class="step-card glass-card">
      <h2>3. 约拍数量</h2>
      <div v-if="activeTab === 'custom'" class="custom-ref-mode-hint">
        <el-alert title="您已开启 AI 写真定制模式" type="success" :closable="false" show-icon>
          将为您逐一生成 {{ referenceImages.length || 0 }} 张照片。
        </el-alert>
      </div>
      <div v-else>
        <div class="count-selector">
          <div 
            v-for="count in photoshootCounts" 
            :key="count" 
            class="count-item"
            :class="{ active: imageCount === count }"
            @click="imageCount = count"
          >
            {{ count }} 张
          </div>
        </div>
        <p class="count-hint">选择多张将自动开启“全套摄影手法”：包含全景、特写、侧位等不同视角</p>
      </div>
      
      <div class="total-cost-box">
        消耗：<span class="cost-value">{{ ((activeTab === 'custom' ? referenceImages.length : imageCount) * CREDITS_PER_IMAGE).toFixed(1) }}</span> 积分
        <span class="cost-unit">({{ CREDITS_PER_IMAGE }} 积分/张)</span>
      </div>
    </div>


    <div class="action-bar">
      <el-button 
        type="primary" 
        class="primary-button large" 
        :loading="isGenerating"
        @click="submitTask"
      >
        开启 AI 镜像约拍 (生成 {{ activeTab === 'custom' ? referenceImages.length : imageCount }} 张写真)
      </el-button>
    </div>

    <div v-if="taskStatus" class="result-section glass-card">
      <div v-if="taskStatus === 'failed'" class="error-container">
        <el-alert
          :title="errorMessage"
          type="error"
          description="您可以检查上传的图片是否清晰，或者稍后重新提交任务。"
          show-icon
          :closable="false"
        />
      </div>
      <div v-if="taskStatus === 'processing'" class="leave-hint">
        <el-alert
          title="后台持续生成中，您可以放心离开本页面"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            拍照任务在后台排队生成，不会中断。您可以先去逛其他页面，稍后到 <strong>「相册」</strong> 查看全部成果，或返回本页继续等待。
          </template>
        </el-alert>
      </div>
      <div v-if="taskStatus === 'processing' && isLongWait" class="leave-hint">
        <el-alert
          :title="`已等待 ${formattedElapsed}，不如先去逛逛？`"
          type="warning"
          :closable="false"
          show-icon
        >
          <template #default>
            生成仍在后台进行中（最长 15 分钟），任务结果会自动保存到 <strong>「相册」</strong>。本页超过 15 分钟无结果将自动停止等待。
          </template>
        </el-alert>
      </div>
      <h2>3. 约拍成果
        <el-tag v-if="taskStatus === 'processing'" type="warning" size="small">拍摄中 ({{ resultImages.length }}/{{ activeTab === 'custom' ? referenceImages.length : imageCount }}) 已等待 {{ formattedElapsed }}</el-tag>
        <el-tag v-else-if="taskStatus === 'failed'" type="danger" size="small">生成出错</el-tag>
      </h2>
      <div class="result-grid">
        <!-- 已完成的图片 -->
        <div v-for="(url, index) in resultImages" :key="url" class="result-item">
          <el-image 
            :src="url" 
            :preview-src-list="isMobile ? [] : resultImages"
            :initial-index="index"
            :key="url"
            fit="cover"
            preview-teleported
          ></el-image>
          <div class="result-download-btn" @click.stop="downloadImage(url)">
            <el-icon><Download /></el-icon>
          </div>
        </div>
        <!-- 正在生成的占位符 -->
        <div v-for="n in Math.max(0, (activeTab === 'custom' ? referenceImages.length : imageCount) - resultImages.length)" :key="'loading-'+n" class="result-item loading-placeholder" v-if="taskStatus === 'processing'">
            <div class="loading-content">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>正在冲洗... {{ formattedElapsed }}</span>
            </div>
        </div>
      </div>
      <div class="result-actions">
        <el-button type="success" @click="downloadAll">
          {{ isMobile ? '保存图片' : '下载全组照片' }}
        </el-button>
        <el-button @click="taskStatus = ''">再拍一组</el-button>
      </div>
      <p v-if="isMobile" class="mobile-hint">提示：长按图片即可保存到相册，或点击图片右下角按钮一键下载</p>
    </div>

    <div class="legal-notice">
        <el-checkbox v-model="isAgreed">我已确认照片为本人或已获授权，且仅用于个人娱乐</el-checkbox>
        <el-checkbox v-model="addWatermark" style="margin-left: 20px">生成图片添加"AI生成"文字水印</el-checkbox>
    </div>
  </div>
</template>

<style scoped>
.generate-container {
  padding: 20px 16px 100px 16px; /* 增加底部间距，为导航栏留出呼吸空间 */
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  box-sizing: border-box;
}

.step-card {
  padding: 24px 20px; /* 增加内边距 */
  margin-bottom: 30px; /* 增加卡片间距 */
}

.step-card h2 {
  font-size: 1.2rem;
  margin-bottom: 20px;
  color: var(--primary-color);
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); /* 增加最小宽度，让图片在手机上更大 */
  gap: 16px;
}

@media (min-width: 480px) {
  .template-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }
}

.template-item {
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.3s;
  background: rgba(255, 255, 255, 0.05);
}

.template-item.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
}

.template-img-container {
  width: 100%;
  aspect-ratio: 3/4; /* 使用比例取代固定高度 */
  position: relative;
}

.template-img {
  width: 100%;
  height: 100%;
}

.zoom-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1.1rem;
  backdrop-filter: blur(4px);
  z-index: 2;
  transition: all 0.2s;
}

.zoom-btn:hover {
  background: var(--primary-color);
  transform: scale(1.1);
}


.suggest-item {
  border: 2px dashed rgba(255, 255, 255, 0.1) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 3/4; /* 与其它项保持一致 */
}

.suggest-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--text-muted);
}

.plus-icon {
  font-size: 2rem;
  margin-bottom: 8px;
  font-weight: 300;
}

.template-item span {
  display: block;
  text-align: center;
  padding: 10px 8px;
  font-size: 1rem; /* 增加字号 */
  font-weight: 500;
}

.upload-area {
  margin-bottom: 12px;
}

.upload-box {
  width: 100%;
}

:deep(.el-upload-dragger) {
  background: rgba(255, 255, 255, 0.05);
  border: 2px dashed rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-box {
  width: 100%;
  height: 100%;
  position: relative;
}

.uploaded-img {
  max-width: 100%;
  max-height: 180px;
  border-radius: 8px;
}

.change-hint {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.5);
  padding: 4px;
  font-size: 0.8rem;
}

.hint-text {
  color: var(--text-muted);
  font-size: 0.85rem;
  text-align: center;
}

.action-bar {
  margin-top: 32px;
}

.primary-button.large {
  width: 100%;
  padding: 16px;
  font-size: 1.1rem;
}

.legal-notice {
    margin-top: 20px;
    text-align: center;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px 24px;
}

.result-section {
  padding: 20px;
  margin-top: 24px;
  animation: fadeIn 0.5s ease;
}

.error-container {
  margin-bottom: 20px;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.result-item {
  border-radius: 12px;
  overflow: hidden;
  height: 240px;
  position: relative;
}

.result-download-btn {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
  backdrop-filter: blur(4px);
  transition: all 0.2s;
  z-index: 2;
}

.result-download-btn:hover {
  background: var(--primary-color);
  transform: scale(1.1);
}

.result-actions {
  display: flex;
  gap: 12px;
}

.result-actions .el-button {
  flex: 1;
}

.leave-hint {
  margin-bottom: 16px;
}

.mobile-hint {
  margin-top: 12px;
  font-size: 0.8rem;
  color: var(--primary-color);
  text-align: center;
  background: rgba(99, 102, 241, 0.1);
  padding: 8px;
  border-radius: 8px;
}

/* 适配大屏幕，让结果网格和高度动态调整 */
@media (min-width: 768px) {
  .result-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
  .result-item {
    height: 300px;
  }
  .template-item span {
    font-size: 1rem;
    padding: 12px;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.count-selector {
  display: flex;
  gap: 10px;
}

.count-item {
  flex: 1;
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid transparent;
  cursor: pointer;
  text-align: center;
  transition: all 0.3s;
  font-weight: bold;
}

.count-item.active {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.2);
  color: #fff;
}

.count-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 12px;
  text-align: center;
}

:deep(.el-checkbox__label) {
    color: var(--text-muted);
    font-size: 0.8rem;
}

.saved-faces-section {
  margin-bottom: 20px;
}

.sub-hint {
  font-size: 0.95rem; /* 增加字号 */
  color: var(--text-muted);
  margin-bottom: 12px;
  line-height: 1.5;
}

.face-list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.face-item {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.3s;
}

.face-item.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
}

.face-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.save-face-action {
  text-align: center;
  margin-top: 12px;
  margin-bottom: 12px;
}
.loading-placeholder {
  background: rgba(255, 255, 255, 0.03);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse 2s infinite;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--text-muted);
}

.loading-content i {
  font-size: 2rem;
}

@keyframes pulse {
  0% { opacity: 0.5; }
  50% { opacity: 1; }
  100% { opacity: 0.5; }
}
.total-cost-box {
  margin-top: 16px;
  text-align: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.cost-value {
  color: var(--primary-color);
  font-size: 1.2rem;
  font-weight: bold;
  margin: 0 4px;
}

.cost-unit {
  font-size: 0.75rem;
  margin-left: 4px;
}

.custom-ref-area {
  margin-top: 16px;
}

.mode-tabs {
  display: flex;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 24px;
}

.mode-tab {
  flex: 1;
  text-align: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-muted);
  font-weight: 500;
  transition: all 0.3s;
}

.mode-tab.active {
  background: var(--primary-color);
  color: #fff;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 16px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.2);
}

.divider span {
  padding: 0 16px;
}

.ref-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.ref-item {
  width: 80px;
  height: 120px;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid var(--primary-color);
}

.ref-img {
  width: 100%;
  height: 100%;
}

.del-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: rgba(0,0,0,0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
}

.del-btn:hover {
  background: var(--danger-color, #f56c6c);
}

.ref-upload-box {
  width: 80px;
  height: 120px;
}

.ref-upload-btn {
  width: 80px;
  height: 120px;
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.3s;
}

.ref-upload-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.custom-ref-mode-hint {
  margin-bottom: 16px;
}
</style>

