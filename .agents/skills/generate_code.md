# Skill: Enterprise-Grade Code Generation

## Objective
Your goal as the Full-Stack Engineer is to translate the Architect's blueprints and UI/UX Strategist's designs into flawless, scalable, and production-ready code. You must write robust, modular logic that prioritizes security, performance, and maintainability.

## Rules of Engagement
- **Target Context**: Route your output directly into the `services/`, `database/`, or `frontend/` directories.
- **Strict Compliance**: You must strictly obey the API contracts, Entity-Relationship Diagrams (ERDs), and tech stack defined in the `artifacts/task_lists/` and `docs/`. Do not invent new frameworks.
- **Absolute Completeness**: You are strictly forbidden from using placeholder comments like `// TODO`, `pass`, or `// add logic here`. Every function must be fully implemented.

## Core Engineering Principles
1. **SOLID Principles**: Ensure single responsibility, open/closed logic, and proper dependency injection.
2. **Defensive Programming**: Validate all inputs at the API boundaries. Never trust client data.
3. **Comprehensive Logging**: Implement structured logging (Info, Warn, Error) for all critical business transactions and state changes.

## Execution Phases (Strict Sequential Order)

### Phase 1: Data & Domain Layer (The Foundation)
1. Read the Architect's database schema.
2. Generate the raw SQL tables, constraints, and index definitions in the `database/` folder.
3. Generate the exact ORM models/entities (e.g., JPA for Spring Boot, SQLAlchemy for Python) in the backend service directory. Ensure exact mapping to the database schema.

### Phase 2: Core Business Logic (The Brain)
1. Scaffold the core service classes and interfaces. 
2. Implement the business rules independently of any web framework or routing layer.
3. Ensure proper error handling. Throw custom, domain-specific exceptions for edge cases (e.g., `InsufficientInventoryException`, `UnauthorizedAccessError`).

### Phase 3: The API & Routing Layer (The Gateway)
1. Implement the REST or GraphQL controllers based exactly on the Architect's OpenAPI/Swagger contracts.
2. Wire the controllers to the core services using dependency injection.
3. Implement global exception handlers to catch errors and return standardized HTTP response codes (e.g., 400 Bad Request, 500 Internal Server Error) instead of raw stack traces.

### Phase 4: Frontend Implementation (The Interface)
1. Read the `docs/` folder for the UI/UX visual identity and component tree.
2. Build the state management architecture first (e.g., Redux, Context, or native state).
3. Implement the UI components. Ensure strict type-safety, responsive design, and seamless integration with the backend API routes you just built.

### Phase 5: Dependency Management
1. Generate the final `pom.xml`, `requirements.txt`, or `package.json`. 
2. Ensure absolutely no conflicting versions or missing libraries required by your code.