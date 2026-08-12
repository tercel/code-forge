# Finding Suppression Gate (Sub-Agent Pre-Emission Check)

**Before the sub-agent writes ANY finding into the output YAML, it MUST pass that finding through the five gates below.** A finding that fails a gate is either DROPPED or DOWNGRADED per the gate's instructions. This discipline is required because the dimensional framework (`dimensions-intra.md` / `dimensions-cross.md`) pushes the agent toward exhaustive per-dimension checking — without counter-pressure, that bias produces speculative noise: "if metadata ever holds non-primitives", "could theoretically RecursionError on self-referential dicts", "attacker-controlled `module_id` in a dev tool reading the user's own local files". Such findings waste reviewer attention, inflate counts, and erode trust in the report.

The gates are applied **after** call-graph analysis and dimension classification, **before** the issue is serialized into the YAML output. Every finding in the final report is an output of this gate.

---

## Severity Levels (strict, enforced by Gate 3)

| Severity     | Symbol | Meaning                                                                                                                                                                                                                              | Merge Policy              |
|--------------|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| `blocker`    | :no_entry: | Production data loss, security breach with a real attacker model, or crash on normal-use inputs. Reproducible on day one. **Requires `evidence` field.**                                                                             | **Must fix before merge** |
| `critical`   | :warning: | Demonstrable correctness bug with a concrete reachable trigger in the project's actual use case, producing observable wrong behavior. **NOT:** design preferences, pattern inconsistencies, speculative edge cases. **Requires `evidence` field.** | **Must fix before merge** |
| `warning`    | :large_orange_diamond: | Fix recommended **with a concrete, named downside** — cross-module inconsistency that produces divergent caller behavior, missing guard on a GENUINELY external input (Gate 2), missing test on a path with an observable failure mode, silent divergence from a convention the project enforces for a behavioral reason. **NOT** pure pattern or stylistic divergence. If you cannot name the observable downside in one line, the finding is noise — drop. `evidence` SHOULD be provided; when omitted, the description itself must name the downside. **Additional rule — factual claims (Gate 5):** if the description asserts a falsifiable property of the codebase ("zero references", "never called", "dead code", "only used in X", "duplicates Y", "N lines exceed limit"), the finding MUST carry a verification artifact in `evidence` (the actual grep/search command AND a representative slice of its output, OR explicit file:line citations proving the claim). Unverified factual claims are dropped by Gate 5 — not downgraded. | Should fix                |
| `suggestion` | :blue_book: | Concrete improvement with an observable benefit — dead code deletion, comment clarifying a non-obvious invariant, extraction of a duplicated block that has drifted. **NOT** "defensive improvements for unlikely scenarios", **NOT** speculative "might be clearer / nicer / simpler" preferences, **NOT** pure renames for clarity, **NOT** "consider using X instead of Y" style swaps, **NOT** extract-helper proposals against <3 lines of near-duplication, **NOT** formatting / casing consistency (linter territory). If the benefit cannot be named concretely AND the current code is functional, drop. Also subject to the **suggestion budget** and **same-theme consolidation** rules enforced at orchestrator validation time (SKILL.md Step 4F validation #6-7). `evidence` optional; when the suggestion makes a factual claim (Gate 5), verification is still required. | Nice-to-have              |

**Speculative-phrasing drop rule.** If a finding's description relies on speculative phrasing ("could theoretically", "if X ever happens", "in case someone", "potentially might", "might be nicer", "smells wrong", "feels off"), **DROP the finding at ANY severity**. Previously this was "downgrade one level", but downgrading merely relocated noise into `warning`/`suggestion` where no further gate ran; the only action that actually cleans the report is to drop. The rescue path is to rewrite the description with a concrete, reachable trigger and re-submit. Full protocol in Gate 3 below.

---

## Gate 1 — Reachability

**Question:** Under the project's actual use case — the one the README / project type / threat model describes — is the failure mode reachable by a concrete input the user could hit?

**Drop the finding if any of these is true:**
- The trigger requires inputs that the project's use case excludes (e.g., "self-referential dict causes RecursionError" in a YAML config written by humans — humans don't author self-referential YAML).
- The trigger requires bugs in upstream code that the type system or upstream invariant already prevents.
- The description starts with or leans on: **"if X ever happens"**, **"could theoretically"**, **"in case someone passes"**, **"potentially might"**, **"non-deterministic in unspecified scenario"**. These phrases are speculative tells — the finding has no concrete reproduction path.
- The "failure" requires the developer to author malicious input against their own tool (e.g., "a malicious scanner could emit `\"\"\"` in the module_id" — the developer writing their own scanner is not a threat actor).

