# Review Feedback Workflow

Evaluate and respond to incoming code review feedback with technical rigor.

## Core Principle

**Technical evaluation, not emotional performance.** Evaluate each suggestion on its technical merit for THIS codebase, not in the abstract.

## Iron Law

**NO BLIND IMPLEMENTATION. EVALUATE BEFORE ACTING.**

Read → Understand → Verify → Evaluate → Respond → Implement (if warranted).

## Step 1: Collect Feedback

Determine the feedback source:

**From a PR:**
```bash
# If PR number provided
gh pr view {number} --comments
gh api repos/{owner}/{repo}/pulls/{number}/reviews
gh api repos/{owner}/{repo}/pulls/{number}/comments
```

**From user input:**
If the user pasted review comments directly, parse them as-is.

**From a file:**
If the user provided a file path, read it.

List all review items with:
- Reviewer name (if available)
- File and line reference
- The comment/suggestion text
- Severity (if indicated by reviewer)

## Step 2: Evaluate Each Item

For EACH feedback item, assess independently:

### 2.1 Understand the Suggestion

- What exactly is being suggested?
- What problem does it claim to solve?
- Is the context/reasoning provided?

### 2.2 Verify Technically

**Check if the suggestion is correct for THIS codebase:**
- Read the referenced file and surrounding code
- Check if the described problem actually exists
- Check if the suggested fix would work in this context
- Check for side effects the reviewer may not have considered

### 2.3 Classify

| Classification | Action |
|---------------|--------|
| **Correct and valuable** | Implement the fix |
| **Correct but YAGNI** | Push back — adds unused complexity |
| **Partially correct** | Implement the valid part, explain the rest |
| **Incorrect for this codebase** | Push back with technical evidence |
| **Unclear** | Ask for clarification before implementing |
| **Style preference** | Follow project conventions, not reviewer taste |

## Step 3: Respond

### Forbidden Responses

NEVER use these performative phrases:
- "You're absolutely right!"
- "Great catch!"
- "Thanks for pointing that out!"
- "Good point, I should have..."

These are social performance, not technical communication.

### Correct Response Patterns

**When implementing a fix:**
> Fixed. Changed X to Y because Z.

**When partially implementing:**
> Fixed the null check. Didn't add the type guard — the union is exhaustive here (see line 42).

**When pushing back:**
> This code intentionally uses X instead of Y because [technical reason]. See [reference].

**When asking for clarification:**
> Not sure I follow — do you mean X or Y? The current behavior handles Z because [reason].

**When correcting wrong pushback:**
If you initially pushed back but the reviewer was right:
> You're right, I missed that. Fixed.

No apologies. No self-deprecation. State the correction factually and move on.

## Step 4: Implement

Process items in order:
1. **Blocking issues** (security, correctness) — fix immediately
2. **Simple fixes** (naming, formatting) — batch and fix
3. **Complex fixes** (architecture, design) — one at a time, verify each

For each fix:
- Make the change
- Run relevant tests
- Verify the fix addresses the feedback
- Commit with reference to the review item

## Step 5: Report

```
Review Feedback Processed: {N} items

Implemented:  {count}
Pushed back:  {count}
Clarifying:   {count}

Changes made:
  {file}: {description of change}
  {file}: {description of change}

Pushed back on:
  #{item}: {reason}

Needs clarification:
  #{item}: {question}

All tests: {pass/fail}
```

If responding to a PR, post individual replies to each comment thread using:
```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies -f body="..."
```

## Common Mistakes

- Implementing every suggestion without evaluating it first
- Using performative language to seem agreeable
- Pushing back without technical evidence
- Implementing fixes without running tests after each change
- Responding to all comments in bulk instead of per-thread
