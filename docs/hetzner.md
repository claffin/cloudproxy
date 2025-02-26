# Hetzner Configuration

To use Hetzner as a provider, you'll need to generate an API token.

## Steps

1. Login to your [Hetzner Cloud Console](https://console.hetzner.cloud/).
2. Select your project (or create a new one).
3. Go to Security > API Tokens.
4. Click "Generate API Token".
5. Enter a token name (e.g., "CloudProxy").
6. Select "Read & Write" for the permission.
7. Click "Generate API Token".
8. Copy the token immediately (it will only be displayed once).

Now you have your token, you can use Hetzner as a proxy provider by configuring the environment variables as shown below.

## Configuration options
### Environment variables:
#### Required:
``HETZNER_ENABLED`` - to enable Hetzner as a provider, set as True. Default value: False

``HETZNER_API_TOKEN`` - the API token to allow CloudProxy access to your account.

#### Optional:
``HETZNER_MIN_SCALING`` - the minimum number of proxies to provision. Default value: 2

``HETZNER_MAX_SCALING`` - currently unused, but will be when autoscaling is implemented. We recommend you set this to the same value as the minimum scaling to avoid future issues. Default value: 2

``HETZNER_SIZE`` - the server type to use. Default value: cx11 (the smallest available server type)

``HETZNER_LOCATION`` - the location where the server will be deployed. Default value: nbg1 (Nuremberg, Germany)

``HETZNER_DATACENTER`` - alternatively, you can specify a specific datacenter rather than just a location. Note that a datacenter value will override the location setting.

## Multi-Account Support

CloudProxy supports running multiple Hetzner accounts simultaneously. Each account is configured as a separate "instance" with its own settings.

### Default Instance Configuration

The configuration variables mentioned above configure the "default" instance. For example:

```
HETZNER_ENABLED=True
HETZNER_API_TOKEN=your_default_token
HETZNER_LOCATION=nbg1
HETZNER_MIN_SCALING=2
```

### Additional Instances Configuration

To configure additional Hetzner accounts, use the following format:
```
HETZNER_INSTANCENAME_VARIABLE=VALUE
```

For example, to add a second Hetzner account in a different location:

```
HETZNER_FINLAND_ENABLED=True
HETZNER_FINLAND_API_TOKEN=your_second_token
HETZNER_FINLAND_LOCATION=hel1
HETZNER_FINLAND_MIN_SCALING=3
HETZNER_FINLAND_SIZE=cx11
HETZNER_FINLAND_DISPLAY_NAME=Finland Hetzner Account
```

### Available instance-specific configurations

For each instance, you can configure:

#### Required for each instance:
- `HETZNER_INSTANCENAME_ENABLED` - to enable this specific instance
- `HETZNER_INSTANCENAME_API_TOKEN` - the API token for this instance

#### Optional for each instance:
- `HETZNER_INSTANCENAME_MIN_SCALING` - minimum number of proxies for this instance
- `HETZNER_INSTANCENAME_MAX_SCALING` - maximum number of proxies for this instance
- `HETZNER_INSTANCENAME_SIZE` - server type for this instance
- `HETZNER_INSTANCENAME_LOCATION` - location for this instance
- `HETZNER_INSTANCENAME_DATACENTER` - datacenter for this instance (overrides location)
- `HETZNER_INSTANCENAME_DISPLAY_NAME` - a friendly name for the instance that will appear in the UI

Each instance operates independently, maintaining its own pool of proxies according to its configuration.
