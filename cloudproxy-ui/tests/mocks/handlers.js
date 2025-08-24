import { http, HttpResponse } from 'msw';

// Default mock data
export const mockProviders = {
  providers: {
    digitalocean: {
      instances: {
        default: {
          enabled: true,
          display_name: 'DigitalOcean Main',
          ips: ['192.168.1.1', '192.168.1.2'],
          scaling: { min_scaling: 2, max_scaling: 2 },
          region: 'nyc1'
        }
      }
    },
    aws: {
      instances: {
        default: {
          enabled: true,
          display_name: null,
          ips: ['10.0.0.1'],
          scaling: { min_scaling: 1, max_scaling: 1 },
          zone: 'us-east-1'
        }
      }
    },
    gcp: {
      instances: {
        default: {
          enabled: false,
          display_name: null,
          ips: [],
          scaling: { min_scaling: 0, max_scaling: 0 },
          location: 'us-central1'
        }
      }
    }
  }
};

export const mockRollingConfig = {
  config: {
    enabled: false,
    min_available: 3,
    batch_size: 2
  },
  status: {
    'digitalocean/default': {
      recycling: 0,
      pending_recycle: 0,
      recycling_ips: [],
      pending_recycle_ips: []
    }
  }
};

export const mockAuth = {
  username: 'admin',
  password: 'secretpass',
  auth_enabled: true
};

export const mockDestroyQueue = {
  proxies: []
};

// Request handlers
export const handlers = [
  // Get providers list
  http.get('/providers', () => {
    return HttpResponse.json(mockProviders);
  }),

  // Update provider configuration
  http.patch('/providers/:provider', async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json({
      message: `Provider ${params.provider} updated successfully`,
      ...body
    });
  }),

  // Update provider instance configuration
  http.patch('/providers/:provider/:instance', async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json({
      message: `Provider ${params.provider}/${params.instance} updated successfully`,
      ...body
    });
  }),

  // Get rolling deployment configuration
  http.get('/rolling', () => {
    return HttpResponse.json(mockRollingConfig);
  }),

  // Update rolling deployment configuration
  http.patch('/rolling', async ({ request }) => {
    const body = await request.json();
    mockRollingConfig.config = { ...mockRollingConfig.config, ...body };
    return HttpResponse.json({
      message: 'Rolling deployment configuration updated',
      config: mockRollingConfig.config
    });
  }),

  // Get authentication settings
  http.get('/auth', () => {
    return HttpResponse.json(mockAuth);
  }),

  // Get destroy queue
  http.get('/destroy', () => {
    return HttpResponse.json(mockDestroyQueue);
  }),

  // Destroy a proxy
  http.delete('/destroy', ({ request }) => {
    const url = new URL(request.url);
    const ipAddress = url.searchParams.get('ip_address');
    
    // Add to destroy queue
    mockDestroyQueue.proxies.push({ ip: ipAddress });
    
    return HttpResponse.json({
      message: `Proxy ${ipAddress} scheduled for removal`
    });
  })
];

// Error handlers for testing error scenarios
export const errorHandlers = {
  providersError: http.get('/providers', () => {
    return new HttpResponse(null, { status: 500 });
  }),
  
  rollingError: http.get('/rolling', () => {
    return new HttpResponse(null, { status: 500 });
  }),
  
  updateError: http.patch('/providers/:provider', () => {
    return new HttpResponse(null, { status: 400 });
  }),
  
  destroyError: http.delete('/destroy', () => {
    return new HttpResponse(null, { status: 500 });
  })
};