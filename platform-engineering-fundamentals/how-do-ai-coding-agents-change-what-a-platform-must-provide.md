---
title: "How do AI coding agents change what a platform must provide?"
id: 13
category: "Platform Engineering Fundamentals"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# How do AI coding agents change what a platform must provide?

**Short answer:** AI coding agents become a second class of platform user: they write code, open pull requests, run pipelines, and increasingly call platform APIs on a developer's behalf, at a volume and speed no human team matches. That changes the platform in four ways - its interfaces must be machine-readable and discoverable (typically through APIs and Model Context Protocol servers rather than portals), agents need their own scoped and auditable identity, guardrails and fast feedback matter more because more change arrives with less human attention, and the capacity of CI, preview environments, and review becomes the new bottleneck. The platform does not stop serving humans; it has to make agents safe and useful without letting them bypass the controls humans go through.

## Detail

**Agents are a user with different needs.** A human engineer reads documentation once, remembers the conventions, and tolerates a portal form. An agent starts each task with no memory, reads whatever context it is given, acts through tools, and repeats the loop many times an hour. So the properties that make a platform good for people - clear contracts, consistent defaults, fast feedback - matter even more for agents, while the properties people put up with - tribal knowledge, click-only interfaces, error messages that need a human to interpret - make agents fail. DORA's 2025 research on AI-assisted development makes the same point from the other direction: AI amplifies whatever system it lands in, and a quality internal platform is one of the capabilities it found associated with teams getting real benefit rather than more instability.

**1. Interfaces agents can discover and call.** An agent can only use what it can find and invoke programmatically. That favours platforms whose capabilities are already declarative files in the repository, a CLI with structured output, or an API - and it pushes platform teams to expose those capabilities through Model Context Protocol (MCP) servers, the open protocol agents use to discover tools with typed input schemas. A good platform MCP server is a thin, well-described layer over the platform's existing API, not a second implementation: the same validation, the same policy, the same audit trail. Documentation also becomes an interface: machine-readable context such as a repository instruction file (for example `AGENTS.md`) describing how to build, test, and deploy, and golden path templates that agents can reproduce reliably. See [designing the developer-facing API of a platform](../platform-architecture/how-do-you-design-the-developer-facing-api-of-a-platform.md).

**2. Identity, delegation, and least privilege for agents.** An agent acting with a developer's full personal credentials is the worst of both worlds: it has broad access, and the audit log cannot tell the person from the agent. The platform should issue agents short-lived, narrowly scoped credentials tied to both the agent and the delegating human, using the same workload identity federation it already uses for CI - never long-lived keys pasted into a tool's configuration. Scope by capability and environment: an agent may open preview environments and read logs; it may not change production IAM or delete data. Every action should record who delegated it. The mechanics are the same as in [workload identity without long-lived credentials](../platform-security/how-does-a-platform-provide-workload-identity-without-long-lived-credentials.md).

**3. Guardrails move from review to enforcement.** When a human wrote every change, a reviewer might notice a public bucket or an over-broad role. When agents produce many more pull requests, reviewer attention per change falls, so anything that must hold has to be enforced by the platform, not hoped for in review: policy as code in CI and at admission, required signed provenance for what gets deployed, and dependency and secret scanning on every change. Destructive operations exposed to agents should need explicit human confirmation, and the platform should expose read-only and dry-run modes so an agent can plan before it acts. Agent tools also widen the attack surface - prompt injection through a README, an issue, or a log line can steer an agent into calling tools it should not - which is another reason the permission boundary must live in the platform rather than in the agent's instructions. See [where policy as code belongs in a platform](../policy-as-code-and-governance/what-is-policy-as-code-and-where-does-it-belong-in-a-platform.md).

**4. Feedback loops and capacity.** Agents work by trying something and reading the result, so the speed and clarity of the platform's feedback directly sets how good their output is. Fast, deterministic tests, structured error messages that say what to fix, ephemeral environments an agent can deploy to and inspect, and observability it can query all improve agent results. They also multiply load: more pull requests mean more CI minutes, more preview environments, and more flaky-test noise. Platform teams need quotas and fair scheduling per team, automatic teardown of agent-created environments, and cost attribution so agent spend is visible rather than buried in the CI bill.

**What stays the same.** Agents do not remove the need for golden paths, versioned interfaces, or product thinking - they raise the stakes. An agent will copy whatever pattern is most common in the codebase, so a platform with one clear, well-documented path produces consistent agent output, while a platform with five half-supported ways produces five kinds of drift at machine speed.

**Trade-offs and open problems.** Exposing more capability to agents increases productivity and blast radius together, so start read-only and widen deliberately. Human review capacity, not agent speed, becomes the throughput limit, and measuring rework rate and change failure rate alongside throughput matters more than ever. And accountability must stay with a named human: the platform can make agent actions traceable, but it cannot make an agent the owner of a service.

## Example

```json
{
  "tools": [
    {
      "name": "create_preview_environment",
      "description": "Deploy the given branch of a service to an ephemeral preview environment. Expires automatically after 24h. Does not touch staging or production.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "service": { "type": "string", "description": "Catalogue name, e.g. checkout" },
          "branch": { "type": "string" },
          "ttl_hours": { "type": "integer", "minimum": 1, "maximum": 24, "default": 24 }
        },
        "required": ["service", "branch"]
      },
      "annotations": { "readOnlyHint": false, "destructiveHint": false }
    },
    {
      "name": "query_service_logs",
      "description": "Return recent structured log lines for a service in a non-production environment, filtered by level.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "service": { "type": "string" },
          "environment": { "type": "string", "enum": ["preview", "staging"] },
          "level": { "type": "string", "enum": ["error", "warn", "info"], "default": "error" },
          "since_minutes": { "type": "integer", "minimum": 1, "maximum": 120, "default": 15 }
        },
        "required": ["service", "environment"]
      },
      "annotations": { "readOnlyHint": true }
    }
  ]
}
```

```text
What sits behind that MCP server (not visible to the agent):

  agent -> MCP server -> platform API -> same policy + audit as the CLI and portal

  identity   short-lived token: agent=coding-agent, on_behalf_of=a.developer,
             scopes=[preview:write, logs:read:nonprod], expires in 1h
  policy     no production targets exposed; preview quota 5 per team;
             every call logged with the delegating human
  cost       preview environments tagged agent=true, torn down on TTL
  deliberately absent: delete_database, modify_iam, deploy_production
```

## Interview tips

- Open with the framing that agents are a new class of platform user, then organise the answer as interfaces, identity, guardrails, and capacity - it shows structure rather than enthusiasm.
- Say that an MCP server should be a thin layer over the existing platform API with the same policy and audit, not a new back door.
- Name the security issues specifically: delegated, scoped, short-lived credentials; prompt injection; human confirmation for destructive actions.
- Point out that agents amplify the platform they land on - one clear golden path yields consistent agent output, while inconsistency gets reproduced at scale.
- Expect "how would you measure whether agents are helping?" - throughput alongside change failure rate, rework rate, review load, and CI cost, not pull request counts alone.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
