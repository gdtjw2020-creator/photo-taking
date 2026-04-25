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
  max-width: 600px;
  margin: 0 auto;
  min-height: 100vh;
  position: relative;
  padding-bottom: 70px; /* 为导航栏留出空间 */
}

.tab-bar {
  position: fixed;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 40px);
  max-width: 560px;
  height: 60px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  border-radius: 20px;
  z-index: 1000;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 -5px 20px rgba(0, 0, 0, 0.3);
}

.tab-item {
  text-decoration: none;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.3s;
  padding: 8px 12px;
  border-radius: 12px;
}

.tab-item:hover, .router-link-active {
  color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
}

.tab-label {
  font-size: 0.8rem;
  font-weight: bold;
}
</style>
