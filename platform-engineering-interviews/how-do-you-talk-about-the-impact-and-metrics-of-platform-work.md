---
title: "How do you talk about the impact and metrics of platform work?"
id: 259
category: "Platform Engineering Interviews"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# How do you talk about the impact and metrics of platform work?

**Short answer:** Connect what you built to a change in how your users - the product engineers - work, then to something the business cares about, and be explicit about how you know. Use a small chain: adoption shows they chose it, a flow or experience measure shows it helped them, and a business measure shows why it mattered. Always give provenance and caveats, because platform impact is indirect and interviewers are listening for whether you can tell your contribution apart from everything else that changed at the same time.

## Detail

**Why this is harder for platform work.** A product engineer can say "this feature raised conversion by two percent". Platform work acts through other teams: you make them faster, safer, or cheaper, and they produce the business outcome. The interview question is therefore partly a test of whether you understand that indirection and can still make a defensible claim.

**Use a three-level chain.**

| Level          | What it shows                    | Typical measures                                                                               |
| -------------- | -------------------------------- | ---------------------------------------------------------------------------------------------- |
| Adoption       | Engineers chose it               | Teams or services on the path, share of deploys through it, voluntary versus mandated          |
| Flow and DevEx | It changed how they work         | Lead time, time to first deploy, time to a new service, tickets, survey scores, cognitive load |
| Business       | Why the organisation should care | Engineering hours returned, incidents avoided, audit effort, cost per unit, time to market     |

A claim at one level without the others is weaker. Adoption without an outcome might be a mandate. An outcome without adoption might be a coincidence. A business number without the other two is usually a guess.

**Know the frameworks and use them lightly.** DORA's metrics are the common vocabulary: deployment frequency, change lead time, and failed deployment recovery time for throughput; change failure rate and, since 2024, rework rate for instability. SPACE and the DevEx framework argue for combining system data with what developers report, and DX Core 4 packages speed, effectiveness, quality, and impact together. Naming them shows literacy; hanging a whole answer on one framework reads as recited. The more recent DORA research on AI-assisted development is worth knowing: it found AI tends to amplify whatever the delivery system already is, which is a useful argument for platform investment.

**Give provenance for every number.** Where did it come from - pipeline timestamps, the ticket system, a survey, a cost report? Over what period, and with what sample? "Median lead time from pipeline events, across the 31 migrated teams, the quarter before versus the quarter after" is credible. "Deploys got about ten times faster" invites the follow-up you cannot answer.

**Address attribution before you are asked.** Other things changed too: headcount, a reorganisation, a new release process. Say what you did to separate your effect - comparing migrated with not-yet-migrated teams over the same period is the strongest simple method, and a staggered rollout gives you that for free. If you could not isolate the effect, say so; that honesty scores better than an overclaim.

**Translate carefully into money or time.** Converting "tickets fell by sixty a month" into "about 60 engineer-hours a month returned" is reasonable if you state the assumption. Multiplying by salary and calling it savings is less convincing, because returned hours are not banked; say what teams did with the time if you know.

**Avoid vanity metrics.** Number of templates, number of catalogue entries, number of pipelines run, portal page views. They measure activity, not effect. If that is all you had, say what you would measure now.

**Include the metrics that went the wrong way.** A change failure rate that rose briefly during a migration, a survey score that fell for one team. Explaining it shows you were actually watching.

**Current reality.** Interviewers increasingly ask how you would measure the effect of AI coding assistants or agents on a platform. The honest answer is the same chain: adoption, then flow and quality measures including rework and change failure rate, then outcomes, with a caution that self-reported productivity and measured delivery often diverge.

## Example

```text
"What was the impact of the shared pipeline you built?"

  WEAK
    "It made deploys much faster and everyone loved it. We saved loads of time."
    -> no number, no provenance, no attribution, no user

  STRONG - the chain, with provenance and caveats

    ADOPTION - they chose it
    "31 of 40 teams moved over two quarters, voluntarily. The 9 that did not
     had a real reason - mostly mobile release trains the path did not fit -
     which became the next roadmap item."

    FLOW - it changed how they work
    "Median commit-to-production went from about 2 days to 45 minutes, from
     pipeline event timestamps. Change failure rate held at around 6%, so we
     did not buy speed with instability. Pipeline-related support questions
     fell from roughly 60 a month to under 10, from our ticket categories."

    ATTRIBUTION - before being asked
    "Migration was staggered, so for two months I could compare migrated and
     unmigrated teams side by side. Migrated teams' lead time dropped; the
     others' did not. That is the main reason I am confident it was the
     pipeline and not the reorganisation that happened the same quarter."

    BUSINESS - why it mattered, assumptions stated
    "At roughly an hour per ticket, that is about 50 engineer-hours a month
     back. And the checkout team used the faster path to ship pricing
     experiments weekly instead of monthly - their product manager cited it
     in their planning review."

    WHAT WENT THE WRONG WAY
    "Our developer survey score dropped for two teams during migration because
     build caching was not warm. We fixed it within three weeks; I would now
     pre-warm caches before cutover."
```

```text
Useful phrasings when the data is imperfect.

  no baseline          "We did not baseline, so this is from the ticket queue and
                        interviews rather than instrumentation - roughly X to Y."
  indirect effect      "I cannot claim the revenue outcome; I can say the team
                        shipped N times more often and they attribute part of it."
  mixed signals        "Throughput rose and stability held. Satisfaction rose for
                        most teams but not the two with the slowest builds."
  vanity metric only   "At the time we counted templates used, which I would not
                        do now. I would measure time to first production deploy."
```

## Interview tips

- Use the chain - adoption, then flow and experience, then business - and give at least one number at each level you can support.
- State provenance for every figure: source, period, sample. It pre-empts the follow-up and signals rigour.
- Address attribution unprompted. A staggered rollout comparison is the simplest convincing method; admitting you could not isolate the effect is better than overclaiming.
- Know DORA's five metrics, including rework rate and the renamed failed deployment recovery time, and know SPACE, DevEx, and DX Core 4 well enough to say why you combine system and survey data.
- Treat hours-saved conversions cautiously and state the assumption. Returned time is not money in the bank.
- Mention a metric that went the wrong way and what you did about it. It shows you were watching rather than collecting good news.
- Be ready for "how would you measure the effect of AI assistants?" - apply the same chain and warn that perceived and measured productivity diverge.
- Related reading: [How do you measure platform adoption and success?](../platform-team-and-operating-model/how-do-you-measure-platform-adoption-and-success.md) and [What is developer experience and how do you measure it?](../developer-experience/what-is-developer-experience-and-how-do-you-measure-it.md)

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
