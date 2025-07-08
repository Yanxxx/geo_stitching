import os
import argparse
import yaml
import shutil

# The root directory for all raw data
DATA_ROOT = 'data'

def init_project(project_name):
    """
    Initializes a new project directory structure and configuration file.
    
    Args:
        project_name (str): The name for the new project.
    """
    project_path = os.path.join(DATA_ROOT, project_name)
    
    if os.path.exists(project_path):
        print(f"Project '{project_name}' already exists.")
        response = input("Do you want to overwrite it? This will delete all existing data in it. (y/n): ").lower()
        if response == 'y':
            shutil.rmtree(project_path)
            print(f"Removed existing project '{project_name}'.")
        else:
            print("Initialization cancelled.")
            return

    print(f"Initializing new project: {project_name}")

    # Create directory structure
    sub_dirs = ['rgb_video', 'multispectral', 'hyperspectral', 'flight_logs', 'frames']
    for sub_dir in sub_dirs:
        os.makedirs(os.path.join(project_path, sub_dir), exist_ok=True)
    
    # Create a default config file
    config = {
        'project_name': project_name,
        'data_type': 'rgb_video',  # Default data type, can be 'rgb_video', 'multispectral', or 'hyperspectral'
        'paths': {
            'project_root': project_path,
            'rgb_video': os.path.join(project_path, 'rgb_video'),
            'multispectral': os.path.join(project_path, 'multispectral'),
            'hyperspectral': os.path.join(project_path, 'hyperspectral'),
            'flight_logs': os.path.join(project_path, 'flight_logs'),
            'frames': os.path.join(project_path, 'frames'),
        },
        'processing_params': {
            'frame_extraction_interval_ms': 5000,
            'blur_threshold': 100.0,
            'multispectral_band_for_stitching': 1, # Which band to use for feature matching
        }
    }
    
    config_path = os.path.join(project_path, 'project_config.yaml')
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print("\nProject structure created successfully.")
    print(f"Configuration file saved at: {config_path}")
    print("\nPlease place your raw data files into the corresponding subdirectories.")

def main():
    """
    Main function to parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Data management tool for the UAV GIS Pipeline.")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # 'init' command
    parser_init = subparsers.add_parser('init', help='Initialize a new project structure.')
    parser_init.add_argument('--project_name', type=str, required=True, help='The name of the new project.')

    args = parser.parse_args()

    if args.command == 'init':
        init_project(args.project_name)

if __name__ == '__main__':
    main()

