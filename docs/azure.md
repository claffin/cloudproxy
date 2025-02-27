# Azure Provider for CloudProxy

This provider enables CloudProxy to create and manage proxy servers using Azure Virtual Machines.

## Setup

To use the Azure provider, you need to set up the following:

1. An Azure account
2. An Azure service principal with permissions to create and manage resources
3. Configure CloudProxy with your Azure credentials

## Creating a Service Principal

1. Install the Azure CLI
2. Log in to your Azure account:
   ```
   az login
   ```
3. Create a service principal with contributor role:
   ```
   az ad sp create-for-rbac --name "cloudproxy" --role contributor --scopes /subscriptions/<subscription-id>
   ```
4. Note the output which contains the following values:
   - `appId` (This is your client_id)
   - `password` (This is your client_secret)
   - `tenant` (This is your tenant_id)

## Environment Variables

Configure the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_ENABLED` | Enable Azure provider | `False` |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID | - |
| `AZURE_CLIENT_ID` | Service principal client ID | - |
| `AZURE_CLIENT_SECRET` | Service principal client secret | - |
| `AZURE_TENANT_ID` | Azure tenant ID | - |
| `AZURE_RESOURCE_GROUP` | Resource group name | `cloudproxy-rg` |
| `AZURE_MIN_SCALING` | Minimum number of VMs | `2` |
| `AZURE_MAX_SCALING` | Maximum number of VMs | `2` |
| `AZURE_SIZE` | VM size | `Standard_B1s` |
| `AZURE_LOCATION` | Azure region | `eastus` |
| `AZURE_DISPLAY_NAME` | Display name for the provider | `Azure` |

## Example Configuration

```
AZURE_ENABLED=True
AZURE_SUBSCRIPTION_ID=your_subscription_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
AZURE_RESOURCE_GROUP=cloudproxy-rg
AZURE_MIN_SCALING=2
AZURE_MAX_SCALING=2
AZURE_SIZE=Standard_B1s
AZURE_LOCATION=eastus
```

## VM Specifications

The Azure provider creates Ubuntu 20.04 LTS VMs with the following:

- SSH access using a predefined key
- Proxy port (8899) open
- Proxy authentication using the CloudProxy username and password
- Tags to identify CloudProxy-managed resources

## Resource Management

The provider automatically creates and manages the following resources:
- Resource Group (if it doesn't exist)
- Virtual Networks
- Subnets
- Network Security Groups
- Public IP Addresses
- Network Interfaces
- Virtual Machines

All resources are tagged with `type: cloudproxy` to enable easy identification. 