<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const savedFaces = ref([])
const isLoading = ref(false)

const fetchFaces = async () => {
  isLoading.value = true
  try {
    const res = await api.get('/api/photoshoot/faces')
    savedFaces.value = res.data
  } catch (err) {
    console.error('Failed to load faces:', err)
  } finally {
    isLoading.value = false
  }
}

const deleteFace = async (faceId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个形象存档吗？', '提示', {
      type: 'warning'
    })
    
    await api.delete(`/api/photoshoot/faces/${faceId}`)
    
    savedFaces.value = savedFaces.value.filter(f => f.id !== faceId)
    ElMessage.success('删除成功')
  } catch (err) {
    // 用户取消或请求失败
  }
}

onMounted(() => {
  fetchFaces()
})
</script>

<template>
  <div class="faces-container">
    <div class="header">
      <h1>形象存档</h1>
      <p>管理您的专属形象，永久保存以便随时约拍</p>
    </div>

    <div v-loading="isLoading" class="face-grid">
      <div v-for="face in savedFaces" :key="face.id" class="face-card glass-card">
        <div class="face-preview">
          <el-image 
            :src="face.face_url" 
            :preview-src-list="[face.face_url]" 
            preview-teleported 
            fit="cover"
          ></el-image>
        </div>
        <div class="face-info">
          <h3>{{ face.name }}</h3>
          <p>{{ new Date(face.created_at).toLocaleDateString() }} 保存</p>
          <div class="actions">
            <el-button size="small" type="primary" @click="$router.push({ name: 'generate', query: { face_url: face.face_url } })">去约拍</el-button>
            <el-button size="small" type="danger" plain @click="deleteFace(face.id)">删除</el-button>
          </div>
        </div>
      </div>
    </div>

    <el-empty v-if="!isLoading && savedFaces.length === 0" description="您还没有保存过形象档案">
        <el-button type="primary" @click="$router.push('/generate')">去上传并保存</el-button>
    </el-empty>
  </div>
</template>

<style scoped>
.faces-container {
  padding: 20px;
  padding-bottom: 80px;
}

.header {
  margin-bottom: 24px;
}

.header h1 {
  font-size: 1.5rem;
  margin-bottom: 8px;
}

.face-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 16px;
}

.face-card {
  display: flex;
  padding: 16px;
  align-items: center;
}

.face-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 16px;
  border: 2px solid var(--primary-color);
  flex-shrink: 0;
  cursor: pointer;
}

.face-preview .el-image {
  width: 100%;
  height: 100%;
}

.face-info {
  flex: 1;
}

.face-info h3 {
  margin: 0 0 4px 0;
  font-size: 1.1rem;
}

.face-info p {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.actions {
  display: flex;
  gap: 8px;
}

@media (min-width: 768px) {
  .face-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
