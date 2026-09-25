---
title: "What is the difference between declarative and imperative configuration?"
id: 28
category: "Platform Architecture"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# What is the difference between declarative and imperative configuration?

**Short answer:** Imperative configuration is a sequence of commands - "create this, then scale that, then attach this" - and the result depends on the state the world was in when you ran them. Declarative configuration describes the end state you want - "there should be three replicas of this image" - and leaves a tool to work out and apply the difference. Platforms prefer declarative interfaces because a desired state can be stored, reviewed, diffed, re-applied safely, and continuously reconciled; a list of commands can only be run and hoped about.

## Detail

**Imperative: you own the steps.** `kubectl create deployment`, `aws rds create-db-instance`, a bash script calling a cloud CLI. Each command is an instruction to change something now. That is intuitive and fast for one-off work, but the knowledge of what should exist lives in whoever ran the commands. Run the script twice and the second run may fail ("already exists") or, worse, create a duplicate. Run it against an environment someone has changed by hand and it has no idea.

**Declarative: you own the outcome.** A Kubernetes manifest, a Terraform or OpenTofu configuration, a Crossplane composite resource. You state what should be true; the tool compares that with what is actually true and computes the actions. The same file applied ten times produces the same result, because after the first apply there is nothing left to do.

**The mechanism behind declarative: diff, then act.** Every declarative tool has three pieces - the desired state (your file), the observed state (what exists), and a planner that turns the difference into operations. Terraform does this once per `plan` and `apply`. Kubernetes controllers do it continuously in a reconciliation loop, which is why a Deployment whose Pod is deleted gets a new one without anyone running anything. That continuous loop is also what corrects drift: a manual change is simply more difference to remove.

**What the platform's users get from it.** For the application developer consuming a platform, declarative configuration means their service is described in a file in their own repository. They change it through a pull request, a reviewer sees exactly what will change, the history is in Git, and rolling back is reverting a commit. This is the foundation GitOps is built on - see [what GitOps actually guarantees](../gitops-and-continuous-delivery/what-is-gitops-and-what-does-it-actually-guarantee.md).

**It is a spectrum, not a binary.** A declarative file is usually implemented by imperative code underneath - a controller still calls `CreateDBInstance`. The question is which layer the user works at. Tools also mix: Helm templates are declarative output produced by a templating step, and a Terraform `local-exec` provisioner is an imperative escape inside a declarative tool.

**Trade-offs worth naming.**

- **Declarative hides ordering.** When order genuinely matters - migrate the schema, then deploy the code, then flip the flag - a pure desired-state model struggles. You end up with sync waves, hooks, or a workflow engine layered on top.
- **The diff can surprise you.** Declaring less than you thought (a field you left out gets reset to a default) or fighting another controller over the same field are classic declarative bugs. Kubernetes server-side apply tracks field ownership partly to make these conflicts visible.
- **Imperative is right for genuine actions.** "Restart this pod", "rotate this key now", "run this database failover" are events, not states. Forcing them into a desired-state file produces awkward fields like `restartedAt`. Kubernetes itself uses an annotation for `kubectl rollout restart` for exactly this reason.
- **Deletion is the dangerous edge.** In a declarative system, removing a block from a file means "this should not exist", and the tool will delete it. That is powerful and is how production databases get dropped by a tidy-up commit.

## Example

```bash
# Imperative: three commands, each depending on the state the last left behind.
kubectl create deployment checkout --image=ghcr.io/example/checkout:1.4.2
kubectl scale deployment checkout --replicas=3
kubectl set env deployment/checkout LOG_LEVEL=info

# Run the first line again and it fails:
#   error: failed to create deployment: deployments.apps "checkout" already exists
# Nothing records that replicas should be 3 - if someone scales it to 1, it stays at 1.
```

```yaml
# Declarative: the end state, stored in Git, applied with `kubectl apply -f`
# (or reconciled by Argo CD / Flux). Applying it again is a no-op.
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout
spec:
  replicas: 3
  selector:
    matchLabels: { app: checkout }
  template:
    metadata:
      labels: { app: checkout }
    spec:
      containers:
        - name: checkout
          image: ghcr.io/example/checkout:1.4.2
          env:
            - { name: LOG_LEVEL, value: info }
```

```text
$ kubectl diff -f checkout.yaml      # someone scaled it to 1 by hand
-  replicas: 1
+  replicas: 3

The diff is the review artefact. With a GitOps reconciler, the drift is
corrected without anyone running the command at all.
```

## Interview tips

- Define both in one sentence each - "steps versus end state" - then explain the diff-and-act mechanism. The mechanism is what shows understanding.
- Tie it to the user: declarative configuration is what lets a developer change their service with a pull request and roll back with a revert.
- Volunteer where imperative is correct - one-off actions such as restarts, key rotations, and failovers. Candidates who claim declarative is always better sound rehearsed.
- Mention that removing something from a declarative file deletes it. It is the most common way declarative systems cause outages, and interviewers like to hear that you know it.
- A likely follow-up is "how does this relate to idempotency?" - declarative apply is idempotent by construction, which is a good bridge to the next topic.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
