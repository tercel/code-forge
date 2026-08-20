#!/usr/bin/env python3
"""Partition a review scope into module groups (review SKILL.md 3F.3 / 3P.3).

This implements the DETERMINISTIC half of module grouping: build the file-level
graph, measure how badly a directory split would cut it, pick the axis, apply
the size cap, merge down to the group-count cap, and decide whether the scope
guardrail fires.

It is deliberately a PARTITIONER, not an analyst. It does not read source, does
not resolve imports, and does not judge findings. The caller supplies the edges
(from the impact-zone expansion it already ran) and the architecture pattern
(from PA.2.2); this returns the partition and the numbers behind it.

Two invariants it enforces, both of which were silent-failure modes before:
  * coverage        — union(group files) == input files, always
  * count-over-size — group count is a hard cap; group size yields to it

Usage:
  cf-group.py < scope.json
  cf-group.py --input scope.json

Input JSON:
  {
    "files":  ["src/a.ts", ...],            # required, the review scope
    "edges":  [["src/a.ts", "src/b.ts"]],   # optional, file -> file imports
    "barrels": ["src/index.ts"],            # optional, re-export files
    "manifests": ["package.json", ...],     # optional, package boundary markers
    "architecture_pattern": "Layered API"   # optional, from PA.2.2
  }
Output: JSON on stdout.
"""

import argparse
import json
import os
import posixpath
import sys

sys.dont_write_bytecode = True  # never write .pyc into a possibly read-only install dir

# --- Thresholds. These mirror SKILL.md 3F.3.4; change both together. ---
SIZE_CAP = 4              # files per group
SIZE_CAP_LARGE = 6        # once the scope reaches LARGE_SCOPE files
LARGE_SCOPE = 33
GROUP_CAP = 8             # hard cap on group count -> agent fan-out
SCOPE_GUARDRAIL = 48      # files above which we stop and ask the user
S3_FAST_PATH_MAX = 12     # an undivided scope one agent can still read in full
CUT_RATIO_SPLIT = 0.3     # directory partition above this cuts too many chains
BLOB_SHARE = 0.7          # one component holding this share of files => S3

S1_PATTERNS = {"plugin/extension", "plugin", "extension", "component-based", "monorepo"}
S2_PATTERNS = {"layered api", "layered", "mvc", "clean/hexagonal", "clean", "hexagonal"}


def norm(p):
    """Normalize to forward slashes so grouping is platform-stable.

    Always folds backslashes, not just os.sep — a scope can carry Windows-style
    paths into a POSIX run (diff produced elsewhere, CI artifact, pasted list),
    and grouping must not depend on which host it executes on.
    """
    return p.replace("\\", "/").strip("/")


def parent(p):
    d = posixpath.dirname(p)
    return d if d else "."


def common_prefix_depth(a, b):
    """Number of leading path segments two directories share."""
    pa, pb = a.split("/"), b.split("/")
    n = 0
    for x, y in zip(pa, pb):
        if x != y:
            break
        n += 1
    return n


def package_of(path, boundaries):
    """Longest manifest directory that prefixes path; '' when none applies."""
    best = ""
    for b in boundaries:
        if b == "." or b == "":
            continue
        if path == b or path.startswith(b + "/"):
            if len(b) > len(best):
                best = b
    return best


def collapse_barrels(edges, barrels):
    """A -> barrel -> B becomes A -> B; barrels never become graph nodes.

    Applied repeatedly so a chain of barrels (a re-export of a re-export)
    collapses too. Bounded by the barrel count, so it always terminates.
    """
    if not barrels:
        return [(a, b) for a, b in edges if a != b]
    barrels = set(barrels)
    out = set()
    for a, b in edges:
        if a in barrels:
            continue  # the edge into the barrel carries the real target
        seen = set()
        targets = [b]
        resolved = []
        while targets:
            t = targets.pop()
            if t in seen:
                continue
            seen.add(t)
            if t in barrels:
                targets.extend(y for x, y in edges if x == t)
            else:
                resolved.append(t)
        for r in resolved:
            if r != a:
                out.add((a, r))
    return sorted(out)


def cut_ratio(partition, edges):
    """Fraction of edges crossing group boundaries under this partition."""
    if not edges:
        return 0.0
    owner = {}
    for gid, files in partition.items():
        for f in files:
            owner[f] = gid
    crossing = sum(1 for a, b in edges
                   if owner.get(a) is not None and owner.get(b) is not None
                   and owner[a] != owner[b])
    return round(crossing / len(edges), 3)


