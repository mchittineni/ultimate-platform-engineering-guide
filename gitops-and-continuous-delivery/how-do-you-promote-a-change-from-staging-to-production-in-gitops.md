---
title: "How do you promote a change from staging to production in GitOps?"
id: 90
category: "GitOps and Continuous Delivery"
difficulty: "Advanced"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# How do you promote a change from staging to production in GitOps?

**Short answer:** Promote the same immutable artefact by changing one reference - an image digest or a rendered configuration version - in the production environment's directory, as an automated pull request that carries the evidence from the previous environment. What you must not do is rebuild, re-template, or hand-copy configuration between environments, because then the thing you tested is not the thing you deployed.

## Detail

**Promote the artefact, not the source.** The build happens once, producing an image identified by a digest. Promotion changes which digest production references. If a promotion triggers a rebuild, the binary in production was never tested anywhere - a subtly different dependency resolution or base image is enough to invalidate everything you verified.

**Reference by digest, not by tag, for production.** Tags are mutable; a digest is content-addressed and cannot be repointed. `image: app@sha256:...` is a guarantee, `image: app:1.4.2` is a convention. This matters most in exactly the case you care about - someone re-pushing a tag.

**Configuration must be promoted too, and it is the part people get wrong.** If staging renders a Helm chart with staging values and production renders the same chart with production values, you tested a different manifest than you deployed - a changed chart default or a template condition can differ. The strong form is to render manifests once, commit the rendered output per environment, and promote the rendered artefact. Then the diff between environments is fully visible and there is no hidden templating step at deploy time.

**Automate the promotion pull request and attach the evidence.** A bot should open the production change with what is being promoted, how long it soaked in staging, the SLO status during that window, the test and scan results, and the diff. That converts an approval from an act of faith into a review of evidence, and it makes the audit trail a by-product. You no longer have to build this bot from scratch: Kargo (open source, from Akuity) models stages and promotion of "freight" - image digests plus the config commits that go with them - on top of Argo CD, and Argo CD's source hydrator can write rendered manifests to an intermediate branch that you promote to the sync branch by pull request.

**Gate on evidence, not on elapsed time alone.** Useful gates: staging soak duration, no SLO burn during the soak, integration tests green against staging, no new critical vulnerabilities in the image, and the change window if one applies. Time-only gates give the appearance of caution without the substance.

**Promotion is not the same as rollout.** Merging the production change starts the rollout; how it reaches 100% - canary, progressive traffic shift, automated abort on burn rate - is a separate concern layered on top. Conflating the two is a common weakness in answers.

**Rollback is a revert, which is the main payoff of this design.** Because the previous state is a commit, rolling back is reverting to the previous digest reference. It is worth being precise, though: a revert restores configuration, not data. A schema migration that ran forward is not undone by reverting the deployment, which is why expand-and-contract migrations matter.

**Watch for cross-environment configuration drift.** Because environments are separate directories, they can silently diverge in ways unrelated to the promotion - a flag set in production during an incident and never mirrored. A scheduled report of non-image differences between staging and production catches this before it invalidates your testing.

## Example

```text
The pipeline, with the boundary between build, promote, and roll out made explicit.

  BUILD ONCE
    commit abc123 -> image ghcr.io/example/checkout@sha256:9f2c8b1d...
                  -> SBOM, signature, vulnerability scan attached
                  -> manifests RENDERED for each environment and committed

  DEPLOY TO STAGING (automatic)
    envs/staging/checkout.yaml: image digest updated by CI
    -> reconciled, soak begins

  EVIDENCE ACCUMULATES (4h soak)
    integration suite against staging ......... pass
    staging SLO burn during soak .............. none
    new critical/high CVEs in the image ....... 0
    signature verified ........................ yes

  PROMOTE (automated PR, human approval)
    envs/production/checkout.yaml
      - image: ghcr.io/example/checkout@sha256:4a1e77c2...
      + image: ghcr.io/example/checkout@sha256:9f2c8b1d...
    One line. Same artefact. Nothing rebuilt, nothing re-templated.

  ROLL OUT (separate concern, begins after merge)
    canary 5% -> 25% -> 50% -> 100%, automated abort on burn rate
```

```text
What the promotion PR body contains - so approval reviews evidence, not intent:

  Promote checkout to production

  ARTEFACT   ghcr.io/example/checkout@sha256:9f2c8b1d...   (built from abc123)
             signed: yes (keyless, CI identity verified)
             SBOM: attached   CVEs: 0 critical, 0 high, 3 medium (no fix available)

  SOAK       staging, 4h12m
             availability SLO: no burn      p99 latency: 240ms (baseline 245ms)
             error rate: 0.02% (baseline 0.03%)

  TESTS      integration 412/412   contract 38/38   load: p99 within budget

  DIFF       envs/production/checkout.yaml: image digest only
             NO other configuration changes in this promotion

  CONFIG DRIFT CHECK (staging vs production, excluding image)
             ⚠ production has FEATURE_NEW_PRICING=false, staging has true
               set during INC-2287 on 2026-08-04, never mirrored
             -> flagged: staging did not test the production configuration
```

```yaml
# Rendered-manifest promotion: no templating happens at deploy time, so the
# diff between environments is completely visible.
# envs/production/checkout/deployment.yaml  (generated, committed, reviewed)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout
  namespace: team-payments
  annotations:
    platform.example.com/rendered-from: "platform-modules/charts/service@v3.2.0"
    platform.example.com/source-commit: "abc123"
spec:
  replicas: 6
  template:
    spec:
      containers:
        - name: checkout
          image: ghcr.io/example/checkout@sha256:9f2c8b1d... # digest, not tag
```

## Interview tips

- "Promote the artefact, not the source" is the thesis. Follow it with the consequence: a rebuild on promotion means production runs a binary that was never tested.
- Digest over tag for production, with the specific reason that tags are mutable and can be re-pushed.
- The configuration-promotion point separates strong answers from average ones. Rendering manifests once and promoting the rendered output removes the hidden templating step at deploy time.
- Distinguish promotion from rollout explicitly. Merging starts the rollout; canary analysis and abort criteria are a separate layer.
- Be precise about rollback: reverting restores configuration, not data, which is why expand-and-contract migrations matter. That precision is a strong senior signal.
- The cross-environment configuration drift check - a production flag set during an incident and never mirrored - is a realistic detail worth volunteering.

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
