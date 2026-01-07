import RPi.GPIO as GPIO
import time
import cv2
from ultralytics import YOLO
from flask import Flask, Response

class robot_follow(object):
    
    def __init__(self,ain1=12,ain2=13,ena=6,bin1=20,bin2=21,enb=26):
        self.AIN1 = ain1
        self.AIN2 = ain2
        self.BIN1 = bin1
        self.BIN2 = bin2
        self.ENA = ena
        self.ENB = enb
        self.PA  = 50
        self.PB  = 50

        GPIO.setmode(GPIO.BCM)
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

    def setPWMA(self,value):
        self.PA = value
        self.PWMA.ChangeDutyCycle(self.PA)

    def setPWMB(self,value):
        self.PB = value
        self.PWMB.ChangeDutyCycle(self.PB)

    def setMotor(self, left, right):
        if 0 <= right <= 100:
            GPIO.output(self.AIN1,GPIO.HIGH)
            GPIO.output(self.AIN2,GPIO.LOW)
            self.PWMA.ChangeDutyCycle(right)
        elif -100 <= right < 0:
            GPIO.output(self.AIN1,GPIO.LOW)
            GPIO.output(self.AIN2,GPIO.HIGH)
            self.PWMA.ChangeDutyCycle(-right)

        if 0 <= left <= 100:
            GPIO.output(self.BIN1,GPIO.HIGH)
            GPIO.output(self.BIN2,GPIO.LOW)
            self.PWMB.ChangeDutyCycle(left)
        elif -100 <= left < 0:
            GPIO.output(self.BIN1,GPIO.LOW)
            GPIO.output(self.BIN2,GPIO.HIGH)
            self.PWMB.ChangeDutyCycle(-left)

def follow_person(results, frame_width):
    BASE_SPEED = 40      # constant forward speed
    TURN_GAIN = 0.20     # how strongly to turn toward the person

    persons = []

    # Collect all detected persons
    for box in results[0].boxes:
        if int(box.cls[0]) == 0:  # class 0 = person
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            persons.append((x1, y1, x2, y2))

    # No person detected → stop
    if not persons:
        Ab.left()
        print("There's no person")
        time.sleep(0.5)
        Ab.stop()
        time.sleep(0.5)
        return

    # Choose the closest person (largest bounding box height)
    x1, y1, x2, y2 = max(persons, key=lambda b: (b[3] - b[1]))

    # Compute center of the person
    cx = (x1 + x2) // 2
    center = frame_width // 2
    print("Center: ", center)
    error = cx - center

    if cx < center - 40:
        Ab.left()
        print("Turning left")
        time.sleep(0.5)
        Ab.forward()
        time.sleep(0.5)
        Ab.stop()
    elif cx > center + 40:
        Ab.right()
        print("Turning right")
        time.sleep(0.5)
        Ab.forward()
        time.sleep(0.5)
        Ab.stop()
    else:
        Ab.forward()
        print("Going straight")

    # Steering control
    turn = int(error * TURN_GAIN)

    # Motor speeds
    left = BASE_SPEED - turn
    right = BASE_SPEED + turn

    # Clamp motor values
    left = max(-100, min(100, left))
    print("Left: ", left)
    
    right = max(-100, min(100, right))
    print("Right: ", right)

    # Ab.setMotor(left, right)
    
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

from threading import Thread

app = Flask(__name__)
model = YOLO("yolo11n_openvino_model", task="detect")
cap = cv2.VideoCapture(0)
ret, _ = cap.read()
if not ret:
    cap.release()
    cap = cv2.VideoCapture(1)

cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG")) 
# Request 30 FPS 
cap.set(cv2.CAP_PROP_FPS, 30) 
# Set resolution 
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
Ab = robot_follow()
control_mode = "manual"

def robot_loop():
    global control_mode
    try:
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                Ab.stop()
                break

            # ONLY run AI logic if in auto mode
            if control_mode == "auto":
                frame_count += 1
                if frame_count % 3 != 0:
                    continue

                results = model(frame, stream=True, verbose=False, classes=[0])
                results = list(results)
                follow_person(results, frame.shape[1])
            else:
                # In manual mode, we just clear the frame buffer so it's fresh 
                # when we switch back to auto
                time.sleep(0.1) 

    except KeyboardInterrupt:
        Ab.stop()
    finally:
        Ab.stop()
        GPIO.cleanup()
        cap.release()

@app.route('/video')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
                    
@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>Robot Control</title>
            <style>
                body { font-family: sans-serif; text-align: center; background: #222; color: white; }
                .status-box { padding: 10px; margin: 10px; border-radius: 5px; background: #444; }
                button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
            </style>
        </head>
        <body>
            <h1>Robot Live Stream</h1>
            <img src="/video" width="640" style="border: 2px solid #555;">
            
            <div class="status-box">
                <h2 id="status">Mode: AUTO (Following)</h2>
                <button onclick="setMode('auto')">AI Follow Mode</button>
                <button onclick="setMode('manual')">Manual Control Mode</button>
            </div>
            <p>Hold <b>W, A, S, D</b> to move. Release to stop.</p>

            <script>
                let activeKey = null;

                function setMode(mode) {
                    fetch('/mode/' + mode);
                    document.getElementById('status').innerText = "Mode: " + mode.toUpperCase();
                }

                document.addEventListener('keydown', function(event) {
                    let key = event.key.toLowerCase();
                    // Prevent repeated fetch calls when holding key down
                    if (activeKey === key) return; 
                    
                    let cmd = '';
                    if (key === 'w') cmd = 'forward';
                    else if (key === 's') cmd = 'backward';
                    else if (key === 'a') cmd = 'left';
                    else if (key === 'd') cmd = 'right';
                    
                    if (cmd) {
                        activeKey = key;
                        setMode('manual'); // Force manual mode on press
                        fetch('/control/' + cmd);
                    }
                });

                document.addEventListener('keyup', function(event) {
                    let key = event.key.toLowerCase();
                    if (key === activeKey) {
                        activeKey = null;
                        fetch('/control/stop');
                    }
                });
            </script>
        </body>
    </html>
    """

@app.route('/mode/<mode_type>')
def set_mode(mode_type):
    global control_mode
    control_mode = mode_type
    Ab.stop() # Stop the robot when switching modes for safety
    return "OK", 200

@app.route('/control/<direction>')
def control(direction):
    # We only allow manual control if the mode is manual
    if control_mode == "manual":
        if direction == 'forward': 
            Ab.forward()
        elif direction == 'backward': 
            Ab.backward()
        elif direction == 'left': 
            Ab.left()
        elif direction == 'right': 
            Ab.right()
        elif direction == 'stop': 
            Ab.stop()
    return "OK", 200
    
if __name__ == '__main__':
    # Start robot control loop in background
    t = Thread(target=robot_loop, daemon=True)
    t.start()

    # Start Flask server
    app.run(host='0.0.0.0', port=8080, debug=False)


