---
title: "How do you manage secrets as a platform capability?"
id: 124
category: "Platform Security"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# How do you manage secrets as a platform capability?

**Short answer:** Start by eliminating the secrets that do not need to exist - workload identity and database IAM authentication remove whole categories - then for what remains, provide one store with per-tenant path scoping, delivery by reference rather than by copy, rotation that does not require a deploy, and an audit trail of every read. The platform's job is that no team ever has to invent a way to get a credential to a process.

## Detail

**The hierarchy to work down, because each step is better than the one below:**

1. **No secret.** Federated workload identity to the cloud, IAM authentication to the database, mTLS between services. Nothing to store, rotate, or leak.
2. **A secret the platform generates and nobody sees.** When the platform provisions a database, it creates the credential and writes it where the workload can read it. No human ever holds it.
3. **A secret referenced from a store.** A declaration naming a path; a controller or CSI driver fetches the value at runtime.
4. **A secret encrypted in version control.** Workable, but the ciphertext is permanent and rotation requires a commit.
5. **A secret pasted into a variable somewhere.** What you are replacing.

Most conversations start at level three. The valuable move is to ask which secrets can be moved to one or two.

**Scope paths per tenant and enforce it.** A team should read `secret/team-payments/*` and nothing else. Flat namespaces with a shared read policy are a common finding, and because secrets are the material that lets you cross every other boundary, this is the highest-consequence version of over-broad access.

**Deliver by reference, never by copy.** The workload spec names a path; the platform resolves it. Copying values between systems multiplies the places they exist and guarantees that rotation misses one.

**Prefer mounted files over environment variables.** Environment variables appear in crash dumps and process listings, are often logged inadvertently, and cannot change without a restart. A mounted volume - particularly via a CSI driver reading directly from the store - can be updated in place, and with that driver no Kubernetes secret object exists at all.

**Rotation must not require a deploy.** Either the application re-reads the mounted file on change, or the platform triggers a rolling restart. The requirement to design for is that rotating a credential should be an operation in the store, not a coordinated release. Databases need overlapping validity - two active credentials during the change - or rotation causes an outage, which is why rotation is usually avoided until it becomes an incident.

**Audit every read, and alert on the unusual.** Who read which secret, when, from where. That log is what turns a suspected compromise from guesswork into a scope you can state. Alert on reads from unexpected identities and on bulk enumeration.

**Assume a leak will happen and prepare the response.** Pre-commit and CI scanning to catch most of them, and a written procedure that starts with rotate, then assess exposure, then clean up. The order matters: removing the line from a repository is not remediation, because history, forks, and clones persist.

**Report what exists.** A register of secrets by owner, age, last rotation, and last read. Secrets nobody has read in six months are usually removable, and that is the cheapest reduction in exposure available.

## Example

```text
The hierarchy applied to one service's actual needs - most of them turn out not
to need a secret at all.

  NEED                        LEVEL   MECHANISM
  read from S3                 1      EKS Pod Identity - federated, no secret
  connect to Postgres          1      IAM database authentication, token per
                                      connection, no password anywhere
  call the pricing service     1      mTLS with a workload identity certificate
  Redis password               2      platform-generated at provisioning; written
                                      to a mounted secret; no human sees it
  payment provider API key     3      referenced from the store; vendor has no
                                      OIDC support
  SMTP relay password          3      referenced from the store; same reason

  Two real secrets out of six needs. Both are third-party, both are on the
  register with an owner and a rotation schedule. That reduction is the actual
  work of secret management.
```

```yaml
# Delivery by reference, mounted, fetched directly from the store so no
# Kubernetes secret object exists for it.
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: checkout-secrets, namespace: team-payments }
spec:
  provider: aws
  parameters:
    usePodIdentity: "true" # driver authenticates as the workload, via EKS Pod Identity
    objects: |
      - objectName: "team-payments/checkout/payment-provider"   # tenant-scoped path
        objectType: "secretsmanager"
        jmesPath:
          - path: "api_key"
            objectAlias: "payment_api_key"
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: checkout, namespace: team-payments }
spec:
  template:
    spec:
      serviceAccountName: checkout # federated; how the driver authenticates
      containers:
        - name: checkout
          volumeMounts:
            - name: secrets
              mountPath: /var/run/secrets/app # mounted, not an env var
              readOnly: true
      volumes:
        - name: secrets
          csi:
            driver: secrets-store.csi.k8s.io
            readOnly: true
            volumeAttributes: { secretProviderClass: checkout-secrets }
```

```text
The register - reviewed quarterly, and the review is where exposure gets reduced:

  $ platform secrets register

  SECRET                          OWNER   AGE    LAST ROTATED  LAST READ   NOTE
  team-payments/checkout/
    payment-provider              alice   180d   32d ago       4m ago      ok
  team-payments/checkout/
    legacy-gateway-key            alice   612d   NEVER         214d ago    <-- 1
  team-search/indexer/
    vendor-search-token           bob     94d    94d ago       2h ago      <-- 2
  team-data/etl/
    warehouse-password            carol   401d   401d ago      1h ago      <-- 3

  1. never rotated, not read in 7 months -> almost certainly dead. DELETE.
     The cheapest possible exposure reduction.
  2. never rotated since creation, and the vendor supports OIDC -> move to
     level 1 and remove the secret entirely.
  3. 401 days without rotation on an actively used credential -> rotation is
     being avoided because the database has no overlapping-credential support
     configured. Fix the mechanism, then rotate.
```

## Interview tips

- Lead with the hierarchy and the reframe: the best secret management is having fewer secrets. Naming workload identity and database IAM authentication as eliminations is what distinguishes this from a tool answer.
- Per-tenant path scoping deserves emphasis because secrets are what let an attacker cross every other boundary you built.
- Mounted files over environment variables, with the specific reasons - crash dumps, process listings, no refresh without restart.
- Rotation without a deploy, and the overlapping-credential requirement for databases, is the operational detail that shows you have actually rotated something in production.
- The register with last-read timestamps is a strong, concrete practice: unread secrets are usually removable, which is free risk reduction.
- On leaks, get the order right - rotate first, then assess, then clean up. Deleting the line is not remediation.

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
