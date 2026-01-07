from ultralytics import YOLO

model = YOLO("runs/detect/train3/weights/best.pt")
model.export(format="openvino") 
print("Export complete.")
