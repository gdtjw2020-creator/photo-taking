<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import api from '../api'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'

const route = useRoute()
const authStore = useAuthStore()
const isLoggedIn = computed(() => authStore.isLoggedIn)

const templates = ref([])
const savedFaces = ref([])

onMounted(async () => {
  try {
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
          startPolling(task.id)
          
          // 如果有正在进行的任务，自动切换到结果视图
          isGenerating.value = true
      }
    }
    // 处理从“人脸存档”跳转过来的情况
    if (route.query.face_url) {
      uploadedImageUrl.value = route.query.face_url
      ElMessage.info('已自动装载人脸存档')
    }
  } catch (err) {
    console.error('Failed to init data:', err)
  }
})

const selectedTemplate = ref(null)
const uploadedImageUrl = ref('')
const imageCount = ref(1) // 默认 1 张
const isUploading = ref(false)
const isGenerating = ref(false)
const autoSaveFace = ref(true) // 默认开启自动保存
const taskId = ref('')
const isAgreed = ref(false)
const photoshootCounts = [1, 2, 3, 4, 5]

const selectTemplate = (template) => {
  selectedTemplate.value = template
}

const handleUpload = async (file) => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后开始上传照片')
    return
  }
  isUploading.value = true
  const formData = new FormData()
  formData.append('file', file.raw)

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
    ElMessage.error('上传失败，请重试')
  } finally {
    isUploading.value = false
  }
}

const saveCurrentFace = async () => {
  if (!uploadedImageUrl.value) return
  console.log('[DEBUG] Attempting to save face:', uploadedImageUrl.value)
  try {
    const res = await api.post('/api/photoshoot/faces', {
      face_url: uploadedImageUrl.value,
      name: `人脸存档 ${savedFaces.value.length + 1}`
    })
    console.log('[DEBUG] Save face success:', res.data)
    savedFaces.value.unshift(res.data)
    ElMessage.success('已永久保存到人脸存档')
  } catch (err) {
    console.error('[DEBUG] Save face error:', err)
    ElMessage.error('保存失败')
  }
}

const selectSavedFace = (face) => {
  uploadedImageUrl.value = face.face_url
}

