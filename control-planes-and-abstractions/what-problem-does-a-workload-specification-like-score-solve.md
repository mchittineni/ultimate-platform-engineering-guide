---
title: "What problem does a workload specification like Score solve?"
id: 71
category: "Control Planes and Abstractions"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# What problem does a workload specification like Score solve?

**Short answer:** It gives a developer one platform-agnostic description of what their workload needs - container, ports, environment, resource dependencies - which is then translated into whatever each target environment actually uses: Docker Compose locally, Kubernetes manifests in production. The problem it addresses is that developers otherwise maintain several parallel descriptions of the same service, which drift apart and cause the "works locally, fails in staging" class of failure.

## Detail

**The duplication problem it targets.** A typical service is described in a Compose file for local development, a Helm chart or Kustomize overlay for Kubernetes, and often a third form in CI. Each says the same things - image, ports, environment variables, dependencies - in different syntax, maintained separately. Adding an environment variable means editing three files, and forgetting one produces an environment-specific failure that is expensive to diagnose.

**How the model works.** The developer writes one specification declaring intent - "I need a Postgres and an object store, I listen on 8080, I need these variables". A per-environment implementation resolves that into concrete resources: locally a Compose service and a container, in production a managed database and a bucket with the platform's naming, tagging, and network placement. The specification does not mention any provider, and the resolution is where all environment-specific knowledge lives.

**Why this is a platform concern rather than a developer convenience.** The specification is a clean contract boundary. Developers own the workload description; the platform owns the resolution. That means the platform can change how a Postgres is provisioned - a different instance family, a new backup policy, a different cloud - without any service repository changing. It is the same "intent, not implementation" principle that governs good platform API design, applied to the whole workload.

**Where it fits relative to other tools.** It is not a replacement for Helm or Kustomize; those are usually what the resolution produces. It sits above them, and the value is a single developer-facing source with multiple targets. Nor is it a deployment tool: it generates configuration, and something else applies it.

**The honest limitations.** The specification is deliberately minimal, so anything unusual - a specific scheduling constraint, a sidecar, an odd probe - is not expressible and needs an escape hatch in the resolution layer. It adds a translation step, which means debugging sometimes involves reading generated output. And the local resolution is necessarily an approximation: a Postgres container is not a managed database with failover, so parity has limits you should state rather than pretend away.

**You may not need the standard to get the benefit.** Many platforms achieve exactly this with their own service specification and a controller that renders it per environment. The value is in the pattern - one developer-facing description, per-environment resolution - and a shared specification format mainly buys portability of skills and tooling between organisations. Being able to say that is more useful than advocating for a particular project.

## Example

```yaml
# score.yaml - one file, committed with the service. No provider names appear.
apiVersion: score.dev/v1b1
metadata:
  name: checkout

containers:
  checkout:
    image: ghcr.io/example/checkout:1.4.2
    variables:
      # Resource placeholders - resolved differently per environment
      DATABASE_URL: ${resources.db.url}
      BUCKET_NAME: ${resources.receipts.name}
      LOG_LEVEL: info
    resources:
      requests: { cpu: "250m", memory: "512Mi" }
      limits: { memory: "1Gi" }

service:
  ports:
    http: { port: 8080, targetPort: 8080 }

resources:
  db:
    type: postgres # intent - not "RDS", not "a container"
  receipts:
    type: object-storage
```

```text
The same file, resolved for two environments by two different implementations:

LOCAL (score-compose)
  $ score-compose generate score.yaml && docker compose up
    -> service `checkout` on :8080
    -> container `postgres:16` with a generated password
       DATABASE_URL=postgres://user:pass@db:5432/checkout
    -> MinIO container standing in for object storage
       BUCKET_NAME=checkout-receipts-local

PRODUCTION (score-k8s, or the platform's own controller)
  $ score-k8s generate score.yaml --env prod
    -> Deployment + Service + HPA + PDB + topology spread (platform defaults)
    -> PostgresInstance claim: size small, daily backups, PITR, private subnet,
       cost tags, secret written to `checkout-db-conn`
       DATABASE_URL sourced from that secret, never in the manifest
    -> S3 bucket: naming convention `example-team-payments-checkout-receipts`,
       encryption, lifecycle policy, access bounded to the workload identity

  Same declaration. The developer never learned RDS parameter groups or bucket
  policies, and the platform can change either resolution for every service at
  once without touching a single service repository.
```

```text
The limitation to be honest about:

  Local Postgres container          Production managed Postgres
    single instance                   multi-AZ with failover
    no backups                        daily + PITR
    no connection limits worth        connection pooling, real limits
    speaking of
    no TLS                            TLS required

  Parity is on interface, not behaviour. A connection-pool exhaustion bug or a
  failover-handling bug will not reproduce locally, and the specification does
  not claim otherwise. Say this before an interviewer says it to you.
```

## Interview tips

- Frame it as removing duplicated descriptions of the same workload, and name the concrete symptom - "works locally, fails in staging" from a variable added to two of three files.
- The contract boundary is the platform-engineering point: developers own the workload description, the platform owns the resolution, so provisioning can change with no service repository edits.
- Be clear it is not a replacement for Helm or Kustomize - it typically generates them - and not a deployment tool.
- State the parity limitation yourself. A local container is not a managed database, and pretending otherwise is the weak version of this answer.
- The most useful close is that you can get most of the value with your own service specification, and a shared format mainly buys portability. It shows you value the pattern over the branding.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
