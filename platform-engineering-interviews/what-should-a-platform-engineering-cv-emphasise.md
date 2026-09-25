---
title: "What should a platform engineering CV emphasise?"
id: 253
category: "Platform Engineering Interviews"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# What should a platform engineering CV emphasise?

**Short answer:** Outcomes for the engineers you served, not the tools you touched. Each bullet should say what you built or changed, who used it, and what happened to a number - lead time, time to a new service, adoption, tickets, cost, incidents. Tools belong in a short skills line and inside the bullets as context, because a CV that is a list of technologies is indistinguishable from one written by someone who has only read about them.

## Detail

**Understand who reads it and how.** A CV is first filtered, often by an applicant tracking system and a recruiter who is matching keywords against the job description, and then read for perhaps a minute by an engineer or hiring manager deciding whether to spend an hour on you. It therefore has to do two jobs: contain the right nouns so it passes the filter, and tell a story of impact so it passes the human.

**Lead each bullet with the change and the user.** The platform-specific twist is that your customers are other engineers. "Built a self-service database capability used by 38 product teams, cutting median provisioning time from 3 days to 10 minutes" names the user, the change, and the outcome in one line. "Worked with Crossplane, Terraform, and AWS RDS" names none of them.

**Quantify, and keep the numbers honest.** Adoption (teams, services, percentage of deploys through the golden path), speed (lead time, time to first deploy, time to a new environment), load (tickets per month in a category), reliability (incidents, change failure rate, recovery time), and cost (percentage reduction, cost now attributable to owners). If a number is approximate, it is fine to use it - but be ready to explain where it came from, because a good interviewer will ask, and a suspiciously precise figure you cannot source damages everything around it.

**Show scope and level.** For early-career roles, show that you can build and operate things reliably: a pipeline, a module, an automation, an on-call rotation you took part in. For senior roles, show scope beyond your own code: an interface other teams adopted, a migration you led, a decision you drove through an RFC. The same project can be described at different altitudes; pick the one that matches the role.

**Keep the skills section short and current.** One or two lines grouped by area - cloud, Kubernetes and GitOps, infrastructure as code, languages, observability, security. Use current names: Microsoft Entra ID rather than Azure AD, Artifact Registry rather than Container Registry, and name OpenTofu alongside Terraform if you have used it. Outdated names quietly signal that the experience is old.

**Include evidence outside work if you have it.** A maintained open-source contribution, a talk, a blog post explaining a real problem, a public module with tests. For people early in their career or changing into platform work, this is often the strongest material available. A personal lab counts if you describe what you learned rather than which tools you installed.

**Respect confidentiality.** Do not include internal system names, architecture details, customer names, or incident specifics that your employer would not publish. "A payments platform serving 40 teams" is enough.

**Be careful with AI-written CVs.** Assistants are useful for tightening wording, but generated CVs tend towards the same inflated verbs and vague claims, and reviewers now recognise the pattern. Every line must be something you can defend for five minutes in an interview.

**Trade-off: tailoring versus maintenance.** Tailoring the summary and the order of bullets to each role improves the match noticeably; rewriting the whole CV each time is not worth it. Keep one master version with every bullet and cut from it.

## Example

```text
The same experience, written two ways.

WEAK - a tool list
  Platform Engineer, 2023-present
  - Worked on Kubernetes, Argo CD, Terraform, Backstage, Prometheus
  - Responsible for CI/CD pipelines
  - Helped with cloud cost optimisation
  - Participated in on-call

  -> no users, no numbers, no scope, no way to tell what this person did

STRONG - change, user, outcome
  Platform Engineer, 2023-present  (platform team of 6, ~40 product teams)
  - Designed and built a reusable CI pipeline adopted by 31 of 40 teams within
    two quarters, replacing nine bespoke pipelines; median commit-to-production
    time fell from 2 days to 45 minutes.
  - Built self-service preview environments on namespaces with automatic
    cleanup; engineers no longer file tickets for test environments (~60 a
    month before).
  - Led the move from long-lived cloud keys to workload identity for 120
    services; zero stored cloud credentials remain in CI or clusters.
  - Introduced cost allocation by owning team, making ~90% of cloud spend
    attributable and enabling a 22% reduction in idle non-production capacity.
  - Member of a five-person on-call rotation; wrote the runbooks and SLO alerts
    for the deploy capability after an incident nothing had alerted on.

  Skills: AWS (EKS, IAM, Organizations) · Kubernetes, Argo CD, Kyverno ·
          Terraform, OpenTofu · Go, Python · OpenTelemetry, Prometheus, Grafana
```

```text
Early-career variant - fewer years, same shape.

  Junior DevOps Engineer, 2025-present
  - Wrote a Terraform module for standard S3 buckets (encryption, versioning,
    lifecycle, tagging) with tests; now used by 14 services.
  - Automated weekly base-image rebuilds and signing, so teams get patched
    images without asking.

  Projects
  - Home lab: kind cluster managed by Argo CD; blog post on debugging a
    readiness probe that failed only under load.
```

## Interview tips

- Expect every bullet to be a conversation starter. Interviewers pick one and go three levels down, so write only what you can defend in detail.
- Name the users - how many teams, which kind of engineers - on the CV itself. It is the fastest way to signal that you understand platform work is a product for other engineers.
- If asked where a number came from, give the provenance and any caveat. "From the ticket queue, not instrumentation" is a good answer.
- Mirror the job description's nouns where they are true, so the CV passes keyword filters, but never add a tool you have not used.
- Keep it to two pages at most; one is fine early in a career.
- Use current product names. Deprecated names are a small but real signal that knowledge is stale.
- Be ready to say what you personally did versus the team. A CV written in "I" for team work will be exposed by the first follow-up.

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
