"""
CLI entry point.

Usage:
  python run.py <repo_url> <function_name> [options]

Options:
  --provider    LLM provider: deepseek (default), anthropic, openai, ollama
  --model       Override the model name
  --preset      Pipeline preset: fast, default (default), thorough
  --output-dir  Where to write output (default: eval_output)
  --desc        Plain-English description of what the function should do
  --no-install  Skip pip-installing the repo

Examples:
  python run.py https://github.com/keon/algorithms binary_search
  python run.py https://github.com/keon/algorithms binary_search --provider anthropic --preset thorough
"""

import sys
import argparse
from src.pipeline import run_pipeline
from src.reporter import print_bug_report, write_bug_report

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main():
    p = argparse.ArgumentParser(description="Generate and run tests for a GitHub repo function.")
    p.add_argument("repo_url")
    p.add_argument("function_name")
    p.add_argument("--provider",    default="deepseek")
    p.add_argument("--model",       default=None)
    p.add_argument("--preset",      default="default", choices=["fast", "default", "thorough"])
    p.add_argument("--output-dir",  default="eval_output")
    p.add_argument("--desc",        default="")
    p.add_argument("--no-install",  action="store_true")
    args = p.parse_args()

    result = run_pipeline(
        repo_url=args.repo_url,
        fn_name=args.function_name,
        description=args.desc,
        provider=args.provider,
        model=args.model,
        preset=args.preset,
        output_dir=args.output_dir,
        install_deps=not args.no_install,
    )

    if result["status"] == "error":
        print(f"\nERROR: {result['error']}")
        sys.exit(1)

    print_bug_report(result["failures"], args.repo_url)
    write_bug_report(result["failures"], args.repo_url, result["output_dir"])
    print(f"\nDone. Output: {result['output_dir']}")


if __name__ == "__main__":
    main()
