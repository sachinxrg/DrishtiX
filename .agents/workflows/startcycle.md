---
description: Start the Autonomous AI Developer Pipeline sequence with a new idea
---

When the user types `/startcycle <idea>`, orchestrate a comprehensive, multi-agent development pipeline strictly using `.agents/agents.md` and `.agents/skills/`.

### Guiding Principles:
- **Iterative Refinement:** Code is never generated in a single pass. It must be planned, drafted, reviewed, and refactored.
- **Strict Context Boundaries:** Agents must only act within their assigned roles to prevent hallucinations and overlapping logic.
- **Fail Fast:** If any test or security audit fails, the cycle halts and loops back to the Engineering phase before proceeding.

### Execution Sequence:

#### Phase 1: Ideation & Architecture
1. Act as the **Product Manager** and execute `write_specs.md`. Generate a comprehensive Business Requirements Document (BRD) outlining user stories, edge cases, and success metrics for `<idea>`.
   *(PAUSE: Wait for user to type "Approved". If feedback is given, revise and loop until approved.)*
2. Shift context, act as the **Systems Architect**. Define the underlying data models, entity relationships, API contracts, and technology stack. Ensure the architecture supports scalability and strict data integrity.
   *(PAUSE: Wait for user to type "Approved". Do not write application code until the foundation is validated.)*

#### Phase 2: Implementation & Guardrails
3. Shift context, act as the **UI/UX Strategist**. Generate a component tree and visual styling guidelines to ensure a cohesive, high-retention user experience across all interfaces.
4. Shift context, act as the **Full-Stack Engineer**, and execute `generate_code.md`. Implement the application incrementally (e.g., core domain logic first, then API routes, then frontend). Strictly adhere to the Architect's API contracts and the UI/UX rules.

#### Phase 3: Extreme Validation
5. Shift context, act as the **QA Engineer**, and execute `audit_code.md`. Verify business logic against the PM's original BRD, check edge cases, and ensure proper error handling is in place.
6. Shift context, act as the **Security & Performance Auditor**. Scan the generated codebase for vulnerabilities (e.g., injection risks, insecure endpoints) and inefficient queries.
   *(CONDITIONAL LOOP: If QA or Security finds critical flaws, compile an error report and loop back to Step 4. Do not proceed to deployment until all checks pass.)*

#### Phase 4: Delivery
7. Shift context, act as the **DevOps Master**, and execute `deploy_app.md`. Generate production-ready artifacts (e.g., `Dockerfile`, environment variable templates, deployment manifests).
8. Shift context, act as the **Technical Writer**. Auto-generate a comprehensive `README.md`, API documentation, and local setup instructions. Output a final readiness summary to the user.