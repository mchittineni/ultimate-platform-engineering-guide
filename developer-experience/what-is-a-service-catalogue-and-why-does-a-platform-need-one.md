---
title: "What is a service catalogue and why does a platform need one?"
id: 11
category: "Developer Experience"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# What is a service catalogue and why does a platform need one?

**Short answer:** A service catalogue is the authoritative inventory of everything running in your organisation, with an owner, a tier, dependencies, and links to its runtime reality - dashboards, runbooks, repository, on-call rotation. A platform needs one because almost every platform capability requires knowing who owns a thing: routing an alert, applying a policy by tier, attributing cost, notifying consumers of a breaking change, or answering "who do I page" at 3am.

## Detail

**Ownership is the field that matters.** An unowned service is an unanswerable page, an unpatched CVE, and a cost line nobody defends. The catalogue's single most valuable property is that every running thing maps to a team that exists. Everything else is useful; this one is load-bearing.

**What the entry needs to carry:**

| Field                        | What it unlocks                                              |
| ---------------------------- | ------------------------------------------------------------ |
| Owner (a team, not a person) | Alert routing, review requests, migration notifications      |
| Tier or criticality          | SLO defaults, backup policy, review requirements, on-call    |
| Repository and CI location   | Automated migration pull requests, provenance                |
| Dependencies                 | Blast radius analysis, deprecation impact, incident triage   |
| Runtime links                | Dashboards, logs, runbook, SLO - the incident starting point |
| Data classification          | Policy selection, residency and encryption requirements      |
| Lifecycle state              | Distinguishes production from experiment from abandoned      |

**It must be generated, not curated.** A catalogue maintained by asking teams to update a page is stale within a quarter, and a stale catalogue is worse than none because people trust it once and get burned. The workable pattern is descriptor files in each service repository, harvested automatically, cross-checked against what is actually running. Anything found running without a catalogue entry is a finding, and anything in the catalogue with no running workload is drift.

**The reconciliation loop is the part people skip.** Compare the catalogue against reality - workloads in clusters, cloud resources by tag, DNS records, cloud accounts - and report both directions of mismatch. Undocumented workloads and orphaned entries are both real problems, and this reconciliation is usually how organisations discover services nobody remembers owning.

**Ownership decay is the operating problem.** Teams reorganise, people leave, and owners silently become invalid. Validate owners against your identity provider on a schedule, and escalate an unresolvable owner rather than letting it rot. A quarterly ownership confirmation, prompted automatically, is cheap insurance.

**What it enables that is hard to get otherwise.** Scorecards need a subject and an owner. Cost showback needs a mapping from resources to teams. A critical CVE response needs "which services use this library" answered in minutes. Deprecating an API needs "who calls this" answered accurately. Each of these is nearly impossible without a catalogue and straightforward with one.

## Example

```yaml
# checkout/.platform/catalog-info.yaml - lives with the code, harvested automatically.
# Backstage's descriptor format is the de facto standard here; the format matters
# less than the fact that it is versioned next to the service it describes.
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: checkout
  description: Cart checkout and payment orchestration
  annotations:
    github.com/project-slug: example/checkout
    prometheus.io/rule: checkout-slo
    pagerduty.com/service-id: PXXXXXX
  tags: [go, tier-1, pci]
spec:
  type: service
  lifecycle: production # production | experimental | deprecated
  owner: group:team-payments # validated against the identity provider
  system: commerce
  dependsOn:
    - component:pricing
    - resource:checkout-postgres
    - resource:orders-queue
  providesApis:
    - checkout-http
```

```text
The reconciliation that keeps it honest - run daily, report both directions:

  catalogue entries ......................... 218
  workloads observed in clusters ............ 231
  cloud resources with an owner tag ......... 1,847

  IN CLUSTER, NOT IN CATALOGUE ....... 14   <- undocumented; unroutable alerts
  IN CATALOGUE, NOT RUNNING .......... 9    <- drift; delete or mark deprecated
  OWNER NOT IN IDENTITY PROVIDER ..... 6    <- team dissolved; escalate for reassignment
  TIER-1 WITHOUT AN SLO .............. 3    <- policy violation, not just untidiness
```

## Interview tips

- Lead with ownership. If you can only say one thing, say that a catalogue exists so that everything running maps to a team that still exists.
- "Generated, not curated" is the sentence that shows you have maintained one. Curated catalogues always rot.
- The reconciliation loop - both directions, undocumented workloads and orphaned entries - is the detail most candidates omit and interviewers value.
- Be ready for "isn't this just Backstage?" - Backstage is one implementation of the catalogue and portal; the descriptor format and the reconciliation are the substance.
- Have two downstream uses ready, for example CVE blast-radius queries and cost showback. It demonstrates the catalogue is infrastructure, not documentation.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
