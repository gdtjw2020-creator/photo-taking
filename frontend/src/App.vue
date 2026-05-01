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
        <span class="tab-label">开始约拍</span>
      </router-link>
      <router-link to="/gallery" class="tab-item">
        <span class="tab-label">相册</span>
      </router-link>
      <router-link to="/faces" class="tab-item">
        <span class="tab-label">人脸</span>
      </router-link>
      <router-link to="/profile" class="tab-item">
        <span class="tab-label">我的</span>
      </router-link>
    </nav>
  </div>
</template>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: #0f172a;
  color: #f8fafc;
}

.app-container {
  width: 100%;
  max-width: 1000px; /* 增加最大宽度以适配 PC 展示 */
  margin: 0 auto;
  min-height: 100dvh; /* 动态视口高度，解决移动端浏览器工具栏遮挡问题 */
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--bg-dark);
}

.tab-bar {
  position: fixed;
  bottom: 0; /* 贴合底部 */
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 1000px; /* 与容器一致 */
  height: calc(65px + env(safe-area-inset-bottom)); /* 适配 iOS 刘海屏底部安全区 */
  padding-bottom: env(safe-area-inset-bottom);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 1000;
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px); /* 兼容 Chrome/Safari 移动端 */
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.4);
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
  transition: all 0.2s;
}

.tab-item:active {
  transform: scale(0.9);
}

.router-link-active {
  color: var(--primary-color);
}

.tab-label {
  font-size: 0.75rem;
  font-weight: 600;
  margin-top: 4px;
}
</style>
