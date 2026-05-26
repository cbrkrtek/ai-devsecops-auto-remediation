import subprocess
import time

def verify_container_runtime(dockerfile_path: str, image_tag: str = "tmp_remediated_img") -> str:
    build_cmd = ["docker", "build", "-t", image_tag, "-f", dockerfile_path, "."]
    build_res = subprocess.run(build_cmd, capture_output=True, text=True)
    
    if build_res.returncode != 0:
        return f"BUILD_ERROR: Dockerfile failed to compile!\nStderr:\n{build_res.stderr}"

    container_name = "tmp_sandbox_container"
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
    
    run_cmd = ["docker", "run", "-d", "--name", container_name, image_tag]
    run_res = subprocess.run(run_cmd, capture_output=True, text=True)
    
    if run_res.returncode != 0:
        return f"RUNTIME_ERROR: Container failed to start!\nStderr:\n{run_res.stderr}"

    time.sleep(5)

    status_cmd = ["docker", "inspect", "-f", "{{.State.Running}}", container_name]
    status_res = subprocess.run(status_cmd, capture_output=True, text=True)
    is_running = status_res.stdout.strip() == "true"

    logs_cmd = ["docker", "logs", container_name]
    logs_res = subprocess.run(logs_cmd, capture_output=True, text=True)
    container_logs = logs_res.stderr + "\n" + logs_res.stdout

    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)

    if not is_running:
        return (
            f"CRITICAL RUNTIME CRASH DETECTED!\n"
            f"The container exited unexpectedly. Real container OS logs:\n"
            f"--- START OF LOGS ---\n{container_logs}\n--- END OF LOGS ---\n"
            f"FIX ACTION: Analyze the logs above (such as 'Permission denied' or 'Missing file'), "
            f"identify which directories or files lack permissions under your non-root USER context, "
            f"and fix the permissions using 'RUN chown/chmod' while still in the root context (PHASE 1)."
        )
        
    if "permission denied" in container_logs.lower() or "could not open" in container_logs.lower():
        return f"POTENTIAL RUNTIME ISSUE (Permission Denied detected in logs):\n{container_logs}"

    return "" 