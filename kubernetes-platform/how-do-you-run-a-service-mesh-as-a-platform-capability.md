---
title: "How do you run a service mesh as a platform capability?"
id: 36
category: "Kubernetes Platform"
difficulty: "Advanced"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# How do you run a service mesh as a platform capability?

**Short answer:** Adopt one only for a requirement you can name - usually mTLS everywhere, L7 authorisation, or traffic shifting for progressive delivery - then own it completely: the platform installs it, configures it, upgrades it, and exposes a small slice of its configuration through the service specification. Developers should never write mesh custom resources. The mesh is data-plane infrastructure, so its failure modes and its upgrade procedure matter more than its feature list.

## Detail

**Start from the requirement, because the cost is real.** A mesh gives you mutual TLS with workload identity, L7 authorisation policy, retries and timeouts and circuit breaking without library changes, uniform golden-signal telemetry, and precise traffic splitting. Each of those has a cheaper partial alternative - network policy for L3/L4 isolation, a library for retries, an ingress controller for splitting at the edge - so the justification is usually that you need several of them uniformly across many languages, or that mTLS everywhere is a compliance requirement.

**What it costs.** A control plane to run and upgrade, per-Pod resource overhead in the sidecar model, added latency on every hop, and a substantial increase in debugging difficulty - a request now traverses two proxies, and "is it the app, the proxy, or the policy?" becomes a routine question. Teams also lose the ability to reason about the network from first principles, which slows incident response until people learn the new mental model.

**Sidecar versus sidecar-less is now a genuine architectural choice.** The sidecar model puts a proxy in every Pod: strongest feature set, highest overhead, and every application restart is coupled to proxy upgrades. Ambient or node-level approaches - Istio's ambient mode, Cilium's mesh - move L4 and mTLS into a shared per-node component and add L7 processing only where needed. The trade-off is lower overhead and decoupled upgrades against a shorter feature list and a larger shared failure domain per node. For a platform team, the decoupling of proxy upgrades from application restarts is the most valuable practical difference.

**Sidecar upgrades are the operational reality nobody plans for.** In the sidecar model, upgrading the mesh means restarting every Pod in the fleet. That must be waved, respect pod disruption budgets, and be coordinated with tenants - and it means version skew between the control plane and the data plane exists for as long as the rollout takes, so the supported skew window is a hard constraint on your rollout speed.

**Failure posture must be deliberate.** If the control plane is unavailable, existing proxies should keep routing with their last configuration - that is the correct design and worth verifying rather than assuming. If a sidecar fails, that Pod is out of service. The genuinely dangerous case is a bad configuration push, which propagates to every proxy quickly; that argues for staged configuration rollout and for treating mesh configuration changes with production change control.

**The platform must own the abstraction.** Expose intent - `mtls: strict`, `retries: 3`, `timeout: 2s`, `allowedCallers: [checkout]` - in the service specification and generate the mesh resources. If teams are writing `VirtualService` or `AuthorizationPolicy` by hand, you have added a large new API surface to every team's cognitive load and undone the reason for having a platform.

**Adopt incrementally.** Namespace by namespace, starting with permissive mTLS so unmeshed callers still work, then strict once all callers are meshed. Enabling strict mTLS globally on day one breaks everything that has not been onboarded, and it is the classic mesh adoption failure.

## Example

```text
The decision, honestly framed:

  Do you need mTLS between all services for compliance?          -> strong yes case
  Do you need L7 authorisation (method/path-level)?               -> strong yes case
  Do you need weighted traffic shifting for canaries?             -> yes, or use an
                                                                     ingress/rollout
                                                                     controller instead
  Do you have many languages and need uniform retries/telemetry?  -> yes case
  Do you just want mTLS at L4 and network isolation?              -> NO. Use network
                                                                     policy + a CNI
                                                                     with encryption.
  Do you want it because it is standard practice?                 -> NO.

  If adopting: sidecar-less/ambient first, unless you need a sidecar-only feature.
  The decoupling of proxy upgrades from application restarts is worth a lot to a
  platform team running a fleet.
```

```yaml
# What a developer writes. No mesh API appears anywhere in their repository.
apiVersion: platform.example.com/v1
kind: Service
metadata: { name: checkout }
spec:
  owner: group:team-payments
  tier: 1
  mesh:
    mtls: strict # platform default for tier 1-2
    timeout: 2s
    retries: { attempts: 3, retryOn: 5xx, perTryTimeout: 600ms }
    allowedCallers: [component:web-bff] # -> generates an AuthorizationPolicy
```

```yaml
# What the platform generates. Note the L7 specificity - the thing network
# policy cannot express, and often the actual justification for the mesh.
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: checkout-callers
  namespace: team-payments
  annotations:
    platform.example.com/generated-from: "service/checkout:mesh.allowedCallers"
spec:
  selector: { matchLabels: { app: checkout } }
  action: ALLOW
  rules:
    - from:
        - source:
            # Workload identity, not IP - survives pod rescheduling
            principals: ["cluster.local/ns/team-web/sa/web-bff"]
      to:
        - operation:
            methods: ["POST"]
            paths: ["/v1/checkout"] # method and path - beyond L3/L4
---
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata: { name: default, namespace: team-payments }
spec:
  mtls: { mode: STRICT } # only after every caller is meshed
```

```text
Adoption sequence that does not cause an outage:

  1. Install control plane. No workloads meshed. Verify it is healthy alone.
  2. Mesh the platform's own namespaces first - dogfood the failure modes.
  3. Per tenant namespace: inject sidecars, mTLS mode PERMISSIVE.
       Permissive accepts both mTLS and plaintext, so unmeshed callers still work.
  4. Verify from telemetry that 100% of traffic to the namespace is mTLS.
  5. Only then switch that namespace to STRICT.
  6. Repeat. Global STRICT is the last step, not the first.
```

## Interview tips

- Insist on naming the requirement first, and be ready to say a mesh is not justified - "network policy plus CNI-level encryption" is often the right, cheaper answer.
- The sidecar-versus-ambient trade-off is the current live question. Framing it around decoupling proxy upgrades from application restarts is the platform-team perspective interviewers want.
- Sidecar upgrades requiring a fleet-wide Pod restart, with version skew during the rollout, is the operational detail that shows you have run one.
- Say firmly that developers never write mesh resources. If they are writing `VirtualService`, the platform failed.
- The permissive-then-strict mTLS sequence is the concrete answer to "how would you adopt it?" and the global-strict-on-day-one mistake is worth naming.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
