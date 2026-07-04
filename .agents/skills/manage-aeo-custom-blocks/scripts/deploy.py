import os
import subprocess
import sys

# Get root directory of project relative to this script
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))

print("[*] Running custom block deploy from skill script...")
try:
    # Run npm run build in app/custom_blocks
    blocks_dir = os.path.join(project_root, "app", "custom_blocks")
    subprocess.check_call("npm run build", shell=True, cwd=blocks_dir)

    # Run deploy_blocks.py in project root
    subprocess.check_call("python app/deploy_blocks.py", shell=True, cwd=project_root)
    print("[SUCCESS] Blocks successfully compiled and deployed.")
    sys.exit(0)
except Exception as e:
    print(f"[ERROR] Deployment failed: {e}")
    sys.exit(1)
