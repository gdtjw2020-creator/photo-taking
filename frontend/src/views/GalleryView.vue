<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const myPhotos = ref([])
const isLoading = ref(false)

const fetchGallery = async () => {
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

onMounted(() => {
  fetchGallery()
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
            :preview-src-list="myPhotos.map(p => p.url)" 
            :initial-index="index"
            :key="photo.url"
            fit="cover"
            class="gallery-img"
            preview-teleported
        ></el-image>
        <div class="photo-info">
          <span class="date">{{ photo.date }}</span>
        </div>
      </div>
    </div>

    <el-empty v-if="!isLoading && myPhotos.length === 0" description="暂无约拍作品，快去开启第一次约拍吧！">
        <el-button type="primary" @click="$router.push('/generate')">去约拍</el-button>
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

@media (min-width: 768px) {
  .photo-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
