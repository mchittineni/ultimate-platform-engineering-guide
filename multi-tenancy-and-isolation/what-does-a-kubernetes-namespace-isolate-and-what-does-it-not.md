---
title: "What does a Kubernetes namespace isolate, and what does it not?"
id: 42
category: "Multi-Tenancy and Isolation"
difficulty: "Beginner"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# What does a Kubernetes namespace isolate, and what does it not?

**Short answer:** A namespace isolates names and gives you a scope to attach policy to - RBAC, resource quotas, limit ranges, network policy, and Pod Security labels all target a namespace. On its own it does not isolate the network, the nodes, the kernel, the control plane, or cluster-scoped resources. A namespace is a useful soft boundary for cooperative tenants only once those other controls are layered on top of it.

## Detail

**What a namespace actually does.** It is a naming scope inside the Kubernetes API. Two teams can each have a Deployment called `api` as long as they are in different namespaces. Beyond that, a namespace is mainly an attachment point: many Kubernetes policies are namespaced objects, so the namespace becomes the natural unit for "this team may do X, up to amount Y".

**What it isolates, once you add the matching control:**

| Concern                | Namespace alone | With the right control added                                                           |
| ---------------------- | --------------- | -------------------------------------------------------------------------------------- |
| Object names           | Yes             | -                                                                                      |
| API access             | No              | RBAC Roles and RoleBindings scoped to the namespace                                    |
| Resource consumption   | No              | ResourceQuota and LimitRange                                                           |
| Pod-to-pod network     | No              | Default-deny NetworkPolicy plus explicit allows                                        |
| Dangerous pod settings | No              | Pod Security Admission labels on the namespace                                         |
| Custom rules           | No              | Admission policy (ValidatingAdmissionPolicy, Kyverno, Gatekeeper) matched on namespace |

The key phrase is "once you add": a freshly created namespace with none of these is a folder, not a boundary.

**What it never isolates, whatever you add:**

- **The kernel.** Pods from every namespace can land on the same node and share the Linux kernel. A container escape crosses namespaces trivially. Sandboxed runtimes such as gVisor or Kata Containers, or dedicated nodes, address this; namespaces do not.
- **The control plane.** Every namespace shares the same API server and etcd. One tenant's controller spamming list and watch calls, or creating tens of thousands of objects, slows everyone. API Priority and Fairness and object-count quotas mitigate this.
- **Cluster-scoped resources.** CustomResourceDefinitions, ClusterRoles, admission webhooks, StorageClasses, PersistentVolumes, IngressClasses and GatewayClasses, and nodes are not in any namespace. A tenant who needs to install their own CRDs or webhooks cannot be given that within a namespace without affecting everybody.
- **DNS visibility.** Service names resolve across namespaces (`api.team-b.svc.cluster.local`). Knowing a name is not the same as reaching it if network policy is in place, but discovery is not hidden.
- **Node-level resources** such as local disk throughput and network bandwidth, unless you separate workloads onto different node pools.

**Why this matters for a platform.** Most internal platforms use "namespace per team or per service" as their default tenancy model, because it is cheap and one cluster upgrade serves everyone. That is a sound choice for semi-trusted internal teams. It becomes a mistake when someone assumes the namespace is a security boundary on its own, or offers it to genuinely untrusted code.

**Who the user is.** Application teams consume namespaces, usually without creating them directly. The platform's job is to make sure no namespace exists without its baseline of RBAC, quota, network policy, and Pod Security labels - applied automatically at creation - so that the team gets a safe space without having to know which five objects make it safe.

**The trade-off.** Namespaces give very good utilisation and a single operational footprint. The price is shared failure domains: the control plane, the kernel, and anything cluster-scoped. When a tenant genuinely needs one of those isolated, the answer is a virtual cluster, a dedicated node pool, a sandboxed runtime, or a dedicated cluster - not more namespace configuration.

## Example

```yaml
# A namespace that is an actual soft boundary, not just a name scope.
apiVersion: v1
kind: Namespace
metadata:
  name: team-checkout
  labels:
    tenant: team-checkout
    pod-security.kubernetes.io/enforce: restricted # reject unsafe pod specs
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: team-edit, namespace: team-checkout }
subjects:
  - kind: Group
    name: team-checkout
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: edit # built-in role, granted only inside this namespace
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: ResourceQuota
metadata: { name: quota, namespace: team-checkout }
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    count/pods: "100"
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny, namespace: team-checkout }
spec:
  podSelector: {}
  policyTypes: [Ingress] # add Egress too, with a DNS allow, once flows are known
```

```text
Quick checks that show the limits of the boundary:

$ kubectl auth can-i create customresourcedefinitions --as-group=team-checkout --as=dev
no          # cluster-scoped: nothing a namespace RoleBinding can grant

$ kubectl get pods -A -o wide | grep node-7
team-checkout   api-7f9c...     node-7
team-analytics  batch-2b1d...   node-7    # same node, same kernel
```

## Interview tips

- Say "a namespace is a naming scope and a policy attachment point" first, then list what you have to attach to make it a boundary.
- The two things namespaces can never isolate are the kernel and the control plane. Naming both, with a mitigation for each, is the strong answer.
- Mention cluster-scoped resources such as CRDs and webhooks. It is the usual reason a team asks for "their own cluster", and a virtual cluster often solves it more cheaply.
- Point out that the baseline must be applied automatically at namespace creation, so no tenant namespace ever exists unprotected.
- Expect "when would you give a tenant a whole cluster?" next; see [When do you give a tenant its own cluster instead of a namespace?](./when-do-you-give-a-tenant-its-own-cluster-instead-of-a-namespace.md).

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
