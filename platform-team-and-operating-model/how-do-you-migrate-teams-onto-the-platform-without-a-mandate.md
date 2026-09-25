---
title: "How do you migrate teams onto the platform without a mandate?"
id: 246
category: "Platform Team and Operating Model"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# How do you migrate teams onto the platform without a mandate?

**Short answer:** Make the migration cheaper for the team than staying, and do the work yourself - raise the pull request, run the change, be present for the first deploy. Start with volunteers who have a real problem, publish what they gained, then approach teams with a specific offer rather than a general invitation. A mandate feels faster and produces compliance plus shadow tooling; earned adoption produces teams who defend the platform for you.

## Detail

**The economics from the team's side.** Migrating costs them time now for a benefit later, and it competes with product work they are accountable for. Any approach relying on them prioritising it will produce a long tail. The way to win is to make the cost close to zero: you write the change, you test it, you are there when it deploys.

**Start with volunteers who have a genuine problem.** Not the most enthusiastic team, and not the most important one - the team whose current pain your capability actually removes. A team fighting a hand-rolled pipeline is a better first customer than a team with a working one, because the improvement is self-evident and they will say so publicly.

**Make the first migration disproportionately good.** Pair with them, fix every rough edge they find immediately, and treat their friction as your highest priority. The first migration's purpose is not the migration - it is producing a reference and a list of defects. A poor first experience is expensive because it becomes the story everyone hears.

**Publish what changed, in their words and with numbers.** "Deploys went from 40 minutes to 6, and they deleted 800 lines of pipeline YAML" is persuasive; "the platform provides a standardised pipeline" is not. A short write-up from the team itself is the most effective piece of internal marketing available.

**Then approach teams with a specific offer.** Not "we would like you to adopt the platform" but "we have prepared a pull request migrating your three services; it passes your tests; can we walk through it on Thursday?" The difference in acceptance rate between a general invitation and a prepared change is large.

**Expect a dip, and plan the story for it.** DORA's 2024 research found that platform adoption tends to come with a short-term drop in throughput and change stability before the gains arrive, and that platforms which let developers work independently did better. Telling early teams and leadership about the dip in advance - and fixing friction fast enough that it stays short - is what stops one bad fortnight becoming the reason the campaign stalls.

**Automate the mechanical part.** Codemods, generated configuration, and bot-raised pull requests for the repetitive portions. Then the human effort concentrates on the genuinely unusual cases, which is where it should be.

**Remove the reasons to stay.** Track why teams decline and treat each as a requirement. If four teams cannot migrate because of one missing capability, building it unblocks four teams at once - which is a much better use of a quarter than persuading them individually.

**Let some teams not migrate, deliberately.** A team with a working bespoke setup and no pain is a poor use of your effort; a team six months from decommissioning its service should not migrate at all. Being explicit about who you are not targeting keeps your adoption numbers honest and your effort focused.

**When a mandate is legitimate.** Security and compliance controls should be enforced - image signing, audit logging, encryption. The distinction is that you mandate the property and offer the path: the control is non-negotiable, and the platform is the easiest way to satisfy it. That is a much better position than mandating the platform itself.

**Watch for the mandate arriving from above.** Leadership frequently offers to mandate adoption, and it is tempting. The cost is losing your feedback signal - complaints become escalations, and shadow tooling appears where the platform does not fit. Asking for time and evidence instead is usually the better play, and being able to argue that is a senior signal.

## Example

```text
A migration campaign for 41 services, no mandate, over five months.

  MONTH 1 - ONE VOLUNTEER WITH A REAL PROBLEM
    chose team-search: their Jenkinsfile was 600 lines, broke weekly, and one
    person understood it. NOT the most enthusiastic team - the team whose pain
    the capability actually removed.
    paired for three days. Fixed 9 rough edges they found, same week.
    result: deploy 38m -> 6m, 640 lines of pipeline deleted, no more weekly breakage.

  MONTH 2 - PUBLISH IT IN THEIR WORDS
    a 400-word write-up BY team-search, not by the platform team:
      "we deleted 640 lines of Jenkins config and our deploys stopped breaking
       on Fridays. It took three days and the platform team did most of it."
    -> five teams asked to be next, unprompted. This is the highest-return
       artefact of the whole campaign.

  MONTH 2-4 - SPECIFIC OFFERS, NOT INVITATIONS
    for each team: codemod run, PR opened, their tests passing, a 30-minute slot
    offered.
      "We have prepared PR #482 migrating your 3 services. It passes your test
       suite. Can we walk through it Thursday at 10?"
    acceptance rate on a prepared PR ............ 31 of 34 approached
    acceptance rate on the general invitation
      we tried first (month 1) .................. 2 of 12
    -> the difference is the entire lesson.

  MONTH 4 - REMOVE THE REASONS TO STAY
    declines tracked, and they clustered:
      4 teams: needed GPU scheduling we did not support  -> BUILT IT. 4 unblocked
               at once, which beat persuading them individually.
      2 teams: needed a runtime we do not offer          -> documented escape,
               recorded as an exception with a review date
      1 team:  service decommissioning in 3 months       -> DELIBERATELY NOT
               MIGRATED. Correct decision.

  MONTH 5 - HONEST FINAL NUMBERS
    migrated ................ 37 of 41
    deliberately excluded .... 1 (decommissioning)
    on a documented escape ... 2 (unsupported runtime)
    still declining .......... 1 (working setup, no pain - fine)
    voluntary adoption ...... 90%, and the teams defend the platform in planning
                             meetings because they chose it.
```

```text
Why the mandate is worse, even though it is faster:

  MANDATE
    week 1  adoption announced as compulsory
    week 6  "adoption" reports 100%
    week 10 you discover: 6 teams wrapped the platform in their own scripts to
            restore behaviour they lost; 3 kept a second pipeline "temporarily";
            2 escalated to leadership rather than telling you what was wrong.
    -> you now support the platform AND the shadow tooling, and your feedback
       channel is escalations rather than usage data.

  EARNED
    slower to a high number, and the number is real. Teams that chose it argue
    for it when leadership asks whether the platform is worth funding - which is
    worth more than any adoption percentage.

  WHEN A MANDATE IS RIGHT: mandate the PROPERTY, offer the PATH.
    "every image in production must be signed and have provenance" - mandated,
    enforced at admission, non-negotiable.
    "the platform pipeline is the easiest way to satisfy that" - offered.
    -> nobody argues with the control, and the platform wins on convenience.
```

## Interview tips

- The thesis: make migration cheaper than staying, and do the work yourself. Bot-raised pull requests that pass the team's tests are the concrete form.
- Choosing the first volunteer by whose pain your capability removes - not by enthusiasm or importance - is a specific, credible piece of judgement.
- The acceptance-rate contrast between a prepared pull request and a general invitation is the most persuasive detail available here.
- Publishing the result in the team's own words is the highest-return marketing artefact, and saying so shows you understand internal adoption.
- Tracking declines and treating clusters as requirements - building one capability unblocks four teams - is better than persuading individually.
- Deliberately excluding some teams keeps your numbers honest and your effort focused, and it signals judgement rather than completionism.
- On mandates: mandate the property, offer the path. And be ready to argue against a leadership-offered mandate, because it costs you the feedback signal and produces shadow tooling. That argument is the senior close.

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
