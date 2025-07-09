# 无人机影像拼接与GIS分析管道 (UAV Image Stitching & GIS Pipeline)

本项目是一个一站式的自动化处理管道，旨在将无人机采集的影像数据（包括RGB视频、多光谱和高光谱图像）处理成带有地理坐标的大型拼接正射影像（GeoTIFF），并生成可交互的Web地图进行可视化。

## 主要功能

- **多数据源管理**: 通过简单的命令即可初始化新项目，管理不同类型的数据源。
- **自动化处理**: 一键式脚本执行从视频/图像帧提取、图像拼接、到地理配准的全过程。
- **多光谱/高光谱支持**: 能够处理多波段数据，在保留完整光谱信息的同时完成拼接和地理配准。
- **GIS可视化**: 生成一个独立的HTML交互式地图，将处理后的影像叠加在标准地图上，并显示飞行轨迹。
- **模块化设计**: 清晰分离了数据管理、核心处理和可视化的逻辑，易于扩展和维护。

## 项目结构


/UAV-GIS-Pipeline
|
|-- data/                     # 存放所有原始数据
|   |-- [project_name]/       # 每个项目一个文件夹
|   |   |-- rgb_video/        # 存放RGB视频
|   |   |-- multispectral/    # 存放多光谱图像
|   |   |-- flight_logs/      # 存放飞行日志 (CSV)
|   |   |-- project_config.yaml # 项目配置文件
|
|-- output/                   # 存放所有处理结果
|   |-- [project_name]/
|   |   |-- stitched_georeferenced.tif
|   |   |-- field_map.html
|
|-- src/                      # 存放所有源代码
|   |-- manage_data.py        # 数据管理脚本
|   |-- process_pipeline.py   # 核心处理管道
|   |-- visualize_map.py      # 地图可视化脚本
|
|-- README.md                 # 本文档


## 安装依赖

本项目使用Python 3.8+。推荐在虚拟环境中使用。

**1. 安装核心库:**
```bash
pip install opencv-python opencv-contrib-python numpy pandas pyyaml gdal rasterio folium pillow
```

2. 安装GDAL的注意事项:
GDAL 的安装可能因操作系统而异，直接使用pip可能会失败。推荐使用Conda进行安装：
```
conda install -c conda-forge gdal
```
如果您不使用Conda，请参考官方GDAL安装文档或使用系统的包管理器（如apt-get install libgdal-dev on Ubuntu）。

使用方法
第1步: 初始化项目并管理数据
使用 manage_data.py 脚本来创建一个新的数据项目。这会自动创建所需的文件夹结构和配置文件。

命令格式:
```
python src/manage_data.py init --project_name [您的项目名称]
```

示例:
```
python src/manage_data.py init --project_name project_1_paddy_field
```

执行后，data/project_1_paddy_field 文件夹和其子目录将被创建。

然后，将您的数据文件放入对应的文件夹中:

将无人机视频 .mp4 文件放入 rgb_video 目录。

将多光谱/高光谱 .tif 文件放入 multispectral 目录。

将飞行日志 .csv 文件放入 flight_logs 目录。

第2步: 运行核心处理管道
当数据准备好后，运行 process_pipeline.py 来生成拼接好的GeoTIFF地图。

命令格式:
```
python src/process_pipeline.py --project_name [您的项目名称]
```
示例:
``````
python src/process_pipeline.py --project_name project_1_paddy_field

该脚本会自动读取配置文件，找到数据，并执行所有处理步骤。处理完成后，拼接好的 stitched_georeferenced.tif 文件会出现在 output/project_1_paddy_field 目录中。

第3步: 生成并查看交互式地图
最后，运行 visualize_map.py 来为处理好的GeoTIFF创建一个HTML地图。

命令格式:
```
python src/visualize_map.py --project_name [您的项目名称]
```
示例:
```
python src/visualize_map.py --project_name project_1_paddy_field
```
执行后，field_map.html 文件会出现在 output/project_1_paddy_field 目录中。在您的浏览器中打开此文件即可查看结果。

飞行日志CSV格式要求
飞行日志文件 (.csv) 必须包含以下列名：

timestamp_ms: 视频或图像采集的UTC时间戳（毫秒）。

latitude: WGS-84 纬度。

longitude: WGS-84 经度。

altitude_m: 海拔高度（米）。

示例:

timestamp_ms,latitude,longitude,altitude_m
1672531200000,37.386051,-122.083855,50
1672531205000,37.386151,-122.083855,50
...

