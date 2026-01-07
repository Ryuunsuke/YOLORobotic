from ultralytics import YOLO

# Download nano model and export to OpenVINO IR
model = YOLO("yolo11n.pt")
model.export(format="openvino")  # creates yolo11n_openvino_model/ with model.xml/bin

print("Export complete.")
