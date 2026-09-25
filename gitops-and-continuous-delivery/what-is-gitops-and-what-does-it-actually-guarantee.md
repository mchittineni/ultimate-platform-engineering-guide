---
title: "What is GitOps and what does it actually guarantee?"
id: 79
category: "GitOps and Continuous Delivery"
difficulty: "Beginner"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# What is GitOps and what does it actually guarantee?

**Short answer:** GitOps means the desired state of a system is declared in version control and an agent in the target environment continuously reconciles reality toward it. What it guarantees is that the declared state is versioned, reviewable, and continuously enforced - so drift is corrected and every change has an author and a diff. What it does not guarantee is that the declared state is correct, that a change is safe, or that everything in your cluster is actually covered by it.

## Detail

**The four principles**, in the form the OpenGitOps project states them: the desired state is declarative; it is versioned and immutable; it is pulled automatically by agents; and it is continuously reconciled. The fourth is the one that separates GitOps from "we keep our YAML in Git" - without an agent converging state continuously, you have version-controlled configuration and a deployment script.

**Pull over push, and why it matters for a platform.** A push model needs credentials to every cluster held in your CI system, which makes CI the highest-value target in the organisation. In a pull model the agent runs inside the cluster and reads from Git, so no external system holds cluster credentials. That difference is often the strongest practical argument for adopting it.

**What you genuinely get:**

- **An audit trail for free.** Every change is a commit with an author, a timestamp, a reviewer, and a diff. This is usually the fastest way to satisfy a change-management control.
- **Drift correction, not just detection.** A hand-edited resource is reverted on the next reconcile.
- **Recovery as a property.** Rebuilding a cluster becomes pointing an agent at a repository, which changes disaster recovery from a runbook into a procedure that is exercised daily.
- **A meaningful review point.** The diff of what will change in production is a reviewable artefact.

**What it does not give you, and this is the part interviewers probe:**

- **Correctness.** A reconciler applies a broken manifest as faithfully as a good one, and then keeps it there.
- **Safety.** Reconciling a bad change to every replica quickly is not progressive delivery. You still need canaries, health-based rollout, and abort criteria on top.
- **Coverage.** Anything created outside Git - a manual `kubectl apply`, a resource made by another controller - is invisible to it. Without a way to detect uncovered resources, "we do GitOps" can be true and still leave much of the cluster unmanaged.
- **Secret management.** Secrets cannot simply be committed, so this needs a separate mechanism.
- **Ordering and dependencies.** Reconcilers converge; they do not natively sequence "database migration, then deploy". Hooks and waves exist, but this is real work.

**The imperative escape hatch is a design question, not an oversight.** During an incident someone will need to change something faster than a pull request cycle. Pretending otherwise means people do it anyway and the change is silently reverted mid-incident, which is worse. Decide deliberately: a documented break-glass that suspends reconciliation for a specific application, with an alert, and a requirement to reconcile Git back to reality afterwards.

## Example

```text
The distinction that matters, using the same repository two ways:

"YAML in Git" - versioned, not GitOps
  developer merges -> CI runs `kubectl apply -f` with a cluster credential
  - drift after a manual change: persists forever, nobody notices
  - CI holds production cluster credentials
  - cluster state and Git agree only immediately after a pipeline run

GitOps - versioned AND continuously reconciled
  developer merges -> in-cluster agent notices, applies, and keeps applying
  - drift after a manual change: reverted within minutes, and reported
  - no external system holds cluster credentials
  - cluster state converges on Git permanently, and divergence is an alert
```

```yaml
# The declaration of intent. selfHeal is the line that makes this GitOps rather
# than an automated apply; prune is the line that needs the most care.
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: checkout, namespace: argocd }
spec:
  project: team-payments
  source:
    repoURL: https://github.com/example/checkout-deploy
    targetRevision: main # or a pinned tag for production
    path: envs/production
  destination: { server: https://kubernetes.default.svc, namespace: team-payments }
  syncPolicy:
    automated:
      selfHeal: true # revert manual drift - the fourth principle in practice
      prune: true # delete what Git no longer declares (dangerous for stateful)
    syncOptions:
      - CreateNamespace=false # namespaces come from the Tenant controller
```

```text
The three honest gaps, and what covers each:

  GAP                              WHAT ACTUALLY COVERS IT
  a bad manifest is applied         schema validation + policy in CI, plus
  faithfully and kept there         health checks that stop the sync
  a correct change is rolled out    progressive delivery - canary analysis,
  to 100% too fast                  burn-rate abort, traffic shifting
  resources exist outside Git       a reconciliation report: everything in the
                                    cluster with no owning Application is a
                                    finding, not an absence of information

  Being able to name these is the difference between having adopted GitOps and
  understanding it.
```

## Interview tips

- Give the four principles and stress the fourth - continuous reconciliation - because "we store YAML in Git" is the answer interviewers are trying to filter out.
- The pull-versus-push security argument is the most practical benefit: no external system holds cluster credentials.
- Spend real time on what it does not guarantee. Correctness, safety, and coverage are the three, and volunteering them is what makes the answer credible.
- "GitOps is not progressive delivery" is a clean, memorable distinction - reconciling a bad change quickly is still a bad change deployed quickly.
- Be ready for "what do you do during an incident?" - a documented break-glass that suspends reconciliation with an alert, and reconciling Git back afterwards. Denying the need for one is the weak answer.

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
