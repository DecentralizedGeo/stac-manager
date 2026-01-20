import os
import sys
import glob
from pathlib import Path

# Add src to pythonpath so we can import the module
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from stac_manager.cli import main as cli_main

def main():
    root_dir = current_dir.parent
    examples_dir = root_dir / "examples"
    
    # Find all yaml files in examples, recursively
    files = sorted(list(examples_dir.rglob("*.yaml")))
    
    if not files:
        print("No configuration files found in examples/")
        sys.exit(1)
        
    print("\nSelect a configuration file to debug:\n")
    for i, f in enumerate(files):
        # Show relative path from project root for clarity
        rel_path = f.relative_to(root_dir)
        print(f"  [{i + 1}] {rel_path}")
        
    print()
    try:
        choice = input("Enter number (default 1): ").strip()
        if not choice:
            choice = "1"
        idx = int(choice) - 1
        if idx < 0 or idx >= len(files):
            print("Invalid selection.")
            sys.exit(1)
            
        selected_file = files[idx]
        print(f"\nLaunching: {selected_file}\n" + "-"*40 + "\n")
        
        # Set up sys.argv for Click
        # program_name command arg
        sys.argv = ["stac-manager", "run", str(selected_file)]
        
        # Run the CLI
        cli_main()
        
    except ValueError:
        print("Invalid input. Please enter a number.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
