from AlphaBot2 import AlphaBot2
import time

Ab = AlphaBot2()

print("Forward")
Ab.forward()
time.sleep(1)

print("Stop")
Ab.stop()
time.sleep(1)

print("Backward")
Ab.backward()
time.sleep(1)

print("Left")
Ab.left()
time.sleep(1)

print("Right")
Ab.right()
time.sleep(1)

print("Stop")
Ab.stop()
