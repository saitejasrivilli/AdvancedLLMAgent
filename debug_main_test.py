from src.main import main_workflow, get_problem_and_code_from_taskpath, get_unit_tests_from_taskpath
from src.lean_runner import execute_lean_code
import os
import time

task_id = "task_id_0"
task_path = os.path.join("tasks", task_id)
print(f"Processing {task_id}...")

# Load description & template
desc, template = get_problem_and_code_from_taskpath(task_path)
tests = get_unit_tests_from_taskpath(task_path)

# Run main workflow
start = time.time()
solution = main_workflow(desc, template)
elapsed = time.time() - start

code = solution["code"]
# Skip proof for now
lean_code = template.replace("{{code}}", code).replace("{{proof}}", "sorry") + "\n" + tests

print("\n=== Final Code ===\n")
print(lean_code)

# Run Lean
success, msg = execute_lean_code(lean_code)
print("\n=== Execution Result ===")
print("✅ PASS" if success else "❌ FAIL")
print(msg)
print(f"⏱ Runtime: {elapsed:.2f}s")
