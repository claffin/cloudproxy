# AWS Configuration

To use AWS as a provider, you’ll first need to create an IAM User.

## Steps

1. Login to your AWS console.
2. Go to Identity and Access Management (IAM).
3. On the left-hand panel, click 'Users'.
4. Click 'Add user'.
5. Choose a username e.g. CloudProxy and select 'Programmatic access', then click Next.
6. Click 'Attach existing policies directly' and then select 'AmazonEC2FullAccess', then click Next.
7. Tag is optional, you may want to create the key as 'CloudProxy', then click Next.
8. Now Review and then click 'Create user'.

Now you have your access key and secret access key, you can now use AWS as a proxy provider, below details of the environment variables.

## Configuration options
### Environment variables: 
#### Required:
`` AWS_ENABLED`` - to enable AWS as a provider, set as True. Default value: False

`` AWS_ACCESS_KEY_ID`` - the access key to allow CloudProxy access to your account. 

`` AWS_SECRET_ACCESS_KEY`` - the secret access key to allow CloudProxy access to your account.
#### Optional:
``AWS_MIN_SCALING`` - this is the minimal proxies you required to be provisioned. Default value: 2

``AWS_MAX_SCALING`` - this is currently unused, however will be when autoscaling is implemented. We recommend you set this as the same as the minimum scaling to avoid future issues for now. Default value: 2

``AWS_SIZE``  - this sets the instance size, we recommend the smallest instance as the volume even a small instance can handle is high. Default value: t2.micro

``AWS_SPOT`` - use this to launch instances as spot instances. The available options are 'persistent' (if you want to be able to restart them) or 'one-time' (if you plan to terminate them). Not all sizes are able to be launched as spot instances. Default value: False

``AWS_REGION`` - this sets the region where the instance is deployed. Some websites may redirect to the language of the country your IP is from. Default value: eu-west-2

``AWS_AMI`` - this sets the AMI the instance is deployed with. The default AMI is for Ubuntu 20.04, however each region may use a different AMI ID. If not using eu-west-2, you may need to set a different AMI ID. See the AWS AMI Marketplace for Ubuntu 20.04 AMI IDs. Default value: ami-096cb92bb3580c759