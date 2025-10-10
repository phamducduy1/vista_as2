import importlib

def run_scripts_in_order(scripts):
    for script in scripts:
        if script != 'main.py' and script.endswith('.py'):
            # Handle modules in subdirectories
            module_name = script.replace('/', '.').replace('.py', '')
            print(f"Running {script}...")
            module = importlib.import_module(module_name)
            if hasattr(module, 'main'):
                module.main()
            else:
                print(f"No main() function found in {script}")

if __name__ == "__main__":
    scripts_to_run = [
        'models.py', 
        'preprocess.py',
        'data_clustering.py',
        'analysis/corr_matrix_min.py',
        'analysis/correlation_min.py'
    ]
    run_scripts_in_order(scripts_to_run)