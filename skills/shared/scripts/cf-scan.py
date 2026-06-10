#!/usr/bin/env python3
"""Collect raw project facts for the project-analysis protocol (PA.1/PA.2.1/PA.5).

This gathers the *enumeration* signals that otherwise cost many Grep/Glob
round-trips: language mix, build files, dependency names, detected frameworks,
test files + framework + command, source-tree top level, and entrypoints.

It is deliberately a FACTS COLLECTOR, not an analyst. Architecture pattern
recognition, call graphs, data flow, and risk assessment stay with the model —
use this JSON as the starting inventory and verify it.

Usage:
  cf-scan.py [--root PATH] [--max-tree N]
Output: JSON on stdout.
"""

import argparse
import json
import os
import re
import sys

sys.dont_write_bytecode = True  # never write .pyc into a possibly read-only install dir

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

IGNORE_DIRS = {
    ".git", "node_modules", "dist", "build", "target", ".venv", "venv", "env",
    "__pycache__", ".worktrees", "worktrees", "planning", ".code-forge", ".next",
    ".nuxt", "coverage", "vendor", ".mypy_cache", ".pytest_cache", ".idea",
    ".vscode", ".tox", ".gradle", "out", "bin", "obj",
}

EXT_LANG = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".rb": "Ruby", ".php": "PHP",
    ".cs": "C#", ".kt": "Kotlin", ".swift": "Swift", ".scala": "Scala",
    ".c": "C", ".h": "C", ".cpp": "C++", ".cc": "C++", ".hpp": "C++", ".ex": "Elixir",
}

BUILD_FILES = [
    "package.json", "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg",
    "Cargo.toml", "go.mod", "build.gradle", "build.gradle.kts", "pom.xml",
    "composer.json", "Gemfile", "Makefile",
]

# Substring (lowercased) -> framework label. Matched against dependency names.
FRAMEWORKS = {
    "fastapi": "FastAPI", "flask": "Flask", "django": "Django", "starlette": "Starlette",
    "tornado": "Tornado", "aiohttp": "aiohttp", "express": "Express", "@nestjs/core": "NestJS",
    "koa": "Koa", "hono": "Hono", "fastify": "Fastify", "next": "Next.js", "react": "React",
    "vue": "Vue", "svelte": "Svelte", "@angular/core": "Angular", "solid-js": "Solid",
    "click": "Click", "typer": "Typer", "spf13/cobra": "Cobra", "gin-gonic/gin": "Gin",
    "labstack/echo": "Echo", "gofiber/fiber": "Fiber", "clap": "clap", "actix-web": "Actix-web",
    "axum": "Axum", "rocket": "Rocket", "spring-boot": "Spring Boot", "langchain": "LangChain",
    "crewai": "CrewAI", "autogen": "AutoGen",
}

SIGNAL_DEPS = {
    "database": ["prisma", "sqlalchemy", "sequelize", "gorm", "diesel", "knex",
                 "mongoose", "typeorm", "alembic"],
    "auth": ["jsonwebtoken", "pyjwt", "passport", "oauth", "authlib", "bcrypt",
             "argon2", "jose"],
    "message_queue": ["kafka", "pika", "amqp", "rabbit", "nats", "kombu", "confluent"],
    "background_jobs": ["celery", "bullmq", "sidekiq", "dramatiq", "rq"],
    "external_api": ["axios", "requests", "httpx", "reqwest", "node-fetch", "got"],
}

TEST_GLOBS = [".test.", ".spec.", "_test.go", "_test.rs"]
ENTRYPOINT_CANDIDATES = [
    "main.py", "app.py", "manage.py", "index.js", "main.go", "src/index.ts",
    "src/main.ts", "src/main.rs", "src/lib.rs", "src/main.py", "cmd",
]
SOURCE_DIR_NAMES = ["src", "app", "lib", "cmd", "internal", "pkg"]


def _strip_pkg(name):
    """Reduce a dependency spec to its bare package name."""
    name = name.strip().strip('"').strip("'")
    name = re.split(r"[<>=!~;\[\(\s]", name, maxsplit=1)[0]
    return name.strip()


