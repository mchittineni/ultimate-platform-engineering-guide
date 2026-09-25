---
title: "How do you gather feedback from platform users?"
id: 241
category: "Platform Team and Operating Model"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# How do you gather feedback from platform users?

**Short answer:** Combine what users tell you with what they do. Ask through short periodic surveys, interviews, and watching engineers use the platform; observe through support questions by category, escape hatch usage, and teams that adopt a capability and then leave. Then close the loop visibly - tell people what you changed because of their feedback - or they stop giving it. The users are the product engineers who build on the platform, and internal users are unusually likely to put up with pain quietly, so you have to go looking.

## Detail

**Internal users under-report.** A frustrated customer of a public product leaves or complains. A frustrated internal engineer usually writes a workaround script and says nothing, because they assume the platform team is busy or because complaining feels like criticising colleagues. Waiting for feedback to arrive means hearing only from the loudest few.

**Two kinds of signal, and you need both:**

| Type               | Sources                                                             | Good at               | Weak at                      |
| ------------------ | ------------------------------------------------------------------- | --------------------- | ---------------------------- |
| Said (attitudinal) | Surveys, interviews, office hours, retros                           | Why, and how it feels | Accuracy; people misremember |
| Done (behavioural) | Support tickets by category, escape hatches, usage telemetry, churn | What actually happens | Why it happens               |

Behavioural data tells you where to look; conversations tell you what is going on. A spike in "where is my deploy?" questions shows the problem exists; an interview shows that engineers cannot find the pipeline link in the pull request.

**Surveys: short, regular, and comparable over time.** A quarterly survey of five to ten questions is enough. Keep a small core of the same questions each time - satisfaction with the platform overall, ease of the most common tasks, and a free-text "what one thing would you change?" - so you can see trends. Long surveys get low response rates and skewed answers. Frameworks like SPACE or the DevEx framework help choose questions that cover more than just speed.

**Interviews and shadowing: the richest source.** Sit with an engineer while they create a new service or debug a failed deploy, and ask them to narrate. You will see the three tabs they need open, the command they copy from a wiki, and the step they skip because it never works. Five of these a quarter usually surface more than a survey.

**Mine the support channel.** Tag every question by category. The largest categories are either missing documentation, missing visibility, or a missing capability. This is free data you are already generating.

**Watch escape hatches and churn.** If eleven services override the same default, the default is wrong. If a team adopted a capability and moved back to its own tooling, interview that team first - they tried you and found you lacking, which is the most specific feedback available.

**Make it cheap to give feedback in the moment.** A link in the CLI output, a thumbs up or down on documentation pages, a feedback command in the developer portal. Friction captured at the moment it happens is more accurate than friction remembered in a survey.

**Close the loop.** Publish a short "you said, we did" note after each survey or each quarter. When people see their comment turn into a change, response rates rise; when feedback disappears into a void, they stop.

**Trade-offs and traps.** Surveys measure perception and can lag real improvements. Telemetry can be gamed or misread. Do not tie survey scores to individual or team performance reviews, or the answers become political. And avoid treating the loudest team as representative - weight feedback by how many teams share the problem.

## Example

```text
A quarterly feedback cycle for a platform serving 25 product teams.

  WEEK 1   SURVEY (7 questions, anonymous, ~3 minutes)
             core, same every quarter:
               - overall, how satisfied are you with the platform? (1-5)
               - how easy is it to deploy a change? (1-5)
               - how easy is it to find why a deploy failed? (1-5)
               - what one thing would you change? (free text)
             rotating: 3 questions on this quarter's focus (secrets handling)
           responses: 118 of 190 engineers (62%)

  WEEK 2   BEHAVIOURAL DATA, same period
             support questions by category (top 3):
               deploy status 31, secrets rotation 22, preview envs 9
             escape hatches: 9 services override the default memory limit
             churn: team-ml left the batch job capability

  WEEK 3   INTERVIEWS (5), chosen from the data, not volunteers
             team-ml (churned), two teams with the memory override,
             one new starter, one team with the highest satisfaction score
           finding: "why did my deploy fail" score 2.4/5; shadowing showed
           the error is 400 lines down a CI log

  WEEK 4   CLOSE THE LOOP - published to all engineers
             you said: failed deploys are hard to diagnose
             we will:  surface the first error in the PR comment (next sprint)
             you said: default memory limit too low for JVM services
             we did:   raised it for the JVM template; 9 overrides removed
```

## Interview tips

- Say you need both what users say and what they do, and give an example of each.
- Point out that internal users under-report, so feedback has to be sought rather than waited for.
- Treat churned teams and escape hatch clusters as the most specific feedback you have.
- Mention a short, repeatable survey with stable core questions, and name a framework such as SPACE or DevEx.
- Always close the loop publicly; it is what keeps people responding.
- Likely follow-up: "how do you turn feedback into a roadmap?" See [building a roadmap and saying no](./how-do-you-build-a-platform-roadmap-and-say-no.md) and [what developer experience is and how to measure it](../developer-experience/what-is-developer-experience-and-how-do-you-measure-it.md).

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
