# Presentation and demo video: working notes

For the team. Everything here is safe to show publicly: no real person's chats, names or numbers. The example task
below is made up in the same style as the real ones; never put a real phone's data on a slide or in the video.

Deadlines (Pacific): start submitting **3:30 PM**, video uploaded by **4:00 PM**, submissions close **4:30 PM**.
Video: **under 2 minutes** (aim for 60-90 s). Saving the form as a draft does not submit it.

## Judging weights, and what each slide must prove

| Criterion | Weight | Our evidence |
|---|---|---|
| Benchmark evaluation | 40% | 50 held-out tasks on 3 phones never used in training; every model, same agent, same judge; 95% intervals |
| Business value | 25% | Hundreds of millions of people mix languages on their phones; a 3B-active model is cheap enough to serve them |
| Technical execution | 20% | Teacher to student LoRA on Fireworks Training API, on-demand deployment, judge from a different model family |
| Presentation | 10% | One concrete task, one table, one honest takeaway |
| Documentation | 5% | README in this repo |

## The story in one sentence

A small open model (Nemotron 3.5 Lightning, 3B active) can be taught, on Fireworks, to act as a phone assistant for
people who write in mixed Indian languages; we built a rigorous held-out benchmark to measure it against a frontier
model, and show what fine-tuning changes and what it does not yet.

## Slides / video beats

1. **Problem (10 s).** "Ghar ka bijli bill bhar do, mera usual account se, aur bhaiya ko bata do done hai." People ask
   their phones for errands in mixed languages and Roman script. The assistant has to read chats and email to find
   the facts, act in apps (payments, shopping, travel, pharmacy, doctors), and message the right person. Frontier
   models manage much of this; small, cheap models mostly do not.
2. **The benchmark (20 s).** 11 simulated Indian phones (contacts, chats, email, calendar, 8+ apps) built on Meta's
   ARE. 184 tasks in the owners' own words, each with the exact actions a correct assistant takes. Split by phone:
   50 test tasks on 3 phones (Tamil, Assamese, Gujarati owners) that training never sees.
   Visual: one task card (request, then the 3-4 actions: look up bill, pay from default account, message brother).
3. **The setup (15 s).** Frontier: Kimi K3. Student: Nemotron 3.5 Lightning. Judge: Qwen3.8-Max, a different model
   family from both, plus exact checks on IDs, amounts, dates and recipients. All served on Fireworks.
4. **Training (15 s).** Teacher (Nemotron 3 Ultra, open licence) solved 55 of 134 training tasks; its full agent
   conversations are the training data. LoRA SFT with the Fireworks Training API (dataset stays local, dedicated
   trainer), deployed on one B200 with live merge.
5. **Results (20 s).** The table below. Lead with the strongest true claim, then the honest gap.
6. **Takeaway and next step (10 s).** See "Messages" below.

## Results (Qwen3.8-Max judge, 50 held-out tasks, 1 try each)

| Model (all on Fireworks) | Passed | 95% CI | $/run | $/solved |
|---|---|---|---|---|
| Kimi K3 (frontier) | 30/50 (60%) | 46-72% | 0.85 | 1.42 |
| Lightning, untrained | 2/50 (4%) | 1-14% | 0.02 | 0.60 |
| Lightning, LoRA v1 (25 hardest training tasks) | 7/50 (14%) | 7-26% | 0.03 | 0.21 |
| Lightning, LoRA v2 (all 55 training tasks) | 9/50 (18%) | 10-31% | 0.07 | 0.40 |

Judge: Qwen3.8-Max with the two disclosed prompt edits (JUDGE_CHANGES.md), the same for every row.

- Tuned-model cost = deployment time x $13/h (B200): v1's 50 runs took 7 minutes ($1.46), v2's 17 ($3.60). A fuller
  deployment costs less per run.
- Kimi and untrained Lightning are serverless per-token estimates from conversation length.
- Training loss: v1 0.36 to 0.10 over 12 steps; v2 0.36 to 0.14 over 21 steps.

Behaviour change worth a slide: **format errors** (replies the agent cannot execute because they lack a valid
`Action:`) fell from 8-27 per run untrained to about 3 per run after v1. The tuned model stops tripping over the agent
format and actually attempts the task; its remaining failures are wrong decisions (22 wrong or missing actions, 21
right tool with wrong arguments, in v1).

## Message (v2 is in: 4% untrained to 18% tuned, intervals do not overlap)

"With 55 examples and one LoRA run on Fireworks, a 3B-active model went from 4% to 18% on phones it had never seen,
about 4.5x, at about 12x lower cost per task than the frontier model. Data is the lever: 25 to 55 examples took it from
14% to 18%. Next: a second teacher (Kimi K3, 60%) for more training data, then a learning-rate and epoch sweep on
held-out validation phones."

## Message options considered earlier

- **If v2 clearly beats untrained** (non-overlapping intervals, or a big jump): "With 55 examples and one LoRA run on
  Fireworks, a 3B-active model went from X% to Y% on phones it had never seen, at 1/20th the cost per run of the
  frontier model."
- **If v2 is modest:** "Fine-tuning fixed how the model acts (format errors down 3-10x) but not yet what it decides.
  The pipeline is built and measured end to end; the bottleneck is teacher data: 55 examples. Next: use Kimi K3
  (60%) as a second teacher to multiply the training set."
- Always: cost per run 20x lower than the frontier model; held-out by phone; judge independent of every contestant.

## Charts to make

1. Bar chart: pass rate per model with 95% interval whiskers (Kimi, untrained, v1, v2).
2. Two bars: format errors per run, untrained vs tuned.
3. Scatter: cost per run (log x) vs pass rate, one dot per model. The "tradeoff vs baseline" the brief asks for.

## Say this honestly (judges will ask)

- Prepared before the event and disclosed in the README: phones, tasks (drafted by Claude Opus, checked automatically
  against each phone, not reviewed by the owners), the pilot runs and teacher runs. Built today: the Fireworks
  training, deployment, judge switch and all results in the table.
- The teacher (Nemotron 3 Ultra) is open-licensed; no closed model's outputs were used for training.
- Test phones never appear in training. The 25 hardest training tasks (v1) were chosen from task definitions only,
  never from model results.
- 50 tasks is small: intervals are wide (about +/-14 points at 50%).
- The tuned model runs on a dedicated FP4 deployment; the untrained base runs serverless. Same model family and
  weights, different serving.

## Submission checklist

- [ ] Final numbers in this file and in README.md (v2 row, untrained final)
- [ ] Charts exported (PNG) and in the slides/video
- [ ] Video under 2 minutes, uploaded in the form by 4:00 PM
- [ ] Form: project name, description, repo link (https://github.com/thebhupen/fireworks-deploy-cm), technologies
      (Fireworks Training API, Fireworks serverless and on-demand deployments, NVIDIA Nemotron 3.5 Lightning,
      Nemotron 3 Ultra, Kimi K3, Qwen3.8-Max, Meta ARE), team roster
- [ ] Repo is public and the README runs from a fresh clone
- [ ] Submitted (not draft), and shows as submitted
- [ ] Delete the Fireworks deployments (rlu-v1, rlu-v2) after the demo; they bill per hour
