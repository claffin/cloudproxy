<template>
  <div class="provider-section rolling-deployment-section">
    <div class="provider-header">
      <div class="d-flex align-items-center justify-content-between">
        <div class="d-flex align-items-center">
          <div class="provider-icon-wrapper me-2">
            <i
              class="bi bi-arrow-repeat provider-icon"
              style="font-size: 1.5rem;"
            />
          </div>
          <h2 class="mb-0">
            Rolling Deployment
          </h2>
        </div>
        <div class="d-flex align-items-center">
          <span
            v-if="config.enabled"
            class="status-badge status-active me-3"
          >
            <i class="bi bi-check-circle me-1" />
            Active
          </span>
          <span
            v-else
            class="status-badge me-3"
          >
            <i class="bi bi-x-circle me-1" />
            Inactive
          </span>
          <button
            class="btn btn-link text-secondary p-0"
            type="button"
            @click="toggleExpanded"
          >
            <i :class="expanded ? 'bi-chevron-up' : 'bi-chevron-down'" />
          </button>
        </div>
      </div>
    </div>
    
    <div
      v-if="expanded"
      class="rolling-config-body"
    >
      <div class="row align-items-end">
        <div class="col-md-3">
          <div class="form-check form-switch">
            <input
              id="rollingEnabled"
              v-model="config.enabled"
              class="form-check-input"
              type="checkbox"
              @change="checkChanges"
            >
            <label
              class="form-check-label"
              for="rollingEnabled"
            >
              Enable Rolling Deployments
            </label>
          </div>
          <small class="text-muted d-block mt-1">
            Ensure zero-downtime during proxy recycling
          </small>
        </div>
        
        <div class="col-md-3">
          <div class="config-group">
            <label
              for="minAvailable"
              class="form-label small text-muted mb-1"
            >
              <i class="bi bi-shield-check me-1" />
              Minimum Available
            </label>
            <div class="input-group input-group-sm">
              <input
                id="minAvailable"
                v-model.number="config.min_available"
                v-tooltip="'Minimum number of healthy proxies to maintain during recycling'"
                type="number"
                min="1"
                max="100"
                class="form-control custom-input"
                :disabled="!config.enabled"
                @input="checkChanges"
              >
              <span class="input-group-text">proxies</span>
            </div>
          </div>
        </div>
        
        <div class="col-md-3">
          <div class="config-group">
            <label
              for="batchSize"
              class="form-label small text-muted mb-1"
            >
              <i class="bi bi-collection me-1" />
              Batch Size
            </label>
            <div class="input-group input-group-sm">
              <input
                id="batchSize"
                v-model.number="config.batch_size"
                v-tooltip="'Maximum number of proxies to recycle simultaneously'"
                type="number"
                min="1"
                max="50"
                class="form-control custom-input"
                :disabled="!config.enabled"
                @input="checkChanges"
              >
              <span class="input-group-text">at once</span>
            </div>
          </div>
        </div>
        
        <div class="col-md-3">
          <div class="d-flex justify-content-end">
            <button
              v-if="hasChanges"
              class="btn btn-sm btn-primary me-2"
              @click="updateConfig"
            >
              <i class="bi bi-check me-1" />
              Apply Changes
            </button>
            <button
              v-tooltip="'Refresh configuration'"
              class="btn btn-sm btn-outline-secondary"
              @click="fetchConfig"
            >
              <i class="bi bi-arrow-clockwise" />
            </button>
          </div>
        </div>
      </div>
      
      <div
        v-if="status"
        class="mt-3"
      >
        <div class="rolling-status-info">
          <small class="text-muted">
            <i class="bi bi-info-circle me-1" />
            Rolling deployment status across all providers
          </small>
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
    const originalConfig = ref({
      enabled: false,
      min_available: 3,
      batch_size: 2
    });
    const status = ref(null);
    const hasChanges = ref(false);

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
        config.value = { ...data.config };
        originalConfig.value = { ...data.config };
        status.value = data.status;
        hasChanges.value = false;
      } catch (error) {
        toast.show('Failed to fetch rolling deployment configuration', {
          title: 'Error',
          variant: 'danger',
          placement: 'bottom-right',
          solid: true,
        });
      }
    };

    const checkChanges = () => {
      hasChanges.value = JSON.stringify(config.value) !== JSON.stringify(originalConfig.value);
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
          originalConfig.value = { ...config.value };
          hasChanges.value = false;
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
      fetchConfig();
    });

    return {
      expanded,
      config,
      status,
      hasChanges,
      toggleExpanded,
      updateConfig,
      fetchConfig,
      checkChanges
    };
  }
};
</script>

<style scoped>
.rolling-deployment-section {
  border-bottom: 1px solid var(--border-color);
}

.rolling-deployment-section:first-child {
  border-top: none;
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

.rolling-config-body {
  padding: 1.5rem;
  background-color: white;
}

.config-group {
  margin-bottom: 0;
}

.form-check-input:checked {
  background-color: var(--primary-purple);
  border-color: var(--primary-purple);
}

.form-check-input:focus {
  border-color: var(--primary-purple-light);
  box-shadow: 0 0 0 0.25rem rgba(107, 70, 193, 0.25);
}

.custom-input {
  text-align: center;
  font-size: 0.875rem;
}

.input-group-sm .input-group-text {
  font-size: 0.75rem;
  background-color: #f7fafc;
  border-color: var(--border-color);
  color: var(--text-gray);
}

.rolling-status-info {
  padding: 0.75rem;
  background-color: #f7fafc;
  border-radius: 6px;
}

.btn-link.text-secondary {
  color: var(--text-gray) !important;
}

.btn-link.text-secondary:hover {
  color: var(--text-dark) !important;
}
</style>