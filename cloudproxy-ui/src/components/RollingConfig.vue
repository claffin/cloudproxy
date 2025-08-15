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
        
        <!-- Rolling Status Section -->
        <div
          v-if="status && Object.keys(status).length > 0"
          class="rolling-status mt-3"
        >
          <h6 class="text-muted mb-2">
            Current Status
          </h6>
          <div class="row">
            <div
              v-for="(providerStatus, providerKey) in status"
              :key="providerKey"
              class="col-md-6 mb-2"
            >
              <div class="status-card p-2 border rounded">
                <div class="d-flex justify-content-between align-items-center">
                  <strong>{{ providerKey }}</strong>
                  <div class="status-badges">
                    <span
                      v-if="providerStatus.healthy > 0"
                      class="badge bg-success me-1"
                    >
                      {{ providerStatus.healthy }} healthy
                    </span>
                    <span
                      v-if="providerStatus.pending_recycle > 0"
                      class="badge bg-warning me-1"
                    >
                      {{ providerStatus.pending_recycle }} pending
                    </span>
                    <span
                      v-if="providerStatus.recycling > 0"
                      class="badge bg-danger"
                    >
                      {{ providerStatus.recycling }} recycling
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div
          v-else-if="config.enabled"
          class="text-muted text-center py-3"
        >
          No active rolling deployments
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
    const status = ref({});

    const toggleExpanded = () => {
      expanded.value = !expanded.value;
      if (expanded.value) {
        fetchRollingStatus();
      }
    };

    const fetchRollingStatus = async () => {
      try {
        const response = await fetch('/rolling');
        const data = await response.json();
        config.value = data.config;
        status.value = data.status;
      } catch (error) {
        toast.show('Failed to fetch rolling deployment status', {
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
          const data = await response.json();
          status.value = data.status;
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
      // Optionally fetch status on mount if you want it visible by default
      // fetchRollingStatus();
    });

    return {
      expanded,
      config,
      status,
      toggleExpanded,
      updateConfig,
      fetchRollingStatus
    };
  }
};
</script>

<style scoped>
.rolling-config-panel {
  margin-bottom: 1rem;
}

.status-card {
  background-color: #f8f9fa;
}

.status-badges {
  display: flex;
  gap: 0.25rem;
}

.form-check-input:checked {
  background-color: #28a745;
  border-color: #28a745;
}
</style>