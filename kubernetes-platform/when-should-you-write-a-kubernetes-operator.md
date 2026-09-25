---
title: "When should you write a Kubernetes operator?"
id: 63
category: "Kubernetes Platform"
difficulty: "Advanced"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# When should you write a Kubernetes operator?

**Short answer:** Write one when you have ongoing operational logic that must run continuously - reacting to drift, failures, and lifecycle events - and that logic encodes knowledge specific to your organisation. If the requirement is really "generate some manifests from a short spec", that is templating or composition, not an operator. Operators are the right answer far less often than they are chosen, because a controller is a distributed system you now maintain forever.

## Detail

**What distinguishes an operator from a template.** A template runs once, at author time. An operator runs forever: it watches, compares desired to actual, and acts - including on events nobody triggered, such as a node failing, a certificate approaching expiry, or someone changing a resource by hand. If nothing needs to happen after creation, you do not need a controller.

**The test: is there a "day two"?** Provisioning is day one. Backups, failover, credential rotation, scaling with rebalancing, version upgrades with migration steps, and drift correction are day two. Operators exist for day two. A database operator that only creates a StatefulSet has automated the easy part and left the part that actually needs judgement.

**Good reasons to write one:**

- Stateful software with genuinely complex lifecycle operations - a controlled failover, a rolling upgrade requiring a specific ordering, a rebalance after scaling.
- Your own platform abstractions - a `Service` or `Tenant` custom resource whose reconciliation encodes your defaults, tiers, and policies. Nobody can supply this because it is your organisation's opinions.
- Continuous drift correction where a manual change must be reverted rather than merely reported.
- Cross-system coordination - creating a cloud resource, waiting for readiness, writing credentials into a secret, registering in a catalogue, and cleaning all of it up on deletion.

**Bad reasons, in rough order of frequency:** generating manifests from a short spec (use Helm, Kustomize, or a composition engine); running a job on a schedule (use a CronJob); wrapping a CLI in a controller for the appearance of GitOps; and adopting an operator for stateful software you could consume as a managed cloud service. That last one is the most expensive mistake - running your own database operator when a managed database exists means you own failover, backups, and patching for no product benefit.

**The costs you are accepting.** A controller is a distributed system with the hard problems that implies: idempotency, because your reconcile function will run repeatedly on the same object; correct status conditions, or nobody can tell what is happening; finalizers for cleanup, which is where operators most often deadlock and block namespace deletion; exponential backoff; watch and cache correctness; and RBAC that is inevitably broad because you create things on users' behalf. Plus permanent maintenance across Kubernetes upgrades.

**Prefer composition before code.** Crossplane compositions, or kro (Kube Resource Orchestrator, a cross-vendor project that composes resources through a `ResourceGraphDefinition`), cover a large share of "turn this small spec into those resources, and keep them in step" without writing a controller. Reach for code when there is genuine logic - ordering, conditional behaviour, waiting on external state - that declarative composition cannot express. The gap has narrowed: since Crossplane v2, compositions can include any Kubernetes resource - not only cloud resources - and composite resources are namespaced without needing claims, so request 2 below is increasingly composable too; it stays an operator here because of its ordering and cross-system logic.

**If you do write one, the non-negotiables.** Reconcile must be idempotent and level-triggered - act on observed state, never on the event that woke you. Report status conditions honestly, including failures. Emit events for anything a human will need to debug. Use finalizers, with an escape route documented for when they deadlock. And test against a real API server, not mocks, because the interesting bugs are in the interaction.

## Example

```text
Four requests. One justified an operator.

1. "Teams need a Postgres with backups, PITR, private networking, and credentials
    delivered into a secret; deletion must clean up but never drop data."
   day two? yes - drift correction, credential rotation, deletion protection
   organisation-specific? yes - our naming, network layout, tagging, IAM
   -> Crossplane composition, NOT a custom operator. Composition covers create,
      update, drift, and delete. No controller code written.

2. "Our `Service` custom resource should produce a Deployment, HPA, PDB, spread
    constraints, dashboards, SLO rules, and a catalogue entry - from tier."
   day two? yes - tier changes must propagate; new defaults must reach old services
   organisation-specific? entirely - this is our opinions, nobody can sell it
   -> OPERATOR. Justified: cross-system coordination (cluster + monitoring +
      catalogue), conditional logic on tier, and ordering requirements.

3. "Nightly report generation."
   day two? no - it runs and finishes
   -> CronJob. An operator here would be a scheduler with extra steps.

4. "We want to self-host Kafka with an operator instead of using managed Kafka."
   day two? yes, and it is genuinely hard - rebalancing, broker replacement,
             upgrades with partition-leadership care
   -> USE THE MANAGED SERVICE, or adopt a mature upstream operator. Do not write
      one. This is the most expensive version of this mistake: you take on
      failover and data durability for no product benefit.
```

```go
// The three properties that separate a working controller from an outage.
func (r *ServiceReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    var svc platformv1.Service
    if err := r.Get(ctx, req.NamespacedName, &svc); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err) // deleted: nothing to do
    }

    // 1. LEVEL-TRIGGERED: decide from observed state, never from "what event woke me".
    //    Reconcile may run twice for one change, or once for three changes.
    if !svc.DeletionTimestamp.IsZero() {
        // 2. FINALIZER: clean up external resources, then release. The most common
        //    operator bug is a finalizer that never clears, blocking namespace
        //    deletion forever - so failures here must be visible, not silent.
        if err := r.cleanupExternal(ctx, &svc); err != nil {
            r.Recorder.Eventf(&svc, "Warning", "CleanupFailed", "%v", err)
            return ctrl.Result{RequeueAfter: 30 * time.Second}, nil
        }
        controllerutil.RemoveFinalizer(&svc, finalizerName)
        return ctrl.Result{}, r.Update(ctx, &svc)
    }

    // 3. IDEMPOTENT: CreateOrUpdate, never blind Create. This function will run
    //    thousands of times against the same object.
    for _, obj := range r.desiredObjects(&svc) { // Deployment, HPA, PDB, SLO rules
        if _, err := controllerutil.CreateOrUpdate(ctx, r.Client, obj, func() error {
            return controllerutil.SetControllerReference(&svc, obj, r.Scheme)
        }); err != nil {
            return ctrl.Result{}, err // requeue with backoff
        }
    }

    // Status conditions are the only way a human or another controller can tell
    // what happened. An operator with no status is undebuggable.
    return ctrl.Result{}, r.setReadyCondition(ctx, &svc)
}
```

## Interview tips

- The "is there a day two?" test is the cleanest way to answer this, and it immediately rules out the majority of proposed operators.
- Say that composition should be tried before code, and name Crossplane compositions. Candidates who reach straight for controller-runtime look inexperienced rather than capable.
- Level-triggered, idempotent reconciliation is the concept to demonstrate - decide from observed state, not from the event.
- Finalizer deadlock blocking namespace deletion is the specific operational war story worth mentioning; it is the most common real operator failure.
- "Do not write an operator for software you could consume as a managed service" is a strong, defensible position and shows you weigh operational cost over technical interest.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
