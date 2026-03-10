import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil
import subprocess
import tempfile


MUTMUT_TIMEOUT = 300  # 5 minutes per function


def run_mutmut(function_file, test_file, repo_clone_dir):
    tmp = tempfile.mkdtemp()
    try:
        # set up isolated project structure
        src_dir = os.path.join(tmp, "src_module")
        test_dir = os.path.join(tmp, "tests")
        os.makedirs(src_dir)
        os.makedirs(test_dir)

        # copy function file into src_module
        fn_basename = os.path.basename(function_file)
        fn_dest = os.path.join(src_dir, fn_basename)
        shutil.copy2(function_file, fn_dest)

        # write __init__.py so it's importable
        open(os.path.join(src_dir, "__init__.py"), "w").close()

        # copy test file into tests
        test_basename = os.path.basename(test_file)
        test_dest = os.path.join(test_dir, test_basename)
        shutil.copy2(test_file, test_dest)

        # build PYTHONPATH so the test can import the original repo
        env = os.environ.copy()
        paths = [tmp, repo_clone_dir]
        existing = env.get("PYTHONPATH", "")
        if existing:
            paths.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(paths)

        # remove any leftover mutmut cache
        cache_path = os.path.join(tmp, ".mutmut-cache")
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)

        # run mutmut
        result = subprocess.run(
            [
                sys.executable, "-m", "mutmut", "run",
                "--paths-to-mutate", fn_dest,
                "--tests-dir", test_dir,
                "--no-progress",
            ],
            capture_output=True, text=True, env=env, cwd=tmp,
            timeout=MUTMUT_TIMEOUT,
        )

        # parse results using mutmut json output
        killed = set()
        survived = set()
        total = 0

        try:
            jresult = subprocess.run(
                [sys.executable, "-m", "mutmut", "results"],
                capture_output=True, text=True, env=env, cwd=tmp,
                timeout=30,
            )
            output = jresult.stdout

            # parse mutmut results output
            # format is like:
            # Survived mutants (IDs): 1, 2, 3
            # Killed mutants (IDs): 4, 5, 6
            section = None
            for line in output.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if "survived" in line.lower() or "Survived" in line:
                    section = "survived"
                    continue
                if "killed" in line.lower() or "Killed" in line:
                    section = "killed"
                    continue
                if "timeout" in line.lower() or "suspicious" in line.lower():
                    section = "other"
                    continue

                # try to extract mutant IDs from lines
                for part in line.replace(",", " ").split():
                    part = part.strip()
                    if part.isdigit():
                        mid = int(part)
                        total += 1
                        if section == "killed":
                            killed.add(mid)
                        elif section == "survived":
                            survived.add(mid)

        except (subprocess.TimeoutExpired, Exception):
            pass

        # fallback: parse from the run output if results command gave nothing
        if not killed and not survived:
            for line in result.stdout.split("\n"):
                if "mutants killed" in line.lower() or "killed" in line.lower():
                    pass  # basic output parsing as fallback

        if total == 0:
            total = len(killed) + len(survived)

        return {
            "total_mutants": total,
            "killed": killed,
            "survived": survived,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "total_mutants": 0,
            "killed": set(),
            "survived": set(),
            "stdout": "",
            "stderr": "mutmut timed out",
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def compute_unique_kills(all_agent_kills):
    # all_agent_kills = {"statement": {1,3,5}, "block": {1,2}, ...}
    result = {}
    agents = list(all_agent_kills.keys())
    for agent in agents:
        others = set()
        for other_agent in agents:
            if other_agent != agent:
                others |= all_agent_kills[other_agent]
        unique = all_agent_kills[agent] - others
        result[agent] = len(unique)
    return result
