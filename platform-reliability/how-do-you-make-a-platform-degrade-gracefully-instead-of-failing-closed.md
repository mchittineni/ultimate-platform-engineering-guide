---
title: "How do you make a platform degrade gracefully instead of failing closed?"
id: 108
category: "Platform Reliability"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# How do you make a platform degrade gracefully instead of failing closed?

**Short answer:** Decide, for each platform component, whether its unavailability should stop change or stop serving - and then make sure only the second category can affect running workloads. Control-plane components should fail open with respect to traffic and fail loudly with respect to change; the dangerous cases are components that sit in the request path and reject when they cannot function, because an outage of the component becomes an outage of everything.

## Detail

**The principle: a control-plane failure should stop change, not stop serving.** Running workloads should continue when the reconciler, the provisioning controller, the portal, or the pipeline is unavailable. If any of those can take down production traffic, a management component has acquired data-plane blast radius and that is a design error rather than bad luck.

**The classic failure is a fail-closed admission webhook.** A validating webhook with `failurePolicy: Fail` on Pods means that when the webhook is unreachable, no Pod can be created anywhere - including the webhook's own replacement Pods, and including anything needed to fix it. It is self-amplifying: the outage prevents the recovery. Three mitigations, and you want all of them: make the webhook genuinely highly available, exclude its own namespace and kube-system with a `namespaceSelector`, and keep a documented, rehearsed procedure to delete the configuration.

**Fail-closed is sometimes correct, and the answer must acknowledge that.** For a control you must never bypass - image signature verification in a regulated environment - allowing workloads through unverified may be worse than blocking them. The point is that this must be a deliberate, documented decision with the availability investment and break-glass to match, not a default nobody examined.

**Cache and serve stale rather than failing.** Many platform dependencies can be tolerated if the consumer holds a last-known-good copy: flag rulesets cached on disk, secrets read at startup rather than per request, policy bundles cached by the enforcement point, service discovery data retained by proxies. Serving slightly stale data is almost always better than serving errors, and this is the single most reusable degradation technique.

**Keep synchronous per-request dependencies out of the request path.** A secret read per request, a remote flag evaluation per call, or an authorisation lookup with no cache each turn a control-plane service into a data-plane one. Reading at startup and caching, or evaluating locally from streamed rules, moves the dependency off the hot path.

**Degrade the platform's own features before degrading consumers.** If the telemetry pipeline is saturated, drop platform-internal metrics before tenant traces. If capacity is short, evict platform batch work before tenant workloads. The platform should absorb pressure rather than pass it on.

**Make degradation visible.** Silent degradation is worse than failure, because nobody investigates. If policy is not being enforced because the engine is unavailable, that should be loudly visible - a fired alert and a stated status - rather than an unnoticed gap. The same applies to stale flag rules and stale service discovery data.

**Write down the expected behaviour per component and then test it.** A table of "if this is unavailable, what happens" is the design artefact, and a game day that removes each component and verifies the actual behaviour is what turns it from an intention into a fact. Components almost always behave differently from the table the first time you check.

## Example

```text
The degradation table - the design artefact, verified by game day.

  COMPONENT                UNAVAILABLE -> WHAT HAPPENS               PLANE
  GitOps reconciler        deploys pause; running workloads fine     control ✓
                           new merges queue and apply on recovery
  provisioning controller  no new resources; existing ones fine      control ✓
  portal / catalogue       cannot browse; nothing else affected      control ✓
  CI system                cannot build; running workloads fine      control ✓
  policy webhook (Ignore)  policy NOT ENFORCED, loudly alerted;      control ✓
                           workloads continue
  policy webhook (Fail)    NO PODS CAN BE CREATED ANYWHERE           control ✗
                           -> control-plane component with data-plane
                              blast radius. Requires HA + self-exclusion
                              + rehearsed removal, or use Ignore.
  telemetry collector      metrics/traces buffered locally, then      control ✓
                           dropped; workloads unaffected
  secret store             new pods cannot start; RUNNING pods fine   control ✓
                           (because secrets are read at startup and
                            cached - if they were read per request,
                            this would be a data-plane outage)
  flag provider            last-known-good ruleset from disk;         control ✓
                           evaluation continues; rules go stale
                           (visible in status)
  ingress controller       TRAFFIC STOPS                              data
  DNS                      TRAFFIC STOPS                              data
  mesh sidecars            that workload's traffic stops              data
  auth in request path     everything fails                           data

  Every ✓ in the control-plane column is a deliberate design choice. The one ✗
  is the row that needs work.
```

