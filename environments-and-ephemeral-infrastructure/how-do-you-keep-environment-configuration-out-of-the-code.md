---
title: "How do you keep environment configuration out of the code?"
id: 109
category: "Environments and Ephemeral Infrastructure"
difficulty: "Beginner"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# How do you keep environment configuration out of the code?

**Short answer:** Build the application once and have it read everything that differs between environments - hostnames, credentials, limits, feature flag settings - at start-up or run time from outside the artefact: environment variables, mounted files, a secrets manager, or a flag service. The code contains the _names_ of settings and safe defaults, never the per-environment values. That way the exact image tested in staging is the one that runs in production, and changing a value does not need a rebuild.

## Detail

**Why it matters.** If a database URL for production is compiled into the code, or selected with `if env == "prod"` branches, then every environment effectively runs different code, a configuration change needs a full build and release, and secrets end up in the repository history. Separating configuration is what makes "build once, promote the same artefact" possible. It is the configuration principle from the Twelve-Factor App methodology, and it is still the right default.

**What counts as configuration.** Anything that changes between environments or deployments: service endpoints, database names, credentials, timeouts, replica-specific tuning, log levels, and which features are switched on. Things that do _not_ change between environments - routing tables inside the app, business rules, the list of supported currencies - are code, and belong in the repository with tests.

**The mechanisms, from simplest:**

| Mechanism             | Good for                                   | Watch out for                                       |
| --------------------- | ------------------------------------------ | --------------------------------------------------- |
| Environment variables | Simple, flat values; universally supported | Visible in process listings and crash dumps         |
| Mounted config files  | Structured config, larger values           | The app must reload or restart to pick up changes   |
| Secrets manager       | Credentials, keys, tokens                  | Needs workload identity to fetch without a password |
| Feature flag service  | Values that change at run time, per user   | Flags are code paths too - they need cleaning up    |

**Secrets are configuration with extra rules.** They must never sit in the repository, even encrypted by hand, and ideally not in plain Kubernetes manifests either. The usual pattern is a secrets manager such as Vault, OpenBao, or a cloud provider's secret store, with a sync mechanism or a CSI driver delivering the value into the pod, and the workload proving who it is through workload identity rather than a stored password. See [how to manage secrets as a platform capability](../platform-security/how-do-you-manage-secrets-as-a-platform-capability.md).

**Keep the per-environment values declarative and versioned.** Configuration being outside the code does not mean it should be outside version control. Non-secret values live in a configuration repository or in per-environment overlays, reviewed like code, so you can see exactly what changed between Tuesday and Wednesday. Only secret values live in the secrets manager, and the repository holds a reference to them.

**Validate at start-up.** An application that starts with a missing setting and fails on the first request is harder to debug than one that refuses to start and names the missing variable. Fail fast, with a clear message.

**Who the platform serves.** Application engineers should only have to declare what configuration their service needs; the platform provides the injection path - the same one in every environment - plus the secrets store and the flag service. Having the same mechanism everywhere is itself a parity requirement: if staging reads a file and production reads a secrets manager, you have not tested the production path.

**Trade-offs.** More moving parts at run time: if the secrets manager is down, new pods cannot start, so it needs to be highly available and cached sensibly. Too much configuration is also a smell - if every behaviour is a setting, nobody can reason about which combinations are tested. Keep the number of knobs small.

## Example

```yaml
# base/deployment.yaml - the same in every environment. Only names, no values.
apiVersion: apps/v1
kind: Deployment
metadata: { name: checkout }
spec:
  selector: { matchLabels: { app: checkout } }
  template:
    metadata: { labels: { app: checkout } }
    spec:
      serviceAccountName: checkout # workload identity to fetch secrets
      containers:
        - name: app
          image: ghcr.io/example/checkout@sha256:9f2c8b1d... # identical everywhere
          envFrom:
            - configMapRef: { name: checkout-config } # per-environment values
          env:
            - name: DATABASE_PASSWORD
              valueFrom:
                secretKeyRef: { name: checkout-db, key: password } # synced from the secrets manager
```

```yaml
# overlays/staging/kustomization.yaml - values differ, structure does not.
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../../base]
configMapGenerator:
  - name: checkout-config
    literals:
      - DATABASE_HOST=checkout-db.staging.internal
      - PAYMENTS_URL=https://payments-sandbox.example.com
      - LOG_LEVEL=info
      - REQUEST_TIMEOUT=5s
```

```text
What the application does at start-up:

  $ checkout
  config: DATABASE_HOST=checkout-db.staging.internal
  config: PAYMENTS_URL=https://payments-sandbox.example.com
  config: DATABASE_PASSWORD=<set, redacted>
  error: required setting REQUEST_TIMEOUT_RETRIES is not set - refusing to start
```

## Interview tips

- Open with the purpose: the same artefact everywhere, so what you tested is what you run. Configuration separation is the means.
- Draw the line between configuration (differs per environment) and code (does not), with an example of each.
- Treat secrets separately - a secrets manager plus workload identity - and say plainly they never go in the repository.
- Point out that non-secret configuration should still be versioned and reviewed; "outside the code" is not "outside Git".
- Mention fail-fast validation at start-up. It is small, practical, and shows production experience.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
