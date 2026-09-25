---
title: "What is a reconciliation loop?"
id: 67
category: "Control Planes and Abstractions"
difficulty: "Beginner"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# What is a reconciliation loop?

**Short answer:** A reconciliation loop is a controller that repeatedly compares the desired state someone declared with the actual state of the world, and takes whatever action closes the gap - then does it again, forever. It is the core mechanism of Kubernetes and of every tool built in its style, from Argo CD and Flux to Crossplane. The key idea is that the controller does not follow a script of steps; it keeps pushing reality towards the declaration, so it recovers from failures and drift without anyone re-running anything.

## Detail

**The loop itself is simple.** Observe the current state, compare it with the desired state, act to reduce the difference, record what you found in a status field, and repeat. A thermostat is the classic analogy: you set 21 degrees, and it keeps switching the heating on and off to hold that temperature, regardless of whether a window was opened or the sun came out.

**A Kubernetes example.** When you create a Deployment asking for three replicas, you are not telling Kubernetes to "start three pods". You are declaring that three should exist. The Deployment controller creates a ReplicaSet, the ReplicaSet controller counts pods and creates any that are missing. If a node dies and takes a pod with it, the count drops to two, the controller notices, and it creates another. Nobody filed a ticket; the loop simply saw a difference and closed it.

**Level-triggered, not edge-triggered.** This is the property that makes reconciliation robust. An _edge-triggered_ system reacts to events: "a pod was deleted, so create one". If it misses the event - it was restarting, or the message was lost - the work never happens. A _level-triggered_ system looks at the whole current state every time: "there should be three pods, I can see two, so create one". Events are used only as a hint to reconcile _soon_; correctness comes from comparing states, so a missed event just means a slightly later fix.

**How a real controller is built.** Controllers _watch_ the objects they care about through the Kubernetes API and keep a local cache. Changes put the object's name on a _work queue_. A worker takes a name off the queue, fetches the latest version, and runs the reconcile function. If that fails - the cloud API timed out, say - the item is put back with an increasing back-off delay. Controllers also resync periodically, which catches changes the watch never saw, such as someone editing a database in a cloud console.

**Rules for writing a good reconcile function:**

- **Idempotent.** Running it twice with the same input must produce the same result. "Create the bucket" must become "ensure the bucket exists".
- **Stateless between runs.** Read the current state fresh every time, never trust what you remember from last time.
- **Report honestly in status.** Write conditions such as `Ready` and the `observedGeneration` you processed, so users can tell "done" from "not looked at yet".
- **Clean up deliberately.** Deleting the object should trigger ordered clean-up via a finalizer, and for anything holding data, clean-up should be cautious.

**The trade-offs.** Continuous reconciliation corrects drift automatically, which is excellent until the drift was an emergency fix someone made by hand: the controller will quietly revert it. It also makes deletion as easy as creation, which is dangerous for stateful resources. And there is no built-in "preview" step - the change happens as soon as the controller sees it - which is why Terraform users often miss `plan`.

**Who benefits.** For application teams, reconciliation is what lets them declare "I want a Postgres" and walk away; the platform keeps it that way. For platform teams, it means fewer runbooks and fewer 3am pages, because many failures are repaired by the loop before a human notices.

## Example

```go
// The shape of a reconcile function using controller-runtime.
// It is called with only the object's name - never with "what changed".
func (r *BucketReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    var bucket platformv1.Bucket
    if err := r.Get(ctx, req.NamespacedName, &bucket); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err) // deleted: nothing to do
    }

    // OBSERVE: ask the real world, every time.
    actual, err := r.Cloud.GetBucket(ctx, bucket.Spec.Name)
    if err != nil && !isNotFound(err) {
        return ctrl.Result{}, err // requeued with back-off
    }

    // COMPARE and ACT: ensure, never blindly create.
    if actual == nil {
        if err := r.Cloud.CreateBucket(ctx, bucket.Spec); err != nil {
            return ctrl.Result{}, err
        }
    } else if actual.Versioning != bucket.Spec.Versioning {
        if err := r.Cloud.SetVersioning(ctx, bucket.Spec.Name, bucket.Spec.Versioning); err != nil {
            return ctrl.Result{}, err
        }
    }

    // REPORT: record what was reconciled.
    bucket.Status.ObservedGeneration = bucket.Generation
    meta.SetStatusCondition(&bucket.Status.Conditions, metav1.Condition{
        Type: "Ready", Status: metav1.ConditionTrue, Reason: "Reconciled",
        ObservedGeneration: bucket.Generation,
    })
    if err := r.Status().Update(ctx, &bucket); err != nil {
        return ctrl.Result{}, err
    }

    // REPEAT: come back later even if nothing changes, to catch console drift.
    return ctrl.Result{RequeueAfter: 10 * time.Minute}, nil
}
```

```text
Someone disables versioning in the cloud console at 14:02:

  14:02  console change - no Kubernetes event is generated
  14:10  periodic requeue fires; controller observes Versioning=false
         desired Versioning=true -> calls SetVersioning
  14:10  status Ready=True, observedGeneration unchanged

The loop repaired drift that no event announced. An edge-triggered
script would never have noticed.
```

## Interview tips

- Describe the loop in four words - observe, compare, act, repeat - and then give a concrete example such as a Deployment replacing a lost pod.
- "Level-triggered, not edge-triggered" is the phrase that shows real understanding. Explain it as "compare whole states, so a missed event only delays the fix".
- Mention idempotency and back-off requeues; they are the practical rules every controller author learns.
- Volunteer the downsides: it reverts manual emergency fixes, it has no plan step, and deletion is as easy as creation.
- A common follow-up is "when would you write your own controller?" - see [when to write an operator](../kubernetes-platform/when-should-you-write-a-kubernetes-operator.md), and mention that tools like Crossplane and kro let you get reconciliation without writing Go.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
