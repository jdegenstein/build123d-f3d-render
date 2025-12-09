import os
import subprocess
import importlib.util
from pathlib import Path
from build123d import *

def render_with_f3d(file_path):
    print(f"Processing {file_path}...")
    
    # 1. Load the user's script dynamically
    spec = importlib.util.spec_from_file_location("user_model", file_path)
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"  [!] Failed to execute script: {e}")
        return

    # 2. Find the object (part, assembly, or sketch)
    render_target = None
    for name in ['to_export', 'part', 'assembly', 'sketch', 'line']:
        if hasattr(module, name):
            render_target = getattr(module, name)
            break
            
    if not render_target:
        print("  [!] No renderable object found.")
        return

    # 3. Export to STEP (Critical for wires/edges)
    #    STEP preserves exact curves, unlike STL which meshes them.
    temp_step = "temp_render.step"
    try:
        export_step(render_target, temp_step)
        
        # 4. Run F3D Headless
        output_png = file_path.with_suffix('.png')
        
        # F3D Command Line Flags:
        # --output: Where to save
        # --resolution: Image size
        # --samples: Anti-aliasing quality (higher is better)
        # --up: Camera orientation (Z-up is standard for build123d)
        cmd = [
            "f3d", temp_step,
            f"--output={output_png}",
            "--resolution=1024,768",
            "--samples=16", 
            "--up=+Z",
            "--verbose=quiet" 
        ]
        
        subprocess.run(cmd, check=True)
        print(f"  [+] Saved render to {output_png}")
        
    except Exception as e:
        print(f"  [!] Render failed: {e}")
    finally:
        if os.path.exists(temp_step):
            os.remove(temp_step)

def main():
    repo_root = Path(".")
    for root, dirs, files in os.walk(repo_root):
        if ".git" in root or ".github" in root:
            continue
        for file in files:
            if file.endswith(".py") and file != "setup.py":
                render_with_f3d(Path(root) / file)

if __name__ == "__main__":
    main()