**Keep the finding** only when there is a concrete, demonstrable input reachable in the project's actual use case. Record the trigger in the issue's `evidence` field.

## Gate 2 — Trust Boundary (applies to D1 defensive-gap and all D2 security findings)

**Question:** Does the input source actually cross a trust boundary the project's threat model recognizes?

**External sources (real trust boundary) — D1/D2 findings here are valid:**
- Network requests / HTTP / WebSocket / RPC payloads from untrusted peers
- Untrusted user input (form fields, query params, uploaded files)
- Third-party API responses
- Cross-tenant / cross-user data in a multi-tenant system
- Public package / plugin registries consumed by published software
- Files uploaded or fetched from outside the project's own repo

**Internal sources (NO trust boundary) — D1/D2 findings here are noise; DROP unless the project declares a stricter threat model in its README / SECURITY.md:**
- The project's own source files being scanned by the project's own tooling (dev tools, code generators, linters, build scripts)
- Hard-coded constants committed to the repo
- Config files committed to the repo that the developer themselves authored
- Function arguments inside a single trusted process with type-checked signatures
- Data produced by the project's own build pipeline upstream of the point in question

**Canonical anti-pattern to drop:** *"`module_id` could contain `\"\"\"` and inject code into the generated docstring if a malicious scanner / malicious YAML / malicious developer produces it."* The developer running their own dev tool against their own code is not in the threat model. Drop.

**Keep the finding** when the input genuinely crosses a recognized trust boundary, OR the project is itself security-sensitive (auth, crypto, payment processing, multi-tenant SaaS, anything handling secrets of parties other than the developer). **When in doubt for a clearly internal developer tool, drop.**

## Gate 3 — Severity Calibration

Re-check the severity you assigned after writing the description. Each level has a STRICT meaning — see the §Severity Levels table above.

**Downgrade rules — apply these mechanically:**

1. If the description contains any of the speculative phrases from Gate 1, **DROP the finding entirely — do not downgrade-and-keep**. Speculative phrasing is a Gate 1 failure at ANY severity (critical, warning, OR suggestion). Downgrading preserves the noise in the report; dropping is the correct action. The only rescue path: rewrite the description citing a concrete, reachable trigger. If you cannot, drop.
2. If the finding describes a **design choice** (fail-fast vs collect-errors, sync vs async, strict vs permissive) without pointing to a concrete observable failure in the chosen design, **max severity is `warning`**. "Inconsistent with sibling writer" is a warning-level consistency note, not a critical.
3. If the finding is "code doesn't validate an input", check Gate 2 first. If the input source is internal/trusted and type-checked, **drop**. If external, **critical** is warranted only when a malformed input produces a concrete wrong behavior (not just "raises an unexpected exception type").
4. If the finding's fix is "add a guard / add a log / add a doc comment / rename for clarity" with no observable bug behind it, **max severity is `suggestion`**.

## Gate 4 — Quota Avoidance

**The dimension list does NOT impose a finding quota. Empty dimensions are a VALID and CORRECT result.**

If you finish analyzing D8 / D11 / D13 / etc. and have zero real findings, write `issues: []` for that dimension and move on. **DO NOT produce a marginal finding to "show you reviewed the dimension"** — the orchestrator never penalizes empty dimensions; it rejects fabricated ones.

