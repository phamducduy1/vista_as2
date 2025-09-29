import os
import importlib

def run_scripts_in_order(scripts):
    for script in scripts:
        if script != 'main.py' and script.endswith('.py'):
            module_name = script[:-3]
            print(f"Running {script}...")
            module = importlib.import_module(module_name)
            if hasattr(module, 'main'):
                module.main()
            else:
                print(f"No main() function found in {script}")

if __name__ == "__main__":
    # List of scripts to run in order
    scripts_to_run = [
        'preprocessing.py',
        'learning.py'
        # Add more scripts here as needed
    ]
    run_scripts_in_order(scripts_to_run)