const submitTask = async () => {
  if (!isLoggedIn.value) {
    ElMessage.error('请登录后开启约拍任务')
    return
  }
  if (!selectedTemplate.value || !uploadedImageUrl.value) {
    ElMessage.warning('请先选择模板并上传照片')
    return
  }

  // 新增：法律声明强制校验
  if (!isAgreed.value) {
    try {
      await ElMessageBox.confirm(
        '开启 AI 约拍前，请确认您上传的照片已获本人授权，且生成的图片仅用于个人娱乐，不得用于非法用途。确认开启吗？',
        '法律及隐私确认',
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

    const res = await api.post('/api/photoshoot/generate', {
      template_id: selectedTemplate.value.id,
      image_url: uploadedImageUrl.value,
      image_count: imageCount.value
    })
    taskId.value = res.data.task_id
    resultImages.value = [] // 立即重置旧图片，显示新占位符
    ElMessage.success('任务已提交，正在修图中...')
    startPolling(res.data.task_id)
  } catch (err) {
    ElMessage.error('开启任务失败')
    isGenerating.value = false
  }
}

const pollTimer = ref(null)
const taskStatus = ref('')
const resultImages = ref([])

const startPolling = (tid) => {
  taskStatus.value = 'processing'
  pollTimer.value = setInterval(async () => {
    try {
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
        ElMessage.error(data.error_message || '任务失败')
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
  
  if (isMobile.value) {
    ElMessage.success('移动端请点击图片预览，长按图片即可保存到相册')
    return
  }

  ElMessage.info('开始下载照片...')
  for (let i = 0; i < resultImages.value.length; i++) {
    await downloadImage(resultImages.value[i], i)
    // 延迟防止浏览器拦截
    await new Promise(resolve => setTimeout(resolve, 800))
  }
}

const handleSuggest = () => {
    if (!isLoggedIn.value) {
        ElMessage.warning('请登录后提交您的愿望')
        return
    }
    
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
      <h2>1. 选择写真风格</h2>
      <div class="template-grid">
        <div 
          v-for="tpl in templates" 
          :key="tpl.id" 
          class="template-item" 
          :class="{ active: selectedTemplate?.id === tpl.id }"
          @click="selectTemplate(tpl)"
        >
          <el-image 
            :src="tpl.preview" 
            :alt="tpl.name" 
            :preview-src-list="templates.map(t => t.preview)"
            :initial-index="templates.indexOf(tpl)"
            fit="cover"
            preview-teleported
            class="template-img"
            @click.stop
          ></el-image>
          <span>{{ tpl.name }}</span>
        </div>
        
        <!-- 新增：许愿卡片 -->
        <div class="template-item suggest-item" @click="handleSuggest">
          <div class="suggest-content">
            <div class="plus-icon">+</div>
            <span>想要更多风格？</span>
          </div>
        </div>
      </div>
    </div>

    <div class="step-card glass-card">
      <h2>2. 选择或上传正面照片</h2>
      
      <!-- 已存人脸存档 -->
      <div v-if="savedFaces.length > 0" class="saved-faces-section">
        <p class="sub-hint">常用人脸存档：</p>
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
        <el-checkbox v-model="autoSaveFace" class="auto-save-cb">自动保存此人脸到存档</el-checkbox>
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

    <div class="action-bar">
      <el-button 
        type="primary" 
        class="primary-button large" 
        :loading="isGenerating"
        @click="submitTask"
      >
        开启 AI 镜像约拍 (生成 {{ imageCount }} 张写真)
      </el-button>
    </div>

    <div v-if="taskStatus === 'completed' || taskStatus === 'processing'" class="result-section glass-card">
      <h2>3. 约拍成果 <el-tag v-if="taskStatus === 'processing'" type="warning" size="small">正在拍摄中 ({{ resultImages.length }}/{{ imageCount }})</el-tag></h2>
      <div class="result-grid">
        <!-- 已完成的图片 -->
        <div v-for="(url, index) in resultImages" :key="url" class="result-item">
          <el-image 
            :src="url" 
            :preview-src-list="resultImages" 
            :initial-index="index"
            :key="url"
            fit="cover"
            preview-teleported
          ></el-image>
        </div>
        <!-- 正在生成的占位符 -->
        <div v-for="n in (imageCount - resultImages.length)" :key="'loading-'+n" class="result-item loading-placeholder" v-if="taskStatus === 'processing'">
            <div class="loading-content">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>正在冲洗...</span>
            </div>
        </div>
      </div>
      <div class="result-actions">
        <el-button type="success" @click="downloadAll">
          {{ isMobile ? '保存教程' : '下载全组照片' }}
        </el-button>
        <el-button @click="taskStatus = ''">再拍一组</el-button>
      </div>
      <p v-if="isMobile" class="mobile-hint">提示：移动端支持点击图片进入预览模式，长按即可保存</p>
    </div>

    <div class="legal-notice">
        <el-checkbox v-model="isAgreed">我已确认照片为本人或已获授权，且仅用于个人娱乐</el-checkbox>
    </div>
  </div>
</template>

<style scoped>
.generate-container {
  padding: 20px;
  max-width: 600px; /* 限制宽度，在手机上自适应，在电脑上居中 */
  margin: 0 auto;
}

.step-card {
  padding: 20px;
  margin-bottom: 24px;
}

.step-card h2 {
  font-size: 1.2rem;
  margin-bottom: 20px;
  color: var(--primary-color);
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
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

.template-img {
  width: 100%;
  height: 120px;
}

.suggest-item {
  border: 2px dashed rgba(255, 255, 255, 0.1) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 156px; /* 120px img + padding/text */
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
  padding: 8px;
  font-size: 0.9rem;
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
}

.result-section {
  padding: 20px;
  margin-top: 24px;
  animation: fadeIn 0.5s ease;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.result-item {
  border-radius: 12px;
  overflow: hidden;
  height: 240px;
}

.result-actions {
  display: flex;
  gap: 12px;
}

.result-actions .el-button {
  flex: 1;
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

/* 适配大屏幕，让结果网格更宽一些 */
@media (min-width: 768px) {
  .result-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .result-item {
    height: 320px;
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
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 10px;
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
</style>
