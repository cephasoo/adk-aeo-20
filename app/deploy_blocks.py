import os
import shutil
import subprocess
import sys

# Define source and destination paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKS_SRC_DIR = os.path.join(PROJECT_ROOT, "app", "custom_blocks")
WP_PLUGIN_DEST_DIR = r"C:\Users\USER\Local Sites\aeo-copilot\app\public\wp-content\plugins\aeo-custom-blocks"

print("="*60)
print("[*] STARTING GUTENBERG BLOCK BUILD AND DEPLOYMENT PIPELINE")
print(f" - Blocks Source Directory: {BLOCKS_SRC_DIR}")
print(f" - LocalWP Target Directory: {WP_PLUGIN_DEST_DIR}")
print("="*60)

# Step 1: Run npm install
print("\n[*] Step 1: Installing npm dependencies...")
try:
    # Use shell=True for Windows compatibility
    result = subprocess.run(
        ["npm", "install"],
        cwd=BLOCKS_SRC_DIR,
        shell=True,
        check=True,
        capture_output=True,
        text=True
    )
    print(" [OK] npm dependencies installed successfully.")
except subprocess.CalledProcessError as e:
    print(f" [ERROR] FAILED to install npm dependencies:\n{e.stderr}")
    sys.exit(1)

# Step 2: Run npm run build
print("\n[*] Step 2: Compiling React blocks using @wordpress/scripts...")
try:
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=BLOCKS_SRC_DIR,
        shell=True,
        check=True,
        capture_output=True,
        text=True
    )
    print(" [OK] React blocks compiled successfully.")
except subprocess.CalledProcessError as e:
    print(f" [ERROR] FAILED to compile blocks:\n{e.stderr}")
    sys.exit(1)

# Step 3: Copy to LocalWP Plugins Folder
print("\n[*] Step 3: Copying files to LocalWP plugins directory...")
try:
    if os.path.exists(WP_PLUGIN_DEST_DIR):
        print(f" - Clearing existing destination: {WP_PLUGIN_DEST_DIR}")
        shutil.rmtree(WP_PLUGIN_DEST_DIR)

    os.makedirs(WP_PLUGIN_DEST_DIR, exist_ok=True)

    # Copy main plugin file
    shutil.copy2(
        os.path.join(BLOCKS_SRC_DIR, "aeo-custom-blocks.php"),
        os.path.join(WP_PLUGIN_DEST_DIR, "aeo-custom-blocks.php")
    )

    # Copy build folder recursively
    shutil.copytree(
        os.path.join(BLOCKS_SRC_DIR, "build"),
        os.path.join(WP_PLUGIN_DEST_DIR, "build")
    )

    print(" [OK] Files copied successfully.")
except Exception as e:
    print(f" [ERROR] FAILED to copy files: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("[SUCCESS] Custom blocks have been compiled and deployed.")
print("Action Required: Go to your WP dashboard (Plugins page) and activate 'AEO Custom Blocks'.")
print("="*60)
