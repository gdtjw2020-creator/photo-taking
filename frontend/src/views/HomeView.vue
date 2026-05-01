<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const startPhotoshoot = () => {
  router.push('/generate')
}
</script>

<template>
  <div class="home-container">
    <div class="announcement glass-card">
      <div class="announcement-content">
        <span class="announcement-icon">📢</span>
        <p>当前接口调用人数较多，请尽量在非高峰时段来使用或者失败后可适当尝试一下</p>
      </div>
    </div>

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
  padding: 16px;
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  box-sizing: border-box;
}

.announcement {
  margin-top: 5px;
  margin-bottom: 25px;
  padding: 14px;
  border: 1px solid rgba(251, 191, 36, 0.3);
  background: rgba(251, 191, 36, 0.05);
  animation: slideIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.announcement-content {
  display: flex;
  align-items: flex-start; /* 适配长文本 */
  gap: 10px;
}

.announcement-icon {
  font-size: 1.2rem;
  line-height: 1.5;
}

.announcement p {
  margin: 0;
  font-size: 0.85rem;
  color: #fbbf24;
  line-height: 1.5;
}

.hero {
  text-align: center;
  margin: 30px 0;
}

.hero h1 {
  font-size: 2.2rem;
  font-weight: 800;
  background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  background-clip: text; /* 标准属性 */
  -webkit-text-fill-color: transparent;
  color: #fff; /* 回退颜色 */
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.hero p {
  color: var(--text-muted);
  font-size: 1rem;
  opacity: 0.8;
}

.compare-card {
  padding: 20px;
  margin-bottom: 30px;
}

.compare-badge {
  display: inline-block;
  background: rgba(99, 102, 241, 0.2);
  color: var(--primary-color);
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: bold;
  margin-bottom: 12px;
}

.before-after {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 10px;
}

.placeholder-img {
  flex: 1;
  height: 160px;
  background: #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: var(--text-muted);
  font-size: 0.85rem;
  text-align: center;
  padding: 10px;
}

.placeholder-img.premium {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  font-weight: bold;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}

.divider {
  font-weight: 800;
  color: var(--primary-color);
  font-size: 1.2rem;
}

.action-bar {
  text-align: center;
  margin-bottom: 20px;
}

.primary-button.large {
  width: 100%;
  padding: 16px;
  font-size: 1.1rem;
  border-radius: 14px;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}
</style>
