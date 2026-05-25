import os
import sys
import glob
import json
import shutil

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))

from core.ast_builder import build_dockerfile_ast
from core.parser import parse_trivy_report, parse_hadolint_results
from core.scanner import run_trivy_scan, run_hadolint_scan
from core.client import query_local_llm

MAX_ITERATIONS = 5

def load_file_content(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    print("============================================================")
    print("🔄 STARTING: Hybrid Auto-Remediation Pipeline (Trivy + Hadolint)")
    print("============================================================")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(BASE_DIR, "tests")
    fixed_dir = os.path.join(BASE_DIR, "fixed")
    tmp_dir = os.path.join(BASE_DIR, "tmp")
    
    os.makedirs(fixed_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    
    dockerfiles = [f for f in glob.glob(os.path.join(source_dir, "*")) if "dockerfile" in os.path.basename(f).lower() and not f.endswith(".json")]

    for input_file in dockerfiles:
        filename = os.path.basename(input_file)
        print(f"\n🎯 TARGET: {filename}")
        
        current_code = load_file_content(input_file)
        current_ast = build_dockerfile_ast(current_code)
        is_successfully_healed = False
        
        for iteration in range(1, MAX_ITERATIONS + 1):
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
            print(f"  🛡️  Current issues count: {len(all_vulnerabilities)} (Trivy: {len(trivy_vulns)}, Linter: {len(linter_vulns)})")
            
            if len(all_vulnerabilities) == 0:
                print(f"  🎉 Perfect state reached at step #{iteration}! Code is secure AND functional.")
                is_successfully_healed = True
                break
                
            if iteration == MAX_ITERATIONS:
                print("  ⚠️  Reached maximum allowed iterations. Exiting loop.")
                break
                
            system_instruction = (
                "You are an advanced, autonomous DevSecOps Engineering Agent specialized in automated container remediation.\n"
                "Your mission is to resolve security vulnerabilities and static analysis violations in Dockerfiles by applying industry-standard container hardening and strict POSIX operational logic.\n\n"
                
                "CONTEXT & OBJECTIVE:\n"
                "You will receive a raw Dockerfile, its current Abstract Syntax Tree (AST), and a consolidated report of issues from security scanners (Trivy) and linters (Hadolint).\n"
                "You must refactor the Dockerfile to eliminate ALL reported issues while simultaneously generating a precise, matching updated AST that reflects your architectural modifications.\n\n"
                
                "CORE ARCHITECTURAL CONSTRAINTS:\n"
                "1. Functional Parity: Maintain the original application's core intent, multi-stage layout, environment variables, network configurations (EXPOSE), and operational entrypoints (CMD/ENTRYPOINT).\n"
                
                "2. STRICT INSTRUCTION ORDERING (CHRONOLOGICAL RUNTIME LOGIC):\n"
                "   You must structure the Dockerfile layers following a logical, chronologically accurate build lifecycle:\n"
                "   - PHASE 1 (PRIVILEGED ROOT CONTEXT): Execute all system mutations, 'apt-get/apk/yum' updates, package installations, group/user creations ('useradd/groupadd'), and filesystem permission modifications ('chown/chmod') while the builder context is still implicitly or explicitly 'root'.\n"
                "   - PHASE 2 (CONTEXT DOWNGRADE): The 'USER <username>' directive MUST only be declared AFTER Phase 1 is completely finished. NEVER place 'USER' before the 'RUN useradd' command that creates that specific user. A user cannot be invoked or execute commands before it physically exists in /etc/passwd.\n"
                "   - PHASE 3 (NON-PRIVILEGED CONTEXT): Place runtime configurations, WORKDIR definitions, and build artifacts copying (COPY/ADD) that belong to the application layer AFTER the 'USER' directive.\n"
                
                "3. Principle of Least Privilege: Enforce non-root execution targets. However, ensure that any directories the non-root user needs to read, write, or execute (e.g., Nginx cache dirs, logs, application roots) have their ownership correctly modified via 'chown -R' inside PHASE 1 BEFORE transitioning to the 'USER' context.\n"
                "4. Layer Hygiene & Minimization: Consolidate related package operations into single, atomic 'RUN' layers. Always bundle installation directives with explicit metadata cleanup routines (e.g., removing caches, indexes, and lock files) in the exact same layer to reduce image bloating.\n"
                "5. Supply Chain Trust: Avoid mutable image reference patterns (such as pinning strictly to 'latest' tags) where specific architecture definitions or immutability are required by security policies.\n\n"
                
                "STRICT OUTPUT SPECIFICATION:\n"
                "You must respond exclusively with a valid, parsable JSON object containing exactly two root keys:\n"
                "  - 'remediated_dockerfile': A single continuous string containing ONLY the raw, refactored, compilable Dockerfile code lines.\n"
                "  - 'generated_ast': A structured JSON object representing the exact new Abstract Syntax Tree that matches the updated Dockerfile structure.\n"
                "CRITICAL: Do NOT wrap the JSON or its values in markdown blocks (no triple backticks ```). Do NOT include any introductory greetings, markdown prose, annotations, or conversational footers."
            )
            
            user_context = {
                "loop_iteration": iteration,
                "detected_issues_to_patch": all_vulnerabilities,
                "current_source_code": current_code,
                "current_ast_tree": json.loads(current_ast)
            }
            
            ai_response = query_local_llm(system_instruction, json.dumps(user_context, ensure_ascii=False))
            
            next_code = ai_response.get("remediated_dockerfile", "")
            next_ast = ai_response.get("generated_ast", {})
            
            if not next_code or not next_ast:
                print("  ❌ LLM Response Format Error (Empty code or AST). Breaking loop.")
                break
                
            current_code = next_code
            current_ast = json.dumps(next_ast)
        
        output_file_path = os.path.join(fixed_dir, filename)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(current_code.strip())
        
        status = "SUCCESS" if is_successfully_healed else "PARTIAL"
        print(f"✅ Processing {filename} finished with status: {status}")

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    print("\n🎯 Pipeline finished execution successfully!")

if __name__ == "__main__":
    main()