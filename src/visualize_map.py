import os
import argparse
import folium
import rasterio
from folium.raster_layers import ImageOverlay
import pandas as pd
import base64
from PIL import Image
import numpy as np
import io
import glob

def create_map(project_name):
    """
    Creates an interactive HTML map with the georeferenced image overlaid.
    """
    output_dir = os.path.join('output', project_name)
    geotiff_path = os.path.join(output_dir, 'stitched_georeferenced.tif')
    map_output_path = os.path.join(output_dir, 'field_map.html')
    
    if not os.path.exists(geotiff_path):
        print(f"Error: GeoTIFF not found for project '{project_name}'. Please run 'process_pipeline.py' first.")
        return

    # --- Read GeoTIFF to get bounds and image data ---
    with rasterio.open(geotiff_path) as src:
        bounds = src.bounds
        map_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
        
        # Read image data and convert to a displayable format (e.g., RGB)
        if src.count >= 3:
            # Read the first 3 bands as RGB
            img_array = src.read((1, 2, 3))
        else:
            # For single-band images, duplicate to create a grayscale image
            band = src.read(1)
            img_array = np.stack([band, band, band], axis=0)
        
        # Normalize for display if not standard 8-bit
        if img_array.dtype != np.uint8:
            img_array = (255 * (img_array / img_array.max())).astype(np.uint8)

        img_array = np.moveaxis(img_array, 0, -1)

    # --- Calculate map center ---
    center_lat = (bounds.bottom + bounds.top) / 2
    center_lon = (bounds.left + bounds.right) / 2

    # --- Create Folium map ---
    m = folium.Map(location=[center_lat, center_lon], zoom_start=18, tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', attr='&copy; OpenStreetMap contributors')

    # --- Convert image to base64 for embedding ---
    img = Image.fromarray(img_array)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    image_overlay_url = f"data:image/png;base64,{img_str}"

    ImageOverlay(
        image=image_overlay_url,
        bounds=map_bounds,
        opacity=0.8,
        name='无人机拼接影像 (Drone Panorama)'
    ).add_to(m)

    # --- Add flight path ---
    flight_log_dir = os.path.join('data', project_name, 'flight_logs')
    log_files = glob.glob(os.path.join(flight_log_dir, '*.csv'))
    if log_files:
        df_log = pd.concat([pd.read_csv(f) for f in log_files])
        points = df_log[['latitude', 'longitude']].dropna().values.tolist()
        folium.PolyLine(points, color="red", weight=2.5, opacity=1, tooltip="飞行轨迹 (Flight Path)").add_to(m)
        print("Added flight path to the map.")

    folium.LayerControl().add_to(m)
    m.save(map_output_path)

    print(f"\nInteractive map created successfully!")
    print(f"Please open this file in your browser: {os.path.abspath(map_output_path)}")

def main():
    parser = argparse.ArgumentParser(description="Map visualization tool for the UAV GIS Pipeline.")
    parser.add_argument('--project_name', type=str, required=True, help='The name of the project to visualize.')
    args = parser.parse_args()
    
    create_map(args.project_name)

if __name__ == '__main__':
    main()

