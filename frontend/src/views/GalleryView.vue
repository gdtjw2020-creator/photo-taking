<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Delete } from '@element-plus/icons-vue'
import api from '../api'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const authStore = useAuthStore()
const isLoggedIn = computed(() => authStore.isLoggedIn)

const isMobile = ref(/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent))

const myPhotos = ref([])
const isLoading = ref(false)

const fetchGallery = async () => {
  if (!isLoggedIn.value) return
  isLoading.value = true
  try {
    const res = await api.get('/api/photoshoot/gallery')
    const photos = []
    res.data.forEach(task => {
      if (task.output_urls) {
        task.output_urls.forEach((url, idx) => {
          photos.push({
            id: `${task.id}_${idx}`,
            url: url,
            date: new Date(task.created_at).toLocaleDateString()
          })
        })
      }
    })
    myPhotos.value = photos
  } catch (err) {
    console.error('Failed to load gallery:', err)
  } finally {
    isLoading.value = false
  }
}

const handlePhotoDelete = async (photo) => {
    try {
        await ElMessageBox.confirm(
            '确定要删除这张精美的写真吗？删除后将无法找回。',
            '删除确认',
            {
                confirmButtonText: '确定删除',
                cancelButtonText: '再想想',
                type: 'warning',
                center: true,
                roundButton: true
            }
        )
        
        // 解析出真正的 task_id (photo.id 是 taskid_index 格式)
        const taskId = photo.id.split('_')[0]
        
        await api.delete(`/api/photoshoot/gallery/${taskId}`, {
            data: { url: photo.url }
        })
        
        ElMessage.success('已从您的相册中移除')
        // 本地更新列表，避免重新请求后端
        myPhotos.value = myPhotos.value.filter(p => p.id !== photo.id)
    } catch (err) {
        if (err !== 'cancel') {
            console.error('Delete error:', err)
            ElMessage.error('删除失败，请稍后重试')
        }
    }
}

const downloadImage = (url) => {
  const proxyUrl = `/api/photoshoot/download?url=${encodeURIComponent(url)}`
  const link = document.createElement('a')
  link.href = proxyUrl
  link.download = ''
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const downloadAll = async () => {
  if (myPhotos.value.length === 0) return
  ElMessage.info('开始下载照片...')
  for (let i = 0; i < myPhotos.value.length; i++) {
    downloadImage(myPhotos.value[i].url)
    await new Promise(resolve => setTimeout(resolve, 800))
  }
}

const goToLogin = () => {
  router.push('/login?redirect=/gallery')
}

onMounted(() => {
  if (isLoggedIn.value) {
    fetchGallery()
  }
})
</script>

<template>
  <div class="gallery-container">
    <div class="header">
      <h1>我的约拍相册</h1>
      <p>记录您的每一个精彩瞬间 (最近 30 天)</p>
    </div>

    <div v-loading="isLoading" class="photo-grid">
      <div v-for="(photo, index) in myPhotos" :key="photo.id" class="photo-item glass-card">
        <el-image
            :src="photo.url"
            :preview-src-list="isMobile ? [] : myPhotos.map(p => p.url)"
            :initial-index="index"
            :key="photo.url"
            fit="cover"
            class="gallery-img"
            preview-teleported
        ></el-image>
        <div class="photo-download-btn" @click.stop="downloadImage(photo.url)">
          <el-icon><Download /></el-icon>
        </div>
        <div class="photo-delete-btn" @click.stop="handlePhotoDelete(photo)">
          <el-icon><Delete /></el-icon>
        </div>
        <div class="photo-info">
          <span class="date">{{ photo.date }}</span>
        </div>
      </div>
    </div>

    <div v-if="!isLoading && myPhotos.length > 0" class="gallery-actions">
      <el-button type="success" @click="downloadAll">
        {{ isMobile ? '下载全部照片' : '下载全组照片' }}
      </el-button>
    </div>

    <p v-if="isMobile && myPhotos.length > 0" class="mobile-hint">提示：长按图片即可保存到相册，或点击图片右下角按钮一键下载</p>

    <el-empty v-if="!isLoading && isLoggedIn && myPhotos.length === 0" description="暂无约拍作品，快去开启第一次约拍吧！">
        <el-button type="primary" @click="router.push('/generate')">去约拍</el-button>
    </el-empty>

    <el-empty v-if="!isLoggedIn" description="登录后即可查看您的专属约拍作品集">
        <el-button type="primary" @click="goToLogin">立即登录</el-button>
    </el-empty>
  </div>
</template>

<style scoped>
.gallery-container {
  padding: 20px;
  padding-bottom: 80px; /* 留出底部导航空间 */
}

.header {
  margin-bottom: 24px;
}

.header h1 {
  font-size: 1.5rem;
  margin-bottom: 8px;
}

.header p {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.photo-item {
  overflow: hidden;
  position: relative;
  height: 240px;
  border-radius: 12px;
}

.gallery-img {
  width: 100%;
  height: 100%;
}

.photo-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.date {
  font-size: 0.75rem;
  color: #fff;
}

.photo-download-btn {
  position: absolute;
  top: 8px;
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
  z-index: 3;
}

.photo-download-btn:hover {
  background: var(--primary-color);
  transform: scale(1.1);
}

.photo-delete-btn {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 32px;
  height: 32px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
  backdrop-filter: blur(4px);
  transition: all 0.2s;
  z-index: 3;
  opacity: 0; /* 默认隐藏，hover 时显示 */
}

.photo-item:hover .photo-delete-btn {
  opacity: 1;
}

.photo-delete-btn:hover {
  background: #f43f5e;
  transform: scale(1.1);
}

.gallery-actions {
  margin-top: 20px;
  text-align: center;
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

@media (min-width: 768px) {
  .photo-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
