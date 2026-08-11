---
title: "How do you use Bicep for platform modules and subscription vending?"
id: 91
category: "Azure Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# How do you use Bicep for platform modules and subscription vending?

**Short answer:** Publish versioned Bicep modules to a registry, have teams consume them by version rather than by copying files, and use deployment stacks so a deployment owns its resources and can clean them up. For vending, use a subscription-scope or management-group-scope template that creates the subscription, places it under the right management group, and applies the baseline - then reconcile it continuously so subscriptions created a year ago gain this year's baseline.

## Detail

**Bicep over ARM JSON, and know why.** Bicep compiles to ARM templates, so the deployment engine is identical, but the authoring experience is far better: modules, type checking, loops and conditions that are readable, and no JSON expression strings. There is no reason to author new ARM JSON, and being able to say Bicep is a transpiler rather than a different engine shows you understand what you are choosing.

**Publish modules to a registry and consume by version.** A container registry can host Bicep modules, referenced as `br:<registry>/bicep/modules/<name>:<version>`. That gives you the property that matters: a team consumes a version, you release a new version, and consumers upgrade deliberately. Copying module files into each repository produces the same divergence problem as any copied template - you cannot improve them afterwards.

**Scope is a first-class concept and choosing it correctly matters.** `targetScope` can be resource group, subscription, management group, or tenant. Vending needs subscription or management group scope; policy assignment needs management group scope to inherit properly. Getting this wrong is a common source of confusing deployment failures.

**Deployment stacks solve the deletion problem.** A plain Bicep deployment in incremental mode never removes anything - a resource you delete from the template simply stays. Deployment stacks make the deployment own a set of resources, so removing something from the template can delete or detach it according to the action-on-unmanage setting. This is the closest Azure gets to the reconciled lifecycle you would want, and it is the answer to "how do you avoid orphaned resources".

**What-if is your plan, and it belongs on the pull request.** `az deployment ... what-if` shows the predicted changes. Post it as a comment so the diff is reviewed before merge, exactly as you would with any other infrastructure change - and fail the check if the output contains deletions of protected resource types.

**For vending, drive it from a declarative request.** A `Subscription` object naming the workload, environment, owning team, cost centre, and tier; a pipeline that creates the subscription through the billing account, moves it under the correct management group, and deploys the baseline module set. Then re-run it on a schedule so the baseline converges rather than being a one-time application.

**Reconciliation is what keeps the estate uniform.** Policy is inherited from the management group automatically, which handles a large part of the baseline. Everything else - VNet and peering, private DNS zone links, diagnostic settings, budgets, RBAC assignments - should be re-applied continuously by the same deployment, so drift is corrected and new baseline items reach old subscriptions.

**Authenticate the pipeline with federated credentials.** An app registration with a federated identity credential trusting your CI's OIDC issuer, scoped to the repository and environment - no client secret. This is the same pattern as workload identity, applied to your deployment path.

## Example

```bicep
// A versioned platform module. Published once, consumed by version.
// modules/postgres/main.bicep
metadata description = 'Platform Postgres. Private, encrypted, backed up, tagged.'

@description('Workload name; used for the enforced naming convention')
param workload string

@allowed(['small', 'medium', 'large'])
param size string = 'small'

@description('Tenant, for cost attribution and IAM scoping')
param tenant string

param location string = resourceGroup().location

// Size -> SKU is a platform decision, not a team decision
var skuMap = {
  small: { name: 'Standard_B2s', tier: 'Burstable' }
  medium: { name: 'Standard_D2ds_v5', tier: 'GeneralPurpose' }
  large: { name: 'Standard_D8ds_v5', tier: 'GeneralPurpose' }
}

resource pg 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  // Enforced naming - what makes RBAC and cost scoping possible
  name: 'psql-${tenant}-${workload}'
  location: location
  sku: skuMap[size]
  properties: {
    version: '16'
    // --- mandatory; no parameter exposes these ---
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Disabled' // Entra auth only - no password to manage
    }
    storage: { autoGrow: 'Enabled' }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Enabled' }
    highAvailability: { mode: size == 'large' ? 'ZoneRedundant' : 'Disabled' }
    network: {
      publicNetworkAccess: 'Disabled' // private only, always
      delegatedSubnetResourceId: platformSubnetId
      privateDnsZoneArmResourceId: platformDnsZoneId
    }
    // ---------------------------------------------
  }
  tags: {
    'managed-by': 'platform'
    tenant: tenant
    workload: workload
  }
}

output fqdn string = pg.properties.fullyQualifiedDomainName
```

```bicep
// Consumed by version from the registry - not copied into the repository.
module db 'br:acrplatform.azurecr.io/bicep/modules/postgres:3.2.0' = {
  name: 'checkout-db'
  params: {
    workload: 'checkout'
    size: 'small'
    tenant: 'team-payments'
  }
}
```

```bash
# Deployment stacks: the deployment OWNS its resources, so removing something
# from the template actually removes it. Plain incremental deployments never do.
az stack group create \
  --name checkout-infra \
  --resource-group rg-team-payments \
  --template-file main.bicep \
  --action-on-unmanage detachAll \
  --deny-settings-mode denyDelete \
  --deny-settings-excluded-actions Microsoft.Authorization/roleAssignments/write

# action-on-unmanage:
#   detachAll  - leave resources in place (safe default for stateful things)
#   deleteAll  - remove them (correct for stateless infrastructure)
# deny-settings-mode denyDelete adds a guard against out-of-band deletion.

# what-if is the plan, and it belongs on the pull request
az deployment group what-if \
  --resource-group rg-team-payments \
  --template-file main.bicep \
  --result-format FullResourcePayloads
```

```text
Vending, driven by a declarative request and reconciled continuously:

  request (checked into the platform repo)
    subscription: checkout-prod
    workload: checkout       environment: production
    managementGroup: Landing Zones/Corp    tier: 1
    owner: group:team-payments             costCentre: eng-payments
    budget: 40000 USD

  pipeline (re-runs weekly, so the baseline CONVERGES rather than being applied once)
    1. create subscription via the billing account alias
    2. move under MG Landing Zones/Corp   -> policy inherits automatically,
                                             which covers much of the baseline
    3. deploy baseline stack at subscription scope:
         - resource groups by convention
         - spoke VNet, peering to the hub, route table to Azure Firewall
         - private DNS zone links for every PaaS zone the platform supports
         - diagnostic settings -> central Log Analytics workspace
         - budget + anomaly alerts to the owning team
         - RBAC: team group -> reader in prod, contributor in non-prod
         - Defender for Cloud plans enabled
    4. register in the platform inventory and the fleet definition

  Because step 3 re-runs, a subscription vended a year ago gains this year's
  private DNS zone links and diagnostic settings without anyone remembering.
```

## Interview tips

- Say Bicep is a transpiler to ARM, so the engine is the same and the authoring experience is what improves. It shows you know what the choice actually is.
- Publishing modules to a registry and consuming by version is the platform-team answer; copied module files produce the same divergence problem as any copied template.
- Deployment stacks are the highest-value thing to name here, because plain incremental deployments never delete anything and orphaned resources are the predictable result.
- `what-if` posted on the pull request, with a check that fails on deletions of protected types, is the reviewable-plan discipline.
- Getting `targetScope` right - management group for policy, subscription for vending - is a small precise point that signals real experience.
- For vending, emphasise continuous reconciliation over one-shot creation, and give the concrete payoff: an old subscription gaining this year's baseline automatically.
- Federated credentials for the deployment pipeline rather than a client secret closes the loop with the workload identity model.

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
