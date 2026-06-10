#### Scan and Analyze

1. Get the aggregated per-feature data deterministically: `python3 "<cf_scripts>/cf-status.py" --json` returns every feature's `feature`, `completed`, `total`, `status`, `updated`, and `source_doc` — use it to fill the progress/status/link columns instead of re-globbing and re-parsing `state.json` by hand. (`<cf_scripts>` is resolved via *Locating the script layer* in the configuration step. Fall back to scanning `{output_dir}/*/state.json` if `python3` is unavailable.)
2. Read each feature's `overview.md` and `plan.md` only for the parts the data above does not cover: descriptions and inter-feature dependencies
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
