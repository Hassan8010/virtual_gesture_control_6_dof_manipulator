from controller import Robot
import socket
import json

# --- UDP listener ---
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

# --- Robot init ---
robot = Robot()
timestep = int(robot.getBasicTimeStep())

MOTOR_NAMES = ["motor1", "motor2", "motor3", "motor4", "motor5", "motor6"]
motors = []
for name in MOTOR_NAMES:
    m = robot.getDevice(name)
    m.setPosition(0.0)
    m.setVelocity(1.5)
    motors.append(m)

left_finger = robot.getDevice("left_finger")
right_finger = robot.getDevice("right_finger")

current_angles = [0.0] * 7
target_angles = [0.0] * 7
INTERP_SPEED = 0.1

def interpolate(current, target, speed):
    return [c + (t - c) * speed for c, t in zip(current, target)]

print("[INFO] Controller active. Waiting for hand gestures...")

while robot.step(timestep) != -1:
    latest = None
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            latest = data
        except BlockingIOError:
            break

    if latest:
        try:
            msg = json.loads(latest.decode())
            target_angles = msg.get("joints", target_angles)
        except Exception as e:
            print(f"Error: {e}")

    current_angles = interpolate(current_angles, target_angles, INTERP_SPEED)

    for i in range(6):
        motors[i].setPosition(current_angles[i])

    grip_val = current_angles[6]
    left_finger.setPosition(grip_val)
    right_finger.setPosition(-grip_val)