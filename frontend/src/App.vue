<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from './store/auth'

const authStore = useAuthStore()

onMounted(() => {
  authStore.init()
})
</script>

<template>
  <div class="app-container">
    <RouterView />
    
    <!-- 底部固定导航栏 -->
    <nav class="tab-bar glass-card">
      <router-link to="/" class="tab-item">
        <span class="tab-label">首页</span>
      </router-link>
      <router-link to="/generate" class="tab-item">
        <span class="tab-label">约拍</span>
      </router-link>
      <router-link to="/gallery" class="tab-item">
        <span class="tab-label">相册</span>
      </router-link>
      <router-link to="/faces" class="tab-item">
        <span class="tab-label">形象存档</span>
      </router-link>
      <router-link to="/profile" class="tab-item">
        <span class="tab-label">我的</span>
      </router-link>
    </nav>
  </div>
</template>

<style>
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  overflow-x: hidden;
  background-color: var(--bg-dark);
  /* 增加复古暗角效果 */
  background-image: radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.4) 100%);
  color: var(--text-main);
  font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
}

.app-container {
  width: 100vw;
  max-width: 1000px;
  margin: 0 auto;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  position: relative;
  /* 增加微妙的胶片颗粒感 */
  background: linear-gradient(rgba(18, 16, 14, 0.95), rgba(18, 16, 14, 0.95)),
              url('data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)"/%3E%3C/svg%3E');
  box-sizing: border-box;
}

/* 针对部分手机浏览器（如华为）的特殊优化：当屏幕较小时，严格限制最大宽度 */
@media (max-width: 500px) {
  .app-container {
    max-width: 100vw;
  }
}

.tab-bar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 1000px;
  height: calc(65px + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 1000;
  /* 复古暗红/深棕皮革感背景 */
  background: linear-gradient(180deg, #2d2420 0%, #1a1614 100%);
  border-top: 1px solid rgba(212, 167, 106, 0.4); /* 古铜金边框 */
  box-shadow: 0 -4px 30px rgba(0, 0, 0, 0.9);
}

.tab-item {
  text-decoration: none;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  height: 100%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-item:active {
  transform: scale(0.95);
  background: rgba(212, 167, 106, 0.05);
}

.router-link-active {
  color: var(--primary-color);
  /* 激活时增加光晕 */
  text-shadow: 0 0 10px rgba(212, 167, 106, 0.4);
}

.tab-label {
  font-size: 1rem; /* 略微减小字号，更显精致 */
  font-weight: 600;
  margin-top: 4px;
  letter-spacing: 0.05em;
}
</style>
