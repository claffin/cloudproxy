# Scaleway Configuration

To use Scaleway as a provider, you'll need to generate an API token for authentication.

## Steps

1. Login to your Scaleway console.
2. Go to your profile settings by clicking on your username in the top right corner.
3. Navigate to the "Credentials" section.
4. In the "API Keys" section, click "Generate New API Key".
5. Give your key a name (e.g., "CloudProxy") and click "Generate API Key".
6. Copy the secret key that is displayed. This is shown only once, so make sure to save it securely.

Now you have your API token, you can use Scaleway as a proxy provider. Set up the environment variables as shown below:

## Configuration options
### Environment variables:
#### Required:
``SCALEWAY_ENABLED`` - to enable Scaleway as a provider, set as True. Default value: False

``SCALEWAY_AUTH_TOKEN`` - the authentication token to allow CloudProxy access to your account.

``SCALEWAY_REGION`` - this sets the region where the instance is deployed. Default value: fr-par-1

#### Optional:
``SCALEWAY_ORGANIZATION`` - the Scaleway organization ID (required if you have multiple organizations)

``SCALEWAY_MIN_SCALING`` - the minimum number of proxies to provision. Default value: 2

``SCALEWAY_MAX_SCALING`` - currently unused, but will be when autoscaling is implemented. We recommend you set this to the same value as the minimum scaling to avoid future issues. Default value: 2

``SCALEWAY_SIZE`` - this sets the instance type for Scaleway. Default value: DEV1-S

``SCALEWAY_IMAGE`` - this sets the image to use for Scaleway instances. Default value: ubuntu_focal

## Multi-Account Support

CloudProxy supports running multiple Scaleway accounts simultaneously. Each account is configured as a separate "instance" with its own settings.

### Default Instance Configuration

The configuration variables mentioned above configure the "default" instance. For example:

```
SCALEWAY_ENABLED=True
SCALEWAY_AUTH_TOKEN=your_token
SCALEWAY_REGION=fr-par-1
SCALEWAY_MIN_SCALING=2
```

### Additional Instances Configuration

To configure additional Scaleway accounts, use the following format:
```
SCALEWAY_INSTANCENAME_VARIABLE=VALUE
```

For example, to add a second Scaleway account in a different region:

```
SCALEWAY_AMSTERDAM_ENABLED=True
SCALEWAY_AMSTERDAM_AUTH_TOKEN=your_second_token
SCALEWAY_AMSTERDAM_REGION=nl-ams-1
SCALEWAY_AMSTERDAM_MIN_SCALING=1
SCALEWAY_AMSTERDAM_SIZE=DEV1-S
SCALEWAY_AMSTERDAM_DISPLAY_NAME=Amsterdam Account
```

### Available instance-specific configurations

For each instance, you can configure:

#### Required for each instance:
- `SCALEWAY_INSTANCENAME_ENABLED` - to enable this specific instance
- `SCALEWAY_INSTANCENAME_AUTH_TOKEN` - the authentication token for this instance
- `SCALEWAY_INSTANCENAME_REGION` - region for this instance

#### Optional for each instance:
- `SCALEWAY_INSTANCENAME_ORGANIZATION` - organization ID for this instance
- `SCALEWAY_INSTANCENAME_MIN_SCALING` - minimum number of proxies for this instance
- `SCALEWAY_INSTANCENAME_MAX_SCALING` - maximum number of proxies for this instance
- `SCALEWAY_INSTANCENAME_SIZE` - instance type for this instance
- `SCALEWAY_INSTANCENAME_IMAGE` - image to use for this instance
- `SCALEWAY_INSTANCENAME_DISPLAY_NAME` - a friendly name for the instance that will appear in the UI

Each instance operates independently, maintaining its own pool of proxies according to its configuration. 