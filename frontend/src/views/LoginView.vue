<template>
  <div class="login-page">
    <div class="login-card glass-card">
      <div class="logo">
        <span class="emoji">✨</span>
        <h2>AI女神约拍</h2>
      </div>
      <p class="subtitle">{{ isLogin ? '欢迎回来' : '开启女神约拍之旅' }}</p>

      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleSubmit">
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="邮箱地址"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item v-if="!isLogin" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            show-password
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          native-type="submit"
          class="submit-btn"
        >
          {{ isLogin ? '登录' : '注册' }}
        </el-button>
      </el-form>

      <div class="switch-mode">
        <span v-if="isLogin">
          还没有账号？
          <el-link type="primary" @click="isLogin = false">立即注册</el-link>
        </span>
        <span v-else>
          已有账号？
          <el-link type="primary" @click="isLogin = true">立即登录</el-link>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isLogin = ref(true)
const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (!isLogin.value && value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    if (isLogin.value) {
      await authStore.signIn(form.email, form.password)
      ElMessage.success('登录成功')
      const redirectPath = route.query.redirect || '/'
      router.push(redirectPath)
    } else {
      await authStore.signUp(form.email, form.password)
      ElMessage.success('注册成功，请查收验证邮件')
      isLogin.value = true
    }
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px 30px;
  border-radius: 24px;
}

.logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.emoji {
  font-size: 3rem;
  margin-bottom: 12px;
}

.logo h2 {
  font-size: 1.8rem;
  margin: 0;
  background: linear-gradient(to right, #fff, var(--primary-color));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  text-align: center;
  color: var(--text-muted);
  margin-bottom: 32px;
  font-size: 1rem;
}

.submit-btn {
  width: 100%;
  height: 50px;
  font-size: 1.1rem;
  margin-top: 10px;
}

.switch-mode {
  text-align: center;
  margin-top: 24px;
  color: var(--text-muted);
  font-size: 0.9rem;
}
</style>
