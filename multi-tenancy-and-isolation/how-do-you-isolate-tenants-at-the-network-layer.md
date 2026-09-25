---
title: "How do you isolate tenants at the network layer?"
id: 46
category: "Multi-Tenancy and Isolation"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# How do you isolate tenants at the network layer?

**Short answer:** Default-deny both ingress and egress per namespace, then allow only declared flows - and generate those allow rules from the dependency graph the platform already has, rather than asking teams to write network policies. The two details that decide whether this works in practice are that egress control needs DNS-aware or identity-aware policy to be useful, and that a default-deny policy with no allow rules will break DNS resolution and take the tenant down.

## Detail

**Flat by default is the problem.** In a standard Kubernetes cluster every Pod can reach every other Pod. That means a compromised low-value service can reach the payments database, and an accidental misconfiguration can send staging traffic to production. Network policy is the mechanism that turns a flat network into declared, enforced flows.

**Default-deny is the only sane starting posture,** but it must be introduced carefully. A `NetworkPolicy` selecting all pods with no allow rules blocks DNS to CoreDNS, and everything fails in a way that looks unrelated. The correct baseline is default-deny plus an explicit allow for DNS and for the observability path, applied at namespace creation so no tenant ever exists without it.

**Ingress control is straightforward; egress is where the value is.** Restricting what a workload can reach outbound is what limits data exfiltration and blast radius, and it is much harder because destinations are often DNS names with changing addresses. Native Kubernetes `NetworkPolicy` matches on IP CIDR and pod selectors, not hostnames. Options:

- A CNI with DNS-aware policy - Cilium's `CiliumNetworkPolicy` supports FQDN rules - which is the pragmatic answer for external destinations.
- An egress gateway or proxy that all outbound traffic must traverse, with an allowlist enforced there. Also gives you a single audit point and a stable source address for third-party allowlisting.
- Identity-based policy through a service mesh, where authorisation is on workload identity rather than IP.

**Identity beats IP addresses.** Pod addresses are ephemeral and reused; a policy based on them is fragile and, worse, can accidentally authorise a different workload that inherits the address. Label selectors within the cluster and mTLS workload identity between services are both identity-based, which is why a mesh's authorisation policy is stronger than an IP allowlist.

**Where a mesh earns its cost.** Native `NetworkPolicy` is L3/L4 - it cannot express "this service may call `GET /v1/prices` but not `POST /v1/prices`". A service mesh adds mTLS, L7 authorisation, and per-call identity. That is genuine capability, paid for in resource overhead, an extra control plane, and debugging complexity, so it should be justified by a requirement rather than adopted by default. The overhead argument has shifted: Istio's ambient mode (GA since Istio 1.24) provides mTLS and L4 authorisation through a per-node proxy with no sidecars, adding L7 waypoint proxies only where a tenant needs them.

**Platform-owned rules tenants cannot override.** Namespaced `NetworkPolicy` is written by whoever controls the namespace, so it cannot express "no tenant may ever reach the cloud metadata endpoint" in a way a tenant cannot undo. CNI-specific cluster-wide policies (Cilium's `CiliumClusterwideNetworkPolicy`, Calico's `GlobalNetworkPolicy`) cover this today. SIG Network is standardising the same idea as `ClusterNetworkPolicy` (which replaced the earlier AdminNetworkPolicy drafts), with `Admin` and `Baseline` tiers evaluated before and after tenant policies; it is still an alpha API, so check your CNI's support before relying on it.

**Generate the policies.** Asking forty teams to hand-write network policies produces either policies that are too permissive or an outage. Since the platform already knows the dependency graph from the service specification, it can generate the allow rules - which means the network policy is correct by construction and updates when the declared dependencies change.

**Roll it out in audit mode first.** Observe flows for a period, generate the policy from what actually happened, diff it against what was declared, and investigate the difference before enforcing. The undeclared flows you find are usually the interesting part.

## Example

```yaml
# Applied automatically at namespace creation. Note the DNS allow - without it,
# default-deny egress takes the tenant down in a way that looks like a DNS bug.
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: 00-default-deny, namespace: team-payments }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: 01-allow-platform-baseline, namespace: team-payments }
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to: # DNS - the one everyone forgets
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } }
          podSelector: { matchLabels: { k8s-app: kube-dns } }
      ports:
        - { protocol: UDP, port: 53 }
        - { protocol: TCP, port: 53 }
    - to: # telemetry collector - otherwise observability silently stops
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: observability } }
          podSelector: { matchLabels: { app: otel-collector } }
      ports:
        - { protocol: TCP, port: 4317 }
```

```yaml
# Generated from `dependsOn: [component:pricing]` in the service spec.
# Correct by construction, and regenerated when the declaration changes.
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-checkout-to-pricing
  namespace: team-pricing
  annotations:
    platform.example.com/generated-from: "service/checkout:dependsOn"
spec:
  podSelector: { matchLabels: { app: pricing } }
  policyTypes: [Ingress]
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { platform.example.com/tenant: team-payments } }
          podSelector: { matchLabels: { app: checkout } } # identity, not IP
      ports:
        - { protocol: TCP, port: 8080 }
```

```yaml
# Egress to external destinations by hostname - not expressible in native
# NetworkPolicy, which is the usual reason a DNS-aware CNI is adopted.
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata: { name: allow-payment-provider, namespace: team-payments }
spec:
  endpointSelector: { matchLabels: { app: checkout } }
  egress:
    - toFQDNs:
        - matchName: api.payment-provider.example.com
      toPorts:
        - ports: [{ port: "443", protocol: TCP }]
```

## Interview tips

- Say default-deny both directions, then immediately flag the DNS trap. Knowing that a naive default-deny breaks CoreDNS is a strong practitioner signal.
- Egress is where the security value is, and native `NetworkPolicy` cannot express hostnames. Naming FQDN-aware policy or an egress gateway as the fix is the substance of the answer.
- "Identity, not IP addresses" is the principle - and the reason is concrete: pod addresses are reused, so an IP-based allow can authorise the wrong workload later.
- Generating policies from the declared dependency graph is the platform-engineering answer rather than the network-engineering answer, and it is what interviewers for this role are listening for.
- Volunteer the audit-mode rollout, and note that the undeclared flows you discover are usually more interesting than the policy itself.

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