Symptoms that you are quota-filling (stop and drop the finding):
- You are writing a finding whose severity you had to argue yourself into.
- The finding's `why it matters` requires a three-step hypothetical chain ("if A and then B and then C").
- You reached for the finding because the dimension felt under-utilized, not because you found a problem.

The one exception is **D15 (Simplification & Anti-Bloat)** where empty findings are still valid but the agent must *demonstrate* it grep'd for duplicates and read import graphs — see D15's execution requirements in `dimensions-cross.md`.

## Gate 5 — Factual Verifiability (applies to ANY finding that asserts a codebase property)

**Question:** Does this finding's description or evidence make a falsifiable claim about the codebase — and if so, does `evidence` include the verification artifact that would prove the claim?

This gate exists because the dimensional framework rewards specific-sounding assertions ("zero references", "duplicated in three places", "dead code") — but nothing in the Gate 1–4 pipeline *verifies* those assertions are true. A sub-agent writing *"grep returns only the declaration; zero reads"* can ship the finding green when the symbol is actually read three times elsewhere. This is the most common pattern of factually-wrong warnings and the prior gates cannot catch it.

**Trigger phrases — the finding MUST carry a verification artifact when the description OR evidence contains any of these:**
- `"zero references"`, `"zero reads"`, `"never called"`, `"never read"`, `"never invoked"`, `"no callers"`
- `"dead code"`, `"unreachable"`, `"no-op in practice"`, `"unused"`
- `"only used in"`, `"only referenced in"`, `"only read at"`, `"sole consumer"`
- `"duplicates X"`, `"copy of X"`, `"redeclares"`, `"parallel implementation"`, `"reimplements"`
- `"N lines"` where N is a specific count, `"exceeds (50|N) lines"`, `"LOC"` with a specific number
- `"grep returns"`, `"grep shows"`, `"search finds"` — any claim about search results

**Required verification artifact — `evidence` must include at least ONE of:**
1. The **actual search command** executed (e.g., `grep -rn "ERROR_CODE_MAP" src/`) **AND** a representative slice of its output (matched lines with file:line, OR `"0 matches"` if claiming absence). Single-line summaries like *"grep returns only the declaration"* without the actual matched-line output are insufficient — the verification artifact must be the output itself, not a paraphrase.
2. **Explicit file:line citations** listing every site the claim covers (e.g., for a "duplicates X" claim, cite both the original and the duplicate; for "only used in foo.ts", cite the original definition AND every use site).
3. For `"N lines"` / LOC claims: the file:line range being measured and how the count was derived (e.g., `"main.ts:801-1154 = 354 lines"` — a range that can be checked).

**Drop the finding if:**
- The trigger phrase appears but `evidence` has no command+output and no file:line citations supporting the claim. The sub-agent is asserting without showing.
- The trigger phrase is "only used in X" / "only referenced in X" but evidence cites only the definition site — the claim is about absence of OTHER uses; evidence must demonstrate the negative (the grep output showing no other matches).
- The trigger phrase is "duplicates X" but evidence shows only one of the two locations.
- The trigger phrase is "dead code" but the verification scope is a single file — dead-code claims require cross-project grep because a symbol can be re-exported, dynamically resolved (Python `getattr`, TS barrel imports), or called from tests.

**Keep the finding** only when the evidence carries either (1) the command + its representative output, or (2) file:line citations that are themselves directly checkable by the human reviewer in a few seconds.

**Canonical failure this gate catches.** A sub-agent claims `"ERROR_CODE_MAP has zero reads; delete it"` based on reading one file. The map is actually read at `main.ts:1129-1130` in the same file it was declared in — a miss the sub-agent would have caught had it been required to paste the grep output (which would have shown `"main.ts:111:const ERROR_CODE_MAP"` AND `"main.ts:1129: errorCode in ERROR_CODE_MAP"` together). The rule: paste the search output, don't summarize it.

---

## Output requirement — `evidence` field