def _toml_keys(path, *table_path):
    """Best-effort read of a TOML table's keys (uses tomllib when available)."""
    if tomllib is not None:
        try:
            with open(path, "rb") as fh:
                data = tomllib.load(fh)
            for key in table_path:
                data = data.get(key, {})
            return list(data.keys()) if isinstance(data, dict) else []
        except (OSError, ValueError):
            return []
    return []


def extract_dependencies(root):
    """Return (dep_names, raw_by_file) for every build file found at the root."""
    deps = set()
    raw = {}

    pkg = os.path.join(root, "package.json")
    if os.path.isfile(pkg):
        try:
            with open(pkg, encoding="utf-8") as fh:
                data = json.load(fh)
            names = list(data.get("dependencies", {})) + list(data.get("devDependencies", {}))
            deps.update(names)
            raw["package.json"] = {"deps": names, "scripts": data.get("scripts", {})}
        except (OSError, ValueError):
            pass

    pyproject = os.path.join(root, "pyproject.toml")
    if os.path.isfile(pyproject):
        names = []
        if tomllib is not None:
            try:
                with open(pyproject, "rb") as fh:
                    data = tomllib.load(fh)
                for d in data.get("project", {}).get("dependencies", []):
                    names.append(_strip_pkg(d))
                names += [_strip_pkg(k) for k in _toml_keys(pyproject, "tool", "poetry", "dependencies")]
            except (OSError, ValueError):
                pass
        deps.update(n for n in names if n and n.lower() != "python")
        raw["pyproject.toml"] = [n for n in names if n]

    req = os.path.join(root, "requirements.txt")
    if os.path.isfile(req):
        names = []
        for line in _read_lines(req):
            line = line.strip()
            if line and not line.startswith(("#", "-")):
                names.append(_strip_pkg(line))
        deps.update(names)
        raw["requirements.txt"] = names

    cargo = os.path.join(root, "Cargo.toml")
    if os.path.isfile(cargo):
        names = _toml_keys(cargo, "dependencies")
        deps.update(names)
        raw["Cargo.toml"] = names

    gomod = os.path.join(root, "go.mod")
    if os.path.isfile(gomod):
        names = re.findall(r"^\s*([\w\.\-/]+)\s+v[\d]", "\n".join(_read_lines(gomod)), re.M)
        deps.update(names)
        raw["go.mod"] = names

    gemfile = os.path.join(root, "Gemfile")
    if os.path.isfile(gemfile):
        names = re.findall(r"""gem\s+['"]([^'"]+)['"]""", "\n".join(_read_lines(gemfile)))
        deps.update(names)
        raw["Gemfile"] = names

    composer = os.path.join(root, "composer.json")
    if os.path.isfile(composer):
        try:
            with open(composer, encoding="utf-8") as fh:
                data = json.load(fh)
            names = list(data.get("require", {})) + list(data.get("require-dev", {}))
            deps.update(names)
            raw["composer.json"] = names
        except (OSError, ValueError):
            pass

    for gradle in ("build.gradle", "build.gradle.kts", "pom.xml"):
        path = os.path.join(root, gradle)
        if os.path.isfile(path):
            text = "\n".join(_read_lines(path))
            names = re.findall(r"['\"]([\w\.\-]+:[\w\.\-]+)(?::[\w\.\-]+)?['\"]", text)
            if gradle == "pom.xml":
                names += re.findall(r"<artifactId>([^<]+)</artifactId>", text)
            deps.update(names)
            raw[gradle] = names

    return {d.lower() for d in deps if d}, raw


