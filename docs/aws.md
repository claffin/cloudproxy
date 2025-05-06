# AWS Configuration

To use AWS as a provider, you'll need to set up credentials for authentication.

## AWS IAM Setup

1. Login to the AWS Management Console
2. Go to the IAM service
3. Create a new IAM policy with the following permissions:
   - EC2 (for managing instances): DescribeInstances, RunInstances, TerminateInstances, CreateTags, DescribeImages, DescribeInstanceStatus, DescribeInstanceTypes, DescribeAvailabilityZones, DescribeSecurityGroups, AuthorizeSecurityGroupIngress, CreateSecurityGroup, DescribeVpcs
   - Systems Manager (for configuring instances): SendCommand
4. Create a new IAM user or role and attach the policy
5. Generate access key ID and secret access key

## Environment Variables

CloudProxy supports two ways to configure AWS credentials:
1.  **Via Environment Variables (Traditional):** Suitable for static configurations.
2.  **Via API (New):** Allows dynamic adding, updating, and removing of credentials while the application is running. See the [API Documentation](./api.md#credential-management) for details.

### Credentials via Environment Variables

#### Required:
``AWS_ENABLED`` - to enable AWS as a provider, set as True. Default value: False

``AWS_ACCESS_KEY_ID`` - the access key ID for CloudProxy to authenticate with AWS.

``AWS_SECRET_ACCESS_KEY`` - the secret access key for CloudProxy to authenticate with AWS.

### Optional (for Environment Variable Configuration):
``AWS_REGION`` - the AWS region where instances will be deployed, e.g., eu-west-2. Default: us-east-1. **Note:** If adding/updating credentials via the `/api/credentials` endpoint, the `region` must be included directly within the `secrets` payload.

``AWS_AMI`` - the Amazon Machine Image (AMI) ID to use for instances. This should be Ubuntu 22.04. Default: region-specific default AMI

``AWS_MIN_SCALING`` - minimum number of proxies to provision. Default: 2

``AWS_MAX_SCALING`` - maximum number of proxies to provision. Default: 2

``AWS_SIZE`` - the instance type to use. t2.micro is included in the free tier. Default: t2.micro

``AWS_SPOT`` - whether to use spot instances (can be cheaper but may be terminated by AWS). Set to True or False. Default: False

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
- `AWS_INSTANCENAME_MIN_SCALING` - minimum number of proxies for this instance
- `AWS_INSTANCENAME_MAX_SCALING` - maximum number of proxies for this instance
- `AWS_INSTANCENAME_SIZE` - instance type for this instance
- `AWS_INSTANCENAME_SPOT` - whether to use spot instances for this instance
- `AWS_INSTANCENAME_DISPLAY_NAME` - a friendly name for the instance that will appear in the UI

Each instance operates independently, maintaining its own pool of proxies according to its configuration.
