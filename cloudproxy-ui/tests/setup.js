import { config } from '@vue/test-utils';
import { vi } from 'vitest';

// Create a global mock toast that can be shared
const globalMockToast = {
  show: vi.fn()
};

// Mock Bootstrap Vue Next toast
vi.mock('bootstrap-vue-next', () => ({
  useToast: () => globalMockToast
}));

// Export for use in tests
export { globalMockToast };

// Mock navigator.clipboard
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: vi.fn(() => Promise.resolve())
  },
  writable: true
});

// Global test configuration
config.global.stubs = {
  // Stub any global components if needed
};

config.global.mocks = {
  // Add global mocks if needed
};

// Add global directives
config.global.directives = {
  tooltip: {
    mounted(el, binding) {
      el.setAttribute('data-tooltip', binding.value);
    }
  }
};

// Mock fetch globally
global.fetch = vi.fn();