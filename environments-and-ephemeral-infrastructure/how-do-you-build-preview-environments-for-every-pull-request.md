---
title: "How do you build preview environments for every pull request?"
id: 116
category: "Environments and Ephemeral Infrastructure"
difficulty: "Advanced"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# How do you build preview environments for every pull request?

**Short answer:** Make the environment a declarative object created from the pull request, reconciled like anything else, with a namespace, a wildcard DNS entry and TLS certificate, a database restored from a template snapshot rather than migrated from empty, request-level routing to a shared baseline for services you are not deploying, and a hard TTL. Then optimise relentlessly for time to ready, because that number determines whether anyone uses it.

## Detail

**Drive it from the pull request, declaratively.** A pull-request event creates an `Environment` object; a controller reconciles it into a namespace, workloads, data, ingress, and credentials; closing the pull request deletes the object and the controller tears everything down through owner references. Doing this with a create script and a delete script instead means the two drift and you accumulate orphans.

**Isolation by namespace, with the same tenancy controls as anywhere else.** Quotas so one preview cannot exhaust the cluster, network policy so previews cannot reach each other or production, and its own service account and secrets. A preview reachable from another preview is a confusing test; a preview that can reach production is a serious incident waiting to happen.

**Solve DNS and TLS once with wildcards.** A wildcard record and a wildcard certificate for `*.preview.example.internal` means a new preview needs no DNS or certificate provisioning at all - which removes both a latency source and a per-environment failure mode. Requesting a certificate per preview also risks hitting issuance rate limits.

**Never expose previews publicly.** Authentication in front of every preview URL, ideally your single sign-on. Preview environments accumulate real-looking data and are otherwise an unauthenticated copy of your application on the internet.

**Restore data from a template, do not migrate from empty.** Running the full migration history plus seeding on every environment is slow and gets slower forever. Maintain a prepared snapshot, refreshed nightly, and restore it - or use a database that supports cheap copy-on-write clones - see [how to give each pull request its own database](./how-do-you-give-each-pull-request-its-own-database.md). This is usually the single biggest lever on time to ready.

**Handle the services you are not deploying with request-level routing.** Deploy only what the pull request changes. Everything else routes to a shared baseline running the current main branch. A header carrying the preview identity is propagated through calls, and the routing layer sends a request to the preview's own version of a service if it exists and to the baseline otherwise. This is the mechanism that makes previews affordable beyond a handful of services, and its requirement - context propagation through every hop - is worth naming because it is real work. OpenTelemetry baggage is a convenient carrier, because services instrumented with OpenTelemetry already forward it; a sidecar or waypoint then lifts the value into the routing header. The routing rule itself is increasingly written as a Gateway API `HTTPRoute` with a header match rather than a mesh-specific resource; it is the portable form, and it is what Istio's ambient mode uses for waypoint routing.

**Post the URL and the state into the pull request.** A comment with the URL, what was deployed, what came from the baseline, and the seed data version. Reviewers should not have to work out how to reach it, and knowing which services are previewed versus baseline prevents misleading conclusions.

**Reap aggressively and from several triggers.** Pull request closed or merged, TTL expired, and an idle timeout. Report what is running and what it costs, so the capability stays defensible.

## Example

```yaml
# Created by the PR event, reconciled like any other resource. Deleting this
# object tears down everything through owner references.
apiVersion: platform.example.com/v1
kind: Environment
metadata:
  name: pr-4821
  namespace: previews
spec:
  type: ephemeral
  ttl: 72h
  idleTimeout: 8h # reaped early if nobody touches it
  reapOn: [pull-request-closed, pull-request-merged, ttl-expired, idle]
  pullRequest: { repo: example/checkout, number: 4821, author: alice }
  services: # ONLY what this PR changes
    - { name: checkout, image: "ghcr.io/example/checkout@sha256:9f2c8b1d..." }
    - { name: pricing, image: "ghcr.io/example/pricing@sha256:3c7ab2e0..." }
  baseline: shared-preview-baseline # the other 58 services
  data:
    source: template
    template: checkout-seed-v14 # nightly snapshot, restored not migrated
    method: clone # copy-on-write where the engine supports it
  ingress:
    host: pr-4821.preview.example.internal # matches the wildcard cert
    auth: sso-required
  quota: { cpu: "4", memory: 8Gi, pods: 20 }
```

```yaml
# Request-level routing: the preview's own version if it exists, baseline otherwise.
# This is what makes previews viable without deploying 60 services per PR.
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata: { name: pricing, namespace: shared-preview-baseline }
spec:
  hosts: [pricing.preview.svc.cluster.local]
  http:
    - match:
        - headers:
            x-preview-id: { exact: pr-4821 }
      route:
        - destination: { host: pricing.previews-pr-4821.svc.cluster.local }
    - route: # everything else falls through to the baseline
        - destination: { host: pricing.shared-preview-baseline.svc.cluster.local }
```

```text
Time to ready - where the minutes actually go, and what each fix bought.

  STAGE                          naive     optimised   how
  image build                    6m00s     0m20s       cached layers; and the
                                                       image is already built by CI
  namespace + quota + netpol     0m05s     0m05s
  DNS record                     1m30s     0m00s       wildcard record - nothing
                                                       to provision per preview
  TLS certificate                2m00s     0m00s       wildcard cert, reused
  database create                1m10s     0m10s
  migrations from empty          4m40s     -           replaced entirely
  restore from template          -         0m35s       nightly snapshot, CoW clone
  seed data                      3m20s     -           included in the template
  workloads ready                1m15s     0m50s       pre-warmed node capacity
                                -----     -----
  TOTAL                          20m00s    2m00s

  Under 5 minutes: previews get used. Over 15: people merge without waiting, and
  the whole capability is wasted effort. The data stage was the biggest lever.

  $ platform previews list
    pr-4821  team-payments  2h  running   ~$0.42 so far
    pr-4790  team-search   19h  IDLE 9h   -> reaping (idle timeout)
    pr-4712  team-data     71h  running   -> TTL expires in 1h
    total running: 14   estimated monthly at this rate: ~$1,850
```

## Interview tips

- Lead with the declarative object reconciled by a controller, and explain why: create and delete scripts drift, and orphaned environments are the predictable result.
- Wildcard DNS and TLS is a small, concrete optimisation that removes both latency and a failure mode - and mentioning certificate issuance rate limits shows you have hit it.
- Restoring from a template instead of migrating from empty is the single biggest time-to-ready lever. Have the stage-by-stage breakdown ready; it is persuasive.
- Request-level routing to a shared baseline is the answer to scale, and naming its cost - context propagation through every hop - is what makes it credible.
- Authentication in front of every preview is the security point. An unauthenticated copy of your application with realistic data is a genuine exposure.
- Multiple reap triggers including an idle timeout, plus a cost report, is what keeps the capability defensible in a budget conversation.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