```yaml
# The single most consequential setting in a platform. Both values are
# defensible; the default must not be accidental.
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata: { name: platform-policy }
webhooks:
  - name: validate.platform.example.com
    # Ignore: an outage means policy is temporarily unenforced (and alerted).
    # Fail:   an outage means nothing can be created anywhere, including the fix.
    failurePolicy: Ignore
    timeoutSeconds: 5 # the API server WAITS for you - a slow webhook is a slow cluster
    namespaceSelector:
      matchExpressions:
        # Self-exclusion: the webhook must never be able to block its own
        # replacement pods, or the outage prevents the recovery.
        - key: kubernetes.io/metadata.name
          operator: NotIn
          values: [kube-system, platform, policy-system]
    rules:
      - operations: ["CREATE", "UPDATE"]
        apiGroups: ["apps"] # narrow - not every resource and every verb
        apiVersions: ["v1"]
        resources: ["deployments", "statefulsets"]
```

```yaml
# Where fail-closed IS correct - and what it obliges you to do.
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: verify-image-signatures
  annotations:
    platform.example.com/fail-closed-justification: >
      Running an unverified image in the PCI-scoped cluster is worse than being
      unable to start pods. Deliberate, approved by security-lead 2026-04-11.
    platform.example.com/availability-commitment: >
      5 replicas across 3 zones, PDB minAvailable 3, dedicated node pool,
      excluded from its own enforcement. SLO 99.99%.
    platform.example.com/break-glass: >
      RB-118: delete this configuration. Requires break-glass activation, alerts
      #security, and the deletion is auto-reverted after 30 minutes.
webhooks:
  - name: verify.images.platform.example.com
    failurePolicy: Fail # deliberate, with the investment above to justify it
    namespaceSelector:
      matchExpressions:
        - key: kubernetes.io/metadata.name
          operator: NotIn
          values: [kube-system, platform, policy-system]
```

```text
Game day - because components behave differently from the table:

  $ platform game-day degradation --component policy-webhook

    1. scale the webhook to 0
       expected: policy unenforced, alert fires, pods still create
       ACTUAL:   ✓ pods create, ✓ alert fired in 40s
    2. scale the telemetry collector to 0
       expected: buffered locally for 4h then dropped, workloads unaffected
       ACTUAL:   ✗ two services CRASHED - they used a blocking exporter with no
                    timeout. Found here rather than during an incident.
    3. block egress to the flag provider
       expected: last-known-good ruleset from disk, evaluation continues
       ACTUAL:   ✓ evaluation continued, ✓ staleness surfaced in status
    4. suspend the reconciler
       expected: deploys pause, running workloads unaffected
       ACTUAL:   ✓

  One finding out of four, and it was a data-plane consequence hidden inside a
  component everyone assumed was control-plane. That is why you run the drill.
```

## Interview tips

- The principle to lead with: a control-plane failure should stop change, not stop serving. Then identify which of your components violate it.
- The fail-closed webhook is the canonical example, and the self-amplifying property - the outage prevents its own recovery - is what makes it memorable.
- Give all three mitigations: high availability, `namespaceSelector` self-exclusion, and a rehearsed removal procedure. Naming self-exclusion specifically is a strong signal.
- Acknowledge that fail-closed is sometimes correct, and describe what it obliges you to do. Candidates who say "always fail open" sound naive about regulated environments.
- "Cache and serve stale rather than failing" is the most reusable technique - flag rulesets, secrets at startup, policy bundles, discovery data.
- Degrading the platform's own features before consumers' is a distinctive point that shows you think of the platform as absorbing pressure.
- Making degradation visible, and game-daying the table because components behave differently from expectations, is the close. The blocking-exporter finding is exactly the kind of thing only a drill reveals.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
