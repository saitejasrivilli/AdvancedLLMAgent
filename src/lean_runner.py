import subprocess
import os
import time
import logging

logger = logging.getLogger(__name__)

def execute_lean_code(code: str) -> tuple[bool, str]:
    """
    Executes Lean code using `lean`, returning (success_flag, message).
    """
    temp_file = "TempTest.lean"
    temp_path = os.path.join("lean_playground", temp_file)
    os.makedirs("lean_playground", exist_ok=True)

    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(code)

    logger.debug(f"[DEBUG] Executing Lean on: {temp_path}")
    start = time.time()
    try:
        result = subprocess.run(
            ["lean", temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        end = time.time()
        logger.debug(f"[DEBUG] Lean execution completed in {end - start:.2f}s")

        if result.returncode == 0:
            return True, result.stdout.strip() or "Lean executed successfully."
        return False, result.stderr.strip() or result.stdout.strip()

    except FileNotFoundError:
        return False, "Lean is not installed or not in PATH."
    except subprocess.TimeoutExpired:
        return False, "Lean execution timed out."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
