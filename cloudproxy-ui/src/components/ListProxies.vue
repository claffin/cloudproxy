<template>
  <div>
    <div class="provider-section" v-for="(item, key, index) in data" :key="index">
      <div class="provider-header">
        <div class="d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center">
            <b-icon :icon="getProviderIcon(key)" class="mr-2" font-scale="1.5"></b-icon>
            <h2 class="mb-0">{{ formatProviderName(key) }}</h2>
          </div>
          <b-form class="scaling-control" @submit.prevent="updateProvider(key, item.scaling.min_scaling)">
            <div class="d-flex align-items-center">
              <span class="status-badge" :class="{'status-active': item.ips.length > 0}">
                {{ item.ips.length }} Active
              </span>
              <label for="sb-inline" class="mx-3">Scale to</label>
              <b-form-spinbutton
                v-model="item.scaling.min_scaling"
                min="0"
                max="100"
                inline
                @change="updateProvider(key, $event)"
                class="custom-spinbutton"
              ></b-form-spinbutton>
            </div>
          </b-form>
        </div>
      </div>

      <div class="proxy-list">
        <div
          class="proxy-item"
          v-for="ips in item.ips"
          :key="ips"
        >
          <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center">
              <div class="proxy-status">
                <b-icon icon="circle-fill" class="status-icon"></b-icon>
              </div>
              <div>
                <p class="mb-0 proxy-ip">{{ ips }}</p>
                <small class="text-muted">HTTP/HTTPS Proxy</small>
              </div>
            </div>
            <div>
              <b-button 
                variant="outline-danger" 
                size="sm"
                :disabled="listremove_data.includes(ips)"
                @click="removeProxy(ips); makeToast(ips);"
                class="remove-btn"
              >
                <template v-if="listremove_data.includes(ips)">
                  <b-spinner small></b-spinner>
                  <span class="ml-2">Removing...</span>
                </template>
                <template v-else>
                  <b-icon icon="trash"></b-icon>
                  <span class="ml-2">Remove</span>
                </template>
              </b-button>
            </div>
          </div>
        </div>

        <div
          v-if="item.enabled && item.scaling.min_scaling > item.ips.length"
          class="progress-item"
        >
          <div class="text-center mb-3">
            <b-icon icon="arrow-clockwise" animation="spin" class="text-purple"></b-icon>
            <span class="ml-2 text-gray-600">Deploying new proxies...</span>
          </div>
          <b-progress
            :max="item.scaling.min_scaling"
            height="8px"
            class="custom-progress"
          >
            <b-progress-bar :value="item.ips.length"></b-progress-bar>
          </b-progress>
          <div class="text-center mt-2">
            <small class="text-muted">{{ item.ips.length }} of {{ item.scaling.min_scaling }} proxies ready</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "ListProxies",
  mounted() {
    window.setInterval(() => {
      this.getName();
      this.listremoveProxy();
    }, 3000);
  },
  data() {
    return {
      data: {},
      listremove_data: {},
      toastCount: 0,
    };
  },
  beforeMount() {
    this.getName();
    this.listremoveProxy();
  },
  methods: {
    formatProviderName(name) {
      const specialCases = {
        'digitalocean': 'DigitalOcean',
        'aws': 'AWS',
        'gcp': 'GCP',
        'hetzner': 'Hetzner'
      };
      return specialCases[name] || name.charAt(0).toUpperCase() + name.slice(1);
    },
    getProviderIcon(provider) {
      const icons = {
        digitalocean: 'droplet',
        aws: 'cloud',
        gcp: 'cloud-fill',
        hetzner: 'server'
      };
      return icons[provider] || 'cloud';
    },
    async getName() {
      const res = await fetch("/providers");
      const data = await res.json();
      this.data = data;
    },
    async removeProxy(proxy) {
      const remove_res = await fetch(
        "/destroy?ip_address=" + proxy,
        { method: "DELETE", body: JSON.stringify(proxy) }
      );
      const remove_data = await remove_res.json();
      this.remove_data = remove_data;
    },
    async listremoveProxy() {
      const listremove_res = await fetch("/destroy");
      const listremove_data = await listremove_res.json();
      this.listremove_data = listremove_data;
    },
    async updateProvider(provider, min_scaling) {
      const updateProvider_res = await fetch(
        "/providers/" +
          provider +
          "?min_scaling=" +
          min_scaling +
          "&max_scaling=" +
          min_scaling,
        { method: "PATCH" }
      );
      const updateProvider_data = await updateProvider_res.json();
      this.updateProvider_data = updateProvider_data;
    },
    makeToast(ips, append = false) {
      this.toastCount++;
      this.$bvToast.toast(`${ips}`, {
        title: "Removing proxy from pool",
        variant: 'danger',
        toaster: 'b-toaster-bottom-right',
        solid: true,
        autoHideDelay: 5000,
        appendToast: append,
      });
    },
  },
};
</script>

<style scoped>
.provider-section {
  background: white;
}

.provider-section:not(:last-child) {
  border-bottom: 1px solid var(--border-color);
}

.provider-header {
  padding: 1.5rem;
  background-color: #faf5ff;
  border-bottom: 1px solid var(--border-color);
}

.provider-header h2 {
  color: var(--primary-purple);
  font-family: var(--font-family);
  font-weight: 700;
  font-size: 1.25rem;
  letter-spacing: -0.2px;
}

.provider-header .b-icon {
  color: var(--primary-purple);
}

.status-badge {
  font-family: var(--font-family);
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
  background-color: #edf2f7;
  color: var(--text-gray);
}

.status-badge.status-active {
  background-color: #c6f6d5;
  color: #2f855a;
}

.custom-spinbutton {
  font-family: var(--font-family);
  height: 38px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: white;
}

.custom-spinbutton >>> .btn-spin {
  border: none;
  background: transparent;
  color: var(--primary-purple);
  opacity: 1;
  cursor: pointer;
  padding: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.custom-spinbutton >>> .btn-spin:hover {
  background-color: var(--primary-purple-light);
  color: white;
}

.custom-spinbutton >>> .btn-spin:focus {
  box-shadow: none;
  outline: none;
}

.custom-spinbutton >>> input {
  border: none;
  text-align: center;
  font-weight: 500;
  color: var(--text-dark);
}

.custom-spinbutton >>> input:focus {
  box-shadow: none;
  outline: none;
}

.proxy-list {
  padding: 0.5rem 0;
}

.proxy-item {
  padding: 1rem 1.5rem;
  transition: background-color 0.2s ease;
}

.proxy-item:hover {
  background-color: #f7fafc;
}

.proxy-status {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
}

.status-icon {
  font-size: 0.5rem;
  color: #48bb78;
}

.proxy-ip {
  font-family: 'Roboto Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 1rem;
  color: var(--text-dark);
  font-weight: 500;
  letter-spacing: -0.3px;
}

.remove-btn {
  font-family: var(--font-family);
  font-size: 0.875rem;
  padding: 0.375rem 0.75rem;
  letter-spacing: 0.2px;
}

.progress-item {
  padding: 2rem 1.5rem;
  background-color: #faf5ff;
  border-top: 1px solid var(--border-color);
}

.text-purple {
  color: var(--primary-purple);
}

.text-gray-600 {
  color: var(--text-gray);
  font-family: var(--font-family);
}

.custom-progress {
  background-color: #e9d8fd;
  border-radius: 9999px;
}

.custom-progress .progress-bar {
  background-color: var(--primary-purple);
  border-radius: 9999px;
}
</style>
