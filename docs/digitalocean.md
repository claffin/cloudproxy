# DigitalOcean Configuration

To use DigitalOcean as a provider, you'll first generate a personal access token.

## Steps

1. Login to your DigitalOcean account.
2. Click on [API](https://cloud.digitalocean.com/account/api) on the side menu
3. In the Personal access tokens section, click the Generate New Token button. This opens a New personal access token window:
4. Enter a token name, this can be anything, I recommend 'CloudProxy' so you know what it is being used for.
5. Select read and write scopes, write scope is needed so CloudProxy can provision droplets.
6. When you click Generate Token, your token is generated and presented to you on your Personal Access Tokens page. Be sure to record your personal access token. For security purposes, it will not be shown again.

Now you have your token, you can now use DigitalOcean as a proxy provider, on the main page you can see how to set it is an environment variable. 

## Configuration options
### Environment variables: 
#### Required:
``DIGITALOCEAN_ENABLED`` - to enable DigitalOcean as a provider, set as True. Default value: False

``DIGITALOCEAN_ACCESS_TOKEN`` - the token to allow CloudProxy access to your account. 

``DIGITALOCEAN_REGION`` - this sets the region where the droplet is deployed. Some websites may redirect to the language of the country your IP is from. Default value: lon1

#### Optional:
``DIGITALOCEAN_MIN_SCALING`` - this is the minimal proxies you required to be provisioned. 
Default value: 2

``DIGITALOCEAN_MAX_SCALING`` - this is currently unused, however will be when autoscaling is implemented. We recommend you set this as the same as the minimum scaling to avoid future issues for now. Default value: 2

``DIGITALOCEAN_SIZE``  - this sets the droplet size, we recommend the smallest droplet as the volume even a small droplet can handle is high. Default value: s-1vcpu-1gb

## Multi-Account Support

CloudProxy supports running multiple DigitalOcean accounts simultaneously. Each account is configured as a separate "instance" with its own settings.

### Default Instance Configuration

The configuration variables mentioned above configure the "default" instance. For example:

```
DIGITALOCEAN_ENABLED=True
DIGITALOCEAN_ACCESS_TOKEN=your_default_token
DIGITALOCEAN_REGION=lon1
DIGITALOCEAN_MIN_SCALING=2
```

### Additional Instances Configuration

To configure additional DigitalOcean accounts, use the following format:
```
DIGITALOCEAN_INSTANCENAME_VARIABLE=VALUE
```

For example, to add a second DigitalOcean account with different region settings:

```
DIGITALOCEAN_USEAST_ENABLED=True
DIGITALOCEAN_USEAST_ACCESS_TOKEN=your_second_token
DIGITALOCEAN_USEAST_REGION=nyc1
DIGITALOCEAN_USEAST_MIN_SCALING=3
DIGITALOCEAN_USEAST_SIZE=s-1vcpu-1gb
DIGITALOCEAN_USEAST_DISPLAY_NAME=US East Account
```

### Available instance-specific configurations

For each instance, you can configure:

#### Required for each instance:
- `DIGITALOCEAN_INSTANCENAME_ENABLED` - to enable this specific instance
- `DIGITALOCEAN_INSTANCENAME_ACCESS_TOKEN` - the token for this instance
- `DIGITALOCEAN_INSTANCENAME_REGION` - region for this instance

#### Optional for each instance:
- `DIGITALOCEAN_INSTANCENAME_MIN_SCALING` - minimum number of proxies for this instance
- `DIGITALOCEAN_INSTANCENAME_MAX_SCALING` - maximum number of proxies for this instance
- `DIGITALOCEAN_INSTANCENAME_SIZE` - droplet size for this instance
- `DIGITALOCEAN_INSTANCENAME_DISPLAY_NAME` - a friendly name for the instance that will appear in the UI

Each instance operates independently, maintaining its own pool of proxies according to its configuration.
