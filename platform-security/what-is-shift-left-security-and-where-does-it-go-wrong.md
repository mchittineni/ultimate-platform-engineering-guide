---
title: "What is shift-left security and where does it go wrong?"
id: 123
category: "Platform Security"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# What is shift-left security and where does it go wrong?

**Short answer:** Shift-left means moving security checks earlier in the delivery timeline - into the editor, the pull request, and the build - so problems are found when they are cheapest to fix, rather than in a pre-release audit or in production. It goes wrong when "shift left" becomes "hand developers every scanner and every finding": noisy tools, blocking gates on issues nobody can fix, and no help deciding what matters. The platform-engineering correction is to shift security _down_ into the platform - secure defaults that need no action - and only shift left the small set of findings a developer can and should act on.

## Detail

**The idea, and why it is sound.** Picture the delivery process as a timeline running left to right: design, code, review, build, deploy, run. A flaw found on the left costs a few minutes to fix; the same flaw found in production costs an incident, a hotfix, and possibly a disclosure. Checks that run early - a secret scanner in a pre-commit hook, a dependency scan on the pull request, a policy check on a Terraform plan - give fast feedback while the author still has context.

**Where it goes wrong:**

- **Tool dumping.** The security team buys scanners and turns them all on in every pipeline. Developers suddenly see hundreds of findings with no context. The work of security triage has been moved to people without the training or the time to do it.
- **Noise.** Most findings in a typical container scan are in packages the application never loads, or have no fix available. When 95% of alerts are irrelevant, developers learn to ignore all of them - including the one that matters.
- **Blocking on the unfixable.** A gate that fails the build on any critical CVE, including ones with no upstream patch, stops delivery without offering a remedy. Teams respond by disabling the check or adding blanket ignores.
- **No owner for exceptions.** Suppressions pile up in config files with no reason, owner, or expiry, and a year later nobody knows which are still valid.
- **Left instead of, not left as well as.** Checks at build time do not see a vulnerability disclosed next month. Shifting left does not remove the need for runtime detection and continuous rescanning of what is deployed.
- **Measuring activity, not outcomes.** "Number of scans run" goes up; time to fix exploitable issues does not change.

**The fix: shift down first, then shift left selectively.** Many security problems should never reach a developer at all, because the platform prevents them by construction:

| Instead of telling developers... | ...the platform makes it the default                  |
| -------------------------------- | ----------------------------------------------------- |
| "Don't run containers as root"   | Pod Security `restricted` enforced on every namespace |
| "Rotate your cloud keys"         | Workload identity - there are no keys                 |
| "Patch your base image"          | Platform rebuilds images and raises tested PRs        |
| "Don't expose services publicly" | Default-deny network and authenticated ingress        |
| "Sign your images"               | The build template signs every image                  |

What remains for the developer is what only they can fix - a vulnerable direct dependency with a fix available, a secret accidentally committed, an injection flaw in their code. Those are the findings worth shifting left.

**Make the left-shifted checks good.** A useful developer-facing check is fast, runs where the developer already is (the pull request, not a separate portal), reports only actionable findings, explains the fix, and has a self-service exception path with an owner and an expiry. Gate the build on a narrow, high-confidence set - for example, critical vulnerabilities _with a fix available_ in reachable code, or a verified live secret - and report everything else without blocking.

**Who the user is.** Application developers. The measure of success is whether they fix real problems faster, not whether they see more alerts. The security team is a second user: it gets consistent coverage and one place to tune policy, instead of forty pipelines configured differently.

## Example

```yaml
# The platform's reusable pull-request check. Teams call it; they do not
# configure scanners themselves.
name: pr-security
on:
  workflow_call:

permissions:
  contents: read

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0 # the secret scan diffs against main
      # Pinned tool versions - the security check is itself part of the supply chain.
      - name: Install scanners
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/v0.119.0/install.sh | sh -s -- -b "$HOME/.local/bin" v0.119.0
          curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/v3.97.9/scripts/install.sh | sh -s -- -b "$HOME/.local/bin" v3.97.9
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"
      # Blocking: only critical findings that have a fix available.
      # Everything else is reported, not enforced.
      - name: Dependency scan (blocking on fixable criticals only)
        run: grype dir:. --only-fixed --fail-on critical
      # Blocking: verified live secrets only, not every string that looks random.
      - name: Secret scan
        run: trufflehog git file://. --since-commit origin/main --results=verified --fail
```

```yaml
# .grype.yaml - suppressions live in the repo, reviewed like code.
# A platform check rejects entries without an owner and a review date comment,
# and flags ones whose review date has passed.
ignore:
  # CVE-2024-0000 in libfoo: not reachable, only used in the build stage.
  # owner: team-payments  review: 2027-01-31
  - vulnerability: CVE-2024-0000
    package:
      name: libfoo
```

```text
The same service before and after moving to "shift down, then left":

                                  before      after
  findings shown per PR .......... 212         3
  of which actionable ............   4         3
  builds blocked per month .......  37         2
  median days to fix a fixable
    critical in a direct dep ......  41         4
  blanket ignores in config ......  19         0

  Fewer alerts, faster fixes. The 200 removed findings were not hidden; most
  disappeared because the platform's minimal base image no longer contains
  the packages they were in.
```

## Interview tips

- Define shift-left in one line - find problems earlier where they are cheaper to fix - then spend most of the answer on where it goes wrong. That is what the question is really asking.
- Name the failure modes concretely: tool dumping, noise, blocking on unfixable issues, unowned suppressions, and neglecting runtime.
- "Shift down before shifting left" is the platform-engineering answer: secure defaults remove whole classes of findings so developers never see them.
- Name the user - application developers - and measure success by time to fix real issues, not by number of scans.
- Be specific about gating: block on a narrow, high-confidence set (fixable criticals, verified secrets) and report the rest.
- Related: [policy as code](../policy-as-code-and-governance/what-is-policy-as-code-and-where-does-it-belong-in-a-platform.md), [rolling out a policy without breaking teams](../policy-as-code-and-governance/how-do-you-roll-out-a-new-policy-without-breaking-every-team.md), and [keeping base images patched](./how-do-you-keep-base-images-patched-across-every-team.md).

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
