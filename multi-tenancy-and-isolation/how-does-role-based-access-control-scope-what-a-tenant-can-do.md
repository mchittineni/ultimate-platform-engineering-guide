---
title: "How does role-based access control scope what a tenant can do?"
id: 44
category: "Multi-Tenancy and Isolation"
difficulty: "Beginner"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# How does role-based access control scope what a tenant can do?

**Short answer:** Kubernetes RBAC is allow-only: a Role or ClusterRole lists permitted verbs on resources, and a RoleBinding grants that role to users, groups, or service accounts within one namespace. Binding a tenant's identity-provider group to a role in its own namespaces - and nowhere else - is what stops one tenant changing or reading another's objects. The design work is choosing narrow roles, binding groups rather than people, and keeping cluster-wide permissions out of tenants' hands.

## Detail

**The four objects.** RBAC has two kinds of role and two kinds of binding:

| Object             | Scope         | What it does                                                       |
| ------------------ | ------------- | ------------------------------------------------------------------ |
| Role               | One namespace | Lists allowed verbs on resources in that namespace                 |
| ClusterRole        | Cluster-wide  | Same, but can cover cluster-scoped resources or be reused anywhere |
| RoleBinding        | One namespace | Grants a Role or ClusterRole to subjects, inside that namespace    |
| ClusterRoleBinding | Cluster-wide  | Grants a ClusterRole to subjects everywhere                        |

The important combination is a **RoleBinding that references a ClusterRole**: you define a role such as `edit` once, and each binding grants it only within the binding's namespace. That is how most platforms give every tenant the same permissions in their own space without copying role definitions.

**Rules are additive and allow-only.** There is no "deny" in RBAC. A subject can do whatever the union of all its bindings allows, and nothing else. This makes RBAC easy to reason about for a single binding and easy to get wrong in aggregate: one stray ClusterRoleBinding to a broad group silently widens every tenant's reach. Anything you need to forbid outright - for example "no one may create a Service of type LoadBalancer here" - belongs to quota or admission policy, not RBAC.

**Subjects should be groups from your identity provider.** Bind `team-checkout` the group, not twelve named engineers. Group membership is managed where joiners and leavers are already handled, so access follows the organisation chart automatically. Workloads get their own service accounts, bound separately and more narrowly than humans.

**The built-in roles are a reasonable starting point.** Kubernetes ships user-facing ClusterRoles called `view`, `edit`, and `admin`. `edit` lets a team manage most workload objects in a namespace; `admin` adds the ability to manage Roles and RoleBindings within it. Platforms typically grant `edit` to the tenant group, keep `admin` for a small set of tenant leads or for automation, and add custom ClusterRoles for their own CRDs via role aggregation.

**Things tenants should almost never get:**

- **Any ClusterRoleBinding**, because it crosses every namespace.
- **The `escalate`, `bind`, or `impersonate` verbs**, which let a subject grant itself more than it has.
- **Write access to Namespaces, CRDs, or admission webhooks** - cluster-scoped objects that change the rules for everyone.
- **`create` on `pods/exec` in production**, unless you have decided that shell access is acceptable and audited.
- **Broad `get` on Secrets** outside their own namespace, which is a direct route across the boundary.

**RBAC scopes the Kubernetes API only.** It says nothing about what a pod can reach on the network, what cloud resources its credentials open, or whether its spec is safe. Tenant isolation combines RBAC with network policy, scoped workload identity in the cloud, Pod Security, and quota.

**Who the user is.** Tenant engineers, who should find they can do everything their job needs in their own namespaces through normal group membership, and the platform and security teams, who need to answer "who can do what where?" quickly. Generating bindings from the tenant definition means nobody hand-edits RBAC, and every binding has a traceable origin.

**The trade-off.** Narrow roles are safer but produce requests for exceptions; broad roles such as `admin` everywhere are convenient and eventually become an audit finding. The balance most platforms reach is `edit` by default, time-bound elevation for incidents, and GitOps as the path to production so humans need less direct write access at all.

## Example

```yaml
# Generated for each tenant namespace from the Tenant definition.
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tenant-edit
  namespace: search-api-prod
  labels: { tenant: team-search, platform.example.com/generated: "true" }
subjects:
  - kind: Group
    name: team-search # identity provider group
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: view # production: humans read, GitOps writes
  apiGroup: rbac.authorization.k8s.io
---
# Let tenants manage the platform's own CRDs by aggregating into edit/admin.
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: platform-services-edit
  labels:
    rbac.authorization.k8s.io/aggregate-to-edit: "true"
    rbac.authorization.k8s.io/aggregate-to-admin: "true"
rules:
  - apiGroups: ["platform.example.com"]
    resources: ["databases", "queues"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

```text
Checking the boundary from the tenant's point of view:

$ kubectl auth can-i delete deployments -n search-api-dev  --as=alice --as-group=team-search
yes
$ kubectl auth can-i delete deployments -n checkout-api-dev --as=alice --as-group=team-search
no
$ kubectl auth can-i create clusterrolebindings --as=alice --as-group=team-search
no
$ kubectl auth can-i get secrets -n search-api-prod --as=alice --as-group=team-search
no      # view excludes Secrets by design
```

## Interview tips

- Explain the RoleBinding-to-ClusterRole pattern. It is how a platform gives every tenant the same permissions without duplicating roles, and many candidates do not know it.
- Say RBAC is allow-only and additive, so the risk is in the aggregate; one broad ClusterRoleBinding undoes everything.
- Name `escalate`, `bind`, and `impersonate` as verbs tenants must not hold. It signals you have reviewed real RBAC.
- Bind groups, not users, and give workloads their own narrowly bound service accounts.
- Close by saying RBAC only covers the Kubernetes API; cloud access is a separate boundary, covered in [How do you isolate tenant identity and data?](./how-do-you-isolate-tenant-identity-and-data.md).

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
