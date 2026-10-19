# Release and Deployment Policy

| Environment | Deployment condition | Who deploys |
|---|---|---|
| staging | Tests and lint pass + **code approval (②) recorded** | The deployment agent can do it directly |
| production | Staging smoke test passes + **production deploy approval (③)** | **Only after explicit approval by the owner (a human)** |

1. For every change, leave the stage outputs in `docs/cr/<CR-ID>/` (impact analysis → design → implementation notes → tests → review → release plan → operations report).
2. Three human approvals: ① **Design approval**, ② **Code approval**, ③ **Production deploy approval**. Approval records are kept in `approvals/<CR-ID>/`.
3. If an output changes after approval, the approval becomes **invalid** and must be obtained again.
4. Every deployment must have a rollback method prepared, and a smoke test is run right after deployment.
5. Agents cannot modify the approval records folder, the agent definitions, the hooks (guardrails) or the standards documents.
