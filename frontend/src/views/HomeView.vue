<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const startPhotoshoot = () => {
  router.push('/generate')
}
</script>

<template>
  <div class="home-container">
    <header class="hero">
      <h1>AI女神约拍神器</h1>
      <p>记录身边人的美，定格最动人的瞬间</p>
    </header>

    <div class="marketing-section">
      <div class="compare-card glass-card">
        <div class="compare-badge">视觉冲击</div>
        <div class="compare-content">
          <div class="before-after">
            <!-- 这里将来放对比图 -->
            <div class="placeholder-img">普通生活照</div>
            <div class="divider">VS</div>
            <div class="placeholder-img premium">AI 顶级写真</div>
          </div>
          <h3>与其羡慕，不如让她成为主角</h3>
          <p>无需昂贵设备，一张照片秒变名模大片</p>
        </div>
      </div>
    </div>

    <div class="action-bar">
      <button class="primary-button large" @click="startPhotoshoot">立即开启约拍</button>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  padding: 20px;
}

.hero {
  text-align: center;
  margin-top: 40px;
  margin-bottom: 40px;
}

.hero h1 {
  font-size: 2.5rem;
  background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 10px;
}

.hero p {
  color: var(--text-muted);
  font-size: 1.1rem;
}

.compare-card {
  padding: 24px;
  margin-bottom: 40px;
}

.compare-badge {
  display: inline-block;
  background: rgba(99, 102, 241, 0.2);
  color: var(--primary-color);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
  margin-bottom: 16px;
}

.before-after {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 12px;
}

.placeholder-img {
  flex: 1;
  height: 200px;
  background: #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.placeholder-img.premium {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  font-weight: bold;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
}

.divider {
  font-weight: bold;
  color: var(--primary-color);
}

.action-bar {
  text-align: center;
  margin-top: 40px;
}

.primary-button.large {
  width: 100%;
  padding: 18px;
  font-size: 1.2rem;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}
</style>
