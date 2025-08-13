# DigitalOcean Configuration

Configure CloudProxy to use DigitalOcean for creating proxy servers.

## Quick Start

```bash
# Run with Docker (recommended)
docker run -d \
  -e PROXY_USERNAME='your_username' \
  -e PROXY_PASSWORD='your_password' \
  -e DIGITALOCEAN_ENABLED=True \
  -e DIGITALOCEAN_ACCESS_TOKEN="your-token-here" \
  -e DIGITALOCEAN_REGION="lon1" \
  -p 8000:8000 \
  laffin/cloudproxy:latest

# Or using an environment file
cat > .env << EOF
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
DIGITALOCEAN_ENABLED=True
DIGITALOCEAN_ACCESS_TOKEN=your-token-here
DIGITALOCEAN_REGION=lon1
EOF

docker run -d --env-file .env -p 8000:8000 laffin/cloudproxy:latest
```

<details>
<summary>For development (Python)</summary>

```bash
export DIGITALOCEAN_ENABLED=True
export DIGITALOCEAN_ACCESS_TOKEN="your-token-here"
python -m cloudproxy
```
</details>

## Getting Your Access Token

1. Login to your DigitalOcean account.
2. Click on [API](https://cloud.digitalocean.com/account/api) on the side menu
3. In the Personal access tokens section, click the Generate New Token button. This opens a New personal access token window:
4. Enter a token name, this can be anything, I recommend 'CloudProxy' so you know what it is being used for.
5. Select read and write scopes, write scope is needed so CloudProxy can provision droplets.
6. When you click Generate Token, your token is generated and presented to you on your Personal Access Tokens page. Be sure to record your personal access token. For security purposes, it will not be shown again.

Now you have your token, you can now use DigitalOcean as a proxy provider, on the main page you can see how to set it is an environment variable. 

## Configuration options
### Environment Variables

#### Required
| Variable | Description | Default |
|----------|-------------|---------||
| `DIGITALOCEAN_ENABLED` | Enable DigitalOcean as a provider | `False` |
| `DIGITALOCEAN_ACCESS_TOKEN` | Your DigitalOcean API token | Required |

#### Optional
| Variable | Description | Default |
|----------|-------------|---------|
| `DIGITALOCEAN_REGION` | Region for droplet deployment | `lon1` |
| `DIGITALOCEAN_MIN_SCALING` | Target number of proxies to maintain | `2` |
| `DIGITALOCEAN_MAX_SCALING` | Reserved for future autoscaling (currently unused) | `2` |
| `DIGITALOCEAN_SIZE` | Droplet size (we recommend smallest) | `s-1vcpu-1gb` |

**Available Regions**: nyc1, nyc3, ams3, sfo3, sgp1, lon1, fra1, tor1, blr1, syd1

**Available Sizes**: s-1vcpu-1gb, s-2vcpu-2gb, s-4vcpu-8gb (smallest is usually sufficient)

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
- `DIGITALOCEAN_INSTANCENAME_MIN_SCALING` - target number of proxies to maintain for this instance
- `DIGITALOCEAN_INSTANCENAME_MAX_SCALING` - reserved for future autoscaling (currently unused)
- `DIGITALOCEAN_INSTANCENAME_SIZE` - droplet size for this instance
- `DIGITALOCEAN_INSTANCENAME_DISPLAY_NAME` - a friendly name for the instance that will appear in the UI

Each instance operates independently, maintaining its own pool of proxies according to its configuration.

## Troubleshooting

### Common Issues

#### Droplets not being created
- Verify your access token has write permissions
- Check your account limits and quotas in DigitalOcean dashboard
- Ensure the region you selected is available
- Check CloudProxy logs for API error messages

#### Authentication errors
```bash
# Test your token
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.digitalocean.com/v2/account"
```

#### Region-specific issues
- Some regions may have capacity limitations
- Try a different region if droplets fail to create
- Consider using multiple regions with different instances

### Cost Optimization

- Use the smallest droplet size (s-1vcpu-1gb) - it's sufficient for proxy usage
- Set MIN_SCALING to the exact number of proxies you need (this is the fixed count that will be maintained)
- Use the AGE_LIMIT environment variable to rotate proxies regularly
- Monitor your DigitalOcean billing dashboard

## See Also

- [API Documentation](api.md) - Complete API reference
- [Multi-Provider Setup](python-package-usage.md#managing-multiple-provider-instances) - Using multiple providers
- [DigitalOcean API Documentation](https://docs.digitalocean.com/reference/api/) - Official DO API docs
