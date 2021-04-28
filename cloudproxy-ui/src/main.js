import '@babel/polyfill'
import 'mutationobserver-shim'
import Vue from "vue"
import "./plugins/bootstrap-vue"
import App from './App.vue'
import { ListGroupPlugin } from 'bootstrap-vue'
Vue.use(ListGroupPlugin)

Vue.config.productionTip = false

new Vue({
  render: h => h(App),
}).$mount('#app')
