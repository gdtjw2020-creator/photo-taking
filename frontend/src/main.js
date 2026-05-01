import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import VConsole from 'vconsole'

// vConsole 隐藏式触发逻辑：快速点击屏幕 6 次开启
let clickCount = 0;
let lastClickTime = 0;
let vconsoleInstance = null;

window.addEventListener('click', () => {
    const now = Date.now();
    if (now - lastClickTime < 500) {
        clickCount++;
    } else {
        clickCount = 1;
    }
    lastClickTime = now;

    if (clickCount >= 6 && !vconsoleInstance) {
        vconsoleInstance = new VConsole();
        console.log('vConsole 已通过隐藏手势激活');
        clickCount = 0;
    }
});

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
