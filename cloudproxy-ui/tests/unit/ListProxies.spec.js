import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { nextTick } from 'vue';
import ListProxies from '@/components/ListProxies.vue';
import { globalMockToast } from '../setup';

describe('ListProxies.vue', () => {
  let wrapper;

  const mockProvidersData = {
    providers: {
      digitalocean: {
        instances: {
          default: {
            enabled: true,
            display_name: 'DigitalOcean Main',
            ips: ['192.168.1.1', '192.168.1.2'],
            scaling: { min_scaling: 2, max_scaling: 2 },
            region: 'nyc1'
          },
          secondary: {
            enabled: true,
            display_name: null,
            ips: ['10.0.0.1'],
            scaling: { min_scaling: 1, max_scaling: 1 },
            region: 'sfo3'
          }
        }
      },
      aws: {
        instances: {
          default: {
            enabled: false,
            display_name: null,
            ips: [],
            scaling: { min_scaling: 0, max_scaling: 0 },
            zone: 'us-east-1'
          }
        }
      }
    }
  };

  const mockRollingStatus = {
    status: {
      'digitalocean/default': {
        recycling: 1,
        pending_recycle: 1,
        recycling_ips: ['192.168.1.1'],
        pending_recycle_ips: ['192.168.1.2']
      }
    }
  };

  const mockAuthData = {
    username: 'testuser',
    password: 'testpass',
    auth_enabled: true
  };

  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();

    // Mock fetch responses
    global.fetch = vi.fn((url) => {
      if (url === '/providers') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockProvidersData)
        });
      }
      if (url === '/rolling') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockRollingStatus)
        });
      }
      if (url === '/auth') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAuthData)
        });
      }
      if (url === '/destroy') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ proxies: [] })
        });
      }
      if (url && url.startsWith('/destroy?')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: 'Proxy removed successfully' })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });

    // Mock clipboard
    navigator.clipboard.writeText = vi.fn(() => Promise.resolve());
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
    }
    vi.clearAllMocks();
  });

  it('renders provider sections correctly', async () => {
    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Check provider headers
    const providerSections = wrapper.findAll('.provider-section');
    expect(providerSections.length).toBeGreaterThan(0);

    // Check DigitalOcean section
    const headers = wrapper.findAll('h2');
    expect(headers.some(h => h.text().includes('DigitalOcean'))).toBe(true);
  });

  it('displays correct proxy count and status', async () => {
    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Check active proxy count
    const statusBadges = wrapper.findAll('.status-badge');
    expect(statusBadges.some(badge => badge.text().includes('2 Active'))).toBe(true);
  });

  it('shows proxy IP addresses correctly', async () => {
    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Check proxy IPs are displayed
    const proxyIps = wrapper.findAll('.proxy-ip');
    expect(proxyIps.some(ip => ip.text() === '192.168.1.1')).toBe(true);
    expect(proxyIps.some(ip => ip.text() === '192.168.1.2')).toBe(true);
  });

  it('handles copy to clipboard functionality', async () => {
    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Find and click copy button
    const copyButtons = wrapper.findAll('.copy-btn');
    expect(copyButtons.length).toBeGreaterThan(0);

    await copyButtons[0].trigger('click');
    await nextTick();

    // Check clipboard was called with correct proxy URL
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining('http://testuser:testpass@')
    );

    // Check toast was shown
    expect(globalMockToast.show).toHaveBeenCalledWith(
      expect.stringContaining('copied'),
      expect.any(Object)
    );
  });

  it('handles proxy removal', async () => {
    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Mock successful removal
    global.fetch = vi.fn(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ message: 'Proxy removed successfully' })
      })
    );

    // Find and click remove button
    const removeButtons = wrapper.findAll('.remove-btn');
    expect(removeButtons.length).toBeGreaterThan(0);

    await removeButtons[0].trigger('click');
    await flushPromises();

    // Check API was called
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/destroy?ip_address='),
      expect.objectContaining({ method: 'DELETE' })
    );

    // Check success toast
    expect(globalMockToast.show).toHaveBeenCalled();
  });

  it('updates provider scaling', async () => {
    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Mock successful update
    global.fetch = vi.fn(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ message: 'Provider updated' })
      })
    );

    // Find scaling input
    const scalingInputs = wrapper.findAll('.custom-spinbutton');
    expect(scalingInputs.length).toBeGreaterThan(0);

    // Change value and trigger change event
    await scalingInputs[0].setValue(5);
    await scalingInputs[0].trigger('change');
    await flushPromises();

    // Check API was called
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/providers/'),
      expect.objectContaining({
        method: 'PATCH',
        body: expect.stringContaining('"min_scaling":5')
      })
    );
  });

  it('displays rolling deployment status correctly', async () => {
    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Check for rolling status indicators
    const statusBadges = wrapper.findAll('.badge');
    expect(statusBadges.some(badge => badge.text() === 'Recycling')).toBe(true);
    expect(statusBadges.some(badge => badge.text() === 'Pending Recycle')).toBe(true);
  });

  it('shows empty state when provider is disabled', async () => {
    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Check for disabled provider empty state
    const emptyStates = wrapper.findAll('.empty-state');
    expect(emptyStates.some(state => 
      state.text().includes('Provider not enabled')
    )).toBe(true);
  });

  it('shows progress bar when scaling up', async () => {
    // Modify mock data to show scaling in progress
    const scalingData = {
      providers: {
        digitalocean: {
          instances: {
            default: {
              enabled: true,
              ips: ['192.168.1.1'],
              scaling: { min_scaling: 3, max_scaling: 3 },
              region: 'nyc1'
            }
          }
        }
      }
    };

    global.fetch = vi.fn((url) => {
      if (url === '/providers') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(scalingData)
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });

    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Check for progress indicator
    const progressItems = wrapper.findAll('.progress-item');
    expect(progressItems.length).toBeGreaterThan(0);
    expect(wrapper.text()).toContain('Deploying new proxies');
  });

  it('formats provider names correctly', async () => {
    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Check formatted names
    expect(wrapper.text()).toContain('DigitalOcean Main'); // Uses display_name
    expect(wrapper.text()).toContain('DigitalOcean (secondary)'); // Falls back to formatted name
  });

  it('displays correct provider icons', async () => {
    wrapper = mount(ListProxies);

    await flushPromises();
    await nextTick();

    // Check for provider-specific icons
    const icons = wrapper.findAll('.provider-icon');
    expect(icons.length).toBeGreaterThan(0);
    
    // Check DigitalOcean has water icon
    expect(wrapper.find('.bi-water').exists()).toBe(true);
  });

  it('handles auto-refresh with interval', async () => {
    vi.useFakeTimers();

    wrapper = mount(ListProxies);

    await flushPromises();

    // Initial calls
    expect(global.fetch).toHaveBeenCalledWith('/providers');

    // Advance timer by 3 seconds
    vi.advanceTimersByTime(3000);
    await flushPromises();

    // Check fetch was called again
    expect(global.fetch).toHaveBeenCalledWith('/providers');
    expect(global.fetch).toHaveBeenCalledWith('/destroy');

    vi.useRealTimers();
  });
});