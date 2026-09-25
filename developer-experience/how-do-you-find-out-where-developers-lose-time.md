---
title: "How do you find out where developers lose time?"
id: 18
category: "Developer Experience"
difficulty: "Beginner"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# How do you find out where developers lose time?

**Short answer:** Combine three sources and look for where they agree. Ask developers directly, with a short, regular survey about specific friction points and how much time they lose to each. Watch them work, by shadowing a real task or asking them to keep a friction log. Measure the waiting that systems already record: CI duration, time waiting for review, time waiting for environments or access. Surveys tell you what hurts, observation tells you why, and system data tells you how much. None of the three is reliable on its own.

## Detail

**Who this is for.** The users are product engineers, and the output is the platform team's backlog. Getting this wrong is expensive, because platform teams naturally fix the problems they can see from their own side (cluster upgrades, pipeline internals) rather than the ones developers actually hit (waiting two days for database access). Finding out where time goes is how you avoid building the wrong thing well.

**Source 1: ask, with a survey that can be acted on.** A vague question ("how satisfied are you with tooling?") produces a number nobody can use. Ask about specific parts of the work, and ask about time:

- "In a typical week, how much time do you lose to: slow builds, flaky tests, waiting for code review, finding documentation, waiting for access or environments, understanding unfamiliar code?"
- "What was the single most frustrating thing about shipping your last change?" (free text, which is often the most useful part)

Run it quarterly or twice a year, keep most questions the same so you can see trends, and publish what you changed as a result. People stop answering surveys that lead nowhere. Industry developer surveys regularly find engineers reporting several hours a week lost to friction. A self-reported time estimate is rough, but it is worth collecting because it lets you compare very different problems in the same unit.

**Source 2: watch.** Sit with an engineer while they do a real task, such as adding an endpoint or setting up a new service, and do not help. Or ask volunteers to keep a friction log for a week: each time they get stuck, one line with what they were trying to do, what blocked them, and how long it took. Observation finds problems nobody mentions in surveys because they have stopped noticing them, like the four manual steps everyone "just knows" to do before a deploy.

**Source 3: measure the waiting.** Much lost time is waiting, and waiting leaves timestamps:

| Where time goes            | Where the data already is                          |
| -------------------------- | -------------------------------------------------- |
| CI and build duration      | CI system run history (look at p95, not just p50)  |
| Flaky test re-runs         | CI retries and tests that pass on a second attempt |
| Waiting for code review    | PR opened to first review, from the Git host API   |
| Waiting for access         | Ticket system: request created to fulfilled        |
| Waiting for an environment | Provisioning job start to ready                    |
| Local build and test loop  | Build tool telemetry, if you instrument it         |
| Repeated questions         | Support channel messages, tagged by category       |

Split totals into their parts. "PR lead time is two days" is not actionable. "Thirty-eight hours of it is waiting for the first review and two hours is CI" tells you the fix is a review process, not a faster pipeline.

**Put it together and rank.** For each friction point, estimate the time lost per developer per week and multiply by the number of developers affected. A daily ten-minute annoyance for 300 engineers often outweighs a painful but rare problem for 20. Then check the top items against all three sources: if the survey, the friction logs, and the data all point at flaky tests, you have found your next quarter.

**The traps.** Do not use this data to judge individuals or rank teams, or people will stop telling you the truth. Do not measure activity (commits, lines of code) as a stand-in for lost time. And do not rely only on the loudest voices in the support channel. They are real, but they are a biased sample.

## Example

```text
One quarter's findings for a 250-engineer organisation.
Hours lost = self-reported median hours/week x engineers affected, checked against data.

  friction point            survey (median   affected   hrs lost/wk   system data agrees?
                            hrs/wk/person)
  flaky tests               1.5              210        315           yes: 9% of CI runs
                                                                      pass only on retry
  waiting for 1st review    2.0              150        300           yes: p50 19h to first
                                                                      review
  finding docs / owners     1.0              230        230           partly: 40 support
                                                                      questions/wk "who owns X"
  slow local builds         1.5              90         135           yes: Java monorepo
                                                                      p50 6m per build
  waiting for DB access     4.0              12         48            yes: p50 2.5d per ticket

  What observation added (six shadowing sessions):
    - Every engineer re-ran CI "just in case" before asking for review. This is flaky
      tests showing up as review delay too.
    - Nobody used the docs site search. They searched chat instead.

  Decision: flaky-test quarantine and review SLAs first. DB access is painful but
  affects 12 people - automate it, but it is not the top item.
```

## Interview tips

- Name all three sources (ask, watch, measure) and what each one is good for. Relying on only one is the common weak answer.
- Stress specific survey questions that ask about time, and closing the loop by publishing what changed.
- Show that you split a total into waiting and working time. It is the step that turns data into a fix.
- Rank by time lost multiplied by people affected. It shows you prioritise by impact, not by who complains loudest.
- Say you would never use this data on individuals. Then relate it to [developer experience measurement](./what-is-developer-experience-and-how-do-you-measure-it.md) and [onboarding time](./how-do-you-reduce-the-time-it-takes-a-new-engineer-to-ship-to-production.md) if the conversation goes deeper.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
