---
description: Trigger a non-destructive, surgical development loop to add new features or fix bugs. Orchestrates regression testing, security audits, and updates the Master Blueprint without overwriting code.
---

# Workflow: Continuous Iteration & Feature Deployment

## Trigger
When the user types `/iteratecycle <feature_request_or_bug>`, orchestrate a non-destructive, surgical development loop using `.agents/agents.md` and `.agents/skills/`.

## Guiding Principles:
- **Zero Regression:** Existing functionality must not break. 
- **Surgical Precision:** Agents must only modify files explicitly related to the new feature or bug. Total application rewrites are strictly forbidden.
- **State Synchronization:** The `Master_Blueprint.md` must be updated to reflect the new reality of the codebase.

## Execution Sequence:

### Phase 1: Impact Analysis & Strategy
1. Act as the **Product Manager**. Read the existing `artifacts/task_lists/Master_Blueprint.md` and the user's `<feature_request_or_bug>`. Write a concise `Feature_Update_Spec.md` detailing the new user stories and acceptance criteria.
2. Shift context, act as the **Systems Architect**. Analyze the existing `database/` schemas (e.g., SQL tables) and `services/` architecture (e.g., Spring Boot or Python controllers). Define exactly which tables, APIs, or components need modification, and which new ones must be created.
   *(PAUSE: Wait for user to type "Approved". Do not allow code modification until the update strategy is validated.)*

### Phase 2: Surgical Implementation
3. Shift context, act as the **Full-Stack Engineer**, and execute `generate_code.md` with a strict override: **DO NOT scaffold a new app**. Only implement the specific changes outlined by the Architect. 
    * If modifying a database, write an incremental SQL migration script (do not drop existing tables).
    * If updating an API, maintain backward compatibility or bump the endpoint version (e.g., `/api/v2/`).

### Phase 3: Regression & Security Auditing
4. Shift context, act as the **QA Engineer**, and execute `audit_code.md`. Focus heavily on **Regression Testing**. Ensure the new logic connects perfectly with the existing state management and does not break previously working routes.
5. Shift context, act as the **Security Auditor**. Scan the modified files for vulnerabilities (e.g., ensuring new database queries are parameterized to prevent SQL injection).
   *(CONDITIONAL LOOP: If QA or Security finds a break, generate a diff report and loop back to Step 3. Do not proceed until regression tests pass.)*

### Phase 4: Blueprint Sync & Deployment
6. Shift context, act as the **Technical Writer**. Read the successfully implemented code and update the `Master_Blueprint.md`, API documentation, and `README.md` so the documentation perfectly matches the new codebase.
7. Shift context, act as the **DevOps Master**, and execute `deploy_app.md` or `deploy_cloud_run.md` depending on the environment. If deploying to production, utilize traffic splitting (e.g., route 10% of traffic to the new container revision) to monitor for silent failures before a full rollout.