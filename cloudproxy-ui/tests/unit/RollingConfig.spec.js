import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { nextTick } from 'vue';
import RollingConfig from '@/components/RollingConfig.vue';
import { globalMockToast } from '../setup';

describe('RollingConfig.vue', () => {
  let wrapper;

  const mockConfigData = {
    config: {
      enabled: true,
      min_available: 3,
      batch_size: 2
    },
    status: {
      'digitalocean/default': {
        recycling: 1,
        pending_recycle: 2
      }
    }
  };

  beforeEach(() => {
    // Clear mock before each test
    vi.clearAllMocks();

    // Mock fetch
    global.fetch = vi.fn(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockConfigData)
      })
    );
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
    }
    vi.clearAllMocks();
  });

  it('renders collapsed state by default', () => {
    wrapper = mount(RollingConfig);

    // Check header is visible
    expect(wrapper.find('.card-header').exists()).toBe(true);
    expect(wrapper.find('h5').text()).toContain('Rolling Deployment Configuration');

    // Check body is not visible
    expect(wrapper.find('.card-body').exists()).toBe(false);

    // Check chevron icon is down
    expect(wrapper.find('.bi-chevron-down').exists()).toBe(true);
  });

  it('expands and collapses on toggle button click', async () => {
    wrapper = mount(RollingConfig);

    const toggleButton = wrapper.find('button.btn-link');
    
    // Click to expand
    await toggleButton.trigger('click');
    await nextTick();

    // Check expanded state
    expect(wrapper.find('.card-body').exists()).toBe(true);
    expect(wrapper.find('.bi-chevron-up').exists()).toBe(true);

    // Click to collapse
    await toggleButton.trigger('click');
    await nextTick();

    // Check collapsed state
    expect(wrapper.find('.card-body').exists()).toBe(false);
    expect(wrapper.find('.bi-chevron-down').exists()).toBe(true);
  });

  it('fetches configuration when expanded', async () => {
    wrapper = mount(RollingConfig);

    // Initially no fetch
    expect(global.fetch).not.toHaveBeenCalled();

    // Click to expand
    await wrapper.find('button.btn-link').trigger('click');
    await flushPromises();

    // Check fetch was called
    expect(global.fetch).toHaveBeenCalledWith('/rolling');
  });

  it('displays configuration values correctly', async () => {
    wrapper = mount(RollingConfig);

    // Expand the panel
    await wrapper.find('button.btn-link').trigger('click');
    await flushPromises();
    await nextTick();

    // Check enabled checkbox
    const enabledCheckbox = wrapper.find('#rollingEnabled');
    expect(enabledCheckbox.element.checked).toBe(true);

    // Check min_available input
    const minAvailableInput = wrapper.find('#minAvailable');
    expect(minAvailableInput.element.value).toBe('3');

    // Check batch_size input
    const batchSizeInput = wrapper.find('#batchSize');
    expect(batchSizeInput.element.value).toBe('2');
  });

  it('updates configuration on checkbox change', async () => {
    wrapper = mount(RollingConfig);

    // Expand and wait for initial fetch
    await wrapper.find('button.btn-link').trigger('click');
    await flushPromises();
    await nextTick();

    // Mock successful update
    global.fetch = vi.fn(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ message: 'Configuration updated' })
      })
    );

    // Toggle the enabled checkbox
    const enabledCheckbox = wrapper.find('#rollingEnabled');
    await enabledCheckbox.setValue(false);
    await enabledCheckbox.trigger('change');
    await flushPromises();

    // Check API was called with correct data
    expect(global.fetch).toHaveBeenCalledWith('/rolling', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        enabled: false,
        min_available: 3,
        batch_size: 2
      })
    });

    // Check success toast
    expect(globalMockToast.show).toHaveBeenCalledWith(
      'Rolling deployment configuration updated',
      expect.objectContaining({ variant: 'success' })
    );
  });

  it('updates configuration on input change', async () => {
    // Mock initial config fetch with specific values
    global.fetch = vi.fn(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          config: {
            enabled: true,
            min_available: 3,
            batch_size: 2
          }
        })
      })
    );

    wrapper = mount(RollingConfig);

    // Expand and wait for initial fetch
    await wrapper.find('button.btn-link').trigger('click');
    await flushPromises();
    await nextTick();

    // Mock successful update
    global.fetch = vi.fn(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ message: 'Configuration updated' })
      })
    );

    // Find and change the min_available input
    const minAvailableInput = wrapper.find('#minAvailable');
    
    // Set new value and trigger change
    await minAvailableInput.setValue(5);
    await minAvailableInput.trigger('change');
    await flushPromises();
    await nextTick();

    // Check API was called with updated value
    expect(global.fetch).toHaveBeenCalledWith('/rolling', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        enabled: true,
        min_available: 5,
        batch_size: 2
      })
    });
  });

  it('disables inputs when rolling deployment is disabled', async () => {
    // Mock config with disabled state
    global.fetch = vi.fn(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          config: {
            enabled: false,
            min_available: 3,
            batch_size: 2
          }
        })
      })
    );

    wrapper = mount(RollingConfig);

    // Expand the panel
    await wrapper.find('button.btn-link').trigger('click');
    await flushPromises();
    await nextTick();

    // Check inputs are disabled
    const minAvailableInput = wrapper.find('#minAvailable');
    const batchSizeInput = wrapper.find('#batchSize');

    expect(minAvailableInput.element.disabled).toBe(true);
    expect(batchSizeInput.element.disabled).toBe(true);
  });

  it('validates input ranges', async () => {
    wrapper = mount(RollingConfig);

    // Expand the panel
    await wrapper.find('button.btn-link').trigger('click');
    await flushPromises();
    await nextTick();

    // Check min_available input attributes
    const minAvailableInput = wrapper.find('#minAvailable');
    expect(minAvailableInput.attributes('min')).toBe('1');
    expect(minAvailableInput.attributes('max')).toBe('100');
    expect(minAvailableInput.attributes('type')).toBe('number');

    // Check batch_size input attributes
    const batchSizeInput = wrapper.find('#batchSize');
    expect(batchSizeInput.attributes('min')).toBe('1');
    expect(batchSizeInput.attributes('max')).toBe('50');
    expect(batchSizeInput.attributes('type')).toBe('number');
  });

  it('handles API errors gracefully', async () => {
    wrapper = mount(RollingConfig);

    // Mock fetch failure
    global.fetch = vi.fn(() => Promise.reject(new Error('Network error')));

    // Expand the panel (triggers fetch)
    await wrapper.find('button.btn-link').trigger('click');
    await flushPromises();

    // Check error toast was shown
    expect(globalMockToast.show).toHaveBeenCalledWith(
      'Failed to fetch rolling deployment configuration',
      expect.objectContaining({ variant: 'danger' })
    );
  });

  it('handles update failures gracefully', async () => {
    wrapper = mount(RollingConfig);

    // Expand and wait for initial fetch
    await wrapper.find('button.btn-link').trigger('click');
    await flushPromises();
    await nextTick();

    // Mock failed update
    global.fetch = vi.fn(() => 
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ error: 'Update failed' })
      })
    );

    // Try to update
    const enabledCheckbox = wrapper.find('#rollingEnabled');
    await enabledCheckbox.setValue(false);
    await enabledCheckbox.trigger('change');
    await flushPromises();

    // Check error toast was shown
    expect(globalMockToast.show).toHaveBeenCalledWith(
      'Failed to update rolling deployment configuration',
      expect.objectContaining({ variant: 'danger' })
    );
  });

  it('displays tooltips on inputs', async () => {
    wrapper = mount(RollingConfig);

    // Expand the panel
    await wrapper.find('button.btn-link').trigger('click');
    await flushPromises();
    await nextTick();

    // Check tooltips exist
    const minAvailableInput = wrapper.find('#minAvailable');
    const batchSizeInput = wrapper.find('#batchSize');

    expect(minAvailableInput.attributes('data-tooltip')).toContain('Minimum number of healthy proxies');
    expect(batchSizeInput.attributes('data-tooltip')).toContain('Maximum number of proxies to recycle');
  });

  it('has proper styling classes', () => {
    wrapper = mount(RollingConfig);

    // Check main structure classes
    expect(wrapper.find('.rolling-config-panel').exists()).toBe(true);
    expect(wrapper.find('.card').exists()).toBe(true);
    expect(wrapper.find('.card-header').exists()).toBe(true);

    // Check icon
    expect(wrapper.find('.bi-arrow-repeat').exists()).toBe(true);
  });
});