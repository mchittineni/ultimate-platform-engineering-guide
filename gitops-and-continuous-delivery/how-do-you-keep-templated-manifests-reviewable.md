---
title: "How do you keep templated manifests reviewable?"
id: 50
category: "GitOps and Continuous Delivery"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# How do you keep templated manifests reviewable?

**Short answer:** Render the templates in CI and show the diff of the rendered output on the pull request - ideally by committing the rendered manifests so the diff is the artefact under review. The problem being solved is that a one-line change to a chart value or a shared library can produce a large and surprising change in the actual Kubernetes objects, and no human can reliably predict that by reading the template diff.

## Detail

**Why the template diff is insufficient.** A reviewer sees `replicaCount: 3` becoming `replicaCount: 6` and approves. What actually changed might also include a new pod anti-affinity rule because the chart's logic branches on replica count, a different resource request from a conditional, and a changed disruption budget. Bumping a shared chart version from 3.1.0 to 3.2.0 is the extreme case: one line in the diff, potentially hundreds of lines of change to real objects across dozens of services.

**The rendered-manifests pattern.** Render templates in CI and commit the output to a separate branch or directory, which is what the reconciler consumes. Consequences: the review artefact is the real Kubernetes objects; no templating happens at deploy time so there is no chance of rendering differently in production; policy and schema validation run against the actual output; and rollback is reverting to a previous rendered state. The costs are a generated artefact in version control, a rendering step to maintain, and larger diffs - which is the point, not a drawback.

**If you do not commit rendered output, at minimum post the diff.** A CI job that renders both the base and the head of the pull request and comments the difference gives you the review benefit without the committed artefact. It is weaker - production still renders at deploy time, so the possibility of divergence remains - but it is far better than reviewing template changes blind.

**Make chart and module upgrades visible fleet-wide.** When a shared chart version changes, the interesting question is what it does to all consumers, not to one. A platform team should render the change against every consumer and summarise it before merging. That is how you discover that a "safe" default change removes a probe from twelve services.

**Reduce template complexity as a design goal.** Templates with deep conditional logic are unreviewable by construction. Prefer more, simpler variants over one chart with thirty toggles, and push conditional behaviour into a controller that reconciles from a small declarative spec - where the logic is testable code rather than string interpolation in YAML.

**Validate the rendered output, not the template.** Schema validation against the target cluster's API versions, policy checks, and a server-side dry run all operate on rendered manifests. This is how you catch a removed API version or a policy violation before merge rather than at sync time.

**Keep provenance in the output.** Annotate rendered manifests with the chart version, the values, and the source commit they came from. When someone asks in six months why a field is set the way it is, that annotation is the answer, and without it the generated artefact is genuinely hard to reason about.

## Example

```text
The problem, concretely. Two diffs for the same change.

WHAT THE REVIEWER SEES (template diff)
  -  version: 3.1.0
  +  version: 3.2.0

WHAT ACTUALLY CHANGES (rendered diff, 3 services shown of 41)
  team-payments/checkout/deployment.yaml
    +     topologySpreadConstraints:
    +       - maxSkew: 1
    +         topologyKey: topology.kubernetes.io/zone
    -     livenessProbe:                       <-- REMOVED. The new chart default
    -       httpGet: { path: /healthz }             changed and this service relied
    -       initialDelaySeconds: 30                 on the old one.
  team-search/indexer/poddisruptionbudget.yaml
    -     minAvailable: 2
    +     maxUnavailable: 1                    <-- semantics changed for a
                                                   1-replica deployment
  team-data/etl/deployment.yaml
    -     resources: { requests: { memory: 4Gi } }
    +     resources: { requests: { memory: 512Mi } }   <-- new default; this
                                                            workload will OOM

  One line reviewed. Three latent incidents. This is why the rendered diff is
  the artefact that must be under review.
```

```yaml
# CI: render, validate, and post the rendered diff. Fails on removed APIs and
# policy violations before merge rather than at sync time.
name: render-and-review
on: pull_request

permissions:
  contents: read
  pull-requests: write

jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with: { fetch-depth: 0 }

      - name: Render base and head
        run: |
          git worktree add /tmp/base "${{ github.event.pull_request.base.sha }}"
          ./scripts/render-all.sh /tmp/base /tmp/rendered-base
          ./scripts/render-all.sh .       /tmp/rendered-head

      - name: Validate the rendered output, not the template
        run: |
          kubeconform -strict -kubernetes-version 1.32.0 /tmp/rendered-head
          kyverno apply policies/ --resource /tmp/rendered-head
          pluto detect-files -d /tmp/rendered-head   # removed/deprecated APIs

      - name: Post the rendered diff
        run: |
          diff -ru /tmp/rendered-base /tmp/rendered-head > /tmp/rendered.diff || true
          python3 scripts/comment_diff.py /tmp/rendered.diff
```

```yaml
# Provenance in the committed output, so a generated file is still explicable.
# envs/production/checkout/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout
  namespace: team-payments
  annotations:
    platform.example.com/rendered-by: "render-all.sh"
    platform.example.com/chart: "platform-modules/charts/service@3.2.0"
    platform.example.com/values-hash: "sha256:1b9d6bcd..."
    platform.example.com/source-commit: "abc123def"
    platform.example.com/rendered-at: "2026-08-11T09:14:22Z"
spec:
  replicas: 6
```

## Interview tips

- Open with the concrete failure: a one-line chart version bump producing hundreds of lines of real change. It makes the problem obvious immediately.
- "Render in CI, review the rendered diff" is the answer; committing the rendered output is the strong form, and be ready to give both its benefits and its costs.
- The point that no templating happens at deploy time is the security and correctness argument for committed renders - production cannot render differently from what was reviewed.
- Rendering a shared chart change against every consumer before merge is the platform-team version of this practice and a strong differentiator.
- Mention validating the rendered output - schema against the target Kubernetes version, policy, removed APIs. Validating the template catches nothing useful.
- Provenance annotations are the answer to the obvious objection that generated files in Git are unreviewable and unexplainable.

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
