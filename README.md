# AlphaBot Target Tracking & Detection

An autonomous robotics project utilizing **Ultralytics YOLO** and **OpenVINO** to enable an AlphaBot to detect, track, and navigate toward specific targets using a Raspberry Pi.

## Overview
This project transforms a standard AlphaBot into an intelligent agent. By leveraging the **YOLO11** architecture optimized for the Raspberry Pi's CPU via **OpenVINO**, the robot can process real-time visual data from a USB webcam to differentiate between manual control and autonomous target-following behavior.
However, the primary task is to implement a self trained model and test it on a specific person.

---

## Tech Stack
* **Hardware:** Raspberry Pi 4/5, AlphaBot Chassis, USB Webcam.
* **Language:** Python 3.11.2
* **Inference Engine:** OpenVINO (CPU optimized).
* **Model:** Ultralytics YOLO11/Self trained YOLO model
* **Web Framework:** Flask.

---

## Installation & Setup

### 1. System Preparation
Update your Raspberry Pi and install necessary multimedia tools for the USB camera:
```
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y v4l-utils ffmpeg
```
### 2. Environment Setup
Create a dedicated virtual environment to manage dependencies:
```
python3 -m venv RoboVENV
source RoboVENV/bin/activate
```
You should now see (RoboVENV) in your terminal prompt
### 3. Install dependencies
```
pip install -r requirements.txt
```
### 4. Export the base YOLO11n model to OpenVINO format for efficient CPU inference:
```
python3 export_yolo_to_openvino.py
```

## Usage
### 1. Optimize camera performance
```
v4l2-ctl -d /dev/video0 --set-fmt-video=width=320,height=240,pixelformat=YUYV
v4l2-ctl -d /dev/video0 --set-parm=30
```
### 2. Verify inference
```
yolo predict model=yolo11n_openvino_model source=0 imgsz=320 vid_stride=2 show=True
```
### 3. Launch the robot
```
python3 robot_follow.py
```

### Note
If you want to implement your own model, make changes to export_model_to_openvino.py and run it
As well as self_trained_model_run.py

## Contributors

Hoang Minh Quan Nguyen - Project Lead & Developer

Vít Kůřil - Developer & Data Labelling

Nathalie Sikihimba Kahambu - Documentation & Data Labelling

Yatin Thakkar - Documentation, Presentation & Data Labelling

Rollanas Terentjevas - Research, Presentation & Data Labelling

Special Thanks:

Andrejs Šalms - Technical Instruction & Hardware Provision