# Hetzner Configuration

To use Hetzner as a provider, you’ll first need to generate an API token.

## Steps

1. Login to your Hetzner Cloud account.
2. Select a project, then on the left sidebar, select 'Security'.
3. In the Security section, select 'API Tokens' on the top menu bar, click the Generate API Token button. This opens an API token window.
4. Enter a token name, this can be anything, I recommend 'CloudProxy' so you know what it is being used for.
5. Select 'Read & Write', write permission is needed so CloudProxy can provision instances.
6. When you click 'Generate API Token', your token is generated and presented to you. Be sure to record your API token. For security purposes, it will not be shown again.

Now you have your token, you can now use Hetzner as a proxy provider, on this page you can see how to set it is an environment variable. 

## Configuration options
### Environment variables: 
#### Required:
`` HETZNER_ENABLED`` - to enable Hetzner as a provider, set as True. Default value: False

`` HETZNER_ACCESS_TOKEN`` - the token to allow CloudProxy access to your account. 

#### Optional:
``HETZNER_MIN_SCALING`` - this is the minimal proxies you required to be provisioned. Default value: 2

``HETZNER_MAX_SCALING`` - this is currently unused, however will be when autoscaling is implemented. We recommend you set this as the same as the minimum scaling to avoid future issues for now. Default value: 2

``HETZNER_SIZE``  - this sets the instance size, we recommend the smallest instance as the volume even a small instance can handle is high. Default value: cx11

``HETZNER_LOCATION`` - this sets the location where the instance is deployed. Some websites may redirect to the language of the country your IP is from. Default value: nbg1