Every finding at **`blocker` or `critical` severity MUST include a non-empty `evidence` field** (one to three lines) explaining how the failure is reachable in actual use — the concrete trigger input, the observable wrong behavior, and, where relevant, the trust-boundary argument that Gate 2 checked.

- **`warning`** findings SHOULD include `evidence` when non-obvious.
- **`suggestion`** findings MAY include `evidence` but it is not required.
- **ANY severity that makes a Gate 5 trigger claim** MUST include the verification artifact.

The orchestrator rejects any `critical` or `blocker` finding missing the `evidence` field and returns it to the sub-agent with the instruction: *"Either supply concrete reachability evidence or downgrade / drop the finding per §Finding Suppression Gate."*

---

## Drop Gallery — Concrete Negative Examples (MANDATORY comparison before emission)

**Before emitting ANY finding, compare its shape against the examples below. If your candidate "looks like" one of these — regardless of how you word it — DROP it.**

This gallery codifies the Anthropic multi-shot-with-negative-examples pattern. Abstract prohibitions ("don't emit speculative findings", "avoid preferences") show diminishing returns as more are added; concrete labeled negatives outperform any count of bullet rules. The gates above define the principles; this gallery shows the actual failure patterns that sub-agents produce in practice when they try to fill dimensional quotas.

Each DROP example carries a **`drop_reason` code** — use the code verbatim in `CANDIDATE_INVENTORY[].drop_reason` (see `format-common.md` §Pre-emission Scratchpad). Free-text drop reasons are rejected by the orchestrator; only these codes are accepted. The ✅ KEEP examples below carry no code: kept findings are never ledgered, they go straight into their dimension blocks.

---

### ❌ DROP — `extract_helper_under_3_sites`

```
title: "reserved-set redeclared at two sites"
description: "The literal set {'input','yes','largeInput',...} appears at
  main.ts:937 and main.ts:982. Adding a new built-in option requires updating both."
suggestion: "Extract BUILTIN_OPTION_KEYS as a module-scope constant."
```

**Why drop.** 2 sites. Single-duplicate extraction almost always adds indirection without a maintenance benefit — the threshold is **≥3 sites** before the cost of the new symbol pays for itself. Do not try to word around this with "redeclared" / "drift risk" / "consolidate" / "DRY" — the orchestrator's nitpick blocklist strips these, and the scratchpad audit will flag the bypass.

---

### ❌ DROP — `documented_known_gap`

```
title: "Local Registry / ModuleDescriptor placeholders diverge from upstream apcore-js"
description: "Method names (listModules / getModule) diverge from upstream
  (list / getDefinition) — documented known-gap in CLAUDE.md."
suggestion: "Track for the next apcore-js compatibility bump."
```

**Why drop.** The description *itself* says the divergence is already tracked. A review report is the action list for the current change, not a redundant copy of CLAUDE.md's known-issues section. Trigger phrases that force this drop: `documented known-gap`, `tracked for`, `next release`, `known issue`, `see CLAUDE.md`, `already noted`.

---

### ❌ DROP — `self_admitted_low_value`

```
title: "truncate slices on UTF-16 code units; emoji splits at boundary"
description: "Default limits (80 / 1000) make this reachable when descriptions
  contain emoji near the cutoff."
suggestion: "Use [...text].slice() for code-point-safe slicing
  (behavioral impact is small; only worth doing if broken-glyph reports surface)."
```

**Why drop.** The finding self-downgrades: *"impact is small"*, *"only worth if X surfaces"*, *"edge case"*, *"theoretical concern"*. If you have to caveat the fix's value inside the suggestion itself, the finding has no reader value. Gate 1 should have caught this by the speculative-phrase scan; the gallery is the belt-and-suspenders.

---

### ❌ DROP — `refactor_preference_no_bug`

```
title: "_isShim / _exposureFilter attached via `as unknown as` casts"
description: "Five sites assign dynamic program metadata with cast-bypass.
  A typo (_exposurefilter vs _exposureFilter) would silently no-op at runtime."
suggestion: "Introduce ProgramMeta interface + typed attachMeta() helper; replace all 5 sites."
```

