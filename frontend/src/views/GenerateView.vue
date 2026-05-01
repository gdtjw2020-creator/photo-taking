<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import { Loading, ZoomIn, Close, Plus } from '@element-plus/icons-vue'
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
const referenceImages = ref([]) // 新增：参考图数组
const isRefUploading = ref(false) // 新增：参考图上传状态
const activeTab = ref('template') // 新增：当前激活的模式 ('template' 或 'custom')
const imageCount = ref(1) // 默认 1 张
const isUploading = ref(false)
const isGenerating = ref(false)
const autoSaveFace = ref(true) // 默认开启自动保存
const taskId = ref('')
const isAgreed = ref(false)
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

const handleRefUpload = async (file) => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后开始上传照片')
    return
  }
  isRefUploading.value = true
  const formData = new FormData()
  formData.append('file', file.raw)

  try {
    const res = await api.post('/api/photoshoot/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    referenceImages.value.push(res.data.url)
    ElMessage.success('参考图上传成功')
  } catch (err) {
    ElMessage.error('上传失败，请重试')
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
  
  if (activeTab.value === 'custom') {
    // 自定义参考图模式
    if (referenceImages.value.length === 0) {
      ElMessage.warning('请先上传至少一张换脸底图')
      return
    }
    if (!uploadedImageUrl.value) {
      ElMessage.warning('请先上传一张人脸正面照片')
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

    const payload = {
      template_id: activeTab.value === 'template' ? selectedTemplate.value.id : null,
      image_url: uploadedImageUrl.value,
      reference_image_urls: activeTab.value === 'custom' ? referenceImages.value : undefined,
      image_count: activeTab.value === 'custom' ? referenceImages.value.length : imageCount.value
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
      <div class="mode-tabs">
        <div class="mode-tab" :class="{ active: activeTab === 'template' }" @click="activeTab = 'template'">预设写真风格</div>
        <div class="mode-tab" :class="{ active: activeTab === 'custom' }" @click="activeTab = 'custom'">自定义换脸图</div>
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
        <p class="sub-hint">上传你想要换脸的模特底图（最多 5 张，禁止上传违规图片或过份性感图片，如果换脸失败请重试一，二次）。</p>
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
      <div v-if="activeTab === 'custom'" class="custom-ref-mode-hint">
        <el-alert title="您已开启自定义参考图换脸模式" type="success" :closable="false" show-icon>
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
        消耗：<span class="cost-value">{{ ((activeTab === 'custom' ? referenceImages.length : imageCount) * 5).toFixed(1) }}</span> 积分
        <span class="cost-unit">(5 积分/张)</span>
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
      <h2>3. 约拍成果 
        <el-tag v-if="taskStatus === 'processing'" type="warning" size="small">正在拍摄中 ({{ resultImages.length }}/{{ activeTab === 'custom' ? referenceImages.length : imageCount }})</el-tag>
        <el-tag v-else-if="taskStatus === 'failed'" type="danger" size="small">生成出错</el-tag>
      </h2>
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
        <div v-for="n in Math.max(0, (activeTab === 'custom' ? referenceImages.length : imageCount) - resultImages.length)" :key="'loading-'+n" class="result-item loading-placeholder" v-if="taskStatus === 'processing'">
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
  padding: 16px;
  width: 100%;
  max-width: 1000px; /* 进一步增加最大宽度以适配 PC 展示 */
  margin: 0 auto;
  box-sizing: border-box;
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
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); /* 自动填充，更具响应性 */
  gap: 12px;
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

