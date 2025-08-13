# Hetzner Configuration

Configure CloudProxy to use Hetzner Cloud for creating proxy servers.

## Quick Start

```bash
# Run with Docker (recommended)
docker run -d \
  -e PROXY_USERNAME='your_username' \
  -e PROXY_PASSWORD='your_password' \
  -e HETZNER_ENABLED=True \
  -e HETZNER_API_TOKEN="your-api-token" \
  -e HETZNER_LOCATION="nbg1" \
  -p 8000:8000 \
  laffin/cloudproxy:latest

# Or using an environment file
cat > .env << EOF
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
HETZNER_ENABLED=True
HETZNER_API_TOKEN=your-api-token
HETZNER_LOCATION=nbg1
EOF

docker run -d --env-file .env -p 8000:8000 laffin/cloudproxy:latest
```

<details>
<summary>For development (Python)</summary>

```bash
export HETZNER_ENABLED=True
export HETZNER_API_TOKEN="your-api-token"
python -m cloudproxy
```
</details>

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

## Configuration Options

### Environment Variables

#### Required
| Variable | Description | Default |
|----------|-------------|---------||
| `HETZNER_ENABLED` | Enable Hetzner as a provider | `False` |
| `HETZNER_API_TOKEN` | Your Hetzner Cloud API token | Required |

#### Optional
| Variable | Description | Default |
|----------|-------------|---------|
| `HETZNER_MIN_SCALING` | Target number of proxies to maintain | `2` |
| `HETZNER_MAX_SCALING` | Reserved for future autoscaling (currently unused) | `2` |
| `HETZNER_SIZE` | Server type | `cx11` |
| `HETZNER_LOCATION` | Server location | `nbg1` |
| `HETZNER_DATACENTER` | Specific datacenter (overrides location) | None |

**Available Locations**: 
- `nbg1` - Nuremberg, Germany
- `fsn1` - Falkenstein, Germany
- `hel1` - Helsinki, Finland
- `ash` - Ashburn, USA
- `hil` - Hillsboro, USA

**Recommended Server Types**:
- `cx11` - Smallest, most cost-effective for proxies
- `cx21` - More resources if needed
- `cpx11` - Shared vCPU option for lower cost

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
- `HETZNER_INSTANCENAME_MIN_SCALING` - target number of proxies to maintain for this instance
- `HETZNER_INSTANCENAME_MAX_SCALING` - reserved for future autoscaling (currently unused)
- `HETZNER_INSTANCENAME_SIZE` - server type for this instance
- `HETZNER_INSTANCENAME_LOCATION` - location for this instance
- `HETZNER_INSTANCENAME_DATACENTER` - datacenter for this instance (overrides location)
- `HETZNER_INSTANCENAME_DISPLAY_NAME` - a friendly name for the instance that will appear in the UI

Each instance operates independently, maintaining its own pool of proxies according to its configuration.

## Troubleshooting

### Common Issues

#### Servers not being created
- Verify your API token has read & write permissions
- Check your Hetzner Cloud limits and quotas
- Ensure the location/datacenter is available
- Review CloudProxy logs for specific API errors

#### Authentication failures
```bash
# Test your API token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.hetzner.cloud/v1/servers
```

#### Location capacity issues
- Some locations may be at capacity for certain server types
- Try a different location or server type
- Check Hetzner status page for outages

#### Network issues
- Hetzner servers are created without firewall rules by default
- Ensure CloudProxy can configure the server after creation
- Check if your IP is not blocked by Hetzner's DDoS protection

### Cost Optimization

- Use `cx11` servers - they're the most cost-effective
- Hetzner charges by the hour, so use AGE_LIMIT to rotate proxies
- Consider location-based pricing differences
- Set MIN_SCALING to the exact number of proxies you need (this is the fixed count that will be maintained)
- Delete unused resources promptly

### Performance Tips

- European locations (nbg1, fsn1, hel1) typically have better connectivity to EU sites
- US locations (ash, hil) are better for US-targeted operations
- Hetzner's network is generally very fast and reliable
- Consider using multiple locations for global coverage

## See Also

- [API Documentation](api.md) - Complete API reference
- [Multi-Provider Setup](python-package-usage.md#managing-multiple-provider-instances) - Using multiple providers
- [Hetzner Cloud API](https://docs.hetzner.cloud/) - Official Hetzner API docs
