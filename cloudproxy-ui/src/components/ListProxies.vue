<template>
  <div>
    <div
      v-for="provider in sortedProviderInstances"
      :key="`${provider.providerKey}-${provider.instanceKey}`"
      class="provider-section"
    >
      <div class="provider-header">
        <div class="d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center">
            <div class="provider-icon-wrapper me-2">
              <i
                :class="'bi bi-' + getProviderIcon(provider.providerKey)"
                class="provider-icon"
                style="font-size: 1.5rem;"
              />
            </div>
            <h2 class="mb-0">
              {{ provider.data.display_name || formatProviderName(provider.providerKey, provider.instanceKey) }}
            </h2>
          </div>
          <form
            class="scaling-control"
            @submit.prevent="updateProvider(provider.providerKey, provider.instanceKey, provider.data.scaling.min_scaling)"
          >
            <div class="d-flex align-items-center">
              <span
                v-tooltip="'Number of active proxy instances'"
                :class="{'status-active': provider.data.ips.length > 0}"
                class="status-badge"
              >
                <i class="bi bi-hdd-stack me-1" />
                {{ provider.data.ips.length }} Active
              </span>
              <label
                for="sb-inline"
                class="mx-3"
              >
                <i class="bi bi-sliders me-1" />
                Scale to
              </label>
              <input
                v-model="provider.data.scaling.min_scaling"
                v-tooltip="'Set the number of proxy instances'"
                type="number"
                min="0"
                max="100"
                class="form-control custom-spinbutton"
                @change="updateProvider(provider.providerKey, provider.instanceKey, $event.target.value)"
              >
            </div>
          </form>
        </div>
      </div>

      <div class="proxy-list">
        <div
          v-if="!provider.data.enabled"
          class="empty-state"
        >
          <div class="text-center py-4">
            <i
              class="bi bi-power text-muted mb-2"
              style="font-size: 2rem;"
            />
            <p class="mb-0">
              Provider not enabled
            </p>
            <small class="text-muted">
              Enable this provider in your environment configuration
            </small>
          </div>
        </div>

        <div
          v-else-if="provider.data.enabled && provider.data.ips.length === 0 && provider.data.scaling.min_scaling === 0"
          class="empty-state"
        >
          <div class="text-center py-4">
            <i
              class="bi bi-cloud-slash text-muted mb-2"
              style="font-size: 2rem;"
            />
            <p class="mb-0">
              No proxies configured
            </p>
            <small class="text-muted">
              Use the scaling control above to deploy proxies
            </small>
          </div>
        </div>

        <div
          v-for="ips in provider.data.ips"
          :key="ips"
          class="proxy-item"
        >
          <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center">
              <div
                v-tooltip="'Proxy is active and responding'"
                class="proxy-status"
              >
                <i class="bi bi-check-circle-fill status-icon" />
              </div>
              <div>
                <div class="d-flex align-items-center">
                  <i class="bi bi-hdd-network me-2 text-gray" />
                  <p class="mb-0 proxy-ip">
                    {{ ips }}
                  </p>
                  <button
                    v-tooltip="'Copy proxy address'"
                    type="button"
                    class="btn btn-link copy-btn ms-2"
                    @click="copyToClipboard(ips)"
                  >
                    <i class="bi bi-clipboard-plus" />
                  </button>
                </div>
                <small class="text-muted d-flex align-items-center">
                  <i class="bi bi-shield-lock me-1" />
                  <span class="me-2">HTTP/HTTPS Proxy</span>
                  <span class="region-indicator">
                    <i class="bi bi-geo-alt-fill me-1" />
                    {{ provider.data.region || provider.data.zone || provider.data.location }}
                  </span>
                </small>
              </div>
            </div>
            <div>
              <button
                v-tooltip="'Remove this proxy instance'"
                type="button"
                :disabled="listremove_data.includes(ips)"
                class="btn btn-outline-danger btn-sm remove-btn"
                @click="removeProxy(ips); makeToast(ips);"
              >
                <template v-if="listremove_data.includes(ips)">
                  <div class="spinner-border spinner-border-sm" />
                  <span class="ms-2">Removing...</span>
                </template>
                <template v-else>
                  <i class="bi bi-x-circle" />
                  <span class="ms-2">Remove</span>
                </template>
              </button>
            </div>
          </div>
        </div>

        <div
          v-if="provider.data.enabled && provider.data.scaling.min_scaling > provider.data.ips.length"
          class="progress-item"
        >
          <div class="text-center mb-3">
            <i class="bi bi-arrow-clockwise text-purple" />
            <span class="ms-2 text-gray-600">Deploying new proxies...</span>
          </div>
          <div
            v-tooltip="'Deploying ' + (provider.data.scaling.min_scaling - provider.data.ips.length) + ' new proxies'"
            class="progress custom-progress"
            style="height: 8px;"
          >
            <div
              class="progress-bar"
              role="progressbar"
              :style="{ width: (provider.data.ips.length / provider.data.scaling.min_scaling * 100) + '%' }"
              :aria-valuenow="provider.data.ips.length"
              :aria-valuemin="0"
              :aria-valuemax="provider.data.scaling.min_scaling"
            />
          </div>
          <div class="text-center mt-2">
            <small class="text-muted">
              {{ provider.data.ips.length }} of {{ provider.data.scaling.min_scaling }} proxies ready
            </small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeMount } from 'vue';
