# AWS Configuration

Configure CloudProxy to use Amazon Web Services (AWS) for creating proxy servers.

## Quick Start

```bash
# Run with Docker (recommended)
docker run -d \
  -e PROXY_USERNAME='your_username' \
  -e PROXY_PASSWORD='your_password' \
  -e AWS_ENABLED=True \
  -e AWS_ACCESS_KEY_ID="your-access-key" \
  -e AWS_SECRET_ACCESS_KEY="your-secret-key" \
  -e AWS_REGION="us-east-1" \
  -p 8000:8000 \
  laffin/cloudproxy:latest

# Or using an environment file
cat > .env << EOF
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
AWS_ENABLED=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
EOF

docker run -d --env-file .env -p 8000:8000 laffin/cloudproxy:latest
```

<details>
<summary>For development (Python)</summary>

```bash
export AWS_ENABLED=True
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
python -m cloudproxy
```
</details>

## AWS IAM Setup

1. Login to the AWS Management Console
2. Go to the IAM service
3. Create a new IAM policy with the following permissions:
   - EC2 (for managing instances): DescribeInstances, RunInstances, TerminateInstances, CreateTags, DescribeImages, DescribeInstanceStatus, DescribeInstanceTypes, DescribeAvailabilityZones, DescribeSecurityGroups, AuthorizeSecurityGroupIngress, CreateSecurityGroup, DescribeVpcs
   - Systems Manager (for configuring instances): SendCommand
4. Create a new IAM user or role and attach the policy
5. Generate access key ID and secret access key

## Environment Variables

### Required
| Variable | Description | Default |
|----------|-------------|---------||
| `AWS_ENABLED` | Enable AWS as a provider | `False` |
| `AWS_ACCESS_KEY_ID` | AWS access key ID | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key | Required |

### Optional
| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for instances | `us-east-1` |
| `AWS_AMI` | Ubuntu 22.04 AMI ID (region-specific) | Auto-detected |
| `AWS_MIN_SCALING` | Target number of proxies to maintain | `2` |
| `AWS_MAX_SCALING` | Reserved for future autoscaling (currently unused) | `2` |
| `AWS_SIZE` | Instance type (t2.micro is free tier) | `t2.micro` |
| `AWS_SPOT` | Use spot instances for cost savings | `False` |

**Common Regions**: us-east-1, us-west-2, eu-west-1, eu-central-1, ap-southeast-1

**Recommended Instance Types**: 
- `t2.micro` - Free tier eligible, sufficient for most use cases
- `t3.micro` - Better performance, still cost-effective
- `t2.small` - For higher traffic requirements

## Multi-Account Support

CloudProxy supports running multiple AWS accounts simultaneously. Each account is configured as a separate "instance" with its own settings.

### Default Instance Configuration

The configuration variables mentioned above configure the "default" instance. For example:

```
AWS_ENABLED=True
AWS_ACCESS_KEY_ID=your_default_access_key
AWS_SECRET_ACCESS_KEY=your_default_secret_key
AWS_REGION=us-east-1
AWS_MIN_SCALING=2
```

### Additional Instances Configuration

To configure additional AWS accounts, use the following format:
```
AWS_INSTANCENAME_VARIABLE=VALUE
```

For example, to add a second AWS account in a different region:

```
AWS_EU_ENABLED=True
AWS_EU_ACCESS_KEY_ID=your_second_access_key
AWS_EU_SECRET_ACCESS_KEY=your_second_secret_key
AWS_EU_REGION=eu-west-1
AWS_EU_MIN_SCALING=1
AWS_EU_SIZE=t2.micro
AWS_EU_SPOT=True
AWS_EU_DISPLAY_NAME=EU Account
```

### Available instance-specific configurations

For each instance, you can configure:

#### Required for each instance:
- `AWS_INSTANCENAME_ENABLED` - to enable this specific instance
- `AWS_INSTANCENAME_ACCESS_KEY_ID` - AWS access key ID for this instance
- `AWS_INSTANCENAME_SECRET_ACCESS_KEY` - AWS secret access key for this instance

#### Optional for each instance:
- `AWS_INSTANCENAME_REGION` - AWS region for this instance
- `AWS_INSTANCENAME_AMI` - AMI ID for this instance (region-specific)
- `AWS_INSTANCENAME_MIN_SCALING` - target number of proxies to maintain for this instance
- `AWS_INSTANCENAME_MAX_SCALING` - reserved for future autoscaling (currently unused)
- `AWS_INSTANCENAME_SIZE` - instance type for this instance
- `AWS_INSTANCENAME_SPOT` - whether to use spot instances for this instance
- `AWS_INSTANCENAME_DISPLAY_NAME` - a friendly name for the instance that will appear in the UI

Each instance operates independently, maintaining its own pool of proxies according to its configuration.

## Troubleshooting

### Common Issues

#### Instances not being created
- Verify your IAM credentials have the required permissions
- Check AWS service quotas in your region
- Ensure the AMI ID is valid for your selected region
- Review CloudProxy logs for specific AWS API errors

#### Permission errors
```bash
# Test your credentials
aws sts get-caller-identity --profile cloudproxy
```

#### AMI-related issues
- The AMI must be Ubuntu 22.04 for the proxy setup to work
- Different regions require different AMI IDs
- Find Ubuntu AMIs: `aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"`

#### Spot instance termination
- Spot instances can be terminated by AWS when capacity is needed
- Use on-demand instances (SPOT=False) for more stability
- Monitor spot pricing in your region

### Cost Optimization

- Use `t2.micro` instances if you're on the free tier
- Enable spot instances for up to 90% cost savings (but less stability)
- Choose regions with lower pricing
- Set MIN_SCALING to the exact number of proxies you need (this is the fixed count that will be maintained)
- Use the AGE_LIMIT variable to rotate proxies and avoid long-running instances

### Security Best Practices

- Use IAM roles instead of access keys when running on EC2
- Rotate access keys regularly
- Apply the principle of least privilege to IAM policies
- Use separate AWS accounts for production and testing

## See Also

- [API Documentation](api.md) - Complete API reference
- [Security Best Practices](security.md) - Credential management guide
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/) - Official AWS docs