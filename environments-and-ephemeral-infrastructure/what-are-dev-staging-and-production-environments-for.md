---
title: "What are dev, staging, and production environments for?"
id: 106
category: "Environments and Ephemeral Infrastructure"
difficulty: "Beginner"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# What are dev, staging, and production environments for?

**Short answer:** They are separate running copies of a system, each with a different job. Development is where engineers try changes cheaply and break things freely, staging is where a candidate release is checked in conditions close to production, and production is where real users and real data live. The point of having several is that the same built artefact moves through them in order, gaining confidence at each step, so that the risky learning happens before it can hurt a customer.

## Detail

**An environment is a complete place for the software to run.** It is the compute, the network, the databases, the secrets, the configuration values, and the other services the application talks to. Two environments can run the identical container image and still behave differently because everything around the image differs - which is exactly why you have more than one, and also why the differences need to be deliberate.

**Development is optimised for speed of change.** Engineers deploy often, sometimes many times an hour, and expect things to break. Data is fake or synthetic, access is broad within the team, and nothing in it is precious. If development feels expensive to break, people stop experimenting there and start experimenting somewhere worse.

**Staging is optimised for confidence.** It exists to answer one question: will this exact release behave correctly in production? That means it should match production in the ways that change behaviour - the same artefact, the same database engine and version, TLS, authentication, network policy, feature flag values, and more than one replica - while being smaller and cheaper. Integration tests, end-to-end tests, performance smoke tests, and manual acceptance happen here.

**Production is optimised for safety and stability.** Access is narrow and audited, changes arrive through a pipeline rather than a terminal, and the data belongs to customers. Monitoring, alerting, backups, and on-call exist for this environment first.

**The rule that ties them together: build once, promote the same artefact.** CI builds an image once, identified by its digest, and that exact image is deployed to development, then staging, then production. Only configuration changes between them. Rebuilding for each environment means production runs a binary nobody tested.

| Environment | Main user                     | Data                    | Access             | Change rate      |
| ----------- | ----------------------------- | ----------------------- | ------------------ | ---------------- |
| Development | Engineers writing the change  | Synthetic, disposable   | Broad, within team | Constant         |
| Staging     | Engineers, QA, release owners | Seeded, production-like | Restricted         | Per release      |
| Production  | Customers                     | Real                    | Narrow, audited    | Controlled, safe |

**Who the platform serves here.** Application engineers are the users. The platform's job is to make every environment available from the same definition, so a team does not hand-build staging and discover it has quietly drifted from production. A good platform also makes promotion a single, visible step rather than a copy-and-paste exercise.

**Trade-offs and common problems.** A single shared staging environment becomes a queue: two teams cannot test conflicting changes, and a broken deploy blocks everyone. Many organisations add per-pull-request ephemeral environments to relieve that contention - see [what an ephemeral environment is and when it is worth it](./what-is-an-ephemeral-environment-and-when-is-it-worth-it.md). The other trap is chasing perfect parity: staging will never have real traffic or real data skew, so the final validation still happens in production, made safe with progressive delivery and feature flags. The three-tier model is a convention, not a law; some teams run only preview environments plus production.

## Example

```text
One image digest, three environments, only configuration differs.

  CI builds ghcr.io/example/checkout@sha256:9f2c8b1d...   (once)
        |
        v
  DEVELOPMENT      deploy on every merge to main
    replicas 1     database: dev Postgres, synthetic data
    flags: dev     access: whole team
        |
        v  automated tests pass
  STAGING          deploy the same digest
    replicas 3     database: same engine and version as prod, seeded data
    flags: prod values                   access: restricted
        |
        v  approval + checks pass
  PRODUCTION       deploy the same digest, progressively
    replicas 30    database: real customer data
    flags: prod    access: pipeline only, break-glass for humans
```

```text
# One definition, per-environment values - so staging cannot drift structurally.
deploy/
  base/
    deployment.yaml        # image, probes, security context: shared
    kustomization.yaml
  overlays/
    dev/kustomization.yaml         # replicas: 1, dev config values
    staging/kustomization.yaml     # replicas: 3, prod-like values
    production/kustomization.yaml  # replicas: 30, prod values
```

## Interview tips

- Give each environment its purpose in one phrase - speed, confidence, safety - rather than just listing names.
- Say "build once, promote the same artefact" early. It is the single most important rule and the one beginners most often miss.
- Name the user: application engineers, and the platform's job of generating every environment from one definition.
- Expect the follow-up "what if staging is always broken or busy?" - talk about contention, ephemeral environments, and fixing staging's reliability first. The deeper version is [what environment parity actually requires](./what-does-environment-parity-actually-require.md).
- Admitting that staging cannot fully reproduce production, and that progressive delivery covers the gap, sounds more experienced than claiming it can.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