import { useToast } from 'bootstrap-vue-next';

export default {
  name: "ListProxies",
  setup() {
    const toast = useToast();
    const data = ref({});
    const listremove_data = ref([]);
    const auth = ref({
      username: '',
      password: '',
      auth_enabled: true
    });

    const sortedProviderInstances = computed(() => {
      // Create array of provider instances
      const providers = [];
      
      // Loop through each provider
      Object.entries(data.value).forEach(([providerKey, providerData]) => {
        // Handle both old format (without instances) and new format (with instances)
        if (providerData.instances) {
          // New format with instances
          Object.entries(providerData.instances).forEach(([instanceKey, instanceData]) => {
            providers.push({
              providerKey,
              instanceKey,
              data: instanceData
            });
          });
        } else {
          // Old format for backward compatibility
          providers.push({
            providerKey,
            instanceKey: 'default',
            data: providerData
          });
        }
      });
      
      // Sort enabled providers first, then by name
      return providers.sort((a, b) => {
        if (a.data.enabled && !b.data.enabled) return -1;
        if (!a.data.enabled && b.data.enabled) return 1;
        
        // If same provider type, sort by instance name
        if (a.providerKey === b.providerKey) {
          // Keep 'default' instance first
          if (a.instanceKey === 'default') return -1;
          if (b.instanceKey === 'default') return 1;
          return a.instanceKey.localeCompare(b.instanceKey);
        }
        
        return a.providerKey.localeCompare(b.providerKey);
      });
    });

    const formatProviderName = (name, instance = 'default') => {
      const specialCases = {
        'digitalocean': 'DigitalOcean',
        'aws': 'AWS',
        'gcp': 'GCP',
        'hetzner': 'Hetzner',
        'azure': 'Azure',
        'vultr': 'Vultr'
      };
      
      const providerName = specialCases[name] || name.charAt(0).toUpperCase() + name.slice(1);
      
      if (instance === 'default') {
        return providerName;
      } else {
        return `${providerName} (${instance})`;
      }
    };

    const getProviderIcon = (provider) => {
      const icons = {
        digitalocean: 'water',
        aws: 'cloud-fill',
        gcp: 'google',
        hetzner: 'hdd-rack',
        azure: 'microsoft',
        vultr: 'server'
      };
      return icons[provider] || 'cloud-fill';
    };

    const getName = async () => {
      try {
        const res = await fetch("/providers");
        const responseData = await res.json();
        data.value = responseData.providers;
      } catch (error) {
        toast.show('Failed to fetch providers', {
          title: 'Error',
          variant: 'danger',
          placement: 'bottom-right',
          solid: true,
        });
      }
    };

    const removeProxy = async (proxy) => {
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
        const responseData = await remove_res.json();
        if (responseData.message) {
          toast.show(responseData.message, {
            title: "Success",
            variant: 'success',
            placement: 'bottom-right',
            solid: true,
            delay: 5000,
          });
        }
      } catch (error) {
        toast.show('Failed to remove proxy', {
          title: 'Error',
          variant: 'danger',
          placement: 'bottom-right',
          solid: true,
        });
      }
    };

    const listremoveProxy = async () => {
      try {
        const listremove_res = await fetch("/destroy");
        const responseData = await listremove_res.json();
        listremove_data.value = responseData.proxies.map(proxy => proxy.ip);
      } catch (error) {
        console.error('Failed to fetch removal list:', error);
      }
    };

    const updateProvider = async (provider, instance, min_scaling) => {
      try {
        let update_url = `/providers/${provider}`;
        if (instance !== 'default') {
          update_url += `/${instance}`;
        }
        
        const update_res = await fetch(
          update_url,
          { 
            method: "PATCH",
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              min_scaling: parseInt(min_scaling),
              max_scaling: parseInt(min_scaling)
            }),
          }
        );
        const responseData = await update_res.json();
        if (responseData.message) {
          toast.show(responseData.message, {
            title: "Success",
            variant: 'success',
            placement: 'bottom-right',
            solid: true,
          });
        }
      } catch (error) {
        toast.show('Failed to update provider', {
          title: 'Error',
          variant: 'danger',
          placement: 'bottom-right',
          solid: true,
        });
      }
    };

    const makeToast = (proxy) => {
      toast.show('Removing proxy ' + proxy, {
        title: 'Info',
        variant: 'info',
        placement: 'bottom-right',
        solid: true,
      });
    };

    const getAuthSettings = async () => {
      try {
        const res = await fetch("/auth");
        const responseData = await res.json();
        auth.value = responseData;
      } catch (error) {
        console.error('Failed to fetch auth settings:', error);
      }
    };

    const copyToClipboard = async (ips) => {
      const proxyUrl = auth.value.auth_enabled
        ? `http://${auth.value.username}:${auth.value.password}@${ips}:8899`
        : `http://${ips}:8899`;
      
      await navigator.clipboard.writeText(proxyUrl);
      toast.show('Proxy address copied to clipboard', {
        title: 'Copied!',
        variant: 'success',
        placement: 'bottom-right',
        solid: true,
      });
    };

    onMounted(() => {
      setInterval(() => {
        getName();
        listremoveProxy();
      }, 3000);
    });

    onBeforeMount(() => {
      getName();
      listremoveProxy();
      getAuthSettings();
    });

    return {
      data,
      listremove_data,
      auth,
      sortedProviderInstances,
      formatProviderName,
      getProviderIcon,
      removeProxy,
      updateProvider,
      makeToast,
      copyToClipboard
    };
  }
};
</script>

