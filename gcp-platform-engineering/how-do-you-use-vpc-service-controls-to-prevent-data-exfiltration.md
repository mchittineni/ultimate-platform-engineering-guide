---
title: "How do you use VPC Service Controls to prevent data exfiltration?"
id: 184
category: "GCP Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# How do you use VPC Service Controls to prevent data exfiltration?

**Short answer:** VPC Service Controls draws a service perimeter around a set of projects and restricts Google APIs - BigQuery, Cloud Storage, and the rest - so that data inside can only move to resources inside, and only be reached from contexts you allow. It stops the case IAM cannot: a valid credential, stolen or misused, copying data to a project the attacker controls. You design it with narrow ingress and egress rules instead of perimeter holes, roll it out in dry-run mode first, and route private API traffic through `restricted.googleapis.com` so the perimeter applies to on-premises and VPC traffic too.

## Detail

**What problem it actually solves.** IAM answers "may this principal call this API on this resource?" It does not ask where the data goes next. A service account with `storage.objects.get` on a sensitive bucket can read an object and write it to a bucket in someone else's project; a user with BigQuery access can run `CREATE TABLE ... AS SELECT` into a dataset they own elsewhere. Both are authorised by IAM. VPC Service Controls adds a second, context-based check on every call to a restricted service: are the caller and every resource the call touches on the same side of the perimeter? If not, the call is denied - regardless of IAM.

**The building blocks.**

| Component               | What it is                                                                                                                          |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Access policy           | The organisation-level container for perimeters and access levels; scoped policies can delegate a folder or project to another team |
| Service perimeter       | A set of projects (or VPC networks) plus the list of **restricted services** protected at its edge                                  |
| Access level            | A condition from Access Context Manager - source IP range, device posture, principal - that callers outside can satisfy             |
| Ingress rule            | Allows specific identities, from specific sources, to call specific methods on resources inside                                     |
| Egress rule             | Allows identities inside to call specific methods on specific resources outside                                                     |
| Dry-run configuration   | A shadow perimeter that logs what it would block without blocking                                                                   |
| VPC accessible services | Limits which APIs can be reached at all from networks inside the perimeter                                                          |

**Design perimeters around data, not around org charts.** A perimeter should enclose projects that legitimately exchange sensitive data - the analytics warehouse, the ingestion pipelines that feed it, the projects hosting its consumers. Too many small perimeters produce a mesh of rules; one perimeter around everything protects nothing because everything is inside. A common shape is one perimeter per data classification per environment: `prod-restricted` for regulated data, a separate one for non-production, and ordinary projects outside.

**Prefer ingress and egress rules to bridges.** Perimeter bridges let two perimeters share freely, which is coarse. Ingress and egress rules name the identity, the source, the service, the method or IAM role, and the target project, so you can say "the CI federated identity may call `run.googleapis.com` into project X" and nothing else. Every rule should read as a specific, reviewable exception with a title that explains why.

**Close the network path too.** API calls from VMs, GKE nodes, or on-premises networks should resolve `*.googleapis.com` to the `restricted.googleapis.com` virtual IP range through private DNS, with Private Google Access or Private Service Connect. That endpoint only serves services VPC Service Controls supports, so traffic cannot sidestep the perimeter through an unprotected API. VPC accessible services narrows it further.

**Know the limits - this is where answers get credible.**

- **It protects Google APIs, not arbitrary network traffic.** A compromised VM that can reach the internet can still upload data to an external server. Egress firewalling, Cloud NAT allow-listing, or a proxy are separate controls you still need.
- **Supported services and methods vary.** Check the supported-products list for each restricted service, and remember that some services behave differently at the perimeter - for example, services that run jobs in Google-managed projects need rules for their service agents.
- **It breaks things silently if rolled out carelessly.** Console access from unmanaged laptops, CI pipelines outside the perimeter, log sinks writing to a logging project outside, and cross-project Pub/Sub subscriptions all fail with a `VPC_SERVICE_CONTROLS` error. That is why dry-run is not optional.
- **It is not a substitute for IAM.** A principal inside the perimeter with excessive roles can still read everything inside. The perimeter limits where data goes, not who inside can see it.

**Roll out in dry-run, then enforce.** Create the perimeter as a dry-run configuration, let it run for a representative period covering batch jobs, month-end reports, and deploys, and review the violations in audit logs - each carries a `vpcServiceControlsUniqueId` and the violation analyser shows which rule would have allowed it. Add the minimum ingress and egress rules, repeat until the dry-run log is quiet, then enforce. Keep the dry-run configuration as a staging area for every later change.

