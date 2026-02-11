"""
AI Test Executor Agent (Direct Execution, No Input)
==================================================
Automatically executes generated tests using unittest.
"""

import os
import time
import subprocess
import shlex
PROJECT_PATH = os.path.dirname(__file__)
TIMEOUT_S = 90 


class TestExecutorAgent:
    def __init__(self, project_path: str, timeout_s: int = 90):
        self.project_path = os.path.abspath(project_path)
        self.timeout_s = timeout_s

    def _tests_exist(self) -> bool:
        """Check if generated test files exist in project."""
        test_dirs = [
            self.project_path,
            os.path.join(self.project_path, "generated_tests"),
            os.path.join(self.project_path, "tests"),
        ]
        for tdir in test_dirs:
            if os.path.isdir(tdir):
                for file in os.listdir(tdir):
                    if file.startswith("test_") and file.endswith(".py"):
                        return True
            else:
                print(f" Test directory not found: {tdir}")
        return False

    def execute_tests(self):
        """Execute tests directly using unittest (no input required)."""
        print(f"\n [AI Agent] Starting direct test execution for: {self.project_path}")

        if not os.path.exists(self.project_path):
            print(" Error: Project path does not exist.")
            return {"status": "error", "message": "Invalid project path"}

        if not self._tests_exist():
            print(" No test files found — skipping test execution.")
            return {"status": "skipped", "message": "No tests found"}

        # Ensure report directory exists
        report_dir = os.path.join(self.project_path, "report")
        os.makedirs(report_dir, exist_ok=True)
        log_path = os.path.join(report_dir, "unittest_output.log")

        # Run unittest discover for all generated tests
        cmd = "python -m unittest discover -s . -p 'test_*.py'"
        print(f" Running command: {cmd}")

        start_time = time.time()
        try:
            result = subprocess.run(
                shlex.split(cmd),
                cwd=self.project_path,
                timeout=self.timeout_s,
                capture_output=True,
                text=True,
            )

            # Save logs
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(result.stdout)
                f.write("\n" + result.stderr)

            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            exit_code = result.returncode
            elapsed = time.time() - start_time

            print(f"Tests finished with exit code: {exit_code}")
            print(f"Log saved to: {log_path}")

            result_data = {
                "status": "success" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "time_taken": round(elapsed, 2),
                "log_report": log_path,
            }

            print(f"\n [AI Agent Summary]")
            print(f"   Status: {result_data['status']}")
            print(f"   Exit Code: {exit_code}")
            print(f"   Time Taken: {result_data['time_taken']}s")
            print(f"   Log Report: {result_data['log_report']}")

            return result_data

        except subprocess.TimeoutExpired:
            print(f" Test execution timed out after {self.timeout_s}s.")
            return {"status": "timeout", "message": "Execution timed out"}
        except Exception as e:
            print(f" Error running tests: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    agent = TestExecutorAgent(PROJECT_PATH, timeout_s=TIMEOUT_S)
    summary = agent.execute_tests()
    print("\nFinal Summary:", summary)