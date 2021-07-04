# Google Cloud Configuration

To use Google Cloud as a provider, you’ll first need to create a Service Account.

## Steps

1. Login to your GCP console. Create a new Project if needed.
2. Go to Identity and Access Management (IAM & Admin).
3. On the left-hand panel, click 'Service Accounts'.
3. Click 'Create Service Account'.
4. Choose a service account name e.g. 'cloudproxy' and select Create and Continue.
5. Choose Compute Engine / Compute Admin Role, then click Continue.
6. Click Done.
7. The service account will appear in the list as service-account-name@project-id.iam.gserviceaccount.com.

Now you have your Service Account created, but you still need to create a key for this Service Account.

1. Click the newly created service account.
2. Click 'Keys'.
3. Choose Add Key / Create New Key.
4. Choose JSON as Key type.
5. Click Create.
6. Save the key to your local storage.

Last, you need to create a firewall rule for the default network.

1. On the left-hand panel, select VPC network / Firewall.
2. Click 'Create Firewall Rule'.
3. Name --> cloudproxy
4. Target tags --> cloudproxy
5. Source IP ranges --> 0.0.0.0/0
6. Specified protocols and ports --> tcp --> 8899
7. Leave all other options intact and click 'Create'.

You can now use GCP as a proxy provider, below details of the environment variables.

## Configuration options
### Environment variables: 
#### Required:
``GCP_ENABLED`` - to enable GCP as a provider, set as True. Default value: False

``GCP_PROJECT`` - GCP project ID where to create proxy instances. 

``GCP_SERVICE_ACCOUNT_KEY`` - the service account key to allow CloudProxy access to your account. Please note this is not the path to the key, but the key itself. 

The easiest method to set the ``GCP_SERVICE_ACCOUNT_KEY`` is to use a shell variable. For example, ``GCP_KEY=$(cat /path/to/service_account.json)`` and then use the new variable ``$GCP_KEY``.

#### Optional:
``GCP_MIN_SCALING`` - this is the minimal proxies you require to be provisioned. Default value: 2

``GCP_MAX_SCALING`` - this is currently unused, however will be when autoscaling is implemented. We recommend you set this as the same as the minimum scaling to avoid future issues for now. Default value: 2

``GCP_SIZE``  - this sets the instance size, we recommend the smallest instance as the volume even a small instance can handle is high. Default value: f1-micro

``GCP_ZONE`` - this sets the region & zone where the instance is deployed. Some websites may redirect to the language of the country your IP is from. Default value: us-central1-a

``GCP_IMAGE_PROJECT`` - this sets the project of the image family the instance is deployed with. The default image family project is ubuntu-os-cloud. Default value: ubuntu-os-cloud

``GCP_IMAGE_FAMILY`` - this sets the image family the instance is deployed with. The default image family is Ubuntu 20.04 LTS Minimal. Default value: ubuntu-minimal-2004-lts
