---
title: "What is an Azure subscription and why is it the unit of a landing zone?"
id: 159
category: "Azure Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# What is an Azure subscription and why is it the unit of a landing zone?

**Short answer:** A subscription is a container for Azure resources that trusts exactly one Microsoft Entra tenant, bills to one billing scope, and carries its own quotas, API throttling limits, and role assignments. Those properties make it the smallest boundary that isolates cost, capacity, and access at once, so a landing zone (the pre-configured environment a workload team is handed) is normally a subscription plus the baseline the platform applies to it.

## Detail

**Start with where it sits.** Azure organises resources in four levels: the Entra tenant at the top, management groups that form a hierarchy for policy and access, subscriptions beneath them, and resource groups inside a subscription that hold the actual resources. Every resource lives in exactly one resource group, and every resource group lives in exactly one subscription. When someone says "deploy to Azure", the subscription ID is always part of the address: `/subscriptions/<id>/resourceGroups/<rg>/providers/...`.

**What a subscription actually gives you:**

| Property        | What it means in practice                                                          |
| --------------- | ---------------------------------------------------------------------------------- |
| Identity trust  | Trusts one Entra tenant for sign-in; every principal comes from that directory     |
| Billing         | Costs roll up to one billing scope, so the subscription is a natural cost line     |
| Quotas          | vCPU and many service limits are per subscription and per region                   |
| API throttling  | Azure Resource Manager rate limits apply per subscription                          |
| Access boundary | A role assignment at subscription scope covers everything in it, and nothing else  |
| Policy scope    | Inherits Azure Policy from its management groups; can have its own assignments too |

**Why this makes it the landing zone unit.** A landing zone has to stop one team's workload from hurting another's. Put two teams in one subscription and they share the regional vCPU quota, so one team's scale-out can block the other's deployment. They share the ARM throttling budget, so one noisy pipeline slows everyone. A subscription-scoped `Contributor` for one team is `Contributor` over the other team's resources. And their costs blur into one line that someone has to split by tags. Give each workload and environment its own subscription and all four problems go away without any extra machinery.

**Resource groups look like a boundary and are not.** They are a lifecycle unit, meaning the things you create and delete together, and a convenient RBAC scope. They share the subscription's quotas, throttling, and billing. This is the most common beginner mistake in Azure design, and Microsoft's Cloud Adoption Framework (CAF) exists partly to correct it by recommending subscriptions as the unit of scale and isolation.

**Platform landing zones and application landing zones.** CAF separates the two. Platform landing zones are the few subscriptions the platform team runs once for everyone: identity, management and logging, and connectivity (the hub network, firewall, and private DNS). Application landing zones are the many subscriptions workload teams get. The platform team is the provider; product teams are the users, and what they get is a subscription that already has networking, logging, policy, budgets, and access in place on the first day.

**The trade-off is volume.** One subscription per workload per environment means hundreds of subscriptions. That only works if creating one is automated, known as subscription vending, and if the baseline is re-applied continuously rather than once. Without automation, teams wait days for a subscription and start asking to share, which quietly undoes the isolation. There are also real per-subscription limits (resource groups per subscription, role assignments per subscription) that a very large single subscription runs into, which is another reason not to consolidate.

**When you might share.** Small, tightly coupled components owned by one team can share a subscription with separate resource groups. Sandboxes are often one subscription per engineer or per team with a spend cap. The rule is not "one subscription per service at any cost"; it is "never share a subscription across owners or across production and non-production".

## Example

```text
One workload, three environments, three subscriptions:

  Management group: Landing Zones / Corp
    sub-checkout-dev        owner: team-payments   budget alert, auto-shutdown policy
    sub-checkout-staging    owner: team-payments
    sub-checkout-prod       owner: team-payments   stricter RBAC, no standing write access

  What each subscription gets from the vending pipeline:
    - placed under the right management group -> policy inherited automatically
    - spoke VNet peered to the hub, private DNS zones linked
    - diagnostic settings to the central Log Analytics workspace
    - budget with alerts to the owning team
    - team group assigned Reader in prod, Contributor in dev and staging

  What the team does NOT have to think about: quotas shared with other teams,
  another team's Contributor role reaching their database, or splitting a
  shared invoice by tag.
```

```bicep
// Creating a subscription programmatically with the aliases API.
// Tenant scope: a subscription is not created inside another subscription.
targetScope = 'tenant'

param billingScope string // e.g. an MCA invoice section resource ID

resource checkoutProd 'Microsoft.Subscription/aliases@2021-10-01' = {
  name: 'sub-checkout-prod'
  properties: {
    displayName: 'sub-checkout-prod'
    billingScope: billingScope
    workload: 'Production'
    additionalProperties: {
      managementGroupId: '/providers/Microsoft.Management/managementGroups/lz-corp'
      tags: {
        owner: 'team-payments'
        environment: 'production'
      }
    }
  }
}
```

## Interview tips

- Name the four levels (tenant, management group, subscription, resource group) and say what each one is for. Interviewers use this to check you are not guessing.
- The strongest single point is that quotas, throttling, billing, and access all meet at the subscription. That is why it is the landing zone unit and a resource group is not.
- Say explicitly that resource groups are a lifecycle unit, not an isolation boundary.
- Distinguish platform landing zones (identity, management, connectivity) from application landing zones, and name the product teams as the users of the latter.
- Expect the follow-up "doesn't that create hundreds of subscriptions?" Answer with vending and continuous reconciliation. See [How do you use Bicep for platform modules and subscription vending?](./how-do-you-use-bicep-for-platform-modules-and-subscription-vending.md), and the AWS parallel in [What is account vending and how do you automate it?](../aws-platform-engineering/what-is-account-vending-and-how-do-you-automate-it.md).
- For the hierarchy above the subscription, see [How do you structure an Azure platform with management groups and landing zones?](./how-do-you-structure-an-azure-platform-with-management-groups-and-landing-zones.md).

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
