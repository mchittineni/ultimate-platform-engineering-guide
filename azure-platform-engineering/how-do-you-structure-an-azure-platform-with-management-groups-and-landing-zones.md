---
title: "How do you structure an Azure platform with management groups and landing zones?"
id: 87
category: "Azure Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# How do you structure an Azure platform with management groups and landing zones?

**Short answer:** Management groups form the hierarchy you attach policy and role assignments to; subscriptions are the isolation and quota boundary; resource groups are the lifecycle unit within a subscription. Shape the management group hierarchy around the policies you need to differentiate, put a subscription per workload per environment, and use the Azure landing zone pattern - platform subscriptions for identity, management, and connectivity, separated from the landing zones where workloads live.

## Detail

**Know what each level actually gives you,** because this is the distinction interviewers test:

| Level             | Purpose                                | Inherits               |
| ----------------- | -------------------------------------- | ---------------------- |
| Tenant root group | The whole directory                    | -                      |
| Management group  | Policy and RBAC attachment point       | From parent groups     |
| Subscription      | Isolation, quota, and billing boundary | From management groups |
| Resource group    | Lifecycle and deletion unit            | From subscription      |

Policy and role assignments inherit downward, which is why the hierarchy should mirror policy differences rather than the organisation chart. A hierarchy shaped like your reporting lines needs reshaping at every reorganisation and rarely matches a control you actually apply.

**The subscription is the boundary that matters most in practice.** Quotas are per subscription and per region, so a runaway workload cannot exhaust another subscription's limits. It is also the natural billing and ownership unit. Resource groups feel like a boundary and are not - they share the subscription's quotas, and RBAC scoping to a resource group is convenient rather than isolating.

**The landing zone separation is the pattern worth adopting.** Platform subscriptions hold the things that exist once - identity, management and logging, and connectivity - while workload landing zones hold the applications. Keeping them separate means a workload cannot degrade the shared networking or the log archive, and the platform team's change control on those subscriptions can be stricter.

**A conventional hierarchy:**

| Management group      | Contains                            | Distinct policy                                      |
| --------------------- | ----------------------------------- | ---------------------------------------------------- |
| Platform/Identity     | Domain services, identity resources | Most restricted; no workloads                        |
| Platform/Management   | Log Analytics, automation           | Diagnostic settings enforced everywhere              |
| Platform/Connectivity | Hub VNet, firewall, DNS zones       | Platform team only                                   |
| Landing zones/Corp    | Internal workloads                  | Private endpoints required, no public IPs            |
| Landing zones/Online  | Internet-facing workloads           | WAF required, public exposure allowed but controlled |
| Sandbox               | Experimentation                     | Spend caps, expiry, no production data               |
| Decommissioned        | Subscriptions being retired         | Deny nearly everything                               |

The Corp and Online split is the useful one to name: the difference between them is whether public exposure is permitted at all, which is exactly the kind of policy difference a management group boundary should encode.

**Resource groups should be the deletion unit.** Group resources that share a lifecycle, so deleting the group is a clean teardown. A resource group containing resources from several workloads means you can never delete it safely, which is how orphaned resources accumulate.

**Naming and tagging matter more on Azure than people expect,** because several resource types require globally unique names and because RBAC and cost reporting both lean on the convention. Decide the scheme once, enforce it with policy, and apply it at provisioning.

**Consider the managed landing zone accelerator.** Microsoft publishes a reference implementation of this pattern, and adopting it is often faster and safer than building the equivalent. The trade is opinionated structure; the honest position is to use it unless you have a specific requirement it blocks.

## Example

```text
Hierarchy shaped by policy differences, not by the org chart.

  Tenant Root
  ├── MG: Platform
  │     ├── MG: Identity          policy: no workloads, most restrictive
  │     │     └── sub: identity
  │     ├── MG: Management        policy: diagnostic settings enforced org-wide
  │     │     └── sub: management         (Log Analytics workspace lives here)
  │     └── MG: Connectivity      policy: platform team only
  │           └── sub: connectivity       (hub VNet, Azure Firewall, Private DNS)
  ├── MG: Landing Zones
  │     ├── MG: Corp              policy: DENY public IPs, REQUIRE private
  │     │     │                           endpoints, allowed regions only
  │     │     ├── sub: checkout-prod
  │     │     ├── sub: checkout-staging
  │     │     └── ... (one subscription per workload per environment)
  │     └── MG: Online            policy: public exposure ALLOWED but WAF
  │           │                           required, DDoS protection enforced
  │           └── sub: web-prod
  ├── MG: Sandbox                 policy: spend cap, 30-day expiry, no prod data
  └── MG: Decommissioned          policy: deny all except read and delete

  The Corp/Online split exists because those two groups need genuinely different
  answers to "may this be reachable from the internet". That is what a management
  group boundary is for.
```

```bicep
// Policy assigned at the management group, inherited by every subscription
// beneath it. Assigning per subscription is how hierarchies drift.
targetScope = 'managementGroup'

@description('Deny public IP addresses in Corp landing zones')
resource denyPublicIp 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: 'deny-public-ip-corp'
  properties: {
    displayName: 'Corp landing zones: no public IP addresses'
    policyDefinitionId: tenantResourceId(
      'Microsoft.Authorization/policyDefinitions',
      'deny-public-ip'
    )
    enforcementMode: 'Default' // 'DoNotEnforce' during rollout - audit first
    nonComplianceMessages: [
      {
        // The message is part of the control - it must name the alternative
        message: 'Corp workloads must not have public IPs. Expose via the hub Application Gateway, or move to an Online landing zone with a recorded justification.'
      }
    ]
  }
}

// Diagnostic settings enforced everywhere via DeployIfNotExists, so telemetry
// is a property of existing rather than something teams remember.
resource requireDiagnostics 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: 'deploy-diagnostics-to-law'
  identity: { type: 'SystemAssigned' } // remediation needs an identity
  location: 'westeurope'
  properties: {
    displayName: 'Send all resource logs to the central workspace'
    policyDefinitionId: tenantResourceId(
      'Microsoft.Authorization/policySetDefinitions',
      'deploy-diagnostic-settings'
    )
    parameters: {
      logAnalytics: { value: '/subscriptions/<mgmt-sub>/resourceGroups/rg-management/providers/Microsoft.OperationalInsights/workspaces/law-platform' }
    }
  }
}
```

## Interview tips

- Be precise about the four levels and what each one buys. Getting management groups (policy attachment), subscriptions (isolation and quota), and resource groups (lifecycle) straight is the core of the question.
- Say clearly that resource groups feel like an isolation boundary and are not - they share the subscription's quotas.
- "Shape the hierarchy around policy differences, not the org chart" is the design principle, with the reason: org-shaped hierarchies need reshaping at every reorganisation.
- The Corp versus Online landing zone split is a strong concrete example, because the policy difference - whether public exposure is permitted - genuinely justifies a boundary.
- Platform subscriptions separated from landing zones, with stricter change control on connectivity and management, is the landing zone pattern's real value.
- Mention assigning policy at the management group rather than per subscription; per-subscription assignment is how hierarchies silently drift.
- Take a position on the landing zone accelerator: adopt it unless a specific requirement blocks it, and know what that requirement would be.

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
