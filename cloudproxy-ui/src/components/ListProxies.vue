<template>
  <div>
    <div class="provider-section" v-for="provider in sortedProviders" :key="provider.key">
      <div class="provider-header">
        <div class="d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center">
            <div class="provider-icon-wrapper mr-2">
              <i :class="'bi bi-' + getProviderIcon(provider.key)" style="font-size: 1.5rem;"></i>
            </div>
            <h2 class="mb-0">{{ formatProviderName(provider.key) }}</h2>
          </div>
          <b-form class="scaling-control" @submit.prevent="updateProvider(provider.key, provider.data.scaling.min_scaling)">
            <div class="d-flex align-items-center">
              <span class="status-badge" :class="{'status-active': provider.data.ips.length > 0}" v-b-tooltip.hover title="Number of active proxy instances">
                <i class="bi bi-hdd-stack mr-1"></i>
                {{ provider.data.ips.length }} Active
              </span>
              <label for="sb-inline" class="mx-3">
                <i class="bi bi-sliders mr-1"></i>
                Scale to
              </label>
              <b-form-spinbutton
                v-model="provider.data.scaling.min_scaling"
                min="0"
                max="100"
                inline
                @change="updateProvider(provider.key, $event)"
                class="custom-spinbutton"
                v-b-tooltip.hover title="Set the number of proxy instances"
              ></b-form-spinbutton>
            </div>
          </b-form>
        </div>
      </div>

      <div class="proxy-list">
        <div
          v-if="!provider.data.enabled"
          class="empty-state"
        >
          <div class="text-center py-4">
            <i class="bi bi-power text-muted mb-2" style="font-size: 2rem;"></i>
            <p class="mb-0">Provider not enabled</p>
            <small class="text-muted">Enable this provider in your environment configuration</small>
          </div>
        </div>

        <div
          v-else-if="provider.data.enabled && provider.data.ips.length === 0 && provider.data.scaling.min_scaling === 0"
          class="empty-state"
        >
          <div class="text-center py-4">
            <i class="bi bi-cloud-slash text-muted mb-2" style="font-size: 2rem;"></i>
            <p class="mb-0">No proxies configured</p>
            <small class="text-muted">Use the scaling control above to deploy proxies</small>
          </div>
        </div>

        <div
          class="proxy-item"
          v-for="ips in provider.data.ips"
          :key="ips"
        >
          <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center">
              <div class="proxy-status" v-b-tooltip.hover title="Proxy is active and responding">
                <i class="bi bi-check-circle-fill status-icon"></i>
              </div>
              <div>
                <div class="d-flex align-items-center">
                  <i class="bi bi-hdd-network mr-2 text-gray"></i>
                  <p class="mb-0 proxy-ip">{{ ips }}</p>
                  <b-button 
                    variant="link" 
                    size="sm" 
                    class="copy-btn ml-2" 
                    @click="copyToClipboard(ips)"
                    v-b-tooltip.hover title="Copy proxy address"
                  >
                    <i class="bi bi-clipboard-plus"></i>
                  </b-button>
                </div>
                <small class="text-muted d-flex align-items-center">
                  <i class="bi bi-shield-lock mr-1"></i>
                  <span class="mr-2">HTTP/HTTPS Proxy</span>
                  <span class="region-indicator">
                    <i class="bi bi-geo-alt-fill mr-1"></i>
                    {{ provider.data.region || provider.data.zone || provider.data.location }}
                  </span>
                </small>
              </div>
            </div>
            <div>
              <b-button 
                variant="outline-danger" 
                size="sm"
                :disabled="listremove_data.includes(ips)"
                @click="removeProxy(ips); makeToast(ips);"
                class="remove-btn"
                v-b-tooltip.hover title="Remove this proxy instance"
              >
                <template v-if="listremove_data.includes(ips)">
                  <b-spinner small></b-spinner>
                  <span class="ml-2">Removing...</span>
                </template>
                <template v-else>
                  <i class="bi bi-x-circle"></i>
                  <span class="ml-2">Remove</span>
                </template>
              </b-button>
            </div>
          </div>
        </div>

        <div
          v-if="provider.data.enabled && provider.data.scaling.min_scaling > provider.data.ips.length"
          class="progress-item"
        >
          <div class="text-center mb-3">
            <i class="bi bi-arrow-clockwise text-purple"></i>
            <span class="ml-2 text-gray-600">Deploying new proxies...</span>
          </div>
          <b-progress
            :max="provider.data.scaling.min_scaling"
            height="8px"
            class="custom-progress"
            v-b-tooltip.hover :title="'Deploying ' + (provider.data.scaling.min_scaling - provider.data.ips.length) + ' new proxies'"
          >
            <b-progress-bar :value="provider.data.ips.length"></b-progress-bar>
          </b-progress>
          <div class="text-center mt-2">
            <small class="text-muted">{{ provider.data.ips.length }} of {{ provider.data.scaling.min_scaling }} proxies ready</small>
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
      listremove_data: [],
      toastCount: 0,
      auth: {
        username: '',
        password: '',
        auth_enabled: true
      }
    };
  },
  computed: {
    sortedProviders() {
      // Convert data object to array of {key, data} pairs
      const providers = Object.entries(this.data).map(([key, data]) => ({
        key,
        data
      }));
      
      // Sort enabled providers first, then by name
      return providers.sort((a, b) => {
        if (a.data.enabled && !b.data.enabled) return -1;
        if (!a.data.enabled && b.data.enabled) return 1;
        return a.key.localeCompare(b.key);
      });
    }
  },
  beforeMount() {
    this.getName();
    this.listremoveProxy();
    this.getAuthSettings();
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
        digitalocean: 'water',
        aws: 'cloud-fill',
        gcp: 'google',
        hetzner: 'hdd-rack'
      };
      return icons[provider] || 'cloud-fill';
    },
    async getName() {
      try {
        const res = await fetch("/providers");
        const data = await res.json();
        this.data = data.providers;
      } catch (error) {
        this.$bvToast.toast('Failed to fetch providers', {
          title: 'Error',
          variant: 'danger',
          toaster: 'b-toaster-bottom-right',
          solid: true,
        });
      }
    },
    async removeProxy(proxy) {
      try {
        const remove_res = await fetch(
          "/destroy?ip_address=" + proxy,
          { 
            method: "DELETE",
            headers: {
              'Content-Type': 'application/json',
            }
          }
        );
        const data = await remove_res.json();
        if (data.message) {
          this.$bvToast.toast(data.message, {
            title: "Success",
            variant: 'success',
            toaster: 'b-toaster-bottom-right',
            solid: true,
            autoHideDelay: 5000,
          });
        }
      } catch (error) {
        this.$bvToast.toast('Failed to remove proxy', {
          title: 'Error',
          variant: 'danger',
          toaster: 'b-toaster-bottom-right',
          solid: true,
        });
      }
    },
    async listremoveProxy() {
      try {
        const listremove_res = await fetch("/destroy");
        const data = await listremove_res.json();
        this.listremove_data = data.proxies.map(proxy => proxy.ip);
      } catch (error) {
        console.error('Failed to fetch removal list:', error);
      }
    },
    async updateProvider(provider, min_scaling) {
      try {
        const updateProvider_res = await fetch(
          "/providers/" + provider,
          { 
            method: "PATCH",
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              min_scaling: min_scaling,
              max_scaling: min_scaling
            })
          }
        );
        const data = await updateProvider_res.json();
        if (data.message) {
          this.$bvToast.toast(data.message, {
            title: "Success",
            variant: 'success',
            toaster: 'b-toaster-bottom-right',
            solid: true,
            autoHideDelay: 2000,
          });
        }
      } catch (error) {
        this.$bvToast.toast('Failed to update provider', {
          title: 'Error',
          variant: 'danger',
          toaster: 'b-toaster-bottom-right',
          solid: true,
        });
      }
    },
    makeToast(ips, append = false) {
      this.toastCount++;
      this.$bvToast.toast(`Removing ${ips}`, {
        title: "Removing proxy from pool",
        variant: 'info',
        toaster: 'b-toaster-bottom-right',
        solid: true,
        autoHideDelay: 5000,
        appendToast: append,
      });
    },
    async getAuthSettings() {
      try {
        const res = await fetch("/auth");
        const data = await res.json();
        this.auth = data;
      } catch (error) {
        console.error('Failed to fetch auth settings:', error);
      }
    },
    copyToClipboard(ip) {
      // Create proxy URL with authentication
      const url = this.auth.auth_enabled 
        ? `http://${this.auth.username}:${this.auth.password}@${ip}:8899`
        : `http://${ip}:8899`;
      navigator.clipboard.writeText(url).then(() => {
        this.$bvToast.toast('Proxy address copied to clipboard', {
          title: 'Copied!',
          variant: 'success',
          toaster: 'b-toaster-bottom-right',
          solid: true,
          autoHideDelay: 2000,
        });
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
  font-size: 0.75rem;
  color: #48bb78;
}

.proxy-ip {
  font-family: 'Roboto Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 1rem;
  color: var(--text-dark);
  font-weight: 500;
  letter-spacing: -0.3px;
}

.copy-btn {
  color: var(--text-gray);
  padding: 0.25rem;
  transition: color 0.2s ease;
}

.copy-btn:hover {
  color: var(--primary-purple);
}

.region-indicator {
  font-size: 0.75rem;
  color: var(--text-gray);
  display: inline-flex;
  align-items: center;
  padding-left: 0.5rem;
  border-left: 1px solid var(--border-color);
}

.empty-state {
  color: var(--text-gray);
  background-color: #f7fafc;
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

.provider-icon-wrapper {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(107, 70, 193, 0.1);
  border-radius: 8px;
  color: var(--primary-purple);
}
</style>
