import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from remediator import generate_fix, clean_ai_response

def main():
    print("Executed automatic check Dockerfile...")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    input_dockerfile = os.path.join(BASE_DIR, "tests", "vulnerable.Dockerfile")
    trivy_report = os.path.join(BASE_DIR, "tests", "trivy_report.json")
    output_dockerfile = os.path.join(BASE_DIR, "tests", "fixed.Dockerfile")
    
    if not os.path.exists(input_dockerfile) or not os.path.exists(trivy_report):
        print("Error: can't find Dockerfile or Trivy files")
        return
    raw_response = generate_fix(input_dockerfile, trivy_report)
    final_code = clean_ai_response(raw_response)    
    try:
        with open(output_dockerfile, "w", encoding="utf-8") as f:
            f.write(final_code)
        print("\n" + "="*50)
        print(f"Success!!! output dockerfile has saved in:")
        print(f"👉 {output_dockerfile}")
        print("="*50)
    except Exception as e:
        print(f"Error to write{e}")
if __name__ == "__main__":
    main()