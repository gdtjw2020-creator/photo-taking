<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const services = [
  {
    mode: 'classic_style',
    title: '时代艺术照',
    subtitle: '挑一个年代，让唐师傅给您拍张旧时光里的肖像。',
    meta: '8 款经典年代风格',
    accent: 'classic'
  },
  {
    mode: 'darkroom_random',
    title: '暗房盲盒',
    subtitle: '不用选风格，交给暗房随机冲洗几张惊喜底片。',
    meta: '3 / 6 / 9 张胶卷套餐',
    accent: 'darkroom'
  },
  {
    mode: 'reference_shoot',
    title: '照着样子拍',
    subtitle: '上传一张参考图，唐师傅照着构图和气氛给您重拍。',
    meta: '参考图 + 人脸图',
    accent: 'reference'
  }
]

const startService = (mode) => {
  router.push({ path: '/generate', query: { mode } })
}
</script>

<template>
  <div class="home-container">
    <div class="announcement glass-card">
      <div class="announcement-content">
        <span class="announcement-icon">公告</span>
        <p>当前接口调用人数较多，请尽量在非高峰时段来使用或者失败后可适当尝试一下</p>
      </div>
    </div>

    <header class="hero">
      <p class="hero-kicker">AI OLD PHOTO STUDIO</p>
      <h1>唐师傅的 AI 老照相馆</h1>
      <p>一张照片，回到旧时光</p>
    </header>

    <section class="studio-panel">
      <div class="studio-preview" aria-hidden="true">
        <div class="photo-stack">
          <div class="photo-print print-back"></div>
          <div class="photo-print print-front">
            <div class="portrait-shape"></div>
            <div class="print-caption"></div>
          </div>
        </div>
        <div class="ticket-strip">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>

      <div class="service-grid">
        <button
          v-for="service in services"
          :key="service.mode"
          type="button"
          class="service-card glass-card"
          :class="service.accent"
          @click="startService(service.mode)"
        >
          <span class="service-meta">{{ service.meta }}</span>
          <strong>{{ service.title }}</strong>
          <span class="service-subtitle">{{ service.subtitle }}</span>
          <span class="service-action">去拍这套</span>
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-container {
  padding: 16px 16px 92px;
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
  align-items: flex-start;
  gap: 10px;
}

.announcement-icon {
  flex: 0 0 auto;
  color: #fbbf24;
  font-size: 0.8rem;
  font-weight: 700;
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
  margin: 28px 0 24px;
}

.hero-kicker {
  margin: 0 0 8px;
  color: #f7c873;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.hero h1 {
  font-size: 2.1rem;
  font-weight: 800;
  background: linear-gradient(135deg, #fff8e6 0%, #f7c873 48%, #9bd7cb 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: #fff8e6;
  margin-bottom: 8px;
  letter-spacing: 0;
}

.hero p {
  color: var(--text-muted);
  font-size: 1rem;
  opacity: 0.86;
}

.studio-panel {
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: 18px;
  align-items: stretch;
}

.studio-preview {
  min-height: 420px;
  border: 1px solid rgba(247, 200, 115, 0.22);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(91, 49, 36, 0.28), rgba(16, 38, 43, 0.42)),
    repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.04) 0 1px, transparent 1px 18px);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.photo-stack {
  position: relative;
  width: min(260px, 72%);
  aspect-ratio: 4 / 5;
}

.photo-print {
  position: absolute;
  inset: 0;
  border-radius: 6px;
  background: #efe1c0;
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.36);
}

.print-back {
  transform: rotate(-8deg) translate(-14px, 12px);
  background: #d9c5a1;
}

.print-front {
  transform: rotate(3deg);
  padding: 18px 18px 44px;
  box-sizing: border-box;
}

.portrait-shape {
  height: 100%;
  border-radius: 4px;
  background:
    radial-gradient(circle at 50% 28%, #d5b18a 0 13%, transparent 14%),
    radial-gradient(ellipse at 50% 78%, #6c3f35 0 34%, transparent 35%),
    linear-gradient(180deg, #63716a, #3c4a48);
  filter: sepia(0.38) contrast(0.95);
}

.print-caption {
  position: absolute;
  left: 42px;
  right: 42px;
  bottom: 20px;
  height: 8px;
  border-radius: 999px;
  background: rgba(91, 49, 36, 0.36);
}

.ticket-strip {
  position: absolute;
  left: 20px;
  right: 20px;
  bottom: 20px;
  display: flex;
  gap: 8px;
}

.ticket-strip span {
  flex: 1;
  height: 5px;
  border-radius: 999px;
  background: rgba(247, 200, 115, 0.46);
}

.service-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.service-card {
  width: 100%;
  min-height: 126px;
  padding: 18px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #fff;
  text-align: left;
  cursor: pointer;
  display: grid;
  gap: 8px;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.service-card:hover {
  transform: translateY(-2px);
  border-color: rgba(247, 200, 115, 0.48);
}

.service-card.classic {
  background: linear-gradient(135deg, rgba(97, 64, 45, 0.54), rgba(29, 46, 45, 0.56));
}

.service-card.darkroom {
  background: linear-gradient(135deg, rgba(86, 24, 27, 0.56), rgba(27, 24, 32, 0.64));
}

.service-card.reference {
  background: linear-gradient(135deg, rgba(37, 74, 75, 0.56), rgba(41, 35, 56, 0.6));
}

.service-meta {
  color: #f7c873;
  font-size: 0.78rem;
  font-weight: 700;
}

.service-card strong {
  font-size: 1.22rem;
  letter-spacing: 0;
}

.service-subtitle {
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.92rem;
  line-height: 1.55;
}

.service-action {
  justify-self: start;
  color: #9bd7cb;
  font-weight: 700;
  font-size: 0.9rem;
}

@media (max-width: 760px) {
  .hero h1 {
    font-size: 1.8rem;
  }

  .studio-panel {
    grid-template-columns: 1fr;
  }

  .studio-preview {
    min-height: 250px;
  }

  .photo-stack {
    width: min(180px, 58%);
  }
}
</style>
