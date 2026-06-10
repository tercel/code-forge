#!/usr/bin/env python3
"""Resolve code-forge configuration (the config-loading Step 0) and emit JSON.

Implements project-root detection, the three-layer config merge
(system defaults -> ~/.code-forge.json -> <root>/.code-forge.json), validation,
the --tmp output override, and directory resolution.

This script is READ-ONLY: it never writes files. The gitignore safety step for
--tmp stays in the skill prose because it mutates the user's repo.

Output (stdout) is a JSON object:
  project_root, config, base_dir, input_dir, output_dir, tmp_mode, sources, errors

If `errors` is non-empty the config has already been reset to system defaults
(per the validation rule "on failure, continue with system defaults").
"""

import argparse
import json
import os
import sys

sys.dont_write_bytecode = True  # never write .pyc into a possibly read-only install dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_common as cf


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--root",
        help="Project root (default: auto-detect by walking up for markers)",
    )
    parser.add_argument(
        "--tmp",
        action="store_true",
        help="Resolve the temporary output dir (.code-forge/tmp/) instead of the configured one",
    )
    # Hidden: override HOME so tests can supply a user config.
    parser.add_argument("--home", help=argparse.SUPPRESS)
    args = parser.parse_args()

    root = os.path.abspath(args.root) if args.root else cf.find_project_root()
    config, sources, load_errors = cf.load_config(root, home=args.home)
    errors = load_errors + cf.validate_config(config)

    # On any validation/load failure, fall back to system defaults.
    if errors:
        config = cf.copy_defaults()

    base_dir, input_dir, output_dir = cf.resolve_dirs(root, config, tmp=args.tmp)

    result = {
        "project_root": root,
        "config": config,
        "base_dir": base_dir,
        "input_dir": input_dir,
        "output_dir": output_dir,
        "tmp_mode": bool(args.tmp),
        "sources": sources,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
