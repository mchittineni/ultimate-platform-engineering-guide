---
title: "How do you build a paved road for AWS infrastructure self-service?"
id: 85
category: "AWS Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# How do you build a paved road for AWS infrastructure self-service?

**Short answer:** Expose a small set of intent-shaped resources - a database, a queue, a bucket - as claims against your own API, expand them through compositions or modules that apply your network placement, naming, tagging, encryption, and backup policy unconditionally, and give teams no AWS permissions at all. The paved road is defined by what the interface does not let you express: if there is no field for public access, nobody can create a public bucket.

## Detail

**Start from the requests teams actually make.** Look at your ticket history: databases, queues, buckets, caches, and DNS records account for the overwhelming majority. Build those five properly rather than a general-purpose interface to all of AWS. A narrow, excellent set beats a broad, shallow one, and the long tail should have a documented escape rather than a half-built abstraction.

**Intent, not AWS parameters.** `postgres: { size: small, backups: daily, pitr: true }` rather than instance class, parameter group, subnet group, and maintenance window. The test is whether a developer needs to know anything AWS-specific to use it. If the interface names an RDS parameter, you have moved the decision rather than removed it.

**The mandatory parts must be absent from the interface entirely.** Encryption, private subnet placement, the tagging scheme, deletion protection, and backup configuration should be applied by the expansion and should have no corresponding field in the claim. That is a stronger control than a policy that rejects a bad value, because the bad value cannot be expressed.

**Enforce a naming convention at provisioning, because it is what makes IAM scoping possible.** If every resource a tenant owns matches `example-<tenant>-<workload>-*`, then IAM policies can be bounded by prefix and tag condition rather than granting broad access. The convention is not tidiness - it is the mechanism that makes least privilege achievable.

**Two credible implementations, and the choice follows from your control plane.** Crossplane compositions if your platform is Kubernetes-based, so claims are Kubernetes objects with RBAC, admission control, and audit already applied. Versioned Terraform modules consumed through automation if you want the reviewable plan and already run that path well. Either way, teams get no direct AWS credentials - the controller or the pipeline holds them.

**Return the connection details as a secret, not as documentation.** The workload should reference a secret the platform wrote; the credential should never be seen by a human or pasted anywhere. This is also what makes rotation possible later.

**Handle quotas and the long tail explicitly.** Service quotas are per account and cause the classic "worked in dev, failed in prod" surprise - the platform should raise them at account vending and track them. For requests the paved road cannot serve, provide a documented route: a reviewed Terraform escape in the team's own account boundary, recorded as an exception with an owner.

**Make the escape hatch data.** Every request that could not be served by the paved road is a roadmap item with proven demand. Track them, and when four teams need the same unsupported resource, that is the next abstraction rather than four bespoke pull requests.

## Example

```yaml
# The developer-facing claim. Nothing AWS-specific, and no field exists for the
# things that must always be true.
apiVersion: platform.example.com/v1
kind: PostgresInstance
metadata: { name: checkout-db, namespace: team-payments }
spec:
  size: small # small | medium | large
  backups: daily # none | daily | hourly
  pitr: true
  writeConnectionSecretToRef: { name: checkout-db-conn }
# Deliberately not expressible: encryption off, public accessibility, a public
# subnet, missing tags, deletion protection off. No field, no bad value.
```

```yaml
# The expansion. The commented block is the policy - applied unconditionally.
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata: { name: postgres-aws }
spec:
  compositeTypeRef: { apiVersion: platform.example.com/v1, kind: XPostgresInstance }
  mode: Pipeline
  pipeline:
    - step: render
      functionRef: { name: function-patch-and-transform }
      input:
        apiVersion: pt.fn.crossplane.io/v1beta1
        kind: Resources
        resources:
          - name: instance
            base:
              apiVersion: rds.aws.upbound.io/v1beta2
              kind: Instance
              spec:
                forProvider:
                  engine: postgres
                  engineVersion: "16.3" # platform-pinned, upgraded centrally
                  # --- mandatory, no claim field exposes these ---
                  storageEncrypted: true
                  publiclyAccessible: false
                  dbSubnetGroupName: private-eu-west-1
                  deletionProtection: true
                  backupRetentionPeriod: 7
                  performanceInsightsEnabled: true
                  iamDatabaseAuthenticationEnabled: true # so no password is needed
                  tags:
                    managed-by: platform
                    # tenant, cost-centre, workload patched from the claim below
                # ------------------------------------------------
                deletionPolicy: Orphan # never destroy data on a claim delete
            patches:
              - type: FromCompositeFieldPath
                fromFieldPath: spec.size
                toFieldPath: spec.forProvider.instanceClass
                transforms: # size -> instance class, decided by the platform
                  - type: map
                    map: { small: db.t4g.small, medium: db.m7g.large, large: db.m7g.2xlarge }
              - type: FromCompositeFieldPath
                fromFieldPath: metadata.labels[platform.example.com/tenant]
                toFieldPath: spec.forProvider.tags[tenant]
              - type: FromCompositeFieldPath
                # Enforced naming - this is what makes IAM prefix scoping possible
                fromFieldPath: metadata.name
                toFieldPath: spec.forProvider.identifier
                transforms:
                  - type: string
                    string: { type: Format, fmt: "example-%s" }
```

```text
The paved road's coverage, and the escape hatch as a roadmap input:

  SUPPORTED (5 resources, ~94% of all requests)
    PostgresInstance   Queue   Bucket   Cache   DnsRecord

  ESCAPE HATCH USAGE, last two quarters - this table IS the roadmap
    ElasticSearch/OpenSearch domain ..... 4 teams   <-- BUILD IT. Proven demand.
    Kinesis stream ...................... 3 teams   <-- BUILD IT
    Step Functions state machine ........ 2 teams   watch
    Athena workgroup .................... 1 team    leave as escape
    EMR cluster ......................... 1 team    leave as escape

  Escape route for the unsupported: a reviewed Terraform change in the team's own
  account, using platform modules where they exist, recorded as an exception with
  an owner and a review date. Not a refusal, and not an unmanaged free-for-all.

  What a developer never touches: an AWS console, an IAM policy, a subnet ID, a
  parameter group, a KMS key ARN, or an AWS credential of any kind.
```

## Interview tips

- The defining sentence: the paved road is defined by what the interface does not let you express. A missing field is a stronger control than a policy rejecting a value.
- Start from ticket history and build the five resources that cover most requests. Candidates who propose a general-purpose interface to all of AWS have not run one.
- The naming convention as the enabler of IAM prefix scoping is a strong, non-obvious link between two things that look unrelated.
- Teams holding no AWS permissions at all, with the controller or pipeline owning the credential, is the security core - say it plainly.
- Connection details returned as a secret rather than documentation is the small detail that means no human ever handles the credential.
- Be ready for both implementations - Crossplane compositions and versioned Terraform modules - and choose based on your control plane rather than preference.
- Close on the escape hatch register as the roadmap: four teams needing the same unsupported resource is proven demand, not four exceptions.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
