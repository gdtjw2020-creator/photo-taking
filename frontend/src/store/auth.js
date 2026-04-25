import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { supabase } from '../lib/supabase'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(true)

  const isLoggedIn = computed(() => !!user.value)

  async function init() {
    loading.value = true
    const { data: { session } } = await supabase.auth.getSession()
    user.value = session?.user || null
    
    if (session?.access_token) {
        localStorage.setItem('token', session.access_token)
    }

    // 监听状态变化
    supabase.auth.onAuthStateChange((event, session) => {
      user.value = session?.user || null
      if (session?.access_token) {
        localStorage.setItem('token', session.access_token)
      } else {
        localStorage.removeItem('token')
      }
    })
    loading.value = false
  }

  async function signIn(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    })
    if (error) throw error
    user.value = data.user
    return data
  }

  async function signUp(email, password) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password
    })
    if (error) throw error
    return data
  }

  async function signOut() {
    await supabase.auth.signOut()
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    user,
    loading,
    isLoggedIn,
    init,
    signIn,
    signUp,
    signOut
  }
})
