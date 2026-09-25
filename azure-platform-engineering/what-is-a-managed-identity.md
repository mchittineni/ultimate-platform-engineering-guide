---
title: "What is a managed identity?"
id: 161
category: "Azure Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# What is a managed identity?

**Short answer:** A managed identity is a Microsoft Entra ID identity for an Azure resource, such as a VM, a function app, or a container app, whose credentials Azure creates, stores, and rotates for you. Code running on that resource asks a local endpoint for a token and gets one; there is no client secret or certificate for anyone to copy, leak, or forget to rotate. You then grant it access with ordinary Azure RBAC role assignments.

## Detail

**The problem it solves.** Before managed identities, an application that needed to read from Key Vault or write to Storage needed a credential: a connection string, a storage key, or an app registration with a client secret. That secret had to live somewhere (an app setting, a pipeline variable, a config file), it expired on a date someone forgot, and it could be copied to a laptop. Managed identities remove the secret from the picture entirely, which removes the leak, the rotation work, and the expiry outage.

**How it works underneath.** A managed identity is a special kind of service principal in your Entra tenant. Azure holds its credential on the hosting infrastructure. Code on the resource calls a local token endpoint: on a VM that is the Instance Metadata Service (IMDS) at `169.254.169.254`, which is only reachable from inside the VM; on App Service, Functions, and Container Apps the platform injects an `IDENTITY_ENDPOINT` and a header value into the environment. The endpoint returns an Entra access token for the requested resource, such as `https://vault.azure.net`, and the code presents that token to the target service. Azure SDKs do all of this for you through `DefaultAzureCredential` or `ManagedIdentityCredential`.

**Two kinds, and the choice matters:**

| Type            | Lifecycle                                   | Shared?                              | Good for                                                                   |
| --------------- | ------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------- |
| System-assigned | Created and deleted with the resource       | No, one resource only                | A single long-lived resource with its own permissions                      |
| User-assigned   | A standalone resource you create and delete | Can be attached to several resources | Workloads that are recreated, scaled out, or need access before they exist |

User-assigned is usually the right default for a platform. It can be created, and given its role assignments, by the provisioning pipeline before the workload is deployed, so the first deployment does not fail waiting for access to propagate. It survives the workload being deleted and recreated, which matters for blue-green deployments and cluster replacement. The risk is over-sharing: one user-assigned identity attached to ten services means all ten have the union of the permissions. Keep it to one identity per workload.

**Access still comes from RBAC.** The identity on its own can do nothing. It gets a role assignment, such as `Key Vault Secrets User` on one vault or `Storage Blob Data Contributor` on one storage account, and that assignment is where least privilege lives. The target service must also accept Entra authentication, which most Azure services now do; for Azure SQL and PostgreSQL you enable Entra authentication and create a database user for the identity.

**Beyond Azure-hosted compute.** A user-assigned managed identity can also hold federated identity credentials, which let an outside token issuer be trusted in place of a secret. This is how AKS workload identity works (a Kubernetes service account token is exchanged for the managed identity's token), and how a GitHub Actions workflow can deploy to Azure with no stored secret. The mechanism is the same trust idea extended to workloads that do not run on an Azure resource with its own endpoint.

**Limitations worth knowing.** Tokens are cached, so a new or removed role assignment can take a while to take effect, and a revoked permission is not instant. A managed identity only works from inside Azure (or through federation); a developer's laptop uses their own Entra identity instead, which `DefaultAzureCredential` handles by trying several credential types in order. And some older services or third-party systems accept only keys, which is where a vaulted secret is still needed and should be recorded as an exception.

**Who the user is.** Product teams consume this. The platform's job is to make "my service needs to read this queue" a line in a service definition that produces the identity, the role assignment, and the wiring, so that no team ever has a reason to ask for a connection string.

## Example

```bash
# A user-assigned identity for one workload, created by the platform pipeline
az identity create -g rg-team-payments -n id-checkout
PRINCIPAL_ID=$(az identity show -g rg-team-payments -n id-checkout --query principalId -o tsv)
IDENTITY_ID=$(az identity show -g rg-team-payments -n id-checkout --query id -o tsv)

# Least privilege: read secrets from ONE vault (the vault uses Azure RBAC)
az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope "$(az keyvault show -n kv-checkout-prod --query id -o tsv)"

# Attach it to the container app
az containerapp identity assign -g rg-team-payments -n checkout --user-assigned "$IDENTITY_ID"
```

```bash
# What happens underneath on a VM: ask IMDS for a token. No secret anywhere.
# The Metadata header blocks simple request-forgery from outside code paths.
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net"
```

```python
# What application code looks like: no connection string, no secret.
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient

# Pin the user-assigned identity by client ID so the code never picks up a
# different identity attached to the same resource.
credential = ManagedIdentityCredential(client_id="<id-checkout-client-id>")
client = SecretClient("https://kv-checkout-prod.vault.azure.net", credential)
api_key = client.get_secret("payments-provider-api-key").value
```

## Interview tips

- Define it as an Entra identity whose credential Azure manages, and say what disappears: the secret, its rotation, and its expiry.
- Explain the token endpoint (IMDS on VMs, an injected endpoint on App Service and Container Apps). It shows you know the mechanism rather than the marketing.
- Compare system-assigned and user-assigned, and prefer user-assigned for platforms because it can be granted access before the workload exists and survives recreation.
- Stress that the identity grants nothing on its own; role assignments at narrow scope do.
- Mention federated identity credentials as the bridge to AKS workload identity and secretless CI. See [How do workload identities work on AKS?](./how-do-workload-identities-work-on-aks.md) and [How do you run a secretless CI/CD pipeline?](../platform-security/how-do-you-run-a-secretless-ci-cd-pipeline.md).
- Be ready for the follow-up about propagation delay: token caching means access changes are not instant, which matters during incident response.

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
