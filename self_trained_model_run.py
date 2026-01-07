import RPi.GPIO as GPIO
import time
import cv2
import os
import signal
from ultralytics import YOLO
from flask import Flask, Response
from threading import Thread

# --- ROBOT CLASS DEFINITION ---
class self_trained_model_run(object):
    def __init__(self,ain1=12,ain2=13,ena=6,bin1=20,bin2=21,enb=26):
        GPIO.setmode(GPIO.BCM)
        self.AIN1 = ain1
        self.AIN2 = ain2
        self.BIN1 = bin1
        self.BIN2 = bin2
        self.ENA = ena
        self.ENB = enb
        self.PA  = 50
        self.PB  = 50

        GPIO.setwarnings(False)
        GPIO.setup(self.AIN1,GPIO.OUT)
        GPIO.setup(self.AIN2,GPIO.OUT)
        GPIO.setup(self.BIN1,GPIO.OUT)
        GPIO.setup(self.BIN2,GPIO.OUT)
        GPIO.setup(self.ENA,GPIO.OUT)
        GPIO.setup(self.ENB,GPIO.OUT)
        self.PWMA = GPIO.PWM(self.ENA,500)
        self.PWMB = GPIO.PWM(self.ENB,500)
        self.PWMA.start(self.PA)
        self.PWMB.start(self.PB)
        self.stop()

    def forward(self):
        self.PWMA.ChangeDutyCycle(self.PA)
        self.PWMB.ChangeDutyCycle(self.PB)
        GPIO.output(self.AIN1,GPIO.HIGH)
        GPIO.output(self.AIN2,GPIO.LOW)
        GPIO.output(self.BIN1,GPIO.LOW)
        GPIO.output(self.BIN2,GPIO.HIGH)

    def stop(self):
        self.PWMA.ChangeDutyCycle(0)
        self.PWMB.ChangeDutyCycle(0)
        GPIO.output(self.AIN1,GPIO.LOW)
        GPIO.output(self.AIN2,GPIO.LOW)
        GPIO.output(self.BIN1,GPIO.LOW)
        GPIO.output(self.BIN2,GPIO.LOW)

    def backward(self):
        self.PWMA.ChangeDutyCycle(self.PA)
        self.PWMB.ChangeDutyCycle(self.PB)
        GPIO.output(self.AIN1,GPIO.LOW)
        GPIO.output(self.AIN2,GPIO.HIGH)
        GPIO.output(self.BIN1,GPIO.HIGH)
        GPIO.output(self.BIN2,GPIO.LOW)

    def left(self):
        self.PWMA.ChangeDutyCycle(30)
        self.PWMB.ChangeDutyCycle(30)
        GPIO.output(self.AIN1,GPIO.LOW)
        GPIO.output(self.AIN2,GPIO.HIGH)
        GPIO.output(self.BIN1,GPIO.LOW)
        GPIO.output(self.BIN2,GPIO.HIGH)

    def right(self):
        self.PWMA.ChangeDutyCycle(30)
        self.PWMB.ChangeDutyCycle(30)
        GPIO.output(self.AIN1,GPIO.HIGH)
        GPIO.output(self.AIN2,GPIO.LOW)
        GPIO.output(self.BIN1,GPIO.HIGH)
        GPIO.output(self.BIN2,GPIO.LOW)

# --- UTILITY FUNCTIONS ---

def initialize_camera():
    # Force close any existing camera handles
    os.system("sudo fuser -k /dev/video0 > /dev/null 2>&1")
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    time.sleep(2)
    
    if not cap.isOpened():
        print("Falling back to index 1...")
        cap = cv2.VideoCapture(1, cv2.CAP_V4L2)
    
    # RESOLUTION DOWN: 320x240 for speed
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
    cap.set(cv2.CAP_PROP_FPS, 20)
    return cap

def follow_person(results, frame_width):
    BASE_SPEED = 40
    if not results or not results[0].boxes:
        Ab.stop()
        return

    persons = [box for box in results[0].boxes if int(box.cls[0]) == 0]
    if not persons:
        Ab.stop()
        return

    # Target largest person
    box = max(persons, key=lambda b: (b.xyxy[0][3] - b.xyxy[0][1]))
    x1, _, x2, _ = map(int, box.xyxy[0])
    cx = (x1 + x2) // 2
    center = frame_width // 2

    if cx < center - 40:
        Ab.left()
    elif cx > center + 40:
        Ab.right()
    else:
        Ab.forward()

