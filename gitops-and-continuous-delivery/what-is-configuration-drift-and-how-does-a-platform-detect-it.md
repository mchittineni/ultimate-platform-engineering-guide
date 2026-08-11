---
title: "What is configuration drift and how does a platform detect it?"
id: 49
category: "GitOps and Continuous Delivery"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# What is configuration drift and how does a platform detect it?

**Short answer:** Drift is any difference between the declared desired state and what is actually running. A reconciling agent detects it by comparing continuously and reports it as an out-of-sync condition; with self-healing enabled it also reverts it. The harder problems are the two kinds of drift reconciliation cannot see: resources that exist in the cluster with nothing declaring them, and legitimate mutations by other controllers that make a resource look permanently drifted.

## Detail

**Where drift comes from.** Manual changes during an incident, another controller mutating a field, a cloud-side change made in a console, an operator writing defaults back into the object, and a partial apply that failed halfway. Only the first is the one people imagine.

**Detection is continuous comparison, and the comparison is subtler than it sounds.** The agent compares the desired manifest to the live object, but the live object always contains fields you did not set - defaults filled in by the API server, `status`, `metadata.managedFields`, and values injected by mutating webhooks. A naive diff reports every object as drifted. This is why reconcilers use a three-way comparison between the desired state, the last applied state, and the live state, and why field ownership tracking exists.

**The perpetual-drift problem is the most common practical complaint.** If a mutating webhook injects a sidecar or an autoscaler changes a replica count, and your desired state also specifies those fields, the reconciler will fight the other controller indefinitely - flapping between synced and out of sync, generating noise, and occasionally causing restarts. The fixes are to stop declaring the field you do not own, or to tell the reconciler to ignore specific fields. Knowing this is the difference between having read about GitOps and having operated it.

**Self-heal is not always the right setting.** Automatically reverting drift is correct for most workloads and actively harmful in two cases: during an incident, when someone is deliberately changing something and the reconciler undoes it minutes later; and for fields another controller legitimately owns. The answer is scoped configuration - ignore rules for shared fields, and a documented suspend mechanism for incidents - rather than turning self-heal off wholesale.

**The invisible drift: uncovered resources.** A reconciler compares what it manages. Anything in the cluster with no owning application is not drifted from its perspective - it is simply outside its view. Detecting this requires the opposite query: enumerate everything in the cluster, subtract everything claimed by an owner, and report the remainder. That report is usually surprising the first time it runs, and it is what turns "we do GitOps" from a claim into a measurement.

**Cloud resource drift needs its own mechanism.** For infrastructure managed by run-to-completion tooling, drift is only visible when a plan runs, so a scheduled plan across all workspaces is required. Reconciling control planes correct this continuously, which is one of their main advantages.

**Report drift as an event with attribution.** "Deployment `checkout` drifted at 14:02, changed by `alice`, field `spec.replicas`, reverted" is actionable. A dashboard showing a count is not. The Kubernetes audit log is what gives you the actor, and joining it to the drift event is what makes the report useful during a post-incident review.

## Example

```yaml
# Ignore fields owned by other controllers, so the reconciler does not fight them.
# Without these two rules, this Application flaps between Synced and OutOfSync
# forever and generates a permanent alert nobody trusts.
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: checkout, namespace: argocd }
spec:
  syncPolicy:
    automated: { selfHeal: true, prune: true }
  ignoreDifferences:
    # The HPA owns replicas. Declaring it here would mean reverting every scale event.
    - group: apps
      kind: Deployment
      name: checkout
      jsonPointers: ["/spec/replicas"]
    # The mesh injects a sidecar. It is not in our manifest and should not be
    # reported as drift.
    - group: apps
      kind: Deployment
      name: checkout
      jqPathExpressions:
        - '.spec.template.spec.containers[] | select(.name == "istio-proxy")'
```

```text
The two kinds of drift, and why only one is visible to the reconciler.

VISIBLE - a managed resource differs from Git
  $ argocd app diff checkout
    ==== apps/Deployment team-payments/checkout ====
    -   replicas: 6
    +   replicas: 12
    changed by: alice@example.com at 2026-08-10T14:02Z   (from the audit log)
    context:    INC-2291, deliberate scale-up during a traffic spike
    action:     selfHeal reverted it at 14:04  <-- and this was WRONG. The
                reconciler undid a deliberate incident action two minutes later.
                Correct response: suspend the app during the incident, then
                commit the change to Git if it should persist.

INVISIBLE - resources nothing declares. The reconciler cannot report these,
because from its perspective they do not exist.
  $ platform coverage report --cluster prod-eu-1

    total resources in cluster ................ 4,182
    claimed by a GitOps Application ........... 3,904   (93.4%)
    UNMANAGED ................................. 278

      by origin:
        created by controllers (expected) ..... 241   (Endpoints, ReplicaSets,
                                                       ControllerRevisions...)
        created by humans via kubectl ..........  31   <-- the finding
        origin unknown .........................   6   <-- the concerning finding

      notable unmanaged resources:
        Deployment/debug-proxy (team-search)      created 2026-06-02, 70 days ago
        Secret/temp-api-key (team-data)           created 2026-05-14, no owner
        ClusterRole/temporary-admin               created 2026-03-01  <-- escalate

  "We do GitOps" is a claim. 93.4% coverage is a measurement, and the 6 unknown
  resources are the reason the measurement matters.
```

## Interview tips

- Define drift, then immediately go to what makes detection non-trivial: the live object contains defaults, status, and injected fields you never declared, which is why three-way comparison exists.
- The perpetual-drift fight with an autoscaler or a sidecar injector is the highest-signal detail. Naming the fix - stop declaring fields you do not own, or configure ignore rules - shows operational experience.
- Say that self-heal is wrong during an incident, and give the concrete failure: the reconciler reverts a deliberate scale-up two minutes later. Then give the right mechanism, a documented suspend.
- Coverage as the invisible drift is the strongest structural point. Enumerate the cluster, subtract what has an owner, report the remainder - and treat that percentage as a platform metric.
- Insist on attribution from the audit log. "Who changed it" is what makes a drift report usable in a post-incident review rather than just noise.

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
