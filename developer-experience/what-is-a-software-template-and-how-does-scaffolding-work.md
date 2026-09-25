---
title: "What is a software template and how does scaffolding work?"
id: 17
category: "Developer Experience"
difficulty: "Beginner"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# What is a software template and how does scaffolding work?

**Short answer:** A software template is a parameterised starting point for something new, usually a service repository, that already follows the organisation's golden path. Scaffolding is the process that turns the template into a real thing. It asks the developer a few questions, fills the answers into the template files, creates the repository, and then carries out the registration steps a human would otherwise do by hand: the CI pipeline, the catalogue entry, the access groups. The goal is that a new production-ready service takes minutes instead of days. The main limitation is that a template is copied once, so whatever it generates will drift from the template unless you design against that.

## Detail

**Who uses it and what it saves them.** The user is a product engineer starting something new: a service, a library, a data pipeline, sometimes just a new cloud resource. Without a template they copy an existing repository they believe is "good", delete what they do not need, and miss the parts nobody told them about: the alert routing, the security scan, the catalogue descriptor. A template turns tribal knowledge into a form with five fields. It also saves the platform team, because every new service starts on the supported path instead of as a special case they later have to migrate.

**How the mechanism works, step by step:**

1. **Parameters.** The template declares its inputs: name, owning team, language, whether the service needs a database. Inputs are validated (naming rules, an owner who exists) before anything is created.
2. **Rendering.** A template engine substitutes the values into skeleton files. Backstage uses Nunjucks syntax (`${{ values.name }}`); Cookiecutter and Copier use Jinja. Files and directories can be included or skipped depending on the answers.
3. **Actions.** The scaffolder runs a sequence of steps: publish the rendered files to a new repository, apply branch protection, register the service in the catalogue, and optionally call platform APIs to create environments or resources.
4. **Output.** The developer gets links to the repository, the pipeline run, and the catalogue page. A good template ends with a service already deployed to a development environment, so the first thing the developer sees is something working.

**The tools you will hear about.** Backstage Software Templates run inside a developer portal and are good at the "register everything" steps. Cookiecutter and Copier are command-line generators that work without a portal. Copier can also re-apply a newer template version to an existing project (`copier update`). GitHub template repositories are the simplest option: a copy with no parameters and no follow-up actions.

**The trade-off: templates diverge.** Once generated, the repository belongs to the team, and the template has no further control over it. If the template contains a full 200-line CI pipeline, then changing how images are signed means pull requests to every repository ever created from it. The defence is to keep generated files thin and make them _reference_ things the platform owns centrally rather than copy them:

- CI calls a shared, versioned reusable workflow instead of containing the pipeline steps.
- The Dockerfile starts `FROM` a platform-maintained base image.
- Deployment is described in a short service spec that the platform turns into manifests, rather than a copied Helm chart.

Done this way, the template sets up the wiring once and the platform can keep improving what the wiring points at. The [service, library, or template question](../platform-architecture/when-should-a-platform-capability-be-a-service-a-library-or-a-template.md) covers this decision in more depth.

**Other trade-offs to name.** Too many templates (one per team's preferences) recreate the fragmentation they were meant to remove. Templates with too many questions push the decisions back to the developer. And a template nobody maintains quietly generates outdated services, so each template needs an owner and a test that scaffolds it in CI and checks that the result builds and deploys.

## Example

```yaml
# A Backstage software template (scaffolder.backstage.io/v1beta3).
# Three inputs, then the steps a human would otherwise do by hand.
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: go-http-service
  title: Go HTTP service (golden path)
  description: Go service with CI, base image, SLO dashboard, and a dev deployment
spec:
  owner: group:platform-team
  type: service
  parameters:
    - title: Service details
      required: [name, owner]
      properties:
        name:
          type: string
          pattern: "^[a-z][a-z0-9-]{2,30}$"
        owner:
          type: string
          ui:field: OwnerPicker
          ui:options:
            catalogFilter:
              kind: Group
        needsDatabase:
          type: boolean
          default: false
  steps:
    - id: render
      name: Render skeleton
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: ${{ parameters.name }}
          owner: ${{ parameters.owner }}
          needsDatabase: ${{ parameters.needsDatabase }}
    - id: publish
      name: Create repository
      action: publish:github
      input:
        repoUrl: github.com?owner=example-org&repo=${{ parameters.name }}
        description: ${{ parameters.name }} service
        defaultBranch: main
    - id: register
      name: Register in catalogue
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps.publish.output.repoContentsUrl }}
        catalogInfoPath: /catalog-info.yaml
  output:
    links:
      - title: Repository
        url: ${{ steps.publish.output.remoteUrl }}
      - title: Catalogue entry
        icon: catalog
        entityRef: ${{ steps.register.output.entityRef }}
```

```yaml
# skeleton/.github/workflows/ci.yaml - what the template generates.
# Six lines that point at a centrally owned pipeline, so the platform can
# change signing, scanning, or caching without touching this repository.
name: ci
on: [push, pull_request]
jobs:
  golden-path:
    uses: example-org/platform-workflows/.github/workflows/go-service.yaml@v4
    secrets: inherit
```

## Interview tips

- Explain the mechanism in order: parameters, rendering, actions, output. It shows you know a template is more than a copied folder.
- Name the user and the saving: a product engineer gets a compliant, registered, deployed service in minutes instead of copying a repository and missing half the wiring.
- The point to land is divergence. A template is copied once, so keep generated files thin and point them at centrally versioned pieces.
- Mention testing templates in CI. An unmaintained template produces outdated services at scale.
- If asked about day-two updates, mention Copier's update mechanism or reconciled generation from a spec, and say that the second is usually the better answer for anything that changes often.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