**Why drop.** Fix is to introduce a NEW abstraction replacing a working pattern. The asserted bug ("a typo WOULD no-op") is hypothetical — no typo exists in the code, and the tests would catch it if one were introduced. Architecture preferences do not become findings just because the number of sites is ≥3. Keep only when the pattern has actually produced an observed bug — cite the commit / the failing test.

---

### ❌ DROP — `pure_symmetry_no_bug`

```
title: "logger.setLogLevel silently ignores unknown level strings"
description: "setLogLevel('VERBOSE') is a no-op — inconsistent with resolveIntOption
  and ApcliGroup._parseEnv which warn on unknown values."
suggestion: "Emit a warning on unknown level."
```

**Why drop.** The only argument is "module A does X, module B does Y". No concrete caller is broken, no test fails, no user workflow is hurt. Pure pattern divergence is not a finding. Contract-symmetry pre-flight (§CROSS_MODULE_CONSISTENCY) drops this at the cross-module level; the same logic applies to intra-module symmetry claims. Keep only when the divergence produces divergent *observable* behavior with a named downstream consumer.

---

### ❌ DROP — `rename_for_clarity_no_ambiguity`

```
title: "rename handleResult to processApprovalResult"
description: "The current name doesn't make clear which kind of result is being handled."
suggestion: "Rename for clarity."
```

**Why drop.** Pure preference. Unless you can cite a past commit that confused the names OR demonstrate that the name actively mis-describes behavior (`isEnabled` returning `false` when enabled), "the new name reads better" is never a finding.

---

### ❌ DROP — `defensive_hardening_speculative`

```
title: "BOOLEAN_FLAG default cast accepts non-boolean JSON Schema defaults"
description: "`(propSchema.default as boolean) ?? false` silently accepts
  {'type':'boolean','default':'yes'} — the string lands in Commander at runtime."
suggestion: "Validate the default is a real boolean; raise a schema error."
```

**Why drop.** Schema authoring is developer-controlled (Gate 2: internal/trusted source). A developer writing `default: 'yes'` in their own schema is not a threat actor — they'd fix it the first time their own tool misbehaves. Runtime type-checking against developer self-inflicted typos is infinite work for zero external value. Flag only when the schema comes from an untrusted source per the project's threat model.

---

### ❌ DROP — `typo_hypothetical`

```
title: "dynamic metadata attach is typo-fragile"
description: "A typo like `_exposurefilter` vs `_exposureFilter` would silently
  no-op at runtime with no TS error."
```

**Why drop.** No such typo exists. The finding hypothesizes a future bug that hasn't occurred. If a typo is introduced later, the test suite will catch it. Flagging hypothetical future typos is infinite: every string literal, every property access, every enum name is a potential typo. Drop all of these unless a real typo-induced bug has been reported in the commit history.

---

### ✅ KEEP — `cross_module_drift_observable`

```
title: "apcli exec bypasses checkApproval() and audit-log writes"
description: "registerExecCommand's action (discovery.ts:289) invokes executor.execute
  directly — no checkApproval, no auditLogger.logExecution, no sandbox gating.
  buildModuleCommand (main.ts:1038) wires all three. A module with
  annotations.requires_approval: true executes WITHOUT the approval gate when invoked
  via `apcli exec`; no audit trail entry is written either."
evidence: |
  discovery.ts:289:  const result = await executor.execute(moduleId, merged);
  main.ts:1038:      const approvalDecision = await checkApproval(moduleDef, ...);
  main.ts:1166:      await auditLogger.logExecution('success', exitCode, durationMs);
  main.ts:1184:      await auditLogger.logExecution('error', exitCode, durationMs, err);
  → Concrete trigger: module with requires_approval: true invoked via
    `apcli exec foo` completes with exit 0 and zero audit entries.
```

