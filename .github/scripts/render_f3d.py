import os
import subprocess
import importlib.util
from pathlib import Path
from build123d import * # Import everything to check types

def get_renderable_object(module):
    """
    Intelligently find the object to export.
    Priority:
    1. Explicit 'to_export' variable
    2. Explicit 'result', 'part', or 'assembly' variable
    3. The last variable defined that is a valid Shape or Sketch
    """
    # 1. Check for explicit overrides first (Convention over Configuration)
    for name in ['to_export', 'result', 'part', 'assembly']:
        if hasattr(module, name):
            candidate = getattr(module, name)
            if isinstance(candidate, (Shape, Sketch)):
                return candidate

    # 2. Dynamic Discovery: Scan all variables in the module
    #    This catches 'my_custom_gear = ...'
    candidates = []
    for name, obj in vars(module).items():
        # Skip private/dunder variables and imports (modules)
        if name.startswith("_") or isinstance(obj, type(os)):
            continue
            
        # Check if it's a build123d topology object
        # Shape covers: Solid, Compound, Wire, Edge, Vertex, etc.
        if isinstance(obj, (Shape, Sketch)):
            candidates.append(obj)
            
    if candidates:
        # Return the last valid object found.
        # In Python scripts, the final result is usually defined last.
        return candidates[-1]
        
    return None

def render_with_f3d(file_path):
    print(f"Processing {file_path}...")
    
    spec = importlib.util.spec_from_file_location("user_model", file_path)
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"  [!] Failed to execute script: {e}")
        return

    render_target = get_renderable_object(module)
            
    if not render_target:
        print("  [!] No 3D shape found in script.")
        return

    # Export to STEP (Preserves curves/wires)
    temp_step = "temp_render.step"
    try:
        export_step(render_target, temp_step)
        
        output_png = file_path.with_suffix('.png')
        
        # F3D Render Command
        cmd = [
            "f3d", temp_step,
            f"--output={output_png}",
            "--resolution=1024,768",
            "--samples=32", 
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
    ignored_dirs = {'.git', '.github', '.venv', 'venv', '__pycache__'}

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        
        for file in files:
            if file.endswith(".py") and file != "setup.py":
                render_with_f3d(Path(root) / file)

if __name__ == "__main__":
    main()
