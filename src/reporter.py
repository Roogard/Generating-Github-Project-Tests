import os
import re


def _extract_assertion_info(longrepr):
    info = {"assertion": "", "expected": "", "actual": "", "file": "", "line": ""}
    if not longrepr:
        return info

    lines = longrepr.splitlines() if isinstance(longrepr, str) else []

    # look for file:line pattern
    for line in lines:
        m = re.match(r'^(\S+\.py):(\d+):', line)
        if m:
            info["file"] = m.group(1)
            info["line"] = m.group(2)
            break

    # look for the assert expression
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("assert "):
            info["assertion"] = stripped
            break

    # look for E   assert X == Y (the rewritten assertion)
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("E") and "assert" in stripped:
            # strip leading "E" and whitespace
            expr = re.sub(r'^E\s+', '', stripped)
            m = re.match(r'assert\s+(.+?)\s*==\s*(.+)', expr)
            if m:
                info["actual"] = m.group(1).strip()
                info["expected"] = m.group(2).strip()
            break

    return info


def parse_failures(test_outcomes):
    failures = []

    for (fn_dir, test_filename), result in test_outcomes.items():
        # extract test type from filename (e.g. test_whitebox_statement.py -> whitebox_statement)
        test_type = test_filename
        if test_type.startswith("test_"):
            test_type = test_type[len("test_"):]
        if test_type.endswith(".py"):
            test_type = test_type[:-len(".py")]

        test_file_path = result.get("test_file_path", "")

        # handle actual test failures
        for i, test_name in enumerate(result.get("failed", [])):
            detail = {}
            details_list = result.get("failure_details", [])
            if i < len(details_list):
                detail = details_list[i]

            assertion_info = _extract_assertion_info(detail.get("longrepr", ""))
            crash = detail.get("crash", {})

            failures.append({
                "function": fn_dir,
                "test_file": test_filename,
                "test_file_path": test_file_path,
                "test_type": test_type,
                "test_name": test_name,
                "kind": "failure",
                "assertion": assertion_info["assertion"],
                "expected": assertion_info["expected"],
                "actual": assertion_info["actual"],
                "file": assertion_info["file"] or crash.get("path", ""),
                "line": assertion_info["line"] or str(crash.get("lineno", "")),
                "longrepr": detail.get("longrepr", ""),
                "stdout": result.get("stdout", ""),
            })

        # handle errors (import errors, collection errors, timeouts)
        for i, error_name in enumerate(result.get("errors", [])):
            error_detail = {}
            error_details_list = result.get("error_details", [])
            if i < len(error_details_list):
                error_detail = error_details_list[i]

            failures.append({
                "function": fn_dir,
                "test_file": test_filename,
                "test_file_path": test_file_path,
                "test_type": test_type,
                "test_name": error_name,
                "kind": "error",
                "assertion": "",
                "expected": "",
                "actual": "",
                "file": "",
                "line": "",
                "longrepr": error_detail.get("longrepr", ""),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
            })

    return failures


def format_bug_report(failures, repo_url=""):
    if not failures:
        return "No potential bugs detected. All generated tests passed."

    # count unique functions and total tests
    fn_set = set()
    for f in failures:
        fn_set.add(f["function"])

    lines = []
    lines.append("=================================================================")
    lines.append("BUG REPORT")
    if repo_url:
        lines.append(f"Repo: {repo_url}")
    lines.append("=================================================================")
    lines.append("")
    lines.append(f"Summary: {len(failures)} potential issue(s) across {len(fn_set)} function(s)")
    lines.append("")

    # group by function
    by_fn = {}
    for f in failures:
        by_fn.setdefault(f["function"], []).append(f)

    for fn_name, fn_failures in sorted(by_fn.items()):
        lines.append("-----------------------------------------------------------------")
        lines.append(f"Function: {fn_name}")
        lines.append("-----------------------------------------------------------------")
        lines.append("")

        for f in fn_failures:
            kind_label = "FAIL" if f["kind"] == "failure" else "ERROR"
            lines.append(f"  [{kind_label}] {f['test_file']}::{f['test_name']}")

            # categorize as whitebox or blackbox
            if f["test_type"].startswith("whitebox_"):
                category = "whitebox (" + f["test_type"][len("whitebox_"):] + ")"
            elif f["test_type"].startswith("blackbox_"):
                category = "blackbox (" + f["test_type"][len("blackbox_"):] + ")"
            else:
                category = f["test_type"]
            lines.append(f"    Type: {category}")

            if f["file"] or f["line"]:
                loc = f["file"]
                if f["line"]:
                    loc += f":{f['line']}"
                lines.append(f"    Location: {loc}")

            if f["kind"] == "failure":
                if f["expected"]:
                    lines.append(f"    Expected: {f['expected']}")
                if f["actual"]:
                    lines.append(f"    Actual:   {f['actual']}")
                if f["assertion"]:
                    lines.append(f"    Expression: {f['assertion']}")
            else:
                # error — show the error name and stderr snippet
                if f.get("stderr"):
                    first_line = f["stderr"].strip().splitlines()[0] if f["stderr"].strip() else ""
                    if first_line:
                        lines.append(f"    Error: {first_line}")

            lines.append("")

    lines.append("=================================================================")
    lines.append(f"Total: {len(failures)} issue(s) across {len(fn_set)} function(s)")
    lines.append("=================================================================")

    return "\n".join(lines)


def print_bug_report(failures, repo_url=""):
    report = format_bug_report(failures, repo_url)
    print()
    print(report)


def write_bug_report(failures, repo_url, output_dir):
    report = format_bug_report(failures, repo_url)
    path = os.path.join(output_dir, "bug_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
