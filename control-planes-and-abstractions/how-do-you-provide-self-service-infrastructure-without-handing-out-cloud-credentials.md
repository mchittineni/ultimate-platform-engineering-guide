---
title: "How do you provide self-service infrastructure without handing out cloud credentials?"
id: 78
category: "Control Planes and Abstractions"
difficulty: "Advanced"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# How do you provide self-service infrastructure without handing out cloud credentials?

**Short answer:** Put a control plane between developers and the cloud. Developers get permission to create a platform resource - a claim - and never any cloud permission at all; the controller holds the cloud credential and creates only what the abstraction allows. Authorisation happens on your API with your own RBAC, the credential lives in one place with a workload identity rather than a stored key, and every request is validated and audited before it reaches a provider.

## Detail

**Why direct cloud access does not work for self-service.** Giving a team an IAM role broad enough to create databases means giving them a role broad enough to create anything, including resources with no encryption, no backups, public access, or no cost tags. Attempts to constrain this with policy conditions become unreadable, and the permission surface is enormous. The problem is that cloud IAM authorises API calls, not intents - it cannot express "you may create a Postgres, but only small, only in these subnets, always encrypted, always tagged".

**The indirection is the answer.** The developer's permission is `create postgresinstances in namespace team-payments`. (In Crossplane v2 that object is a namespaced composite resource created directly, with no separate claim kind; "claim" here means any such platform request.) That is checked by your control plane's RBAC. The composition or controller then decides what cloud resources that means, applying your naming, network placement, encryption, tagging, and backup policy as non-negotiable parts of the expansion. The developer cannot express a non-compliant request because the interface has no field for it.

**Where the cloud credential lives.** In the controller, obtained through workload identity - EKS Pod Identity (or IRSA), Workload Identity Federation for GKE, or Microsoft Entra Workload ID - so the controller's service account exchanges a signed token for short-lived credentials. There is no long-lived key anywhere. This is a single, auditable, tightly scoped identity rather than one per team, and it is the only thing in the system with broad provisioning rights.

**Least privilege still applies to the controller.** It should be scoped by resource naming prefix, by tag condition, and by region - so even a compromised or buggy controller cannot touch resources outside the platform's namespace. And separate controllers or provider configurations per environment, so the production credential is not reachable from a development cluster. Crossplane v2's namespaced `ProviderConfig` goes further, letting you pin a tenant namespace to its own cloud account.

**Guardrails belong at three points, not one.** Schema validation rejects impossible requests immediately. Admission policy enforces organisational rules the schema cannot express - budget approval for large sizes, no production claims outside a change window. The composition applies mandatory defaults that no request can override. Layering these means a request has to pass your rules three times before a cloud API is called.

**Audit becomes straightforward, which is a real bonus.** Every request is a Kubernetes API call with an identity, a timestamp, and a diff, recorded in the audit log. "Who provisioned this database and when" is answerable from your own records rather than reconstructed from cloud trail entries that all show the same controller identity - and the controller's cloud calls can be correlated back to the claim by tag.

**The trade-off to name.** You have created a critical dependency: if the control plane is down, nothing new can be provisioned. That is acceptable because it is a control-plane function - existing infrastructure keeps working - but it needs the break-glass path documented, and the platform team retains a separately audited emergency route for the cases where the abstraction genuinely cannot express what an incident requires.

## Example

```text
Who holds what permission - the whole design in one view:

  DEVELOPER (team-payments)
    cloud IAM permissions ................. NONE
    control plane RBAC .................... create/get/update/delete
                                            postgresinstances, buckets, queues
                                            in namespace team-payments only
    can they create an unencrypted, public, untagged database? ... NO - no field
                                                                   exists for it

  CONTROLLER (one identity for the whole platform)
    cloud IAM ............................. rds:*, s3:*, sqs:* BUT bounded by
                                            resource prefix example-*, tag
                                            condition managed-by=platform, and
                                            region eu-west-1 / us-east-1 only
    credential ............................ workload identity federation,
                                            short-lived, no stored key
    separate provider config per environment, so a dev cluster cannot reach
    the production account

  PLATFORM TEAM
    break-glass role ...................... exists, separately audited, alerts
                                            on use, time-bound session
```

```yaml
# The developer's RBAC. Note what is absent: any cloud permission whatsoever.
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: infra-self-service, namespace: team-payments }
rules:
  - apiGroups: ["platform.example.com"]
    resources: ["postgresinstances", "buckets", "queues"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["secrets"] # to read the generated connection secret
    verbs: ["get"]
    resourceNames: ["checkout-db-conn"]
```

```yaml
# The controller's cloud identity - federated, short-lived, and bounded.
# Crossplane v2 namespaced managed resources use the .m. API group and a
# ClusterProviderConfig (platform-wide) or ProviderConfig (per namespace).
apiVersion: aws.m.upbound.io/v1beta1
kind: ClusterProviderConfig
metadata: { name: production }
spec:
  credentials:
    source: PodIdentity # EKS Pod Identity; IRSA also works. No access key to leak
---
# The mandatory parts of the expansion. A developer cannot override these
# because the claim schema exposes no field for them.
# (composition patch set, abbreviated)
# - storageEncrypted: true            always
# - publiclyAccessible: false         always
# - dbSubnetGroup: private-<region>   always, from platform network state
# - tags:                             always, derived from the claim
#     managed-by: platform
#     tenant: <claim namespace>
#     cost-centre: <from Tenant object>
#     claim: <claim name>
```

```yaml
# Admission policy - the rules the schema cannot express.
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata: { name: infra-request-guardrails }
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["platform.example.com"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["postgresinstances"]
  validations:
    # Large instances cost real money - require a recorded approval
    - expression: >
        object.spec.size != 'large' ||
        (has(object.metadata.annotations) &&
         'platform.example.com/budget-approved-by' in object.metadata.annotations)
      message: "size: large requires a platform.example.com/budget-approved-by annotation"
    # Production must keep point-in-time recovery
    - expression: >
        object.metadata.labels['platform.example.com/environment'] != 'production' ||
        object.spec.pitr == true
      message: "production databases must enable pitr"
```

## Interview tips

- The one-line thesis: developers get permission on your API, never on the cloud API, and the controller holds the only credential.
- Explain why cloud IAM cannot do this itself - it authorises API calls, not intents, so it cannot express "a small encrypted Postgres in these subnets with these tags". That reasoning is the heart of the answer.
- Workload identity federation for the controller, with no stored key, plus prefix/tag/region bounds on its role, is the security detail interviewers want.
- Guardrails at three layers - schema, admission, composition - with mandatory fields absent from the interface entirely, is the strongest structural point.
- Volunteer the trade-off: the control plane becomes a dependency for provisioning, and the break-glass path must exist, be documented, and alert on use.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