def group_by_directory(files):
    groups = {}
    for f in files:
        groups.setdefault(parent(f), []).append(f)
    return {k: sorted(v) for k, v in sorted(groups.items())}


def weakly_connected(files, edges):
    """Union-find over undirected edges; returns components as file lists."""
    rank = {f: 0 for f in files}
    up = {f: f for f in files}

    def find(x):
        while up[x] != x:
            up[x] = up[up[x]]
            x = up[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return
        if rank[rx] < rank[ry]:
            rx, ry = ry, rx
        up[ry] = rx
        if rank[rx] == rank[ry]:
            rank[rx] += 1

    fileset = set(files)
    for a, b in edges:
        if a in fileset and b in fileset:
            union(a, b)
    comps = {}
    for f in files:
        comps.setdefault(find(f), []).append(f)
    return [sorted(v) for v in comps.values()]


def group_by_chain(files, edges, boundaries=()):
    """Components become groups; singletons attach to their strongest neighbour.

    A file with no edges at all has no 'most edges to' target, so it attaches by
    longest shared path prefix instead — otherwise config and fixture files each
    become their own group and re-create the fragmentation this axis avoids.

    Boundary rule, and the asymmetry matters: a file that reaches a component
    through a real import edge may join it across a package boundary — a genuine
    cross-package call chain is exactly what this axis exists to keep whole. A
    zero-edge file has no such evidence, only a path guess, so it must stay
    inside its own package; otherwise a frontend component lands in a backend
    agent and the D5 architecture signal is destroyed.
    """
    comps = weakly_connected(files, edges)
    big = [c for c in comps if len(c) > 1]
    singles = [c[0] for c in comps if len(c) == 1]
    if not big:
        return {f"chain{i + 1}": c for i, c in enumerate(sorted(comps))}

    owner = {}
    orphans = []
    for i, c in enumerate(big):
        for f in c:
            owner[f] = i

    for f in sorted(singles):
        votes = {}
        for a, b in edges:
            if a == f and b in owner:
                votes[owner[b]] = votes.get(owner[b], 0) + 1
            elif b == f and a in owner:
                votes[owner[a]] = votes.get(owner[a], 0) + 1
        if votes:
            # most edges wins; ties fall back to deepest shared prefix
            best = max(votes.items(),
                       key=lambda kv: (kv[1],
                                       max(common_prefix_depth(parent(f), parent(x))
                                           for x in big[kv[0]])))[0]
        else:
            pkg_f = package_of(f, boundaries)
            eligible = [i for i in range(len(big))
                        if any(package_of(x, boundaries) == pkg_f for x in big[i])]
            if not eligible:
                orphans.append(f)  # no same-package component: keep it separate
                continue
            best = max(eligible,
                       key=lambda i: (max(common_prefix_depth(parent(f), parent(x))
                                          for x in big[i]), -i))
        big[best].append(f)
        owner[f] = best

    groups = {f"chain{i + 1}": sorted(c) for i, c in enumerate(big)}
    for f in orphans:
        groups[f"orphan:{parent(f)}"] = [f]
    return groups


def split_oversized(groups, cap):
    """Enforce the size cap. Deterministic: split in sorted order, keep names stable."""
    out = {}
    for gid, files in sorted(groups.items()):
        if len(files) <= cap:
            out[gid] = files
            continue
        for i in range(0, len(files), cap):
            chunk = files[i:i + cap]
            out[gid if i == 0 else f"{gid}#{i // cap + 1}"] = chunk
    return out


def merge_to_cap(groups, boundaries, cap):
    """Merge smallest-first, never across a package boundary.

    Returns (groups, merged_flag, blocked_flag). blocked_flag is True when the
    count still exceeds cap and nothing may legally merge — that is a guardrail
    condition, not something to silently accept.
    """
    groups = {k: list(v) for k, v in groups.items()}
    merged = False
    while len(groups) > cap:
        gids = sorted(groups)
        pkg = {g: package_of(groups[g][0], boundaries) for g in gids}
        best = None
        for i, a in enumerate(gids):
            for b in gids[i + 1:]:
                if pkg[a] != pkg[b]:
                    continue  # impassable wall
                size = len(groups[a]) + len(groups[b])
                depth = common_prefix_depth(parent(groups[a][0]), parent(groups[b][0]))
                key = (size, -depth, a, b)
                if best is None or key < best[0]:
                    best = (key, a, b)
        if best is None:
            return groups, merged, True
        _, a, b = best
        groups[a] = sorted(groups[a] + groups[b])
        del groups[b]
        merged = True
    return groups, merged, False


def choose_strategy(pattern, files, edges, dir_ratio):
    """Axis selection. cut_ratio overrides the pattern table when they disagree."""
    comps = weakly_connected(files, edges)
    largest = max((len(c) for c in comps), default=0)
    size_cap = SIZE_CAP_LARGE if len(files) >= LARGE_SCOPE else SIZE_CAP
    # S3 means "indivisible AND big enough that something would divide it".
    # A blob that already fits under the size cap is never split, so labelling
    # it S3 would claim a special case that changes nothing.
    if (files and edges and len(files) > size_cap
            and largest / len(files) > BLOB_SHARE):
        return "S3", largest
    p = (pattern or "").strip().lower()
    if not edges:
        return "S1", largest
    if dir_ratio < CUT_RATIO_SPLIT:
        # the directory split already keeps the chains intact, whatever the pattern
        return "S1", largest
    if p in S1_PATTERNS:
        return "S1", largest
    if p in S2_PATTERNS:
        return "S2", largest
    return "S2", largest  # unknown pattern + high cut ratio: trust the measurement


def partition(scope):
    files = sorted({norm(f) for f in scope.get("files", [])})
    barrels = {norm(b) for b in scope.get("barrels", [])}
    files = [f for f in files if f not in barrels]
    raw_edges = [(norm(a), norm(b)) for a, b in scope.get("edges", [])]
    edges = collapse_barrels(raw_edges, barrels)
    edges = [(a, b) for a, b in edges if a in set(files) and b in set(files)]
    boundaries = sorted({parent(norm(m)) for m in scope.get("manifests", [])})

    n = len(files)
    size_cap = SIZE_CAP_LARGE if n >= LARGE_SCOPE else SIZE_CAP

    dir_groups = group_by_directory(files)
    dir_ratio = cut_ratio(dir_groups, edges)
    strategy, largest_comp = choose_strategy(
        scope.get("architecture_pattern"), files, edges, dir_ratio)

    if strategy == "S3":
        groups = {"whole": files}
        merged, blocked = False, False
    else:
        groups = (dir_groups if strategy == "S1"
                  else group_by_chain(files, edges, boundaries))
        groups = split_oversized(groups, size_cap)
        groups, merged, blocked = merge_to_cap(groups, boundaries, GROUP_CAP)

    reasons = []
    if n > SCOPE_GUARDRAIL:
        reasons.append(f"scope of {n} files exceeds {SCOPE_GUARDRAIL}")
    if len(groups) > GROUP_CAP:
        reasons.append(
            f"{len(groups)} groups exceed the cap of {GROUP_CAP} and no mergeable pair remains"
            if blocked else f"{len(groups)} groups exceed the cap of {GROUP_CAP}")
    if strategy == "S3" and n > S3_FAST_PATH_MAX:
        reasons.append(
            f"scope is one indivisible unit of {n} files, above the {S3_FAST_PATH_MAX}-file "
            "limit a single agent can read in full")

    if strategy == "S3":
        path = "fast" if n <= S3_FAST_PATH_MAX else "blocked"
    elif n < 3 or len(groups) <= 1:
        path = "fast"
    else:
        path = "layered"

    covered = sorted({f for g in groups.values() for f in g})
    return {
        "grouping_strategy": strategy,
        "cut_ratio": dir_ratio,
        "size_cap": size_cap,
        "path": path,
        "groups": [{"group_id": gid, "files": groups[gid]} for gid in sorted(groups)],
        "group_count": len(groups),
        "largest_group": max((len(g) for g in groups.values()), default=0),
        "largest_component": largest_comp,
        "groups_merged": merged,
        "in_diff_files": files,
        "file_count": n,
        "edge_count": len(edges),
        "coverage_ok": covered == files,
        "guardrail": {"triggered": bool(reasons), "reasons": reasons},
    }


def main():
    ap = argparse.ArgumentParser(description="Partition a review scope into module groups.")
    ap.add_argument("--input", help="JSON file; defaults to stdin")
    args = ap.parse_args()
    try:
        raw = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
        scope = json.loads(raw)
    except (OSError, ValueError) as e:
        print(json.dumps({"error": f"cannot read scope JSON: {e}"}), file=sys.stderr)
        return 2
    if not isinstance(scope, dict) or not isinstance(scope.get("files"), list):
        print(json.dumps({"error": "input must be an object with a 'files' array"}),
              file=sys.stderr)
        return 2
    result = partition(scope)
    print(json.dumps(result, indent=2))
    return 0 if result["coverage_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
