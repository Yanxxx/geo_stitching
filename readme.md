# UAV Image Stitching & GIS Pipeline
This project provides a one-stop, automated pipeline for processing aerial imagery data collected by UAVs (including RGB video, multispectral, and hyperspectral images) into a large-scale, georeferenced orthomosaic (GeoTIFF), and generating an interactive web map for visualization.

## Key Features
Multi-Source Data Management: Initialize new projects and manage various data sources with simple commands.

Automated Processing: Execute the entire workflow—from video/image frame extraction to image stitching and georeferencing—with a single command.

Multispectral/Hyperspectral Support: Capable of processing multi-band data, ensuring complete spectral information is preserved throughout the stitching and georeferencing process.

GIS Visualization: Generates a standalone, interactive HTML map that overlays the processed imagery onto a standard map layer and displays the flight path.

Modular Design: Features a clean separation of logic for data management, core processing, and visualization, facilitating easy extension and maintenance.

### Project Structure

```
/UAV-GIS-Pipeline
|
|-- data/                  # Stores all raw data
|   |-- [project_name]/      # A dedicated folder for each project
|   |   |-- rgb_video/       # Stores RGB videos
|   |   |-- multispectral/   # Stores multispectral images
|   |   |-- flight_logs/     # Stores flight logs (CSV)
|   |   |-- project_config.yaml # Project configuration file
|
|-- output/                # Stores all processing results
|   |-- [project_name]/
|   |   |-- stitched_georeferenced.tif
|   |   |-- field_map.html
|
|-- src/                   # Stores all source code
|   |-- manage_data.py       # Data management script
|   |-- process_pipeline.py  # Core processing pipeline
|   |-- visualize_map.py     # Map visualization script
|
|-- README.md              # This document
```

## Installation
This project requires Python 3.8+. It is recommended to use a virtual environment.

1. Install Core Libraries:

Bash

pip install opencv-python opencv-contrib-python numpy pandas pyyaml gdal rasterio folium pillow
2. Note on GDAL Installation:
The installation of GDAL can vary significantly between operating systems, and a direct pip install may fail. It is highly recommended to install it using Conda:

Bash
```
conda install -c conda-forge gdal
```

If you do not use Conda, please refer to the official GDAL installation documentation or use your system's package manager (e.g., apt-get install libgdal-dev on Ubuntu).

Usage
Step 1: Initialize Project and Manage Data
Use the manage_data.py script to create a new data project. The required folder structure and configuration file will be generated automatically.

Command Format:

Bash
```
python src/manage_data.py init --project_name [your_project_name]
```
Example:

Bash
```
python src/manage_data.py init --project_name project_1_paddy_field
```

After execution, the data/project_1_paddy_field directory and its subdirectories will be created.

Next, place your data files into the corresponding folders:

Place the UAV video .mp4 file into the rgb_video directory.

Place the multispectral/hyperspectral .tif files into the multispectral directory.

Place the flight log .csv file into the flight_logs directory.

Step 2: Run the Core Processing Pipeline
Once the data is in place, run process_pipeline.py to generate the stitched GeoTIFF map.

Command Format:

Bash

python src/process_pipeline.py --project_name [your_project_name]
Example:

Bash

python src/process_pipeline.py --project_name project_1_paddy_field
The script will automatically read the configuration file, locate the data, and execute all processing steps. Upon completion, the stitched_georeferenced.tif file will be available in the output/project_1_paddy_field directory.

Step 3: Generate and View the Interactive Map
Finally, run visualize_map.py to create an HTML map for the processed GeoTIFF.

Command Format:

Bash
```
python src/visualize_map.py --project_name [your_project_name]
```
Example:

Bash
```
python src/visualize_map.py --project_name project_1_paddy_field
```

After execution, the field_map.html file will appear in the output/project_1_paddy_field directory. Open this file in your browser to view the result.

Flight Log CSV Format Requirements
The flight log file (.csv) must contain the following column headers:

timestamp_ms: UTC timestamp in milliseconds when the video frame or image was captured.

latitude: WGS-84 latitude.

longitude: WGS-84 longitude.

altitude_m: Altitude above sea level in meters.

Example:

```
timestamp_ms,latitude,longitude,altitude_m
1672531200000,37.386051,-122.083855,50
1672531205000,37.386151,-122.083855,50
...
```