**Why keep.** Concrete reachable trigger + observable wrong behavior (approval gate skipped, audit trail missing) + cross-module asymmetry verified with file:line on both sides + contract-symmetry pre-flight holds (both paths dispatch the same module with the same options). Gate 5 verified.

---

### ✅ KEEP — `consolidation_3plus_sites_verified`

```
title: "emitResult helper re-implemented inline in 5 command registrars"
description: "emitResult (system-cmd.ts:37) is used only by registerHealthCommand.
  Five other registrars re-inline the same format-then-write pattern. Adding a new
  output format requires 5 edits today."
evidence: |
  grep -n 'fmt === "json" || !isTTY' src/system-cmd.ts
  src/system-cmd.ts:42:   if (fmt === "json" || !isTTY) {
  src/system-cmd.ts:209:  if (fmt === "json" || !isTTY) {
  src/system-cmd.ts:241:  if (fmt === "json" || !isTTY) {
  src/system-cmd.ts:271:  if (fmt === "json" || !isTTY) {
  src/system-cmd.ts:303:  if (fmt === "json" || !isTTY) {
  src/system-cmd.ts:339:  if (fmt === "json" || !isTTY) {
  → 5 re-implementations + 1 helper already exists to consolidate into.
```

**Why keep.** ≥3 sites (threshold met: 5 sites), grep output pasted (Gate 5 verified), extraction target already exists (no new abstraction to justify), concrete maintenance cost named.

---

### How to use this gallery

1. **Before emitting any finding**, pattern-match it against the ❌ blocks. If the shape matches — regardless of wording — write it into `CANDIDATE_INVENTORY` with the corresponding `drop_reason` code and do NOT emit it.
2. **Before emitting a finding into a dimension block**, pattern-match it against the ✅ blocks. Your finding should look structurally like them: concrete trigger, observable behavior, evidence with file:line and verification artifact. Kept findings get NO ledger row.
3. **If you cannot decide**, the default is DROP (ledger it). Under-flagging a marginal finding has ~zero cost; over-flagging degrades the whole report.

---

## Anti-rationalization (over-flagging direction)

This table counters the bias introduced by the dimensional framework — "I want to flag this finding". (The mirror table countering "I want to drop this finding" lives in `call-graph-discipline.md`.)

