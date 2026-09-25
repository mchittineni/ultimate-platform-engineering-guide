---
title: "What is a dev container and why do platforms standardise on them?"
id: 108
category: "Environments and Ephemeral Infrastructure"
difficulty: "Beginner"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# What is a dev container and why do platforms standardise on them?

**Short answer:** A dev container is a container used as a full development environment, described by a `devcontainer.json` file committed to the repository. The file names a base image, reusable add-ons called features, editor settings, forwarded ports, and setup commands, and any supporting tool can turn it into a ready-to-code workspace. Platforms standardise on it because it is an open specification that works the same on a laptop, in a cloud development environment, and in CI - one definition, many places to run it.

## Detail

**The mechanism.** A tool that understands the [Development Container Specification](https://containers.dev/) reads `.devcontainer/devcontainer.json`, builds or pulls the image, installs each listed feature as an extra layer, mounts or clones the source code, runs lifecycle commands such as `postCreateCommand`, and connects the editor to a server inside the container. The engineer edits files as usual, but the compilers, linters, and CLIs all run inside the container, at the versions the file pins.

**The main parts of the file:**

| Field               | What it does                                                     |
| ------------------- | ---------------------------------------------------------------- |
| `image` or `build`  | The base environment - a published image or a Dockerfile         |
| `features`          | Reusable, versioned add-ons: a language, a CLI, Docker-in-Docker |
| `customizations`    | Editor-specific settings and extensions                          |
| `forwardPorts`      | Ports from the container made reachable from the editor          |
| `postCreateCommand` | One-off setup, such as downloading dependencies                  |
| `hostRequirements`  | Minimum CPU, memory, and storage for hosted runners              |
| `remoteUser`        | Run as a non-root user inside the container                      |

**Why platforms standardise on it.**

- **It is portable.** The same file works in VS Code with the Dev Containers extension, GitHub Codespaces, JetBrains IDEs, DevPod, Coder, and the open-source `devcontainer` CLI. Choosing it avoids betting on one vendor's workspace format.
- **Features are a distribution channel.** A platform team can publish its own features to a container registry - an internal CLI, company certificates, a pre-configured cloud login - and every team gets them by adding one line.
- **It is reviewable code.** A tool upgrade is a pull request against a pinned version, not an instruction on a wiki that half the team never follows.
- **It closes the gap with CI.** The `devcontainer` CLI can build the same container in a pipeline, so linting and tests run with the exact toolchain engineers use.

**Who the platform serves.** Application engineers get a working environment from a clone and a click. The platform team maintains base images and internal features, and keeps them patched - an unpatched dev container base image is a supply chain risk like any other image. Coding agents benefit too: a repository with a dev container tells an agent exactly how to build and test the project.

**Trade-offs.**

- **Performance on some laptops.** File-system access through a container on macOS or Windows can be slower than native, especially for large dependency trees. Named volumes or a cloud workspace usually fix it.
- **It is a development image, not a production image.** It carries compilers, debuggers, and shells that production images deliberately leave out. Do not ship it.
- **Features are code from someone else.** Pin feature versions and prefer a curated internal set over arbitrary community features.
- **Not everything fits in a container.** Mobile development with device simulators, or GUI-heavy desktop work, may need a full virtual machine instead.

## Example

```json
{
  "name": "checkout-service",
  "image": "mcr.microsoft.com/devcontainers/base:bookworm",
  "features": {
    "ghcr.io/devcontainers/features/go:1": { "version": "1.25" },
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": { "minikube": "none" },
    "ghcr.io/example-org/devcontainer-features/platform-cli:3": {}
  },
  "forwardPorts": [8080],
  "postCreateCommand": "go mod download",
  "remoteUser": "vscode",
  "hostRequirements": { "cpus": 4, "memory": "16gb" },
  "customizations": {
    "vscode": {
      "extensions": ["golang.go", "redhat.vscode-yaml"]
    }
  }
}
```

```bash
# The same definition in CI: lint and test with the exact engineer toolchain.
npx @devcontainers/cli up --workspace-folder .
npx @devcontainers/cli exec --workspace-folder . go test ./...
```

The last feature line is the platform team's own feature, published to a registry. Adding it gives every service the internal CLI, pinned to a major version, without anyone editing a setup script.

## Interview tips

- Define it as a container used as a development environment, described by an open specification in `devcontainer.json`, and name the key parts: image, features, lifecycle commands.
- The portability argument - laptop, cloud workspace, and CI from one file - is the main reason platforms standardise on it. Say it explicitly.
- Mention internal features as the platform's distribution channel; it shows you think about how platform tooling reaches teams.
- Give at least one limitation: macOS file-system performance, or that it must never become a production image.
- A natural follow-up is [what a cloud development environment is](./what-is-a-cloud-development-environment.md); the dev container is the definition, the CDE is one place to run it.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