<style>
.provider-section {
  border-bottom: 1px solid var(--border-color);
}

.provider-section:last-child {
  border-bottom: none;
}

.provider-header {
  padding: 1.5rem;
  background-color: #fafafa;
  border-bottom: 1px solid var(--border-color);
}

.provider-icon-wrapper {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--primary-purple);
  color: white;
  border-radius: 8px;
}

h2 {
  font-family: var(--font-family);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-dark);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  background-color: #edf2f7;
  border-radius: 9999px;
  font-size: 0.875rem;
  color: var(--text-gray);
  font-weight: 500;
}

.status-badge.status-active {
  background-color: #c6f6d5;
  color: #2f855a;
}

.custom-spinbutton {
  width: 80px !important;
  text-align: center;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  border-radius: 6px;
}

.proxy-list {
  padding: 1rem;
}

.proxy-item {
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 1rem;
  background-color: white;
}

.proxy-item:last-child {
  margin-bottom: 0;
}

.proxy-status {
  margin-right: 1rem;
}

.status-icon {
  color: #48bb78;
  font-size: 1.25rem;
}

.proxy-ip {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.9375rem;
  color: var(--text-dark);
}

.copy-btn {
  padding: 0.25rem 0.5rem;
  color: var(--text-gray);
}

.copy-btn:hover {
  color: var(--primary-purple);
}

.region-indicator {
  color: var(--text-gray);
  font-size: 0.8125rem;
}

.remove-btn {
  font-size: 0.875rem;
}

.progress-item {
  padding: 1rem;
  background-color: #f7fafc;
  border-radius: 8px;
  margin-top: 1rem;
}

.text-purple {
  color: var(--primary-purple);
}

.custom-progress {
  background-color: #e2e8f0;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-bar {
  background-color: var(--primary-purple);
  transition: width 0.3s ease;
}

.empty-state {
  padding: 2rem;
  background-color: #f7fafc;
  border-radius: 8px;
  color: var(--text-gray);
}
</style>
