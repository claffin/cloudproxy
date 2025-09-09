import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import App from '@/App.vue';
import ListProxies from '@/components/ListProxies.vue';
import RollingConfig from '@/components/RollingConfig.vue';

describe('App.vue', () => {
  let wrapper;

  beforeEach(() => {
    // Reset window.location.reload mock
    delete window.location;
    window.location = { reload: vi.fn() };
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
    }
  });

  it('renders the application correctly', () => {
    wrapper = mount(App, {
      global: {
        stubs: {
          ListProxies: true,
          RollingConfig: true
        }
      }
    });

    // Check navbar
    expect(wrapper.find('.navbar').exists()).toBe(true);
    expect(wrapper.find('.navbar-brand').text()).toBe('CloudProxy');

    // Check header
    expect(wrapper.find('h1').text()).toBe('Proxy Management');

    // Check main components are rendered
    expect(wrapper.findComponent(ListProxies).exists()).toBe(true);
    expect(wrapper.findComponent(RollingConfig).exists()).toBe(true);
  });

  it('has API docs link that opens in new tab', () => {
    wrapper = mount(App, {
      global: {
        stubs: {
          ListProxies: true,
          RollingConfig: true
        }
      }
    });

    const apiDocsLink = wrapper.find('a[href="/docs"]');
    expect(apiDocsLink.exists()).toBe(true);
    expect(apiDocsLink.attributes('target')).toBe('_blank');
    expect(apiDocsLink.text()).toContain('API Docs');
  });

  it('has refresh button that reloads the page', async () => {
    wrapper = mount(App, {
      global: {
        stubs: {
          ListProxies: true,
          RollingConfig: true
        }
      }
    });

    const refreshButton = wrapper.find('button[type="button"]');
    expect(refreshButton.exists()).toBe(true);
    expect(refreshButton.text()).toContain('Refresh');

    await refreshButton.trigger('click');
    expect(window.location.reload).toHaveBeenCalled();
  });

  it('applies correct CSS classes and structure', () => {
    wrapper = mount(App, {
      global: {
        stubs: {
          ListProxies: true,
          RollingConfig: true
        }
      }
    });

    // Check structure
    expect(wrapper.find('#app').exists()).toBe(true);
    expect(wrapper.find('.header-extension').exists()).toBe(true);
    expect(wrapper.find('.container').exists()).toBe(true);
    expect(wrapper.find('.main-card').exists()).toBe(true);
  });

  it('displays icons correctly', () => {
    wrapper = mount(App, {
      global: {
        stubs: {
          ListProxies: true,
          RollingConfig: true
        }
      }
    });

    // Check for Bootstrap icons
    expect(wrapper.find('.bi-file-text').exists()).toBe(true); // API Docs icon
    expect(wrapper.find('.bi-arrow-clockwise').exists()).toBe(true); // Refresh icon
  });

  it('has proper component hierarchy', () => {
    wrapper = mount(App, {
      global: {
        stubs: {
          ListProxies: true,
          RollingConfig: true
        }
      }
    });

    // RollingConfig should be in the last container (there are multiple containers)
    const containers = wrapper.findAll('.container');
    const mainContainer = containers[containers.length - 1]; // Get the last container
    expect(mainContainer.findComponent(RollingConfig).exists()).toBe(true);

    // ListProxies should be inside the main card
    const mainCard = wrapper.find('.main-card');
    expect(mainCard.findComponent(ListProxies).exists()).toBe(true);
  });
});