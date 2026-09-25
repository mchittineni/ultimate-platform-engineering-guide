---
title: "How do Microsoft Entra ID and Azure RBAC relate?"
id: 160
category: "Azure Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# How do Microsoft Entra ID and Azure RBAC relate?

**Short answer:** Microsoft Entra ID (formerly Azure Active Directory) answers "who are you?": it is the directory that holds users, groups, service principals, and managed identities, and it issues their tokens. Azure role-based access control (RBAC) answers "what may you do to this resource?": Azure Resource Manager checks role assignments, each linking an Entra principal to a role at a scope. Entra authenticates, Azure RBAC authorises, and the two meet at the principal's object ID.

## Detail

**Two systems, one flow.** When an engineer runs `az storage account list`, the CLI first gets a token from Entra ID for Azure Resource Manager. ARM validates the token, reads the caller's object ID and group memberships from it, and then evaluates Azure RBAC: is there a role assignment, for this principal or one of its groups, whose role allows `Microsoft.Storage/storageAccounts/read` at this scope or a parent scope? If yes, the call proceeds. Entra ID never decides whether you may read a storage account, and Azure RBAC never checks a password.

**A role assignment has exactly three parts:**

| Part               | What it is                                                   | Example                                                              |
| ------------------ | ------------------------------------------------------------ | -------------------------------------------------------------------- |
| Security principal | An Entra user, group, service principal, or managed identity | `grp-team-payments-engineers`                                        |
| Role definition    | A named list of allowed actions                              | `Reader`, `Storage Blob Data Contributor`                            |
| Scope              | Where it applies; inherited downward                         | management group, subscription, resource group, or a single resource |

Scopes inherit: `Reader` at a management group is `Reader` on every subscription beneath it. That is why the scope is the part to argue about in a review.

**Do not confuse Entra roles with Azure roles.** This is the trap interviewers set. Entra ID has its own roles, such as Global Administrator, User Administrator, and Application Administrator, which govern the directory itself: creating users, consenting to apps, managing groups. Azure roles, such as Owner, Contributor, and Reader, govern Azure resources. They are separate systems with separate assignments. A Global Administrator has no access to subscriptions by default, although they can elevate themselves to User Access Administrator at root scope, which is why that elevation should be alerted on.

**Control plane and data plane are different permissions.** `Contributor` on a storage account lets you change its configuration but does not let you read the blobs, because reading data is a data action covered by roles like `Storage Blob Data Reader`. The same split exists for Key Vault, Service Bus, and Cosmos DB. Knowing this explains a lot of "I'm Contributor but I get 403" tickets, and it is also a feature: platform operators can manage resources without being able to read customer data.

**Assign to groups, not people.** Put engineers in Entra groups and assign roles to the groups. Joiners and leavers then become a group membership change handled by your identity lifecycle, and an access review is a review of group membership rather than a hunt through thousands of individual assignments. Each subscription also has a limit on role assignments, and per-user assignment hits it in large estates.

**Make privilege temporary.** Privileged Identity Management (PIM), part of Entra ID, turns an assignment into an eligible one: the engineer activates `Contributor` on production for two hours with a justification, and it expires. Standing write access to production is then the exception rather than the norm. PIM works for both Entra roles and Azure roles, and it is the everyday answer to "who can change production right now?".

**Workloads are principals too.** A managed identity or an app registration's service principal is an Entra object like any other, and it gets Azure RBAC role assignments in exactly the same way. The platform's users here are product teams who want their service to reach a database without holding a secret, and the platform should create those identities and their narrowly scoped role assignments for them.

**The trade-off.** Built-in roles are broad; `Contributor` includes nearly everything. Custom roles narrow that but need maintaining as Azure adds actions, and wildcard actions in a custom role quietly pick up new ones. Most platforms use built-in roles at narrow scopes, plus a small number of custom roles for specific jobs, such as an on-call role that can restart virtual machines but not reconfigure or delete them. List actions explicitly in custom roles rather than using wildcards.

## Example

```bash
# Look up the group in Entra ID - identity lives here
GROUP_ID=$(az ad group show --group grp-team-payments-engineers --query id -o tsv)

# Azure RBAC: principal + role + scope. Reader on production, at the
# subscription scope, inherited by every resource group in it.
az role assignment create \
  --assignee-object-id "$GROUP_ID" \
  --assignee-principal-type Group \
  --role "Reader" \
  --scope "/subscriptions/<checkout-prod-sub-id>"

# Data-plane access is a separate role. Contributor would NOT allow this.
az role assignment create \
  --assignee-object-id "$GROUP_ID" \
  --assignee-principal-type Group \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/<checkout-prod-sub-id>/resourceGroups/rg-checkout/providers/Microsoft.Storage/storageAccounts/stcheckoutreceipts"

# See what a principal can actually do, including inherited assignments
az role assignment list --assignee "$GROUP_ID" --all --include-inherited -o table
```

```json
{
  "Name": "On-call VM Operator",
  "IsCustom": true,
  "Description": "Start, restart, and deallocate VMs during an incident. Cannot create, resize, or delete them.",
  "Actions": [
    "Microsoft.Resources/subscriptions/resourceGroups/read",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/virtualMachines/start/action",
    "Microsoft.Compute/virtualMachines/restart/action",
    "Microsoft.Compute/virtualMachines/deallocate/action"
  ],
  "NotActions": [],
  "AssignableScopes": ["/providers/Microsoft.Management/managementGroups/lz-corp"]
}
```

## Interview tips

- Lead with the split: Entra ID authenticates and holds the principals; Azure RBAC authorises actions on resources through principal, role, and scope.
- Volunteer the Entra roles versus Azure roles distinction before you are asked. Mentioning that a Global Administrator can elevate to User Access Administrator at root, and that this should be monitored, reads as real operational experience.
- The control plane versus data plane split (`Contributor` cannot read blobs) is the detail that explains a whole class of support tickets.
- Say "assign to groups" and "use PIM for production" together; they are the two habits that keep access reviewable.
- Note that `NotActions` is not a deny: another assignment granting the excluded action still wins. Real deny assignments are created by Azure itself, for example by deployment stacks' deny settings.
- For how workloads get an Entra identity without a secret, see [What is a managed identity?](./what-is-a-managed-identity.md) and [How do workload identities work on AKS?](./how-do-workload-identities-work-on-aks.md).

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
