---
title: "How do you design tenant onboarding and offboarding?"
id: 52
category: "Multi-Tenancy and Isolation"
difficulty: "Advanced"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# How do you design tenant onboarding and offboarding?

**Short answer:** Make both a single declarative operation that a controller reconciles, so a tenant is defined in one place and every derived resource - namespace, quotas, network policy, identity, secret paths, budget, catalogue entry - is created or removed from that definition. Offboarding is the harder half and the one organisations neglect: without it you accumulate orphaned resources, live credentials belonging to teams that no longer exist, and cost nobody will claim.

## Detail

**One declaration, many derived resources.** A tenant should be an object, not a runbook. Declaring `kind: Tenant` with a name, an owning group, a tier, and a budget should produce everything downstream. The runbook approach fails not because it cannot work once, but because step seven of fourteen gets skipped occasionally and you have no way to detect which tenants are incomplete.

**Reconciliation is what makes it trustworthy.** A controller that continuously converges the tenant's derived resources gives you two properties a script cannot: a tenant created eighteen months ago gains new baseline policies automatically, and a resource deleted by hand is restored. Onboarding becomes a property rather than an event. You rarely need to write that controller from scratch: a Crossplane v2 composition (whose namespaced composite resources can include any Kubernetes resource) or a kro ResourceGraphDefinition can define `Tenant` as an API and fan it out into the derived objects.

**What onboarding must produce:** the namespace or project, resource quotas and limit ranges, the default-deny network policy plus baseline allows, workload identity and its scoped authorisation, secret store paths and access policy, a budget and cost tags, the catalogue entry with a validated owner, alert routing to the right rotation, log and metric destinations with retention, repository access, and the golden-path scaffolding.

**Offboarding is genuinely difficult, and here is why.** Deletion is not the reverse of creation. Some things must be deleted, some retained for compliance, and some deliberately orphaned so you do not destroy data on a mistaken signal. Ordering matters - revoke credentials before deleting the workloads that use them, or you generate a wave of authentication failures and confusing alerts.

**The offboarding checklist, in the order it should happen:**

1. **Mark the tenant terminating** and stop admitting new resources. Prevents a race where new workloads appear mid-teardown.
2. **Revoke access first** - identity federation, repository permissions, secret store policies, cloud roles. Credentials outliving a team is the worst outcome here.
3. **Snapshot anything with a retention obligation** - databases, audit logs, artefacts - and record where the snapshot went, with an expiry.
4. **Drain traffic and remove DNS**, so the failure mode is a clean absence rather than half-working.
5. **Delete workloads**, then the infrastructure they depended on. Stateful resources need an explicit decision - orphan-and-tag is safer than delete for anything holding data.
6. **Release quota, budget, and licences**, or your capacity planning stays wrong indefinitely.
7. **Close the catalogue entry** and re-route or delete alerting so nothing pages a rotation that no longer exists.
8. **Reconcile and prove it.** Query for anything still tagged with the tenant. Whatever remains is either a deliberate retention with an expiry, or a bug.

**The verification is the deliverable.** An offboarding that ends with "we ran the script" is not finished. It ends with a report showing zero unexpected resources tagged to the tenant, no valid credentials, and an explicit list of what was retained and until when.

**Tag everything at creation, or you cannot offboard.** Every derived resource must carry the tenant label or tag from the moment it exists. This is the single decision that determines whether offboarding is a query or an archaeology project - and it is why offboarding design belongs in the onboarding conversation.

## Example

```yaml
# The whole tenant, declared once. Everything else is derived and reconciled.
apiVersion: platform.example.com/v1
kind: Tenant
metadata:
  name: team-search
spec:
  owner: group:team-search # validated against the identity provider
  costCentre: eng-discovery
  tier: 2
  budget: { monthly: 12000, currency: USD, alertAt: [50, 80, 100] }
  quota: { cpu: "40", memory: 80Gi, pods: 200, loadBalancers: 2 }
  environments: [dev, staging, prod]
  dataClassification: internal
  contacts:
    oncall: pagerduty:team-search
    slack: "#team-search"
```

```text
What the controller derives - and continuously reconciles, so a tenant onboarded
last year gains this year's baseline policy automatically:

  per environment:
    Namespace                       labelled tenant=team-search (the tag that
                                    makes offboarding a query, not archaeology)
    ResourceQuota + LimitRange      from spec.quota, scaled by environment
    NetworkPolicy                   default-deny + DNS + telemetry baseline
    ServiceAccounts + IAM roles     scoped to example-team-search-* resources
    Secret store path + policy      secret/team-search/* read-only
    Budget + cost allocation tags   from spec.budget and spec.costCentre
    Log + metric destination        retention from spec.tier
    Alert routing                   from spec.contacts.oncall
  once:
    Catalogue entry                 owner validated, tier recorded
    Repository team + permissions   from spec.owner
    Golden path scaffolding access
```

```text
Offboarding, run as an ordered reconciliation - and the report that proves it.

  $ platform tenant offboard team-search --retain-audit 7y

    [1/8] tenant marked Terminating; admission of new resources blocked
    [2/8] access revoked FIRST
            IAM roles deleted ................. 14
            OIDC federation removed ........... 3 service accounts
            secret store policy revoked ....... secret/team-search/*
            repository access removed ......... 9 repos
    [3/8] retention snapshots taken
            postgres search-prod .............. s3://archive/... expires 2033-08-11
            audit logs ........................ retained 7y per policy
    [4/8] traffic drained; 4 DNS records removed
    [5/8] workloads deleted (31 pods, 12 deployments)
            stateful resources ORPHANED + tagged offboarded=2026-08-11:
              2 RDS instances, 1 EBS volume, 1 S3 bucket
            -> deliberate: deletion of data requires a separate signed approval
    [6/8] quota released (40 CPU, 80Gi), budget closed, 3 licences returned
    [7/8] catalogue entry closed; alert routing removed
    [8/8] verification

      resources still tagged tenant=team-search .... 5
        4 x deliberate retention (expiry recorded)
        1 x UNEXPECTED: LoadBalancer in eu-west-1, created outside the platform
            -> flagged for manual review. This is exactly what the verification
               step exists to catch.

      valid credentials referencing team-search ..... 0
```

## Interview tips

- The framing that earns credit: one declaration, everything derived, continuously reconciled. It turns onboarding completeness into a property rather than a hope.
- Say plainly that offboarding is the harder half and the one usually neglected. Then give the ordering insight - revoke access before deleting workloads.
- "Tag everything at creation or you cannot offboard" is the highest-value single sentence, because it makes offboarding design an onboarding decision.
- Orphan-and-tag rather than delete for stateful resources shows the right instinct about irreversible operations.
- End on verification: an offboarding is finished when a query returns zero unexpected resources and zero valid credentials, not when the script exits successfully.

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
