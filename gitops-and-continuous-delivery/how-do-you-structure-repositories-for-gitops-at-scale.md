---
title: "How do you structure repositories for GitOps at scale?"
id: 89
category: "GitOps and Continuous Delivery"
difficulty: "Advanced"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# How do you structure repositories for GitOps at scale?

**Short answer:** Separate application source from deployment configuration, keep environments as directories or branches within a deployment repository rather than as separate repositories, and let the platform own a fleet repository that defines what every cluster contains. The structure is really an access-control and blast-radius decision: repository boundaries determine who can approve a change to production, so draw them where your review requirements differ.

## Detail

**Separate source from deployment state.** Mixing them means every image tag update commits to the application repository, polluting its history and coupling the deploy record to code review. It also creates a loop where CI commits to the repository that triggers CI. Two repositories - or at minimum a clearly separated directory with different review rules - is the standard shape.

**Environments as directories, not repositories.** A repository per environment sounds tidy and produces the worst outcome: promotion becomes a cross-repository copy, diffing staging against production is manual, and configuration drifts because nothing forces the comparison. Directories in one repository make promotion a diff you can read and review.

**Avoid branch-per-environment for promotion.** It seems natural and causes persistent pain: merges carry unintended changes, cherry-picking becomes routine, and the branches diverge in ways nobody can fully explain. Directories with explicit per-environment overlays, plus an explicit promotion commit, are clearer. Branches are fine for other purposes - just not as the promotion mechanism.

**The repository set that works at scale:**

| Repository            | Owner         | Contains                                               |
| --------------------- | ------------- | ------------------------------------------------------ |
| `<service>` (per app) | Product team  | Application source, Dockerfile, tests, `score.yaml`    |
| `<service>-deploy`    | Product team  | Rendered or templated manifests, per-environment dirs  |
| `platform-bundle`     | Platform team | What every cluster contains, versioned                 |
| `fleet`               | Platform team | Cluster inventory, labels, which bundle version        |
| `platform-modules`    | Platform team | Compositions, Helm charts, reusable modules, versioned |

**Repository boundaries encode review requirements.** Production configuration for a tier-1 service may need two approvals including someone from the owning team; the platform bundle may need platform-team approval; a preview environment may need none. Since branch protection is per-repository and per-path, decide the boundaries by asking who must approve what - that is the real design driver, not tidiness.

**One deployment repository per team, not per service, once you have enough services.** Per-service repositories multiply the number of places to configure branch protection, secrets scanning, and reconciler registration. A team-level deployment repository with one directory per service is usually the sweet spot; hundreds of services may justify a monorepo with path-based ownership.

**Keep the reconciler's scope narrow.** If an agent watches a whole large repository, every commit triggers evaluation of everything. Scope each application to a path and, where the tool supports it, use path-based triggers. At scale this is the difference between reconciliation that keeps up and a permanent backlog.

**Pin production, float non-production.** Development environments can track a branch. Production should reference an immutable tag or commit, so what is deployed is unambiguous and rollback is selecting a previous reference. A production application tracking `main` means you cannot say what is running without checking the commit history.

## Example

```text
Per-team deployment repository. Environments are directories; promotion is a diff.

  team-payments-deploy/
    base/                             shared across environments
      checkout/
        service.yaml                  the platform Service resource
        kustomization.yaml
      refunds-worker/
        service.yaml
    envs/
      dev/
        kustomization.yaml            -> ../../base/..., replicas 1, dev image tag
        patches/
      staging/
        kustomization.yaml            -> production-shaped, staging endpoints
        patches/
      production/
        kustomization.yaml            -> pinned image tags, tier-1 review required
        patches/
          checkout-scaling.yaml
    CODEOWNERS
      /envs/production/  @team-payments @platform-approvers   <- review boundary
      /envs/dev/         @team-payments

  Promotion staging -> production is one readable diff:
    - image: ghcr.io/example/checkout:1.4.1
    + image: ghcr.io/example/checkout:1.4.2

  With a repository per environment, that diff does not exist as an artefact -
  which is why the structure, not the tooling, is what makes promotion reviewable.
```

```text
Platform-owned repositories:

  platform-bundle/                    what a cluster contains, versioned
    components/
      ingress/  cert-manager/  policy-engine/  otel-collector/  csi/
    values/
      base.yaml
      env-production.yaml             variation resolved from cluster labels,
      env-staging.yaml                not per-cluster files
      scope-pci.yaml
    (tagged v2026.08.1, v2026.08.2 ...)

  fleet/                              the inventory the generators read
    clusters/
      prod-eu-1.yaml                  labels: env, region, scope, bundle version
      prod-pci-eu-1.yaml
      staging-eu-1.yaml

  platform-modules/                   versioned, tested, consumed by reference
    compositions/postgres/  charts/service/  terraform/vpc/
```

```yaml
# Scope the reconciler to a path so one commit does not re-evaluate everything.
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata: { name: team-payments-production, namespace: argocd }
spec:
  goTemplate: true # Go templates; the older {{path}} syntax cannot fail on a missing key
  goTemplateOptions: ["missingkey=error"]
  generators:
    - git:
        repoURL: https://github.com/example/team-payments-deploy
        revision: v2026.08.11 # production is PINNED, not tracking main
        directories:
          - path: envs/production/services/* # one Application per service
  template:
    metadata: { name: "prod-{{.path.basename}}" }
    spec:
      project: team-payments
      source:
        repoURL: https://github.com/example/team-payments-deploy
        targetRevision: v2026.08.11
        path: "{{.path.path}}"
      destination: { server: https://prod-eu-1.example.internal, namespace: team-payments }
      syncPolicy:
        automated: { selfHeal: true, prune: true }
```

## Interview tips

- Lead with the insight that repository boundaries encode review requirements. It reframes the question from filesystem tidiness to access control, which is what it actually is.
- Be firm that environments should be directories, and explain why repository-per-environment breaks promotion: the diff you need to review stops existing as an artefact.
- Say branch-per-environment is a trap and give the reason - unintended changes carried by merges, routine cherry-picking, unexplainable divergence.
- Pin production to an immutable reference and float non-production. "You cannot say what is running if production tracks main" is a crisp justification.
- Mention narrowing the reconciler's scope by path. At scale it is the difference between keeping up and a permanent reconciliation backlog, and it shows you have run this beyond a demo.

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
