---
title: "What is a cloud development environment?"
id: 107
category: "Environments and Ephemeral Infrastructure"
difficulty: "Beginner"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# What is a cloud development environment?

**Short answer:** A cloud development environment (CDE) is a remote workspace - a container or virtual machine running in the cloud or your own data centre - where an engineer writes, builds, and runs code, connected to from a browser or a local editor. It is created from a definition kept in the repository, so every engineer gets the same tools and versions in minutes instead of spending days setting up a laptop. It solves consistency, onboarding, and access to heavy compute; it does not automatically make the edit-and-test loop fast.

## Detail

**The mechanism.** A workspace definition - usually a dev container file in the repository plus a platform-owned template - describes the base image, language toolchains, editor extensions, and machine size. When an engineer opens a workspace, the CDE service schedules a container or VM, clones the repository into it, runs setup commands, and connects the editor over a secure tunnel. The code, the build, and the running processes all live remotely; the laptop only draws the editor, or runs a local editor that talks to a remote server.

**What problems it solves:**

- **"Works on my machine."** Everyone runs the same image, so tool versions cannot drift between engineers.
- **Onboarding.** A new engineer, or an engineer switching teams, opens a workspace and has a working build in minutes. This is often the most persuasive number in the business case.
- **Heavy workloads.** Large monorepos, big compile jobs, or GPU work can use a machine far larger than a laptop.
- **Security.** Source code and credentials stay inside the network rather than on laptops, which matters for regulated organisations and for contractors.
- **Proximity to dependencies.** The workspace runs next to development databases and clusters, so network calls are fast and do not need a VPN.

**Common products.** GitHub Codespaces, Coder, Google Cloud Workstations, Microsoft Dev Box (a full cloud-hosted Windows workstation rather than a container), and DevPod, which runs dev containers on infrastructure you choose. Most container-based products read the open [dev container specification](./what-is-a-dev-container-and-why-do-platforms-standardise-on-them.md), which reduces lock-in.

**The trade-offs.**

- **Cost model.** You pay for compute while workspaces run, so idle shutdown and machine-size limits are essential. A workspace left running over a weekend is the default failure.
- **Latency and offline work.** Typing is local in most setups, but anything that round-trips to the server needs a decent connection, and there is no working on a plane.
- **Loop speed is a separate problem.** A remote workspace that rebuilds a container image on every change is just as slow as a laptop doing the same. Pair a CDE with file sync or hot reload - see [how to give developers a fast inner development loop](./how-do-you-give-developers-a-fast-inner-development-loop.md).
- **Vendor risk.** Hosted products change or close; AWS stopped offering Cloud9 to new customers in 2024. Keeping the workspace definition in the open dev container format means you can move.

**Who the platform serves.** Application engineers, and especially new starters. The platform team owns the base images, the templates per language or team, the network access into development clusters, and the policies - idle timeout, maximum size, allowed regions. Engineers own the repository-level definition for their service. AI coding agents are increasingly users too: an agent working on a task needs the same reproducible, isolated workspace a human does, and a CDE is a natural place to give it one without handing it a laptop.

**When it is not worth it.** A small team with a simple stack and fast laptops may get little from a CDE. The strongest cases are large codebases, frequent onboarding, strict data-handling rules, or heavy compute.

## Example

```yaml
# A platform-owned workspace template. Teams pick a template; the repository's
# dev container file adds service-specific tools on top.
apiVersion: platform.example.com/v1
kind: WorkspaceTemplate
metadata: { name: go-service }
spec:
  devcontainer: .devcontainer/devcontainer.json # read from the repository
  machine:
    default: { cpus: 4, memory: 16Gi, disk: 64Gi }
    maximum: { cpus: 16, memory: 64Gi } # bigger needs a request, not a default
  lifecycle:
    idleShutdown: 30m # the control that decides the bill
    maxRuntime: 12h
    deleteAfterUnused: 14d
  network:
    allow: [dev-cluster.internal, artifacts.internal, git.internal]
    deny: [production] # a workspace can never reach production
  prebuild:
    onPushTo: main # dependencies pre-installed so start is fast
```

```text
Onboarding a new engineer, before and after.

  LAPTOP SETUP                          CLOUD DEVELOPMENT ENVIRONMENT
  install toolchain         ~1h         open workspace from the repo   ~1m
  fix version mismatches    ~2h         prebuild already has deps        -
  get VPN + DB access       ~1 day      network policy grants dev access -
  first successful build    day 2       first successful build         ~5m
  first merged change       week 1      first merged change            day 1
```

## Interview tips

- Define it as a remote workspace created from a definition in the repository; the definition is what makes it reproducible.
- Lead with the problems it solves - consistency, onboarding, heavy compute, security - and back the onboarding point with a before-and-after.
- Separate environment consistency from loop speed. Saying a CDE alone does not make the loop fast shows you have used one.
- Name the controls that keep it affordable: idle shutdown, size limits, and prebuilds.
- Expect "how does this relate to dev containers?" - the dev container is the portable definition, the CDE is one place to run it.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
