# Interventions and Follow-up

An intervention is a support action an advisor takes for a student. Recording one starts a follow-up, which compares the student's indicators on the intervention date with their indicators on the follow-up date, six weeks later.

The system shows the comparison as evidence. It does not decide whether the intervention worked. The advisor records the outcome.

## Intervention types

| Value | Meaning |
|---|---|
| `meeting` | The advisor met the student |
| `study_plan` | A study plan was agreed |
| `tutoring_referral` | Referred to academic tutoring |
| `wellbeing_referral` | Referred to wellbeing support |
| `other` | Anything else. Describe it in the notes |

## Outcomes

| Value | Set by | Meaning |
|---|---|---|
| `not_yet_reviewed` | System, on creation | No outcome recorded yet |
| `improving` | Advisor | The advisor judges the student to be improving |
| `no_change` | Advisor | The advisor judges there has been no change |
| `referred_elsewhere` | Advisor | Support has moved to another service |

An advisor can record an outcome more than once, for example after a later review. The latest value and the time it was recorded are kept.

## Follow-up

- The follow-up date is the intervention date plus 42 days. It is stored when the intervention is created, so later changes to the setting don't move existing due dates.
- The "before" indicators are calculated as of the intervention date.
- The "after" indicators are calculated as of the follow-up date.
- `is_due` is `false` until the follow-up date has arrived. Until then, the "after" values cover only part of the window and should not be read as a result.

## Rules

- An intervention can link to a flag only if the flag belongs to the same student.
- Interventions are never deleted through the API.
- Only advisors can record interventions and outcomes. Advisors and administrators can read them.

## Limitations

- The intervention date is not checked against today's date, so future dates can be entered. A later step should reject them.
- The follow-up is a before-and-after comparison, not a controlled evaluation. Other events in the six weeks can change the indicators.
- Notes are free text. Record only what the advisor needs.