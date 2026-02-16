#### Scan and Analyze

1. Scan `{output_dir}/*/state.json` for all existing features
2. Read each feature's `overview.md` and `plan.md` for descriptions and dependencies
3. Determine implementation order based on actual dependencies (not alphabetical)

#### Generate Overview

Create or overwrite `{output_dir}/overview.md` with these required sections:

- **Overall Progress** — progress bar + module counts (completed/in_progress/pending)
- **Module Overview** — table: #, Module (linked to directory), Description, Status, Progress
- **Module Dependencies** — mermaid dependency graph
- **Recommended Implementation Order** — phased with rationale ("Why first", "Why next")

**Key principles:**
- Implementation order must reflect actual dependencies
- Status aggregated from `state.json` files (not manually maintained)
- Use relative links to feature directories
