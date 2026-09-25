---
title: "How do you design the developer-facing API of a platform?"
id: 36
category: "Platform Architecture"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# How do you design the developer-facing API of a platform?

**Short answer:** Design it around the intent a developer has, not the resources you provision - `postgres: { size: small }`, not thirty RDS parameters. Make it declarative so it can be reconciled and reviewed, keep the required surface tiny with strong defaults, express choices as constrained enumerations rather than free-form values, and treat it as a versioned contract from the first day, because forty teams will encode it in their repositories.

## Detail

**Intent, not implementation.** The developer knows they need a small Postgres with daily backups. They do not know, and should not need to decide, the instance class, parameter group, subnet placement, or maintenance window. An interface that asks for those has moved the decision without removing it. The test: could you swap RDS for Cloud SQL without changing a single service's specification? If not, your API leaks implementation.

**Declarative, not imperative.** `kind: Service` with a desired state can be reconciled continuously, diffed in review, and made idempotent. A `platform create-database` call that mutates the world cannot be re-run safely, gives no record of intent, and drifts silently. Even a CLI should write a declaration and let a controller act on it.

**Constrained choice beats free-form.** `size: small | medium | large` is better than `cpu: 2300m`, for reasons that compound: you can change what "small" means for everyone, you can price and capacity-plan a bounded set, and you cannot receive a value nobody anticipated. Where a continuous value is genuinely needed, bound it.

**Defaults carry the policy.** Most fields should be omittable, and the defaults should be the compliant, safe, sensible choice: backups on, encryption on, private networking, resource requests set, an SLO created. This is where a platform delivers most of its value - a team that specifies nothing beyond `owner` and an image should still get a well-configured service.

**Sensible layering.** Put tier or criticality in the interface and let it drive many downstream defaults - replica counts, backup retention, review requirements, on-call routing. One declared fact producing ten correct decisions is the highest-leverage design move available.

**Validate at the edge, with useful messages.** Schema validation with real constraints, rejected at submission time with a message naming the field and the fix. An error surfacing three layers down in a controller log is a support ticket.

**Model dependencies as references, not embedded copies.** `dependsOn: [component:pricing]` lets you compute blast radius, notify consumers of breaking changes, and build the dependency graph incidents need. Copied configuration cannot be traversed.

**Think about the contract before the schema.** What are you promising? If `slo.availability: 99.9` appears in the interface, you are promising the platform delivers the alerting, dashboards, and error budget accounting for it. Fields imply obligations, and every field you add is one you support indefinitely.

**Design for non-human consumers too.** The same interface is increasingly driven by AI coding assistants and agents, often through an MCP server that exposes platform operations as tools. A small, declarative, strictly validated schema with actionable error messages is exactly what makes that safe - an agent cannot guess its way into thirty provider parameters, and a reviewable desired-state file keeps a human in the loop.

## Example

```yaml
# The full interface for a typical service. Two fields are required - owner and
# the image - and everything else has a default that is the compliant choice.
apiVersion: platform.example.com/v1
kind: Service
metadata:
  name: checkout
spec:
  owner: group:team-payments # REQUIRED - no unowned services
  tier: 1 # default: 3. Drives replicas, retention, review, on-call.

  runtime:
    image: ghcr.io/example/checkout:1.4.2 # REQUIRED
    port: 8080 # default: 8080
    size: medium # small|medium|large - not raw cpu/memory
    scaling: { min: 3, max: 30, metric: rps, target: 800 }
    # Defaults applied and visible via `platform explain`:
    #   resource requests + limits, PDB, topology spread, readiness and
    #   liveness probes, non-root, read-only root filesystem, seccomp

  dependencies: # intent, not provider resources
    - postgres: { size: small, backups: daily, pitr: true }
    - queue: { name: orders, dlq: true }

  dependsOn: # references - traversable for blast radius
    - component:pricing

  observability:
    slo: { availability: 99.9, latency: { threshold: 300ms, percentile: 99 } }
    # Implies an obligation: the platform creates the SLI recording rules,
    # the burn-rate alerts, the dashboard, and the error budget report.

  network:
    ingress: internal # internal|public|none - default none
```

```text
The equivalent leaky interface, for contrast. Same outcome, wrong abstraction:

  spec:
    rds:
      engine: postgres
      engineVersion: "17.4"
      instanceClass: db.t4g.small        <- provider-specific, developer must know
      allocatedStorage: 20                  the pricing and performance model
      dbSubnetGroupName: private-b          of one cloud
      parameterGroupName: pg17-default
      backupRetentionPeriod: 7
      preferredMaintenanceWindow: "sun:03:00-sun:04:00"
      multiAZ: true

  Nine decisions pushed to a developer, no default policy applied, and the
  interface cannot survive a move to another provider or even a change of
  instance family. Every service repository now contains your implementation.
```

## Interview tips

- "Intent, not implementation" with the swap test - could you change cloud provider without touching a service spec - is the strongest single point available here.
- Constrained enumerations over free-form values, and the reason (you can redefine "small" for everyone at once), is a detail that reads as hard-won.
- Say that defaults are where the policy lives. It reframes the interface as a compliance mechanism, which is how senior platform engineers think about it.
- The tier field driving many downstream defaults is a concrete, high-leverage example worth volunteering.
- "Every field is an obligation you support indefinitely" is the discipline that keeps interfaces small; interviewers probing for maturity are listening for exactly this.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
