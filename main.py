import os
import sys
import subprocess
import glob

sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from remediator import generate_fix, clean_ai_response

def run_trivy_scan(target_file: str, report_output: str) -> bool:
    print(f"Scanning file: {os.path.basename(target_file)}...")
    
    
    command = [
        "trivy", "config", 
        "--format", "json", 
        "--output", report_output, 
        target_file
    ]
    
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError:
        if os.path.exists(report_output):
            return True
        return False
    except FileNotFoundError:
        print("Can't find Trivy, check PATH")
        sys.exit(1)

def main():
    print("START")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(BASE_DIR, "tests")
    fixed_dir = os.path.join(BASE_DIR, "fixed")
    
    os.makedirs(fixed_dir, exist_ok=True)
    
    dockerfiles = []
    for file_path in glob.glob(os.path.join(source_dir, "*")):
        filename = os.path.basename(file_path).lower()
        if "dockerfile" in filename and not filename.endswith(".json"):
            dockerfiles.append(file_path)
            
    if not dockerfiles:
        print(f"In directory '{os.path.relpath(source_dir, BASE_DIR)}' can't find Dockerfiles for analysis")
        return

    print(f"Found files: {len(dockerfiles)}")
    print(f"Directory to store fixed files: {os.path.relpath(fixed_dir, BASE_DIR)}\n")

    for input_file in dockerfiles:
        filename = os.path.basename(input_file)
        print(f"ANALYSE: {filename}")
        print("-" * 60)
        
        report_name = f"trivy_report_{filename}.json"
        trivy_report_path = os.path.join(source_dir, report_name)
        
        if not run_trivy_scan(input_file, trivy_report_path):
            print(f"Can't find a security report for  {filename}. Skipping...")
            continue
        print(f"Report has created successfully {report_name}")
        
        
        raw_response = generate_fix(input_file, trivy_report_path)
        final_code = clean_ai_response(raw_response)
        
        output_file_path = os.path.join(fixed_dir, filename)
        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(final_code)
            print(f"Secure file has writen in fixed/{filename}\n")
        except Exception as e:
            print(f"Can't save a file{filename}: {e}\n")
    print("🎯 All configurations have been scanned and corrected!!!")
if __name__ == "__main__":
    main()