def _read_lines(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read().splitlines()
    except OSError:
        return []


def walk_facts(root):
    """Single tree walk: language counts, test files, build-file presence."""
    lang_counts = {}
    test_files = []
    has_dirs = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        rel_dir = os.path.relpath(dirpath, root)
        base = os.path.basename(dirpath)
        if base in ("prisma", "migrations", "alembic", "__tests__", "tests", "test"):
            has_dirs.add(base)
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXT_LANG:
                lang_counts[EXT_LANG[ext]] = lang_counts.get(EXT_LANG[ext], 0) + 1
            rel = os.path.normpath(os.path.join(rel_dir, fn))
            low = fn.lower()
            if (any(g in low for g in TEST_GLOBS) or low.startswith("test_")
                    or "__tests__" in rel.replace(os.sep, "/")
                    or "/tests/" in ("/" + rel.replace(os.sep, "/") + "/")):
                if len(test_files) < 2000:
                    test_files.append(rel)

    languages = sorted(
        ({"lang": k, "files": v} for k, v in lang_counts.items()),
        key=lambda x: x["files"], reverse=True,
    )
    return languages, test_files, has_dirs


def detect_test(root, deps, raw, test_count):
    framework = None
    command = None

    pkg = raw.get("package.json")
    if pkg:
        scripts = pkg.get("scripts", {})
        if "test" in scripts:
            command = "npm test"
        for fw in ("jest", "vitest", "mocha", "jasmine"):
            if any(fw in d for d in deps):
                framework = fw
                break

    if framework is None and any("pytest" in d for d in deps):
        framework = "pytest"
        command = command or "pytest"
    if os.path.isfile(os.path.join(root, "Cargo.toml")):
        framework = framework or "cargo test"
        command = command or "cargo test"
    if os.path.isfile(os.path.join(root, "go.mod")):
        framework = framework or "go test"
        command = command or "go test ./..."
    if framework is None and test_count and any(
        os.path.isfile(os.path.join(root, f)) for f in ("pyproject.toml", "setup.py", "requirements.txt")
    ):
        framework = "unittest"
        command = command or "python -m unittest"
    mk = os.path.join(root, "Makefile")
    if command is None and os.path.isfile(mk):
        if re.search(r"(?m)^test:", "\n".join(_read_lines(mk))):
            command = "make test"

    return {"framework": framework, "command": command}


def module_tree(root, max_tree):
    """Top-level entries under each detected source root (capped)."""
    roots = [d for d in SOURCE_DIR_NAMES if os.path.isdir(os.path.join(root, d))] or ["."]
    tree = {}
    for src in roots:
        base = os.path.join(root, src)
        entries = []
        try:
            for name in sorted(os.listdir(base)):
                if name in IGNORE_DIRS or name.startswith("."):
                    continue
                full = os.path.join(base, name)
                if os.path.isdir(full):
                    entries.append(name + "/")
                elif os.path.splitext(name)[1].lower() in EXT_LANG:
                    entries.append(name)
        except OSError:
            continue
        if entries:
            tree[src] = entries[:max_tree]
    return tree


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", help="Project root (default: auto-detect)")
    parser.add_argument("--max-tree", type=int, default=40, help="Max entries per source dir")
    args = parser.parse_args()

    root = os.path.abspath(args.root) if args.root else cf_find_root()
    deps, raw = extract_dependencies(root)
    languages, test_files, has_dirs = walk_facts(root)
    build_files = [f for f in BUILD_FILES if os.path.isfile(os.path.join(root, f))]

    frameworks = sorted({label for key, label in FRAMEWORKS.items()
                         if any(key in d for d in deps)})

    signals = {}
    for signal, needles in SIGNAL_DEPS.items():
        signals[signal] = any(any(n in d for d in deps) for n in needles)
    if has_dirs & {"prisma", "migrations", "alembic"} or os.path.isfile(os.path.join(root, "diesel.toml")):
        signals["database"] = True

    entrypoints = []
    for cand in ENTRYPOINT_CANDIDATES:
        full = os.path.join(root, cand)
        if os.path.isfile(full) or (cand == "cmd" and os.path.isdir(full)):
            entrypoints.append(cand)

    result = {
        "root": root,
        "languages": languages,
        "primary_language": languages[0]["lang"] if languages else None,
        "build_files": build_files,
        "dependencies": sorted(deps)[:200],
        "frameworks": frameworks,
        "signals": signals,
        "test": {
            "file_count": len(test_files),
            "sample": test_files[:5],
            **detect_test(root, deps, raw, len(test_files)),
        },
        "source_tree": module_tree(root, args.max_tree),
        "entrypoints": entrypoints,
        "notes": [
            "Best-effort enumeration only. Verify before relying on it.",
            "Architecture pattern, call graph, data flow, and risk assessment are NOT "
            "inferred here — do that reasoning yourself (project-analysis PA.2/PA.4/PA.7).",
        ],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cf_find_root():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import cf_common as cf
    return cf.find_project_root()


if __name__ == "__main__":
    sys.exit(main())
