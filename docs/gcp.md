# Google Cloud Platform Configuration

To use Google Cloud Platform (GCP) as a provider, you'll need to set up credentials for authentication.

## Steps

1. Login to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new Project or select an existing project.
3. Ensure the Compute Engine API is enabled for your project.
4. Navigate to IAM & Admin > Service Accounts.
5. Create a new service account with the following roles:
   - Compute Admin
   - Service Account User
6. Create a new JSON key for this service account and download the key file.
7. Store this key file securely.

Now you have your credentials, you can use GCP as a proxy provider. Set up the environment variables as shown below:

## Configuration options
### Environment variables:
#### Required:
``GCP_ENABLED`` - to enable GCP as a provider, set as True. Default value: False

``GCP_SA_JSON`` - the path to the service account JSON key file. For Docker, mount the file to the container and provide the path.

``GCP_ZONE`` - the GCP zone where the instances will be created. Default value: us-central1-a

``GCP_IMAGE_PROJECT`` - the project containing the image you want to use. Default value: ubuntu-os-cloud

``GCP_IMAGE_FAMILY`` - the image family to use for the instances. Default value: ubuntu-2204-lts

#### Optional:
``GCP_PROJECT`` - your GCP project ID. This can be found in the JSON key file.

``GCP_MIN_SCALING`` - the minimum number of proxies to provision. Default value: 2

``GCP_MAX_SCALING`` - currently unused, but will be when autoscaling is implemented. We recommend you set this to the same value as the minimum scaling to avoid future issues. Default value: 2

``GCP_SIZE`` - the machine type to use for the instances. Default value: e2-micro

## Multi-Account Support

CloudProxy supports running multiple GCP accounts simultaneously. Each account is configured as a separate "instance" with its own settings.

### Default Instance Configuration

The configuration variables mentioned above configure the "default" instance. For example:

```
GCP_ENABLED=True
GCP_SA_JSON=/path/to/service-account-key.json
GCP_PROJECT=your-project-id
GCP_ZONE=us-central1-a
GCP_MIN_SCALING=2
```

### Additional Instances Configuration

To configure additional GCP accounts, use the following format:
```
GCP_INSTANCENAME_VARIABLE=VALUE
```

For example, to add a second GCP account in a different zone:

```
GCP_EUROPE_ENABLED=True
GCP_EUROPE_SA_JSON=/path/to/europe-service-account-key.json
GCP_EUROPE_PROJECT=europe-project-id
GCP_EUROPE_ZONE=europe-west1-b
GCP_EUROPE_MIN_SCALING=1
GCP_EUROPE_SIZE=e2-micro
GCP_EUROPE_DISPLAY_NAME=Europe GCP Account
```

### Available instance-specific configurations

For each instance, you can configure:

#### Required for each instance:
- `GCP_INSTANCENAME_ENABLED` - to enable this specific instance
- `GCP_INSTANCENAME_SA_JSON` - path to the service account JSON key file for this instance
- `GCP_INSTANCENAME_ZONE` - GCP zone for this instance
- `GCP_INSTANCENAME_IMAGE_PROJECT` - image project for this instance
- `GCP_INSTANCENAME_IMAGE_FAMILY` - image family for this instance

#### Optional for each instance:
- `GCP_INSTANCENAME_PROJECT` - GCP project ID for this instance
- `GCP_INSTANCENAME_SIZE` - machine type for this instance
- `GCP_INSTANCENAME_MIN_SCALING` - minimum number of proxies for this instance
- `GCP_INSTANCENAME_MAX_SCALING` - maximum number of proxies for this instance
- `GCP_INSTANCENAME_DISPLAY_NAME` - a friendly name for the instance that will appear in the UI

Each instance operates independently, maintaining its own pool of proxies according to its configuration.
