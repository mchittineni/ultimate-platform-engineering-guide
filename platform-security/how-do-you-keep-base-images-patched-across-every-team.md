---
title: "How do you keep base images patched across every team?"
id: 70
category: "Platform Security"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# How do you keep base images patched across every team?

**Short answer:** The platform owns a small set of base images, rebuilds them on a schedule and on advisory, and then rebuilds and raises pull requests for every downstream service automatically. Publishing a new base image is not the deliverable - a patched base nobody rebuilds against changes nothing. What makes this work is that the platform does the downstream rebuild rather than asking forty teams to bump a tag.

## Detail

**Why teams cannot be relied on to do it.** Rebuilding for a base image patch has no visible benefit to the team, competes with product work, and is invisible until an audit or an incident. Any mechanism depending on forty teams remembering will have a long tail measured in months. The design principle is the same as any platform migration: do it for them.

**Own a narrow set of images.** One per language runtime, plus a minimal one for static binaries. Each carries the platform's certificate bundle, a non-root user, the timezone data, and any required agents. A wide catalogue of variants multiplies your patching surface for no benefit; teams needing something unusual should have a documented route rather than a new supported image.

**Use minimal or distroless bases.** Fewer packages means fewer advisories, and most of the vulnerabilities reported in a typical image are in packages the application never invokes - a shell, a package manager, utilities. Removing them reduces both real risk and the far larger volume of noise that makes triage exhausting.

**Rebuild on two triggers.** A schedule - weekly is a reasonable policy - picks up accumulated upstream patches. An advisory trigger rebuilds immediately when a critical vulnerability affects a package you ship. The schedule handles the ordinary case, the trigger handles the urgent one.

**Then rebuild downstream, automatically.** For every service whose image derives from the base, rebuild, run its tests, and open a pull request if they pass. That last condition matters: an automated bump that breaks a build creates work rather than removing it, so the bot should test first and only raise green changes, escalating the failures separately.

**Track staleness as a platform metric, per service.** How old is the base each running service was built on. That single number tells you whether the mechanism works, and it belongs on the platform's own dashboard rather than in a security report nobody reads.

**Enforce with admission, once the mechanism is reliable.** Rejecting workloads whose base image exceeds an age threshold makes patch currency a property rather than an aspiration - but only introduce it after the automated rebuild path works, or you have blocked deployments without providing the remedy.

**Distinguish real risk from noise.** A scanner reporting 200 vulnerabilities in an image is usually mostly unreachable code. Prioritise by whether the vulnerable component is actually loaded and reachable, and whether the service is exposed. Treating every finding as equally urgent exhausts the team and hides the ones that matter.

**Have an answer for third-party images.** Vendor agents, ingress controllers, and database operators are not built from your base. They need their own currency tracking, an owner, and an escalation path to the vendor - and they are usually the oldest images in the estate.

## Example

```dockerfile
# The platform's base image - narrow, minimal, non-root, patched centrally.
# platform-images/go/Dockerfile
FROM gcr.io/distroless/static-debian12:nonroot

# Platform-supplied invariants every service inherits
COPY --from=ca-certs /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=tzdata /usr/share/zoneinfo /usr/share/zoneinfo

USER nonroot:nonroot
ENTRYPOINT ["/app"]

# Distroless: no shell, no package manager, no utilities. Most CVEs reported
# against a full base image are in packages that are simply absent here.
```

```yaml
# Trigger 1: schedule. Trigger 2: advisory. Both rebuild the base, then fan out.
name: base-image-rebuild
on:
  schedule: [{ cron: "0 3 * * 1" }] # weekly (our policy)
  repository_dispatch:
    types: [security-advisory] # immediate on a critical advisory

jobs:
  rebuild-bases:
    strategy:
      matrix: { variant: [go, node, python, java, static] } # deliberately narrow
    runs-on: ubuntu-latest
    permissions: { contents: read, id-token: write, packages: write }
    steps:
      - uses: actions/checkout@v5
      - run: |
          docker build -t "ghcr.io/example/base-${{ matrix.variant }}:$(date +%Y%m%d)" \
            platform-images/${{ matrix.variant }}
          docker push "ghcr.io/example/base-${{ matrix.variant }}:$(date +%Y%m%d)"
      - run: cosign sign --yes "ghcr.io/example/base-${{ matrix.variant }}:$(date +%Y%m%d)"

  # The part that actually matters: rebuild every consumer, test, and only then
  # raise a PR. A red automated bump creates work instead of removing it.
  rebuild-consumers:
    needs: rebuild-bases
    runs-on: ubuntu-latest
    steps:
      - name: Fan out to every service built on a platform base
        run: |
          for repo in $(platform catalogue query --base-image 'ghcr.io/example/base-*'); do
            ./scripts/bump-base-and-test.sh "$repo" || {
              platform issue open "$repo" --label base-bump-failed --assign-owner
              continue
            }
            ./scripts/open-pr.sh "$repo" --title "chore: rebuild on patched base image"
          done
```

```text
The metric that tells you whether the mechanism works:

  $ platform images staleness

  BASE AGE OF RUNNING SERVICES
    < 7 days .......... 181 services
    7-14 days .........  24
    14-30 days ........   8
    > 30 days .........   5   <-- investigate
      team-data/legacy-etl        94d   base bump PR failing since 2026-05-12
                                        (test suite depends on a shell in the
                                        image - distroless removed it)
      team-ops/report-gen         61d   no PR raised: repo not in the catalogue
      3 more

  THIRD-PARTY IMAGES (not built on our base - usually the oldest in the estate)
    vendor-search-agent:2.1      412d   owner: bob   vendor contacted 2026-06-01
    legacy-db-operator:0.9       288d   owner: carol  upgrade path blocked
    ingress-controller:1.11       21d   owner: platform  current

  Note the two failure modes: a service whose tests depend on something the
  minimal base removed, and a service missing from the catalogue so the fan-out
  never reached it. Both are mechanism bugs, not team failures.
```

## Interview tips

- The thesis: publishing a patched base is not the deliverable, rebuilding every consumer is. Say that the platform does the rebuild rather than asking teams to.
- Two triggers - scheduled and advisory-driven - is the concrete design, and it shows you distinguish routine currency from urgent response.
- "Test before raising the pull request" is a small detail with a big effect: red automated bumps train teams to ignore the bot.
- Distroless or minimal bases, with the reasoning that most reported vulnerabilities are in packages the application never invokes, addresses both real risk and triage fatigue.
- Staleness per running service is the metric to name, and it belongs on the platform dashboard rather than in a security report.
- Admission enforcement only after the rebuild path is reliable - otherwise you have blocked deployments without supplying the remedy.
- Third-party images as a separate track, usually the oldest in the estate, is the detail that shows you have measured this rather than designed it.

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
