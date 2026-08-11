---
title: "How do Argo CD and Flux differ, and how do you choose?"
id: 45
category: "GitOps and Continuous Delivery"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# How do Argo CD and Flux differ, and how do you choose?

**Short answer:** Both are mature CNCF graduated projects that reconcile Kubernetes state from Git, and either will work. Argo CD centres on a rich UI and an application-centric model, which suits organisations where many teams need visibility into deployment state. Flux is a set of composable controllers with no first-class UI, which suits platform teams that prefer everything expressed as custom resources and want to compose their own tooling. Choose on operating model and multi-tenancy needs, not on feature checklists.

## Detail

**The architectural difference that drives everything else.** Argo CD is one application with a server, a repository service, a controller, and a web UI, organised around the `Application` resource. Flux is a family of small controllers - source, kustomize, helm, notification, image automation - each doing one job and composed by the user. Argo CD gives you a product; Flux gives you components.

**The comparison as it actually affects a decision:**

| Dimension            | Argo CD                                    | Flux                                               |
| -------------------- | ------------------------------------------ | -------------------------------------------------- |
| UI                   | First-class, a major reason people pick it | None official; use CLI or third-party              |
| Model                | `Application` / `ApplicationSet`           | `GitRepository` + `Kustomization` / `HelmRelease`  |
| Multi-tenancy        | Projects, SSO, RBAC in the product         | Namespace-scoped resources plus cluster RBAC       |
| Fleet management     | `ApplicationSet` generators                | Per-cluster resources, often plus a bootstrap repo |
| Image updates        | Separate image updater component           | Built-in image automation controller               |
| Progressive delivery | Argo Rollouts (same family)                | Flagger (same family)                              |
| Footprint            | Larger, one system to run                  | Smaller controllers, more pieces                   |
| API-first ergonomics | Good, UI often the primary interface       | Excellent - everything is a custom resource        |

**Where the UI genuinely matters.** For forty product teams, a UI that shows sync status, health, the live diff, and the history - and lets a developer see why their deploy has not landed - removes an enormous amount of support load. That is often the deciding factor, and it is a legitimate engineering reason rather than a cosmetic preference. Conversely, if your users interact through pull requests and your platform surfaces status in its own portal, the UI is duplicated effort.

**Where Flux's composability matters.** If you are building a platform that programmatically creates and manages delivery configuration, having everything be a plain custom resource with no server-side application state is simpler to generate, template, and reason about. Flux tends to feel better when your platform is the primary user rather than a human.

**Multi-tenancy differs in kind.** Argo CD's projects give you a product-level tenancy model with SSO integration and per-project permissions, typically with one Argo CD serving many teams. Flux relies on Kubernetes-native tenancy - namespaced resources, service account impersonation, standard RBAC - which is cleaner conceptually but means you build the human-facing access story yourself.

**The things people wrongly believe are differentiators.** Both support Helm, Kustomize, and plain manifests. Both support multi-cluster. Both have health assessment, drift detection, and self-healing. Both are CNCF graduated with active communities. Anyone claiming one supports Helm and the other does not is out of date.

**Running both is a real anti-pattern.** It happens through team-by-team adoption and leaves you with two reconcilers, two mental models, two upgrade treadmills, and occasionally two things fighting over the same resource. Pick one for the organisation; that decision is more valuable than the choice itself.

## Example

```yaml
# Argo CD - one Application object, application-centric.
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: checkout, namespace: argocd }
spec:
  project: team-payments # product-level tenancy with SSO-backed RBAC
  source:
    repoURL: https://github.com/example/checkout-deploy
    targetRevision: v1.4.2
    path: envs/production
  destination: { server: https://kubernetes.default.svc, namespace: team-payments }
  syncPolicy:
    automated: { selfHeal: true, prune: true }
```

```yaml
# Flux - the same outcome as two composable resources. Source and reconciliation
# are separated, which is more moving parts and more reusable.
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata: { name: checkout, namespace: team-payments }
spec:
  interval: 1m
  url: https://github.com/example/checkout-deploy
  ref: { tag: v1.4.2 }
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata: { name: checkout, namespace: team-payments }
spec:
  interval: 5m
  path: ./envs/production
  prune: true
  sourceRef: { kind: GitRepository, name: checkout }
  # Kubernetes-native tenancy: reconcile AS the tenant's service account, so
  # the tenant cannot escalate beyond its own RBAC
  serviceAccountName: team-payments-deployer
  targetNamespace: team-payments
  healthChecks:
    - { apiVersion: apps/v1, kind: Deployment, name: checkout, namespace: team-payments }
```

```text
How to decide, in the order the questions matter:

  Will many product teams need to see deployment state themselves?
    yes, and we will not build a portal   -> Argo CD (the UI is the deciding factor)
    yes, and our portal will show it      -> either; Flux is less duplication
    no, teams interact via PRs only       -> either, lean Flux

  Is the platform generating delivery config programmatically at scale?
    yes  -> Flux composes more cleanly; everything is a plain custom resource
    no   -> either

  Do you need product-level tenancy with SSO and per-team permissions out of the box?
    yes  -> Argo CD projects
    no, Kubernetes RBAC and impersonation is enough -> Flux

  What does your team already run well?
    -> this outweighs everything above. Both are good; operational familiarity
       is worth more than any feature in the table.

  Whatever you choose: choose ONE for the organisation. Running both is the
  actual mistake.
```

## Interview tips

- Say clearly that both are mature and either works, then differentiate on operating model. Candidates who declare one objectively superior sound less credible than those who frame it as a fit decision.
- The UI as a support-load reducer for many teams is the most honest and most common real reason organisations pick Argo CD - present it as an engineering argument, not a preference.
- Flux's appeal when the platform itself is the primary user - everything a plain custom resource, easy to generate - is the corresponding argument and shows you think about programmatic use.
- Correct the myths: both do Helm, Kustomize, multi-cluster, drift detection, and self-heal. It signals current knowledge.
- End on "pick one for the organisation" - running both is the real anti-pattern, and it is the answer to the common follow-up about teams having adopted different tools.

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
