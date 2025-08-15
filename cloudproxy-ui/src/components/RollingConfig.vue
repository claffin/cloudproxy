<template>
  <div class="rolling-config-panel">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
          <i class="bi bi-arrow-repeat me-2" />
          Rolling Deployment Configuration
        </h5>
        <button
          class="btn btn-sm btn-link"
          type="button"
          @click="toggleExpanded"
        >
          <i :class="expanded ? 'bi-chevron-up' : 'bi-chevron-down'" />
        </button>
      </div>
      
      <div
        v-if="expanded"
        class="card-body"
      >
        <div class="row">
          <div class="col-md-4">
            <div class="form-check form-switch mb-3">
              <input
                id="rollingEnabled"
                v-model="config.enabled"
                class="form-check-input"
                type="checkbox"
                @change="updateConfig"
              >
              <label
                class="form-check-label"
                for="rollingEnabled"
              >
                Enable Rolling Deployments
              </label>
            </div>
          </div>
          
          <div class="col-md-4">
            <div class="mb-3">
              <label
                for="minAvailable"
                class="form-label"
              >
                Minimum Available Proxies
              </label>
              <input
                id="minAvailable"
                v-model.number="config.min_available"
                v-tooltip="'Minimum number of healthy proxies to maintain during recycling'"
                type="number"
                min="1"
                max="100"
                class="form-control"
                :disabled="!config.enabled"
                @change="updateConfig"
              >
            </div>
          </div>
          
          <div class="col-md-4">
            <div class="mb-3">
              <label
                for="batchSize"
                class="form-label"
              >
                Batch Size
              </label>
              <input
                id="batchSize"
                v-model.number="config.batch_size"
                v-tooltip="'Maximum number of proxies to recycle simultaneously'"
                type="number"
                min="1"
                max="50"
                class="form-control"
                :disabled="!config.enabled"
                @change="updateConfig"
              >
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useToast } from 'bootstrap-vue-next';

export default {
  name: 'RollingConfig',
  setup() {
    const toast = useToast();
    const expanded = ref(false);
    const config = ref({
      enabled: false,
      min_available: 3,
      batch_size: 2
    });

    const toggleExpanded = () => {
      expanded.value = !expanded.value;
      if (expanded.value) {
        fetchConfig();
      }
    };

    const fetchConfig = async () => {
      try {
        const response = await fetch('/rolling');
        const data = await response.json();
        config.value = data.config;
      } catch (error) {
        toast.show('Failed to fetch rolling deployment configuration', {
          title: 'Error',
          variant: 'danger',
          placement: 'bottom-right',
          solid: true,
        });
      }
    };

    const updateConfig = async () => {
      try {
        const response = await fetch('/rolling', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(config.value)
        });
        
        if (response.ok) {
          toast.show('Rolling deployment configuration updated', {
            title: 'Success',
            variant: 'success',
            placement: 'bottom-right',
            solid: true,
          });
        } else {
          throw new Error('Failed to update configuration');
        }
      } catch (error) {
        toast.show('Failed to update rolling deployment configuration', {
          title: 'Error',
          variant: 'danger',
          placement: 'bottom-right',
          solid: true,
        });
      }
    };

    onMounted(() => {
      // Optionally fetch configuration on mount
      // fetchConfig();
    });

    return {
      expanded,
      config,
      toggleExpanded,
      updateConfig,
      fetchConfig
    };
  }
};
</script>

<style scoped>
.rolling-config-panel {
  margin-bottom: 1rem;
}

.form-check-input:checked {
  background-color: #28a745;
  border-color: #28a745;
}
</style>