from ultralytics import YOLO
import cv2, time
from flask import Flask, Response

app = Flask(__name__)
model = YOLO("yolo11n_openvino_model")

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

def generate():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        t0 = time.time()
        results = model(frame)   # DO NOT set imgsz
        fps = 1 / (time.time() - t0)

        annotated = results[0].plot()
        cv2.putText(annotated, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        _, jpeg = cv2.imencode('.jpg', annotated)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               jpeg.tobytes() + b'\r\n')

@app.route('/video')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

app.run(host='0.0.0.0', port=8080)
