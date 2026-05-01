<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const authStore = useAuthStore()
const isLoggedIn = computed(() => authStore.isLoggedIn)

const user = ref({
  username: '女神体验官',
  email: '',
  credits: 0,
  avatar: 'https://placehold.co/100x100/png?text=Avatar'
})

// 移除 myPhotos 引用
// const myPhotos = ref([])

onMounted(async () => {
  if (!isLoggedIn.value) return
  
  try {
    // 获取个人资料
    const profileRes = await api.get('/api/user/profile')
    user.value = {
      username: profileRes.data.username || authStore.user?.email?.split('@')[0] || '女神用户',
      email: authStore.user?.email || '',
      credits: profileRes.data.credits,
      avatar: profileRes.data.avatar_url || user.value.avatar
    }

    // 获取积分明细
    const logsRes = await api.get('/api/user/credit_logs')
    creditLogs.value = logsRes.data
  } catch (err) {
    console.error('Failed to load profile data:', err)
  }
})

const creditLogs = ref([])

const redeemDialogVisible = ref(false)
const redeemCode = ref('')
const isRedeeming = ref(false)

const handleRedeem = async () => {
    if (!redeemCode.value) {
        ElMessage.warning('请输入卡密')
        return
    }
    isRedeeming.value = true
    try {
        const res = await api.post('/api/user/redeem', { code: redeemCode.value })
        ElMessage.success(res.data.message)
        user.value.credits = parseFloat((user.value.credits + res.data.amount).toFixed(2))
        redeemCode.value = ''
        redeemDialogVisible.value = false
    } catch (err) {
        ElMessage.error(err.response?.data?.detail || '兑换失败')
    } finally {
        isRedeeming.value = false
    }
}

const handleLogout = async () => {
    await authStore.signOut()
    router.push('/')
}

const goToLogin = () => {
    router.push('/login')
}
</script>

<template>
  <div class="profile-container">
    <div class="user-card glass-card">
      <el-avatar :size="80" :src="user.avatar"></el-avatar>
      <div v-if="isLoggedIn" class="user-info">
        <h3>{{ user.username }}</h3>
        <p class="user-email">{{ user.email }}</p>
        <p class="credits">可用余额: <span>{{ user.credits }}</span> 积分</p>
      </div>
      <div v-else class="user-info">
        <h3>访客模式</h3>
        <el-button type="primary" size="small" @click="goToLogin">立即登录</el-button>
      </div>
    </div>

    <div v-if="isLoggedIn" class="section-title">积分明细</div>
    <div v-if="isLoggedIn" class="logs-list glass-card">
      <div v-for="log in creditLogs" :key="log.id" class="log-item">
        <div class="log-main">
          <div class="log-desc">{{ log.description || (log.type === 'recharge' ? '积分充值' : '约拍消耗') }}</div>
          <div class="log-time">{{ new Date(log.created_at).toLocaleString('zh-CN', {month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit'}) }}</div>
        </div>
        <div class="log-amount" :class="log.amount > 0 ? 'plus' : 'minus'">
          {{ log.amount > 0 ? '+' : '' }}{{ log.amount }}
        </div>
      </div>
      <el-empty v-if="creditLogs.length === 0" description="暂无变动明细" :image-size="60"></el-empty>
    </div>

    <div class="recharge-section">
      <el-button type="primary" plain class="full-width" @click="redeemDialogVisible = true">充值积分卡密</el-button>
      <p class="recharge-hint">
        可在“面包多”平台购买激活码进行充值 
        <a href="https://mbd.pub/o/author-bWuYlGxpZw==/work" target="_blank" class="buy-link">立即前往</a>
      </p>
    </div>

    <!-- 兑换卡密弹窗 -->
    <el-dialog
      v-model="redeemDialogVisible"
      title="卡密兑换"
      width="90%"
      style="max-width: 400px; border-radius: 16px;"
      center
    >
      <div class="redeem-body">
        <p class="dialog-hint">请输入您从卡密平台获取的 14 位兑换码</p>
        <el-input 
            v-model="redeemCode" 
            placeholder="GD-XXXX-XXXX-XXXX" 
            clearable
            @keyup.enter="handleRedeem"
        ></el-input>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="redeemDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="isRedeeming" @click="handleRedeem">
            立即兑换
          </el-button>
        </span>
      </template>
    </el-dialog>

    <div v-if="!isLoggedIn" class="guest-tip">
        <el-empty description="登录后即可查看您的专属约拍作品集">
            <el-button type="primary" @click="goToLogin">立即登录</el-button>
        </el-empty>
    </div>

    <div v-if="isLoggedIn" class="logout-section">
        <el-button type="danger" plain @click="handleLogout" style="width: 100%">退出登录</el-button>
    </div>
  </div>
</template>

<style scoped>
.profile-container {
  padding: 20px;
  padding-bottom: 80px;
}

.user-card {
  display: flex;
  align-items: center;
  padding: 24px;
  margin-top: 20px;
  margin-bottom: 32px;
}

.user-info {
  margin-left: 20px;
}

.user-info h3 {
  margin: 0 0 4px 0;
  font-size: 1.4rem;
}

.user-email {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0 0 12px 0;
  opacity: 0.8;
}

.credits {
  font-size: 0.9rem;
  color: #fff;
}

.credits span {
  color: var(--primary-color);
  font-weight: bold;
  font-size: 1.2rem;
}

.section-title {
  font-size: 1.1rem;
  font-weight: bold;
  margin-bottom: 16px;
  color: var(--text-muted);
}

.logs-list {
  padding: 8px 16px;
  margin-bottom: 24px;
}

.log-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.log-item:last-child {
  border-bottom: none;
}

.log-main {
  flex: 1;
}

.log-desc {
  font-size: 0.95rem;
  margin-bottom: 4px;
}

.log-time {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.log-amount {
  font-weight: bold;
  font-size: 1.1rem;
}

.log-amount.plus {
  color: #10b981; /* 绿色 */
}

.log-amount.minus {
  color: #f43f5e; /* 红色 */
}

.recharge-section {
  margin-bottom: 20px;
  text-align: center;
}

.recharge-hint {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 8px;
}

.buy-link {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: bold;
  margin-left: 4px;
  border-bottom: 1px solid var(--primary-color);
}

.buy-link:hover {
  opacity: 0.8;
}

.redeem-body {
    padding: 10px 0;
}

.dialog-hint {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 12px;
}

.logout-section {
  margin-top: 40px;
}

.full-width {
  width: 100%;
}

.guest-tip {
  margin-top: 40px;
}
</style>
