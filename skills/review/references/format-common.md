# Sub-agent Response Format — Common Rules

Read together with exactly ONE role-specific format file:

| Role | Format file |
|---|---|
| Fast-path single agent (3F.4a / 3P.3a), GitHub PR mode | `format-single.md` |
| Per-module agent (3F.4b / 3P.3b) | `format-per-module.md` |
| Cross-module aggregation agent (3F.5 / 3P.4) | `format-cross-module.md` |
| Acceptance reconciliation agent (3G.3) | `format-acceptance.md` — self-contained, does NOT use this file |

**`METHOD_CHAINS` is MANDATORY and comes first — the orchestrator rejects any response without it.** See `references/call-graph-discipline.md` (full protocol including anti-rationalization guard). Produce one `METHOD_CHAINS` entry per public method / exported function / entry-point in the reviewed scope, then apply dimensions against the graph, not against surface method bodies.

**`CANDIDATE_INVENTORY` is MANDATORY and comes BETWEEN `METHOD_CHAINS` and the dimension blocks.** It is a **drop ledger** — see §Pre-emission Scratchpad below.

**`evidence` field is MANDATORY for every `critical` and `blocker` finding.** See `references/suppression-gates.md`. The orchestrator rejects critical/blocker findings missing `evidence` and (after one re-invoke) auto-downgrades them with a `[Auto-downgraded: missing evidence]` marker. `evidence` SHOULD be present for `warning` findings when non-obvious; OPTIONAL for `suggestion`. The field must show: (a) the concrete input/condition that triggers the failure, (b) the observable wrong behavior, and (c) for D2 / D1-defensive-gap findings, the trust-boundary argument per Gate 2.

**`evidence` is ALSO MANDATORY at any severity (including `warning` and `suggestion`) when the finding makes a falsifiable factual claim about the codebase** — Gate 5 in `references/suppression-gates.md`. Trigger phrases: `zero references`, `zero reads`, `never called`, `never read`, `dead code`, `unreachable`, `unused`, `only used in`, `only referenced in`, `sole consumer`, `duplicates X`, `copy of`, `redeclares`, `parallel implementation`, `reimplements`, `grep (returns|shows|finds)`, `N lines exceed`, `exceeds N lines`. When any of these appear in `title` / `description`, `evidence` MUST include:

- **Option A — command + output:** The full `grep` / `rg` / search command that was actually run, AND one or more lines of its matched output (in `path:line:content` format), OR the explicit string `0 matches` / `no matches` when claiming absence. A single-sentence summary (*"grep returns only the declaration"*) is NOT sufficient — the raw output itself must be visible.
- **Option B — file:line citations:** Explicit `path/to/file.ext:LINE` references covering every site the claim depends on. A "duplicates Y" claim must cite both the original and the duplicate. An "only used in foo.ts" claim must cite foo.ts AND carry a grep proving no other uses. A "dead code" claim requires cross-directory coverage (src + tests at minimum).

Example (warning-level factual claim) — **acceptable**:
```yaml
evidence: |
  grep -rn "ERROR_CODE_MAP" src/ tests/
  src/main.ts:111:const ERROR_CODE_MAP: Record<string, number> = {
  src/main.ts:1129:    const exitCode = errorCode && errorCode in ERROR_CODE_MAP
  src/main.ts:1130:      ? ERROR_CODE_MAP[errorCode]
  → 2 read sites in same file as declaration; overlaps with errors.ts:135 codeMap
    (which has these entries too: MODULE_NOT_FOUND, SCHEMA_VALIDATION_ERROR, APPROVAL_DENIED).
  Proposed: consolidate readers to codeMap, delete main.ts:111-134.
```

Example (warning-level factual claim) — **rejected by Gate 5**:
```yaml
evidence: "grep returns only the declaration; zero reads."
```
The second example is rejected because the grep *output* is not visible — only a paraphrase. The sub-agent may have mis-read the output or greppped too narrow a scope; without the actual matched lines in evidence, the orchestrator cannot distinguish a true zero-reference claim from a false one.

---

## Pre-emission Scratchpad (`CANDIDATE_INVENTORY`)

`CANDIDATE_INVENTORY` records every candidate finding you considered and decided **NOT** to emit, each with a fixed-enum `drop_reason`. **Findings you keep are NOT listed here** — they appear in full in the dimension blocks, and repeating them in the ledger is pure duplication.

This enforces the Anthropic pre-emission-CoT pattern: the drop judgment is made *with justification, before* the dimension blocks are written — not as a post-hoc filter over everything you already emitted.

