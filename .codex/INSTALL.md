# Installing code-forge for Codex

## Prerequisites

- Codex installed and configured
- Git installed

## Installation

1. Clone the repository:

```bash
git clone https://github.com/tercel/code-forge.git
cd code-forge
```

2. Create the skills directory if it does not exist:

```bash
mkdir -p ~/.agents/skills
```

3. Symlink this repository to the Codex skills directory:

```bash
ln -s "$(pwd)" ~/.agents/skills/code-forge
```

If you are running this from the parent directory instead of the repository root,
use:

```bash
ln -s "$(pwd)/code-forge" ~/.agents/skills/code-forge
```

4. Verify the installation:

```bash
test -f ~/.agents/skills/code-forge/SKILL.md
ls ~/.agents/skills/code-forge/commands/
ls ~/.agents/skills/code-forge/skills/
# commands/ should include: build.md  debug.md  finish.md  fix.md  forge.md
#                           impl.md  parallel.md  plan.md  port.md  review.md
#                           status.md  tdd.md  verify.md  worktree.md
# skills/ should include the child skill directories.
```

## Usage

Once installed, the following commands are available in Codex:

- `/code-forge:build @doc.md` - Full pipeline from spec or prompt to working code
- `/code-forge:forge "task"` - Smart dispatch from natural language
- `/code-forge:plan @doc.md` - Generate implementation plan
- `/code-forge:impl [feature]` - Execute pending tasks
- `/code-forge:status [feature]` - View progress dashboard
- `/code-forge:review [feature]` - Review code quality
- `/code-forge:fix "bug"` - Debug and fix with upstream trace-back
- `/code-forge:debug "issue"` - Systematic root-cause debugging
- `/code-forge:tdd` - Enforce Red-Green-Refactor cycle
- `/code-forge:verify` - Verify before claiming completion
- `/code-forge:worktree <feature>` - Create isolated worktree
- `/code-forge:finish` - Merge, PR, keep, or discard branch work
- `/code-forge:parallel` - Dispatch independent problems to parallel agents
- `/code-forge:port @docs --ref impl --lang java` - Port to another language

## Notes

This repository is installed as a Codex skill tree via `~/.agents/skills`. It is
not currently packaged as a Codex plugin with `.codex-plugin/plugin.json` because
the repository contains `skills/shared/` as shared reference files rather than an
invokable skill directory. Packaging as a Codex plugin would require either
moving shared references out of `skills/` or otherwise adapting the layout to the
plugin validator.

## Uninstall

```bash
rm ~/.agents/skills/code-forge
```