**Who uses this, and what the platform gives them.** The direct users are the security and data platform teams, but every product team that touches protected projects feels it. The platform's job is to make the perimeter invisible when you do the right thing: vending places regulated projects inside the perimeter automatically, CI identities and service agents have pre-approved rules, and a team that needs a new exception requests it through a reviewed change to the perimeter configuration in Git. A clear runbook for decoding a `VPC_SERVICE_CONTROLS` error saves hours per incident.

**The trade-off.** VPC Service Controls is one of the strongest exfiltration controls in any cloud, and one of the most operationally demanding. Every integration now needs a rule, debugging access failures needs a new skill, and a mistake in enforcement can stop production pipelines. It is worth that cost for regulated or high-value data and rarely worth it for everything.

## Example

```bash
# 1. Access level: the corporate network, for console and analyst access.
cat > corp-network.yaml <<'EOF'
- ipSubnetworks:
    - 203.0.113.0/24
EOF
gcloud access-context-manager levels create corp_network \
  --policy=318420573812 --title="corp-network" \
  --basic-level-spec=corp-network.yaml

# 2. Perimeter in DRY-RUN: logs violations, blocks nothing yet.
gcloud access-context-manager perimeters dry-run create prod_restricted \
  --policy=318420573812 --perimeter-title="prod-restricted" \
  --perimeter-type=regular \
  --perimeter-resources=projects/482915537204,projects/730266184451 \
  --perimeter-restricted-services=bigquery.googleapis.com,storage.googleapis.com \
  --perimeter-access-levels=accessPolicies/318420573812/accessLevels/corp_network
```

```yaml
# ingress.yaml - the CI identity may deploy into the warehouse loader project.
- ingressFrom:
    identities:
      - serviceAccount:sa-deployer@ci-prod.iam.gserviceaccount.com
    sources:
      - accessLevel: "*"
  ingressTo:
    operations:
      - serviceName: storage.googleapis.com
        methodSelectors:
          - method: google.storage.objects.create
    resources:
      - projects/482915537204
  title: "CI uploads pipeline artefacts to the loader project"
---
# egress.yaml - the loader may READ one partner's shared dataset outside.
- egressFrom:
    identities:
      - serviceAccount:sa-loader@warehouse-prod.iam.gserviceaccount.com
  egressTo:
    operations:
      - serviceName: bigquery.googleapis.com
        methodSelectors:
          - permission: bigquery.tables.getData
    resources:
      - projects/915003772140
  title: "Loader reads the partner reference dataset"
```

```text
What dry-run showed before enforcement (14 days):

  VIOLATIONS (would have been blocked) ..................... 3 patterns
    sa-deployer@ci-prod     storage.objects.create -> loader   -> ingress rule added
    log sink _Default       logging -> logging-central (outside) -> moved sink project inside
    analyst@example.com     bigquery.jobs.create from home IP  -> intended block; no rule

  EXFILTRATION TEST (red team, with a valid service account key)
    bq query 'CREATE TABLE attacker-proj.x.y AS SELECT * FROM warehouse.customers'
    -> denied: VPC_SERVICE_CONTROLS, RESOURCES_NOT_IN_SAME_SERVICE_PERIMETER
       IAM allowed it. The perimeter did not.
```

## Interview tips

- Start with the gap IAM leaves: an authorised principal moving data to a destination it also has access to. VPC Service Controls closes that by checking where the resources are, not just who is asking.
- Name the components precisely - access policy, perimeter, restricted services, access levels, ingress and egress rules - and prefer rules over perimeter bridges.
- Mention `restricted.googleapis.com` and private DNS as the step that makes the perimeter apply to VPC and on-premises traffic.
- Volunteer the limits: it protects Google APIs, not raw network egress, and it is not a substitute for least-privilege IAM.
- Dry-run first, with a representative observation window, is the operational answer interviewers want - the most common failure is enforcing and breaking pipelines.
- Show platform thinking: vending places projects in the perimeter, rules live in Git and are reviewed, and a runbook decodes `VPC_SERVICE_CONTROLS` errors.
- If compared with other clouds, relate it to AWS resource control policies and data perimeters, and to Azure private endpoints with network restrictions - similar goals, different mechanisms.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
