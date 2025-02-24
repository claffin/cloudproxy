import { createApp } from 'vue'
import App from './App.vue'
import BootstrapVueNext from 'bootstrap-vue-next'
import * as bootstrap from 'bootstrap'

// Import Bootstrap and BootstrapVueNext CSS files
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css'
import 'bootstrap-icons/font/bootstrap-icons.css'

const app = createApp(App)

// Make BootstrapVueNext available throughout the project
app.use(BootstrapVueNext)

// Add tooltip directive
app.directive('tooltip', {
  mounted(el, binding) {
    new bootstrap.Tooltip(el, {
      title: binding.value,
      placement: binding.arg || 'top',
      trigger: 'hover focus'
    })
  },
  unmounted(el) {
    const tooltip = bootstrap.Tooltip.getInstance(el)
    if (tooltip) {
      tooltip.dispose()
    }
  }
})

// Mount the app
app.mount('#app')
