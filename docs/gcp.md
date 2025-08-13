# Google Cloud Platform Configuration

Configure CloudProxy to use Google Cloud Platform (GCP) for creating proxy servers.

## Quick Start

```bash
# Run with Docker (recommended) - mounting service account file
docker run -d \
  -e PROXY_USERNAME='your_username' \
  -e PROXY_PASSWORD='your_password' \
  -e GCP_ENABLED=True \
  -e GCP_SA_JSON="/app/gcp-key.json" \
  -e GCP_PROJECT="your-project-id" \
  -e GCP_ZONE="us-central1-a" \
  -v /path/to/service-account-key.json:/app/gcp-key.json:ro \
  -p 8000:8000 \
  laffin/cloudproxy:latest

# Or using service account content in environment variable
docker run -d \
  -e PROXY_USERNAME='your_username' \
  -e PROXY_PASSWORD='your_password' \
  -e GCP_ENABLED=True \
  -e GCP_SERVICE_ACCOUNT_KEY="$(cat service-account-key.json)" \
  -e GCP_PROJECT="your-project-id" \
  -p 8000:8000 \
  laffin/cloudproxy:latest
```

<details>
<summary>For development (Python)</summary>

```bash
export GCP_ENABLED=True
export GCP_SA_JSON="/path/to/service-account-key.json"
export GCP_PROJECT="your-project-id"
python -m cloudproxy
```
</details>

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

## Configuration Options

### Environment Variables

#### Required
| Variable | Description | Default |
|----------|-------------|---------||
| `GCP_ENABLED` | Enable GCP as a provider | `False` |
| `GCP_SA_JSON` | Path to service account JSON file (preferred) | Required* |
| `GCP_SERVICE_ACCOUNT_KEY` | Service account JSON content as string | Required* |
| `GCP_PROJECT` | Your GCP project ID | Required |

*Note: You must provide either `GCP_SA_JSON` (file path) OR `GCP_SERVICE_ACCOUNT_KEY` (JSON content). If both are set, `GCP_SA_JSON` takes precedence.

#### Optional
| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_ZONE` | GCP zone for instances | `us-central1-a` |
| `GCP_IMAGE_PROJECT` | Project containing the OS image | `ubuntu-os-cloud` |
| `GCP_IMAGE_FAMILY` | Image family to use | `ubuntu-2204-lts` |
| `GCP_MIN_SCALING` | Target number of proxies to maintain | `2` |
| `GCP_MAX_SCALING` | Reserved for future autoscaling (currently unused) | `2` |
| `GCP_SIZE` | Machine type (e2-micro is free tier) | `e2-micro` |

**Common Zones**: us-central1-a, us-east1-b, europe-west1-b, asia-southeast1-a

**Recommended Machine Types**:
- `e2-micro` - Free tier eligible (1 per month)
- `e2-small` - Cost-effective for proxy usage
- `n1-standard-1` - Higher performance option

### Authentication Methods

#### Method 1: Using Service Account File (Recommended)
```bash
export GCP_SA_JSON="/path/to/service-account-key.json"
```

#### Method 2: Using Service Account Content
```bash
# Useful for CI/CD or when you can't use files
export GCP_SERVICE_ACCOUNT_KEY='$(cat service-account-key.json)'
```

#### Method 3: For Docker
```bash
# Mount the file and reference it
docker run -v /local/path/key.json:/app/key.json \
  -e GCP_SA_JSON="/app/key.json" \
  laffin/cloudproxy
```

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
- `GCP_INSTANCENAME_MIN_SCALING` - target number of proxies to maintain for this instance
- `GCP_INSTANCENAME_MAX_SCALING` - reserved for future autoscaling (currently unused)
- `GCP_INSTANCENAME_DISPLAY_NAME` - a friendly name for the instance that will appear in the UI

Each instance operates independently, maintaining its own pool of proxies according to its configuration.

## Troubleshooting

### Common Issues

#### Authentication failures
- Ensure your service account has Compute Admin and Service Account User roles
- Verify the JSON key file is valid and not expired
- Check that the project ID matches the one in your service account

```bash
# Validate service account
gcloud auth activate-service-account --key-file=key.json
gcloud compute instances list
```

#### Quota errors
- Check your GCP quotas: `gcloud compute project-info describe --project=PROJECT_ID`
- Free tier includes 1 e2-micro instance per month
- Request quota increases if needed

#### Zone availability issues
- Some zones may not have capacity for certain machine types
- Try different zones in the same region
- Check zone status: `gcloud compute zones list`

#### Image not found
- Ensure ubuntu-os-cloud project is accessible
- Verify the image family exists: `gcloud compute images list --project=ubuntu-os-cloud --filter="family:ubuntu-2204-lts"`

### Cost Optimization

- Use `e2-micro` instances (1 free per month)
- Choose regions with lower pricing
- Enable preemptible instances for up to 80% savings (similar to AWS spot)
- Set MIN_SCALING to the exact number of proxies you need (this is the fixed count that will be maintained)
- Use committed use discounts for long-term usage

### Security Best Practices

- Use service accounts with minimal required permissions
- Rotate service account keys regularly
- Store keys securely (use secret management tools)
- Enable VPC Service Controls if needed
- Use different service accounts for different environments

## See Also

- [API Documentation](api.md) - Complete API reference
- [Security Best Practices](security.md) - Credential management guide
- [GCP Compute Engine Docs](https://cloud.google.com/compute/docs) - Official GCP documentation