| Thought | Reality |
|---------|---------|
| "The input *could* be malformed if an attacker controls it" | Check Gate 2. Internal / trusted / type-checked input sources do not have an attacker. The attack scenario is fictional. Drop. |
| "I haven't found anything in D8 / D11 / D13 yet — I should produce something" | Empty dimensions are valid. Gate 4. Filling a dimension with marginal findings to show effort is the primary cause of over-flagging. Move on. |
| "This is inconsistent with how the sibling module does it" | Inconsistency is a `warning`, not a `critical`, unless the inconsistency itself produces a wrong observable behavior. Pure pattern divergence is `warning` at most. Gate 3 rule 2. |
| "The fix is one line — might as well flag it" | Fix effort does not determine severity. A one-line fix to a non-bug is still a non-bug. If you can't name the observable failure, drop. |
| "If I phrase the description carefully, the finding sounds plausible" | If you need "could theoretically" or "in case someone" to make it sound plausible, it failed Gate 1. Drop or downgrade. |
| "The code doesn't validate this input — that smells wrong" | Lack of validation is only a finding if (Gate 2) the input is genuinely external AND (Gate 1) a malformed input is reachable in actual use. Internal type-checked call sites do not need runtime validation. |
| "Patterns A and B are mixed in this file — that's a code smell" | A code smell is not a bug. Without a concrete observable failure, `suggestion` at most — often drop. |
| "`yaml.dump` instead of `yaml.safe_dump` is a known footgun" | Footgun-awareness is not the same as a bug. If `metadata` in this codebase is built from primitives under the project's invariants, `yaml.dump` produces the same output as `safe_dump`. Findings of the form "if the codebase ever does X, Y would break" are Gate 1 failures. Drop unless the codebase actually does X. |
| "Non-atomic file write — what if the process crashes mid-write" | For a developer tool generating source files for local dev, a partial file on crash is a rerun-and-fix problem, not a correctness bug. Flag only when the artifact is load-bearing in production (data files, DB state, append-only logs). |
| "The method ignores the `ctx` / `cancellation` / `deadline` parameter" | Only a finding if ignoring it produces observable wrong behavior (hung request, leaked resource). If the method completes in microseconds and cancellation is cosmetic, drop or `suggestion`. |
| "Module A does X, module B does Y — that's inconsistency" | Not every difference is a bug. Different modules often serve different logical roles (different trust boundaries, different lifecycle positions, different caller contracts). Inconsistency only matters if it produces divergent **observable behavior** (different caller results, different error handling semantics, test gap). Pure pattern divergence with identical observable behavior is noise — drop. Contract-symmetry pre-flight required before flagging as a cross-module consistency issue. |
| "This is a style / readability improvement — at worst a `suggestion`" | Only if the benefit is concrete and observable: removes dead code, clarifies a non-obvious invariant, eliminates duplication that has drifted. "Might be clearer", "could be simpler", "consider using X", "for readability" are preferences, not findings. If you cannot name the concrete benefit in one line, **drop** — the orchestrator's suggestion-level concrete-benefit check will drop it anyway; pre-empt by not emitting. |
| "I'm going to downgrade this from critical to warning to be safe" | Downgrade-and-keep was the old policy and it failed: noise relocated from `critical` into `warning`/`suggestion` where no further gate ran. The new policy is: speculative phrasing → **DROP at any severity**; warning without named downside → **DROP**; warning with unverified factual claim → **DROP (Gate 5)**; suggestion without named benefit → **DROP**; suggestion that is pure nitpick → **DROP**. If the finding survives a drop check, keep its original severity; if it would only survive after downgrade, it would not have survived the lower-severity drop check either — so drop it now. |
| "I'll write 'zero references' / 'dead code' / 'only used in foo.ts' based on what I remember seeing while reading" | Gate 5 failure. Memory is not evidence. If the claim is falsifiable ("zero", "never", "only", "duplicates"), `evidence` MUST paste the actual `grep -rn <symbol>` output (or equivalent) covering the full repo — not a single file, not a summary sentence. Without the pasted command+output, the finding is DROPPED. "Zero references in the file I read" is not a zero-reference claim; it's a reading bias. |
| "The symbol is only defined here, so it must be dead" | Definition without caller-discovery is incomplete. A symbol may be: (a) re-exported through a barrel (`index.ts`, `__init__.py`, `mod.rs pub use`), (b) dynamically resolved (Python `getattr`, TS `import()`, Go reflection), (c) referenced only from tests (which some greps exclude by default), (d) used by an external consumer (SDK public API). Before claiming dead code, grep the full repo including tests, and sanity-check the exports surface. Without that, drop. |
| "I found three similar issues in the same file — I'll write three separate suggestions" | No. At orchestrator validation #7 (same-theme consolidation), ≥3 suggestions with the same `(file, theme)` are merged into one themed bullet (extra ones dropped). Emit one consolidated suggestion up front with a list of sites — that is the on-target format. Themes include: renaming, format-consistency, error-message-casing, logging-prefix, null-check-style, iteration-style. |
| "It's just a rename for clarity — that's a legitimate suggestion" | Pure rename-for-clarity is a preference, not a finding. Drop unless the current name creates a concrete bug-producing ambiguity (e.g., two symbols with near-identical names that have been confused by a past commit, or a name that actively mis-describes behavior such as `isEnabled` that returns `false` when enabled). If the best justification is "the new name reads better", drop. |
| "`apcore-cli` binary collides with another tool on $PATH — warning-worthy" | Binary-name collisions between sibling projects are a packaging/distribution concern, not a code review finding. Max severity: `suggestion`, and only if the review scope includes packaging. Flag as warning only if the collision demonstrably breaks a documented user flow. |
