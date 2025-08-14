# Vultr Configuration

Configure CloudProxy to use Vultr for creating proxy servers.

## Quick Start

```bash
# Run with Docker (recommended)
docker run -d \
  -e PROXY_USERNAME='your_username' \
  -e PROXY_PASSWORD='your_password' \
  -e VULTR_ENABLED=True \
  -e VULTR_API_TOKEN="your-token-here" \
  -e VULTR_REGION="ewr" \
  -p 8000:8000 \
  laffin/cloudproxy:latest

# Or using an environment file
cat > .env << EOF
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
VULTR_ENABLED=True
VULTR_API_TOKEN=your-token-here
VULTR_REGION=ewr
VULTR_PLAN=vc2-1c-1gb
EOF

docker run -d --env-file .env -p 8000:8000 laffin/cloudproxy:latest
```

<details>
<summary>For development (Python)</summary>

```bash
export VULTR_ENABLED=True
export VULTR_API_TOKEN="your-token-here"
python -m cloudproxy
```
</details>

## Getting Your API Token

1. Login to your [Vultr account](https://my.vultr.com/)
2. Navigate to Account → [API](https://my.vultr.com/settings/#settingsapi)
3. In the Personal Access Token section, click "Enable API"
4. Your API key will be displayed. Copy this key - it will only be shown once
5. Store this API key securely as your `VULTR_API_TOKEN`

**Important**: Keep your API token secure and never commit it to version control.

## Configuration Options

### Environment Variables

#### Required
| Variable | Description | Default |
|----------|-------------|---------|
| `VULTR_ENABLED` | Enable Vultr as a provider | `False` |
| `VULTR_API_TOKEN` | Your Vultr API token | Required |

#### Optional
| Variable | Description | Default |
|----------|-------------|---------|
| `VULTR_REGION` | Region for instance deployment | `ewr` |
| `VULTR_MIN_SCALING` | Target number of proxies to maintain | `2` |
| `VULTR_MAX_SCALING` | Reserved for future autoscaling (currently unused) | `2` |
| `VULTR_PLAN` | Instance plan ID | `vc2-1c-1gb` |
| `VULTR_OS_ID` | Operating System ID | `1743` (Ubuntu 22.04 LTS x64) |

### Available Regions

Common Vultr regions include:

| Region Code | Location |
|------------|----------|
| `ewr` | New Jersey |
| `ord` | Chicago |
| `dfw` | Dallas |
| `sea` | Seattle |
| `lax` | Los Angeles |
| `atl` | Atlanta |
| `ams` | Amsterdam |
| `lhr` | London |
| `fra` | Frankfurt |
| `sjc` | Silicon Valley |
| `syd` | Sydney |
| `sgp` | Singapore |
| `nrt` | Tokyo |
| `icn` | Seoul |
| `mia` | Miami |
| `cdg` | Paris |
| `waw` | Warsaw |
| `mad` | Madrid |
| `sto` | Stockholm |

For the complete list of regions, use the Vultr API:
```bash
curl "https://api.vultr.com/v2/regions" \
  -H "Authorization: Bearer ${VULTR_API_TOKEN}"
```

### Available Plans

Common Vultr plans for proxy usage:

| Plan ID | Specifications | Monthly Price* |
|---------|---------------|----------------|
| `vc2-1c-1gb` | 1 vCPU, 1GB RAM, 25GB SSD | ~$6 |
| `vc2-1c-2gb` | 1 vCPU, 2GB RAM, 55GB SSD | ~$12 |
| `vc2-2c-4gb` | 2 vCPU, 4GB RAM, 80GB SSD | ~$24 |
| `vc2-4c-8gb` | 4 vCPU, 8GB RAM, 160GB SSD | ~$48 |

*Prices are approximate and may vary by region. The smallest plan (vc2-1c-1gb) is usually sufficient for proxy usage.

For the complete list of plans:
```bash
curl "https://api.vultr.com/v2/plans" \
  -H "Authorization: Bearer ${VULTR_API_TOKEN}"
```

## Multi-Account Support

CloudProxy supports running multiple Vultr accounts simultaneously. Each account is configured as a separate "instance" with its own settings.

### Default Instance Configuration

The configuration variables mentioned above configure the "default" instance. For example:

```
VULTR_ENABLED=True
VULTR_API_TOKEN=your_default_token
VULTR_REGION=ewr
VULTR_MIN_SCALING=2
```

### Additional Instances Configuration

To configure additional Vultr accounts, use the following format:
```
VULTR_INSTANCENAME_VARIABLE=VALUE
```

For example, to add a second Vultr account with different region settings:

```
# European instance
VULTR_EUROPE_ENABLED=True
VULTR_EUROPE_API_TOKEN=your_second_token
VULTR_EUROPE_REGION=ams
VULTR_EUROPE_MIN_SCALING=3
VULTR_EUROPE_PLAN=vc2-1c-1gb
VULTR_EUROPE_DISPLAY_NAME=Europe Proxies

# Asia Pacific instance
VULTR_ASIA_ENABLED=True
VULTR_ASIA_API_TOKEN=your_third_token
VULTR_ASIA_REGION=sgp
VULTR_ASIA_MIN_SCALING=2
VULTR_ASIA_PLAN=vc2-1c-2gb
VULTR_ASIA_DISPLAY_NAME=Asia Proxies
```

### Available Instance-Specific Configurations

For each instance, you can configure:

#### Required for each instance:
- `VULTR_INSTANCENAME_ENABLED` - Enable this specific instance
- `VULTR_INSTANCENAME_API_TOKEN` - API token for this instance
- `VULTR_INSTANCENAME_REGION` - Region for this instance

#### Optional for each instance:
- `VULTR_INSTANCENAME_MIN_SCALING` - Target number of proxies for this instance
- `VULTR_INSTANCENAME_MAX_SCALING` - Reserved for future autoscaling
- `VULTR_INSTANCENAME_PLAN` - Instance plan for this account
- `VULTR_INSTANCENAME_OS_ID` - Operating system ID
- `VULTR_INSTANCENAME_DISPLAY_NAME` - Friendly name shown in the UI

Each instance operates independently, maintaining its own pool of proxies according to its configuration.

## Troubleshooting

### Common Issues

#### Instances not being created
- Verify your API token is valid and has not been revoked
- Check your account balance and billing status
- Ensure the selected plan is available in your chosen region
- Verify the OS ID is valid (default 1743 for Ubuntu 22.04 LTS)
- Check CloudProxy logs for specific API error messages

#### Authentication errors
```bash
# Test your API token
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.vultr.com/v2/account"
```

#### Region-specific issues
- Some regions may have limited availability for certain plans
- Try a different region if instances fail to create
- Check region availability:
```bash
curl "https://api.vultr.com/v2/regions?per_page=100" \
  -H "Authorization: Bearer ${VULTR_API_TOKEN}"
```

#### Plan availability
- Not all plans are available in all regions
- The default plan (vc2-1c-1gb) is widely available
- Check plan availability in a specific region:
```bash
curl "https://api.vultr.com/v2/plans?per_page=100&type=vc2" \
  -H "Authorization: Bearer ${VULTR_API_TOKEN}"
```

### Firewall Configuration

CloudProxy automatically creates a firewall group for Vultr instances with the following rules:
- **Inbound**: Port 8899 (TCP) from all sources (proxy port)
- **Outbound**: All traffic allowed

The firewall group is named `cloudproxy-{instance}` and is automatically applied to all instances.

### Cost Optimization

- **Use the smallest plan**: The `vc2-1c-1gb` plan is sufficient for proxy usage
- **Set precise MIN_SCALING**: CloudProxy maintains exactly this number of instances
- **Use AGE_LIMIT**: Rotate proxies regularly to get fresh IPs:
  ```
  AGE_LIMIT=3600  # Rotate proxies every hour
  ```
- **Monitor usage**: Check your Vultr dashboard regularly for billing
- **Regional pricing**: Some regions may have different pricing
- **Destroy unused instances**: Set MIN_SCALING=0 to remove all instances

### API Rate Limits

Vultr API has rate limits:
- 30 requests per second per IP address
- CloudProxy handles this automatically with built-in retry logic
- If you encounter rate limit errors, they will be logged and retried

## See Also

- [API Documentation](api.md) - Complete API reference
- [Multi-Provider Setup](python-package-usage.md#managing-multiple-provider-instances) - Using multiple providers
- [Vultr API Documentation](https://www.vultr.com/api/) - Official Vultr API docs
- [Vultr Instance Types](https://www.vultr.com/products/cloud-compute/) - Current pricing and specifications