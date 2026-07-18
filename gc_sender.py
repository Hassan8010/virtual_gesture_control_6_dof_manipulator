import cv2
import mediapipe as mp
import numpy as np
import socket
import json

# --- UDP CONFIG ---
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- MEDIAPIPE SETUP ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8, min_tracking_confidence=0.8)

# --- LIMITS & STATE ---
# Radians: J1(Base), J2(Shoulder), J3(Elbow), J4(Wrist Pitch), J5, J6, Gripper
JOINT_LIMITS = [(0.0, 3.14), (-1.57, 1.57), (-1.57, 1.57), (-3.14, 3.14), (-1.57, 1.57), (-3.14, 3.14), (0.0, 0.4)]
current_angles = [1.57, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] 
system_active = False 

def map_range(val, in_min, in_max, out_min, out_max):
    return out_min + (np.clip(val, in_min, in_max) - in_min) * (out_max - out_min) / (in_max - in_min)

def is_finger_up(hl, tip, pip):
    """More robust finger detection using Y-coordinates."""
    return hl.landmark[tip].y < hl.landmark[pip].y

def main():
    global system_active, current_angles
    cap = cv2.VideoCapture(0)
    print("[SYSTEM] Starting HMI. Use 👍 to Enable.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        mode = "IDLE"
        if results.multi_hand_landmarks:
            hl = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)
            
            # --- FINGER STATES ---
            t_up = hl.landmark[4].x < hl.landmark[3].x # Thumb
            i_up = is_finger_up(hl, 8, 6)   # Index
            m_up = is_finger_up(hl, 12, 10) # Middle
            r_up = is_finger_up(hl, 16, 14) # Ring
            p_up = is_finger_up(hl, 20, 18) # Pinky
            wrist = hl.landmark[0]

            # --- 1. SYSTEM CONTROL GESTURES ---
            if t_up and not (i_up or m_up or r_up or p_up):
                system_active = True # 👍 START
            elif not (t_up or i_up or m_up or r_up or p_up):
                system_active = False # ✊ STOP (Closed Fist)
            elif t_up and p_up and not (i_up or m_up or r_up):
                current_angles = [1.57, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # 🤙 RESET

            # --- 2. MOVEMENT GESTURES (Only if active) ---
            if system_active:
                # ☝️ Index Only: Base Left/Right
                if i_up and not (m_up or r_up or p_up):
                    mode = "JOINT 1: BASE"
                    current_angles[0] = map_range(wrist.x, 0.2, 0.8, JOINT_LIMITS[0][0], JOINT_LIMITS[0][1])
                
                # ✌️ Two Fingers: Shoulder Up/Down
                elif i_up and m_up and not (r_up or p_up):
                    mode = "JOINT 2: SHOULDER"
                    current_angles[1] = map_range(wrist.y, 0.2, 0.8, JOINT_LIMITS[1][1], JOINT_LIMITS[1][0])
                
                # 🤟 Three Fingers: Elbow Forward/Back
                elif i_up and m_up and r_up and not p_up:
                    mode = "JOINT 3: ELBOW"
                    current_angles[2] = map_range(wrist.y, 0.2, 0.8, JOINT_LIMITS[2][1], JOINT_LIMITS[2][0])
                
                # 🖐️ Pinky Only: Wrist Up/Down
                elif p_up and not (i_up or m_up or r_up):
                    mode = "JOINT 4: WRIST"
                    current_angles[4] = map_range(wrist.y, 0.2, 0.8, JOINT_LIMITS[4][1], JOINT_LIMITS[4][0])

                # Gripper: Open Palm ✋ vs Fist ✊
                finger_count = sum([i_up, m_up, r_up, p_up])
                if finger_count >= 3: current_angles[6] = 0.0 # OPEN
                elif finger_count == 0: current_angles[6] = 0.4 # CLOSE

        # Send Data
        sock.sendto(json.dumps({"joints": current_angles}).encode(), (UDP_IP, UDP_PORT))

        # UI Overlay
        color = (0, 255, 0) if system_active else (0, 0, 255)
        status = "ACTIVE" if system_active else "STOPPED"
        cv2.putText(frame, f"STATUS: {status} | {mode}", (10, 40), 1, 2, color, 3)
        cv2.imshow("6-DOF Gesture Controller", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()