def generate():
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Inference imgsz=320 matches our camera resolution for speed
        results = model(frame, imgsz=320, verbose=False)
        annotated = results[0].plot()
        
        _, jpeg = cv2.imencode('.jpg', annotated)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

# --- INITIALIZATION ---
app = Flask(__name__)
model = YOLO("runs/detect/train3/weights/best_openvino_model", task="detect")
cap = initialize_camera()
Ab = self_trained_model_run()
control_mode = "manual"

# --- FLASK ROUTES ---

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>AlphaBot Control</title>
            <style>
                body { font-family: sans-serif; text-align: center; background: #222; color: white; }
                .status-box { padding: 10px; margin: 10px; border-radius: 5px; background: #444; }
                button { padding: 12px 24px; font-size: 16px; cursor: pointer; margin: 5px; border-radius: 8px; border: none; }
                .btn-stop { background: #ff4444; color: white; font-weight: bold; margin-top: 30px; width: 250px; }
            </style>
        </head>
        <body>
            <h1>AlphaBot AI Stream</h1>
            <img src="/video" width="600" style="border: 3px solid #555; border-radius: 10px;">
            <div class="status-box">
                <h2 id="status">MODE: MANUAL</h2>
                <button style="background: #4CAF50; color: white;" onclick="setMode('auto')">START AI FOLLOW</button>
                <button style="background: #2196F3; color: white;" onclick="setMode('manual')">MANUAL CONTROL</button>
            </div>
            <p>Use <b>W, A, S, D</b> to drive manually.</p>
            <button class="btn-stop" onclick="shutdownSystem()">TERMINATE SYSTEM</button>
            <script>
                let activeKey = null;
                function setMode(mode) {
                    fetch('/mode/' + mode);
                    document.getElementById('status').innerText = "MODE: " + mode.toUpperCase();
                }
                function shutdownSystem() {
                    if (confirm("Kill Python process and release hardware?")) {
                        fetch('/shutdown').then(() => {
                            document.body.innerHTML = "<h1>SYSTEM SHUTDOWN SUCCESSFUL</h1>";
                        });
                    }
                }
                document.addEventListener('keydown', (e) => {
                    let key = e.key.toLowerCase();
                    if (activeKey === key) return;
                    if (['w','a','s','d'].includes(key)) {
                        activeKey = key;
                        let cmd = key=='w'?'forward':key=='s'?'backward':key=='a'?'left':'right';
                        setMode('manual');
                        fetch('/control/' + cmd);
                    }
                });
                document.addEventListener('keyup', (e) => {
                    if (e.key.toLowerCase() === activeKey) {
                        activeKey = null;
                        fetch('/control/stop');
                    }
                });
            </script>
        </body>
    </html>
    """

@app.route('/video')
def video():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/mode/<mode_type>')
def set_mode(mode_type):
    global control_mode
    control_mode = mode_type
    Ab.stop()
    return "OK", 200

@app.route('/control/<direction>')
def control(direction):
    if control_mode == "manual":
        if direction == 'forward': Ab.forward()
        elif direction == 'backward': Ab.backward()
        elif direction == 'left': Ab.left()
        elif direction == 'right': Ab.right()
        elif direction == 'stop': Ab.stop()
    return "OK", 200

@app.route('/shutdown')
def shutdown():
    print("Shutting down...")
    Ab.stop()
    cap.release()
    GPIO.cleanup()
    os.kill(os.getpid(), signal.SIGINT)
    return "Terminated"

def robot_loop():
    global control_mode
    while True:
        if control_mode == "auto":
            ret, frame = cap.read()
            if ret:
                results = list(model(frame, imgsz=320, stream=True, verbose=False, classes=[0]))
                follow_person(results, frame.shape[1])
        time.sleep(0.05)

if __name__ == '__main__':
    Thread(target=robot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=8080, debug=False)