import os
import sys
import glob
import json
import re

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))

from core.ast_builder import build_dockerfile_ast
from core.parser import parse_trivy_report, parse_hadolint_results
from core.scanner import run_trivy_scan, run_hadolint_scan
from core.client import query_local_llm
from core.sandbox import verify_container_runtime

MAX_ALLOWED_ATTEMPTS = 10

def load_file_content(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def analyze_structural_constraints(dockerfile_code: str) -> str:
    lines = dockerfile_code.split('\n')
    current_user = "root"  
    users_created = set()
    exposed_privileged_ports = []
    errors = []

    for idx, line in enumerate(lines, 1):
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#"): 
            continue
            
        if clean_line.startswith("RUN"):
            created = re.findall(r'(?:useradd|adduser)\s+(?:-[a-zA-Z0-9/-]+\s+)*([a-zA-Z0-9_-]+)', clean_line)
            for user in created:
                if not user.startswith('-'): 
                    users_created.add(user)

        if clean_line.startswith("EXPOSE"):
            ports = re.findall(r'\d+', clean_line)
            for port in ports:
                if int(port) < 1024: 
                    exposed_privileged_ports.append(port)

        if clean_line.startswith("USER"):
            target_user = clean_line.replace("USER", "").strip()
            if target_user and target_user not in ["root", "0", "1000", "nobody"] and not target_user.isdigit():
                if target_user not in users_created:
                    errors.append(f"Line {idx}: Chronological violation! USER '{target_user}' used before creation.")
            current_user = target_user

    if current_user != "root" and exposed_privileged_ports:
        errors.append(
            f"CRITICAL NETWORK PRIVILEGE VIOLATION: Non-root user '{current_user}' cannot bind privileged ports {exposed_privileged_ports}. "
            f"Change EXPOSE and application configurations to use non-privileged ports (e.g., 8080 instead of 80)."
        )
            
    return "\n".join(errors) if errors else ""
#start
def main():
    print("===============================================================")
    print("🔄 STARTING: Universal Autonomous Self-Healing Pipeline (While-Loop Guarded)")
    print("===============================================================")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(BASE_DIR, "tests")
    fixed_dir = os.path.join(BASE_DIR, "fixed")
    tmp_dir = os.path.join(BASE_DIR, "tmp")
    
    os.makedirs(fixed_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    
    dockerfiles = [f for f in glob.glob(os.path.join(source_dir, "*")) if "dockerfile" in os.path.basename(f).lower() and not f.endswith(".json")]

    for input_file in dockerfiles:
        filename = os.path.basename(input_file)
        print(f"\n🎯 TARGET FILE: {filename}")
        
        current_code = load_file_content(input_file)
        is_successfully_healed = False
        
        previous_issues_count = None
        stagnation_counter = 0
        iteration = 0
        need_remediation = True
        
        while need_remediation:
            iteration += 1
            print(f"  🌀 Loop Step #{iteration}...")
            
            tmp_dockerfile_path = os.path.join(tmp_dir, f"tmp_{filename}")
            tmp_report_path = os.path.join(tmp_dir, f"tmp_report_{filename}.json")
            
            with open(tmp_dockerfile_path, "w", encoding="utf-8") as f:
                f.write(current_code)
                
            run_trivy_scan(tmp_dockerfile_path, tmp_report_path)
            trivy_vulns = parse_trivy_report(tmp_report_path)
            
            hadolint_raw = run_hadolint_scan(tmp_dockerfile_path)
            linter_vulns = parse_hadolint_results(hadolint_raw)
            
            all_vulnerabilities = trivy_vulns + linter_vulns
            current_issues_count = len(all_vulnerabilities)
            
            print(f"  🛡️  Current issues: {current_issues_count} (Trivy: {len(trivy_vulns)}, Linter: {len(linter_vulns)})")
            if current_issues_count > 0:
                print(f"     👉 Target issues IDs to fix: {[issue['id'] for issue in all_vulnerabilities]}")
            
            structural_critique = analyze_structural_constraints(current_code)
            if structural_critique:
                print(f"  ⚠️ Static Structural Issues Found:\n{structural_critique}")
            
            print("  🧪 Running sandbox runtime execution test...")
            runtime_logs_critique = verify_container_runtime(tmp_dockerfile_path, image_tag=f"remediate_test_{iteration}")
            
            
            if current_issues_count == 0 and not structural_critique and not runtime_logs_critique:
                print(f"  🎉 Perfect state reached at step #{iteration}!")
                is_successfully_healed = True
                need_remediation = False
                break
                
            if previous_issues_count is not None and current_issues_count == previous_issues_count:
                stagnation_counter += 1
                if stagnation_counter >= 2:
                    print(f"  ⚠️ Stagnation detected (Issues count stalled at {current_issues_count}).")
                    if current_issues_count == 0 and not structural_critique:
                        print("  🎉 Security and Linting goals achieved! Accepting final state despite runtime container warnings.")
                        is_successfully_healed = True
                    else:
                        print("  ❌ Deadlock reached: AI cannot resolve remaining security issues.")
                        is_successfully_healed = False
                    need_remediation = False
                    break
            else:
                stagnation_counter = 0
                
            previous_issues_count = current_issues_count

            if iteration >= MAX_ALLOWED_ATTEMPTS:
                print(f"  🚨 Safety Guardrail: Reached max limit of {MAX_ALLOWED_ATTEMPTS} attempts. Forcing loop break.")
                is_successfully_healed = (current_issues_count == 0 and not structural_critique)
                need_remediation = False
                break


            try:
                current_ast_obj = build_dockerfile_ast(current_code)
            except Exception:
                current_ast_obj = {"type": "Dockerfile_AST", "nodes": []}
                
            system_instruction = (
                "You are an advanced, autonomous DevSecOps Engineering Agent specialized in automated container remediation.\n"
                "Your mission is to resolve security vulnerabilities, static analysis violations, and runtime operational crashes in Dockerfiles by applying industry-standard container hardening and strict POSIX file-system logic.\n\n"
                "CONTEXT & OBJECTIVE:\n"
                "You will receive a raw Dockerfile, its current Abstract Syntax Tree (AST), static scanner issues, and real operating system stderr/crash logs from a sandbox runtime execution environment.\n"
                "You must refactor the Dockerfile to eliminate ALL reported issues, resolve security vulnerabilities, and ensure the container process successfully initializes without permission flags or runtime crashes.\n\n"
                "CORE ARCHITECTURAL CONSTRAINTS:\n"
                "1. Functional Parity: Maintain the original application's core intent, multi-stage layout, environment variables, and operational entrypoints (CMD/ENTRYPOINT).\n"
                "2. Network & Web Server Adjustment: If you transition the container to a non-root USER, ports < 1024 cannot be bound. You MUST update 'EXPOSE' to a non-privileged port (e.g., 8080) and inject commands (like sed) to modify application configurations (e.g., internal Nginx config files) to use that exact same port.\n"
                "3. STRICT INSTRUCTION ORDERING (Lifecycle Phases):\n"
                "   - PHASE 1 (PRIVILEGED ROOT CONTEXT): Execute all system mutations, package installations, group/user creations, and directory permission modifications (e.g., 'chown -R user:group /path') while the execution context is 'root'.\n"
                "   - PHASE 2 (CONTEXT DOWNGRADE): Declare the 'USER <username>' directive strictly AFTER Phase 1 is completely finalized.\n"
                "   - PHASE 3 (NON-PRIVILEGED CONTEXT): Place runtime configurations, WORKDIR definitions, and build artifacts copying (COPY/ADD) AFTER the 'USER' directive.\n"
                "4. Operational Viability: If the runtime crash logs indicate that the application fails to write to files, access caches, or open sockets due to 'Permission Denied', you MUST add necessary 'chown/chmod' adjustments inside PHASE 1 (while still root) for those specific system paths (e.g., for nginx: /var/log/nginx, /var/lib/nginx, /run) before switching users.\n"
                "5. Principle of Least Privilege: Enforce non-root execution targets. Avoid generic 'nobody' accounts; create application-specific system users instead.\n\n"
                "STRICT OUTPUT SPECIFICATION:\n"
                "You must respond exclusively with a valid JSON object containing exactly ONE root key:\n"
                "  - 'remediated_dockerfile': A single continuous string containing ONLY the raw, refactored, compilable Dockerfile code lines. Escape any internal newlines as '\\n'.\n"
                "CRITICAL: Do NOT wrap the JSON or its values in markdown blocks (no triple backticks). Do NOT include any introductory greetings or conversational footers."
            )
            
            user_context = {
                "loop_iteration": iteration,
                "static_structural_critique": structural_critique,
                "runtime_sandbox_crash_logs": runtime_logs_critique,
                "detected_scanner_issues": all_vulnerabilities,
                "current_source_code": current_code,
                "current_ast_tree": current_ast_obj
            }
            
            ai_response = query_local_llm(system_instruction, json.dumps(user_context, ensure_ascii=False))
            next_code = ai_response.get("remediated_dockerfile", "")
            
            if not next_code:
                print("  ❌ LLM Response Format Error (Empty code or invalid JSON structure). Breaking loop.")
                break
                
            try:
                next_ast_obj = build_dockerfile_ast(next_code)
                if not next_ast_obj.get("nodes") or len(next_ast_obj["nodes"]) == 0:
                    print("  ⚠️ Guardrail Warning: LLM generated structurally unparsable code. Reverting.")
                    break
                
                has_from = any(node["instruction"] == "FROM" for node in next_ast_obj["nodes"])
                if not has_from:
                    print("  ⚠️ Guardrail Warning: LLM removed the base image ('FROM'). Rejecting changes.")
                    break
                    
            except Exception as e:
                print(f"  ❌ Guardrail Exception: Structural AST verification failed: {e}")
                break
                
            current_code = next_code
        
        if is_successfully_healed:
            output_file_path = os.path.join(fixed_dir, filename)
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(current_code.strip())
            print(f"✅ Processing {filename} finished with status: SUCCESS")
        else:
            print(f"❌ Processing {filename} finished with status: FAILED")
            failed_file_path = os.path.join(fixed_dir, f"FAILED_{filename}")
            with open(failed_file_path, "w", encoding="utf-8") as f:
                f.write(current_code.strip())

if __name__ == "__main__":
    main()