---
title: "How do Azure Resource Manager, ARM templates, and Bicep relate?"
id: 162
category: "Azure Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# How do Azure Resource Manager, ARM templates, and Bicep relate?

**Short answer:** Azure Resource Manager (ARM) is the control-plane API that every Azure change goes through, whether from the portal, the CLI, Terraform, or anything else. ARM templates are a JSON format that ARM's deployment engine accepts to create many resources declaratively in one deployment. Bicep is a friendlier language that compiles to ARM template JSON, so it uses exactly the same engine; it improves authoring, not what can be deployed.

## Detail

**ARM is the front door, not a file format.** Every request to create, change, or delete an Azure resource is an HTTPS call to `management.azure.com`. ARM authenticates the caller against Microsoft Entra ID, checks Azure RBAC, evaluates Azure Policy, and then forwards the request to the resource provider that owns the type, such as `Microsoft.Storage` or `Microsoft.ContainerService`. This is why policy and RBAC apply consistently no matter which tool made the request: they are enforced at the one door everything uses. Each resource type is versioned by an API version, such as `Microsoft.Storage/storageAccounts@2023-05-01`, and that version decides which properties exist.

**ARM templates add declarative, whole-environment deployment on top.** An ARM template is a JSON document listing resources, parameters, variables, and outputs. You submit it as a deployment at a scope (a resource group, subscription, management group, or tenant), and ARM's deployment engine works out the dependency order, deploys independent resources in parallel, and records the deployment in history. The two deployment modes matter: incremental (the default) adds and updates what is in the template and leaves everything else alone; complete mode deletes resources in the resource group that the template does not mention, which is powerful and dangerous.

**Bicep is a transpiler, not a new engine.** Bicep files compile to ARM JSON, either explicitly with `az bicep build` or automatically when you run `az deployment ... create --template-file main.bicep`. What you gain is authoring: far less syntax, type checking and IntelliSense in the editor, modules, readable loops and conditions, and symbolic references (`storage.id`) instead of hand-written `resourceId()` expression strings. Anything ARM supports, Bicep supports on day one, because a new API version is available to both at the same moment. `az bicep decompile` converts existing JSON templates into Bicep as a starting point.

**There is no state file.** This is the biggest difference from Terraform or OpenTofu. Bicep and ARM treat Azure itself as the source of truth: a deployment compares the template with what exists and makes it match. You have no state file to store, lock, or corrupt. The trade-off is that plain deployments do not track what they previously created, so removing a resource from the template does not remove it from Azure. Deployment stacks fix this by making a deployment own a set of resources, and `what-if` shows the predicted changes before you deploy, which is the closest thing to a plan.

**How this compares with the alternatives:**

| Tool                         | Talks to                      | State              | Scope of use                                     |
| ---------------------------- | ----------------------------- | ------------------ | ------------------------------------------------ |
| Portal / `az` CLI            | ARM directly                  | None               | Ad hoc changes, scripts, inspection              |
| ARM template (JSON)          | ARM deployment engine         | Azure is the truth | Machine-generated templates; avoid hand-writing  |
| Bicep                        | ARM deployment engine         | Azure is the truth | Azure-only infrastructure as code                |
| Terraform / OpenTofu azurerm | ARM API, resource by resource | Own state file     | Multi-cloud estates, one tool for many providers |

**When to choose Bicep.** An Azure-only platform team gets same-day support for new features, no state to manage, and native integration with deployment stacks, what-if, and template specs. A team that already runs Terraform or OpenTofu across several clouds and SaaS providers usually keeps that one tool rather than splitting its workflows. Both are defensible, and both call the same ARM API in the end.

**Who the user is.** Workload teams rarely write raw Bicep for everything. The platform team publishes versioned Bicep modules, often built on Azure Verified Modules (Microsoft's supported module library, `br/public:avm/...`), and teams consume a module with a few parameters. The platform decides the secure defaults once; teams get a storage account or a database that is private, tagged, and logged without learning every property.

## Example

```bicep
// main.bicep - a private storage account with secure defaults
param location string = resourceGroup().location
param name string

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: name
  location: location
  sku: { name: 'Standard_ZRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false // Entra ID auth only, no account keys
    publicNetworkAccess: 'Disabled'
  }
}

output id string = storage.id // symbolic reference, no resourceId() string
```

```bash
# Bicep compiles to ARM JSON - this is what the engine actually receives
az bicep build --file main.bicep --outfile main.json

# Preview, then deploy. The CLI compiles .bicep automatically.
az deployment group what-if -g rg-checkout --template-file main.bicep -p name=stcheckoutreceipts
az deployment group create  -g rg-checkout --template-file main.bicep -p name=stcheckoutreceipts
```

```json
{
  "type": "Microsoft.Storage/storageAccounts",
  "apiVersion": "2023-05-01",
  "name": "[parameters('name')]",
  "location": "[parameters('location')]",
  "sku": { "name": "Standard_ZRS" },
  "kind": "StorageV2",
  "properties": {
    "minimumTlsVersion": "TLS1_2",
    "allowBlobPublicAccess": false,
    "allowSharedKeyAccess": false,
    "publicNetworkAccess": "Disabled"
  }
}
```

The last block is the resource as it appears in the compiled `main.json`: same resource, same API version, more ceremony.

## Interview tips

- Say ARM is the API and the enforcement point for RBAC and Policy, not just a template format. It explains why governance applies to every tool.
- Describe Bicep as a transpiler to ARM JSON: same engine, same capabilities, better authoring. Candidates who treat them as competing engines lose credibility.
- Explain incremental versus complete mode, and that neither tracks what it created previously; deployment stacks are the modern answer to orphaned resources.
- "No state file" is the headline difference from Terraform or OpenTofu, and it cuts both ways. Say both halves.
- Expect "Bicep or Terraform?". Answer by estate shape (Azure-only versus multi-provider), not preference. See [How do you manage Terraform at platform scale?](../control-planes-and-abstractions/how-do-you-manage-terraform-at-platform-scale.md).
- For how a platform packages this for teams, see [How do you use Bicep for platform modules and subscription vending?](./how-do-you-use-bicep-for-platform-modules-and-subscription-vending.md).

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
