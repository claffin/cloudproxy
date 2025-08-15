# Rolling Deployments

CloudProxy now supports rolling deployments to ensure zero-downtime proxy recycling. When enabled, the system ensures a minimum number of healthy proxies are always available during age-based recycling operations.

## Overview

Rolling deployments prevent service disruption by:
- Maintaining a minimum number of healthy proxies at all times
- Limiting the number of proxies being recycled simultaneously
- Deferring proxy recycling when it would violate availability requirements
- Providing real-time visibility into the recycling process

## Configuration

### Environment Variables

Configure rolling deployments using these environment variables:

```bash
# Enable/disable rolling deployments
ROLLING_DEPLOYMENT=True

# Minimum number of proxies to keep available during recycling
ROLLING_MIN_AVAILABLE=3

# Maximum number of proxies to recycle simultaneously
ROLLING_BATCH_SIZE=2
```

### Configuration Details

- **`ROLLING_DEPLOYMENT`**: Set to `True` to enable rolling deployments. Default: `False`
- **`ROLLING_MIN_AVAILABLE`**: The minimum number of healthy proxies that must remain available during recycling. The system will defer recycling if it would reduce availability below this threshold. Default: `3`
- **`ROLLING_BATCH_SIZE`**: The maximum number of proxies that can be in the recycling state simultaneously. This prevents overwhelming the system with too many concurrent deletions and creations. Default: `2`

## How It Works

### Standard Recycling (Rolling Deployment Disabled)

When `ROLLING_DEPLOYMENT=False` or not set:
1. Proxies reaching the age limit are immediately recycled
2. All aged proxies are deleted simultaneously
3. New proxies are created to maintain minimum scaling
4. There may be a period with reduced availability

### Rolling Deployment (Enabled)

When `ROLLING_DEPLOYMENT=True`:
1. The system identifies proxies that have reached the age limit
2. Before recycling, it checks:
   - Would recycling reduce healthy proxies below `ROLLING_MIN_AVAILABLE`?
   - Are we already recycling `ROLLING_BATCH_SIZE` proxies?
3. If checks pass, the proxy is recycled
4. If checks fail, recycling is deferred until conditions improve
5. The process continues until all aged proxies are recycled

### Example Scenario

Configuration:
- `AGE_LIMIT=3600` (1 hour)
- `ROLLING_DEPLOYMENT=True`
- `ROLLING_MIN_AVAILABLE=3`
- `ROLLING_BATCH_SIZE=2`
- `DIGITALOCEAN_MIN_SCALING=5`

Scenario:
1. You have 5 healthy DigitalOcean droplets
2. All 5 reach the age limit simultaneously
3. Rolling deployment kicks in:
   - First 2 droplets are marked for recycling (batch size limit)
   - Remaining 3 stay healthy (minimum availability)
   - Once the first 2 are replaced and healthy, the next batch begins
   - Process continues until all 5 are recycled

## API Endpoints

### Get Rolling Deployment Status

```bash
# Get overall rolling deployment status
curl http://localhost:8000/rolling

# Get status for a specific provider
curl http://localhost:8000/rolling/digitalocean

# Get status for a specific provider instance
curl http://localhost:8000/rolling/digitalocean/default
```

Response example:
```json
{
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "message": "Rolling deployment status retrieved successfully",
  "config": {
    "enabled": true,
    "min_available": 3,
    "batch_size": 2
  },
  "status": {
    "digitalocean/default": {
      "healthy": 3,
      "pending": 0,
      "pending_recycle": 1,
      "recycling": 1,
      "last_update": "2024-01-01T00:00:00Z",
      "healthy_ips": ["192.168.1.1", "192.168.1.2", "192.168.1.3"],
      "pending_recycle_ips": ["192.168.1.4"],
      "recycling_ips": ["192.168.1.5"]
    }
  }
}
```

### Update Rolling Deployment Configuration

```bash
curl -X PATCH http://localhost:8000/rolling \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "min_available": 5,
    "batch_size": 3
  }'
```

## Monitoring

### Log Messages

Rolling deployment activities are logged with clear messages:

```
Rolling deployment: Marked 192.168.1.1 for recycling in digitalocean/default. Currently recycling 1/2 proxies
Rolling deployment: Cannot recycle 192.168.1.2 for digitalocean/default. Would reduce available proxies below minimum (2 < 3)
Rolling deployment: Deferred recycling digitalocean/default droplet -> 192.168.1.3
Rolling deployment: Completed recycling 192.168.1.1 in digitalocean/default
```

### Status Fields

The API provides detailed status information:
- **`healthy`**: Number of proxies currently healthy and serving traffic
- **`pending`**: Number of newly created proxies not yet healthy
- **`pending_recycle`**: Number of proxies marked for recycling but not yet started
- **`recycling`**: Number of proxies currently being deleted
- **`healthy_ips`**: List of IPs for healthy proxies
- **`pending_recycle_ips`**: List of IPs waiting to be recycled
- **`recycling_ips`**: List of IPs currently being recycled

## Best Practices

### Setting Minimum Available

- Set `ROLLING_MIN_AVAILABLE` based on your traffic requirements
- Consider peak load when determining the minimum
- **IMPORTANT**: Ensure `ROLLING_MIN_AVAILABLE` is less than your `MIN_SCALING` value
  - If `ROLLING_MIN_AVAILABLE >= MIN_SCALING`, the system automatically adjusts to use `MIN_SCALING - 1`
  - This prevents a deadlock where no proxies can ever be recycled
  - A warning will be logged when this adjustment occurs

### Setting Batch Size

- Smaller batch sizes provide smoother recycling but take longer
- Larger batch sizes recycle faster but may cause temporary capacity reduction
- Consider your provider's API rate limits when setting batch size

### Age Limits with Rolling Deployment

- Rolling deployments work best with reasonable age limits (e.g., 1-24 hours)
- Very short age limits may cause constant recycling
- Monitor the `/rolling` endpoint to ensure recycling completes successfully

## Troubleshooting

### Proxies Not Being Recycled

If proxies aren't being recycled despite reaching age limit:
1. Check if rolling deployment is enabled
2. Verify you have more than `ROLLING_MIN_AVAILABLE` healthy proxies
3. Check if batch size limit is being reached
4. Review logs for "Deferred recycling" messages

### Recycling Too Slow

If recycling takes too long:
1. Increase `ROLLING_BATCH_SIZE`
2. Ensure new proxies become healthy quickly
3. Check provider API response times
4. Consider reducing `AGE_LIMIT` to spread recycling over time

### API Errors

If the rolling deployment API returns errors:
1. Ensure the provider and instance names are correct
2. Check that the CloudProxy service is running
3. Verify your configuration is valid (positive integers for limits)

## Integration with Existing Features

### Multi-Instance Support

Rolling deployments work with multi-instance configurations:
- Each provider instance maintains its own rolling deployment state
- Settings apply globally but are enforced per instance
- Monitor each instance separately via the API

### Provider Compatibility

Rolling deployments are supported for all providers:
- DigitalOcean
- AWS (including spot instances)
- Google Cloud Platform
- Hetzner
- Vultr

### Interaction with Manual Deletion

- Manual proxy deletion (via `/destroy` endpoint) bypasses rolling deployment rules
- The system will create replacements to maintain minimum scaling
- Rolling deployment continues for age-based recycling