**Rules:**
1. Every candidate you DROP gets a row. Every candidate you KEEP gets NO row — it goes straight to its dimension block.
2. `drop_reason` MUST be one of the fixed enum codes below. Free-text reasons are rejected by the orchestrator (see SKILL.md Step 4F/4P scratchpad audit).
3. No dimension block may contain an issue matching a ledger row (same `file:line` + `title`). Listing a candidate as dropped and then emitting it anyway is a bypass attempt — the finding is rejected outright.
4. An empty ledger is valid: it asserts *"every candidate I considered survived the gates"*. The section header must still be present — a missing header is a protocol violation, not an empty result.

**Keep — do NOT ledger these, emit them in the dimension blocks:**

| Situation | Where it goes |
|---|---|
| Concrete input triggers observable wrong behavior | D1 / D3 / D6 / D8 |
| Sibling modules with symmetric contracts diverge observably — module A has the guard/audit/approval, module B does not (requires the contract-symmetry pre-flight) | D5 / cross-module consistency |
| "Zero references" / "dead code" / "duplicates X" backed by the actual `grep`/`rg` command **and** its output in `evidence` | D12 / D15 |
| ≥3 sites of real duplication verified with grep output, extraction target named | D15 |
| A path with a nameable failure mode has no test coverage | D7 |
| An acceptance criterion from `plan.md` is not met in the code | consistency section |

**DROP reason codes (enum):**

| Code | Canonical trigger |
|---|---|
| `extract_helper_under_3_sites` | Duplicate appears in only 2 sites. |
| `refactor_preference_no_bug` | Fix introduces a new abstraction replacing a working pattern; no observed bug. |
| `documented_known_gap` | Description self-identifies as already-tracked (CLAUDE.md, TODO, next release). |
| `self_admitted_low_value` | "impact is small", "only worth if X surfaces", "edge case", "theoretical concern". |
| `pure_symmetry_no_bug` | "Inconsistent with sibling" with no named caller consequence. |
| `rename_for_clarity_no_ambiguity` | Rename without concrete past-confusion incident or mis-describing name. |
| `speculative_phrasing` | Description contains "could theoretically", "if X ever", "in case someone", "potentially might". |
| `trust_boundary_internal` | D1/D2 finding on developer-authored / type-checked / internal input source. |
| `unverified_factual_claim` | Gate 5 trigger phrase ("zero references", "dead code", "only used in") without grep output or file:line evidence. |
| `defensive_hardening_speculative` | Runtime check against an input source that is developer-controlled. |
| `typo_hypothetical` | "A typo WOULD no-op" — the typo doesn't exist in the code. |
| `packaging_naming_out_of_scope` | Binary-name collision / npm-scope / bin-script rename when review scope doesn't include packaging. |
| `style_swap_no_downside` | "Prefer X over Y" / "consider using X instead" without a named downside of Y. |
| `formatting_casing_linter_territory` | Whitespace, camelCase vs snake_case, `WARNING:` vs `Warning:` — linter concern, not review. |

See `references/suppression-gates.md` §Drop Gallery for the worked example behind each code.

**Ledger schema:**

```
CANDIDATE_INVENTORY:
- id: C1
  dimension: <D1 | D2 | ... | D15>
  file: path/to/file.ext
  line: <number or range>
  title: <short title of the candidate you dropped>
  drop_reason: <one of the enum codes above — NO free text>
  drop_detail: <one line — why THIS code applies to THIS candidate, e.g.
               "2 sites (main.ts:937 and :982), below 3-site threshold">
```

**Example ledger:**

```
CANDIDATE_INVENTORY:
- id: C1
  dimension: D4
  file: src/main.ts
  line: 937
  title: "reserved-set redeclared at two sites"
  drop_reason: extract_helper_under_3_sites
  drop_detail: "appears at main.ts:937 and main.ts:982 — 2 sites, below 3-site threshold"
- id: C2
  dimension: D4
  file: src/cli.ts
  line: 17
  title: "Local Registry placeholders diverge from upstream apcore-js"
  drop_reason: documented_known_gap
  drop_detail: "description itself references CLAUDE.md tracking and next apcore-js compatibility bump"
- id: C3
  dimension: D4
  file: src/output.ts
  line: 39
  title: "truncate slices on UTF-16 code units"
  drop_reason: self_admitted_low_value
  drop_detail: "suggestion text includes 'behavioral impact is small; only worth doing if broken-glyph reports surface'"
- id: C4
  dimension: D4
  file: src/main.ts
  line: 403
  title: "_exposureFilter attached via as unknown as Record cast"
  drop_reason: refactor_preference_no_bug
  drop_detail: "fix introduces ProgramMeta interface; no observed typo or runtime bug — 'a typo WOULD no-op' is hypothetical"
```

None of C1–C4 appear in any dimension block. Findings that survived — e.g. an `apcli exec bypasses checkApproval` D1 issue or an `emitResult re-implemented in 5 registrars` D15 issue — are written directly into their dimension blocks and never touch this ledger.
