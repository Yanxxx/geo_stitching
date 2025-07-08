import os
import argparse
import yaml
import cv2
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_gcps
from rasterio.control import GroundControlPoint
import glob
import time

class ProcessingPipeline:
    def __init__(self, project_name):
        self.project_name = project_name
        self.config_path = os.path.join('data', project_name, 'project_config.yaml')
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found for project '{project_name}'. Please run 'manage_data.py init' first.")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.paths = self.config['paths']
        self.params = self.config['processing_params']
        self.output_dir = os.path.join('output', self.project_name)
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        """Executes the full processing pipeline."""
        start_time = time.time()
        print(f"--- Starting pipeline for project: {self.project_name} ---")

        # Step 1: Prepare image frames
        image_files = self._prepare_frames()
        if not image_files:
            print("Pipeline stopped: No valid frames to process.")
            return

        # Step 2: Stitch images
        stitched_image = self._stitch_images(image_files)
        if stitched_image is None:
            print("Pipeline stopped: Stitching failed.")
            return

        # Step 3: Georeference the stitched image
        self._georeference_image(stitched_image)

        end_time = time.time()
        print(f"--- Pipeline finished in {end_time - start_time:.2f} seconds ---")


    def _prepare_frames(self):
        """Prepares a list of image file paths to be processed."""
        data_type = self.config.get('data_type', 'rgb_video')
        print(f"Processing data type: {data_type}")

        if data_type == 'rgb_video':
            return self._extract_video_frames()
        elif data_type in ['multispectral', 'hyperspectral']:
            # For these types, we assume frames are already individual image files
            image_dir = self.paths[data_type]
            files = sorted(glob.glob(os.path.join(image_dir, '*.tif')))
            if not files:
                 print(f"Warning: No .tif files found in {image_dir}")
            return files
        else:
            print(f"Error: Unsupported data type '{data_type}' in config.")
            return []

    def _extract_video_frames(self):
        """Extracts frames from all videos in the rgb_video directory."""
        video_files = glob.glob(os.path.join(self.paths['rgb_video'], '*.mp4'))
        if not video_files:
            print("Error: No video files (.mp4) found.")
            return []

        print(f"Found {len(video_files)} video(s). Extracting frames...")
        extracted_frames = []
        for video_path in video_files:
            cap = cv2.VideoCapture(video_path)
            last_capture_time = -self.params['frame_extraction_interval_ms']
            
            while True:
                ret, frame = cap.read()
                if not ret: break
                
                current_time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                if current_time_ms >= last_capture_time + self.params['frame_extraction_interval_ms']:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    if cv2.Laplacian(gray, cv2.CV_64F).var() > self.params['blur_threshold']:
                        frame_filename = os.path.join(self.paths['frames'], f"frame_{os.path.basename(video_path)}_{int(current_time_ms)}.jpg")
                        cv2.imwrite(frame_filename, frame)
                        extracted_frames.append(frame_filename)
                        last_capture_time = current_time_ms
            cap.release()
        
        print(f"Extracted {len(extracted_frames)} high-quality frames.")
        return sorted(extracted_frames)

    def _stitch_images(self, image_files):
        """Stitches a list of images into a single panorama."""
        print(f"Starting stitching process for {len(image_files)} images...")
        if len(image_files) < 2:
            print("Error: Need at least two images to stitch.")
            return None

        # For multispectral, we stitch based on a single reference band
        data_type = self.config.get('data_type')
        if data_type in ['multispectral', 'hyperspectral']:
            # This is a simplification: assumes file naming allows finding the reference band.
            # e.g., image_001_band1.tif, image_002_band1.tif
            ref_band_id = self.params['multispectral_band_for_stitching']
            ref_images_paths = [f for f in image_files if f"band{ref_band_id}" in f]
            images_to_stitch = [cv2.imread(p, cv2.IMREAD_GRAYSCALE) for p in ref_images_paths]
        else: # RGB
            images_to_stitch = [cv2.imread(f) for f in image_files]

        stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
        status, stitched_image = stitcher.stitch(images_to_stitch)

        if status != cv2.Stitcher_OK:
            print(f"Stitching failed with status code: {status}")
            return None

        print("Stitching successful. Cropping black borders...")
        # Cropping logic (same as before)
        gray = cv2.cvtColor(stitched_image, cv2.COLOR_BGR2GRAY) if len(stitched_image.shape) == 3 else stitched_image
        _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
            stitched_image = stitched_image[y:y+h, x:x+w]
        
        return stitched_image

    def _georeference_image(self, stitched_image):
        """Assigns geographic coordinates to the final image."""
        print("Starting georeferencing...")
        flight_log_files = glob.glob(os.path.join(self.paths['flight_logs'], '*.csv'))
        if not flight_log_files:
            print("Error: No flight log (.csv) found.")
            return

        # Combine all flight logs into one DataFrame
        df_log = pd.concat([pd.read_csv(f) for f in flight_log_files])
        df_log = df_log.sort_values(by='timestamp_ms').reset_index(drop=True)

        h, w = stitched_image.shape[:2]
        
        # Simplified GCP logic using the full time range of the flight log
        first_log = df_log.iloc[0]
        last_log = df_log.iloc[-1]
        
        top_left_gps = (first_log['longitude'], first_log['latitude'])
        bottom_right_gps = (last_log['longitude'], last_log['latitude'])
        bottom_left_gps = (first_log['longitude'], last_log['latitude'])
        top_right_gps = (last_log['longitude'], first_log['latitude'])
        
        gcps = [
            GroundControlPoint(row=0, col=0, x=top_left_gps[0], y=top_left_gps[1]),
            GroundControlPoint(row=0, col=w - 1, x=top_right_gps[0], y=top_right_gps[1]),
            GroundControlPoint(row=h - 1, col=0, x=bottom_left_gps[0], y=bottom_left_gps[1]),
            GroundControlPoint(row=h - 1, col=w - 1, x=bottom_right_gps[0], y=bottom_right_gps[1])
        ]
        transform = from_gcps(gcps)

        # Handle multi-band (multispectral) or single-band (stitched RGB) output
        num_bands = stitched_image.shape[2] if len(stitched_image.shape) == 3 else 1
        output_path = os.path.join(self.output_dir, 'stitched_georeferenced.tif')

        with rasterio.open(
            output_path, 'w', driver='GTiff', height=h, width=w,
            count=num_bands, dtype=stitched_image.dtype, crs='EPSG:4326', transform=transform
        ) as dst:
            if num_bands == 1:
                dst.write(stitched_image, 1)
            else:
                # This is a simplification. For true multispectral, you would apply the
                # calculated warp to each band individually and stack them.
                # Here we just save the RGB stitched result.
                dst.write(stitched_image.transpose(2, 0, 1))

        print(f"Georeferenced GeoTIFF saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Main processing pipeline for UAV data.")
    parser.add_argument('--project_name', type=str, required=True, help='The name of the project to process.')
    args = parser.parse_args()

    try:
        pipeline = ProcessingPipeline(args.project_name)
        pipeline.run()
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()

