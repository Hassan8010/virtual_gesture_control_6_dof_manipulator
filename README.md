# virtual_gesture_control_6_dof_manipulator
Real-time HMI for a virtual 6-DOF robotic manipulator in Webots using a MediaPipe computer vision gesture tracking pipeline over UDP.
# 6-DOF Manipulator Control via Gesture Tracking (Webots HMI)

This repository implements a real-time Human-Machine Interface (HMI) that extracts hand gesture kinematics via computer vision to control a virtual 6-Degree-of-Freedom (6-DOF) robotic manipulator inside Webots[cite: 1, 2, 3]. 

The system utilizes a decoupled architecture where a MediaPipe vision pipeline processes webcam frames locally (`gc_sender.py`) and streams joint position commands to a Webots simulation robot controller (`rob_receiver.py`) via UDP sockets[cite: 1, 2].

## 🏗️ System Architecture

*   **Vision Pipeline (`gc_sender.py`):** MediaPipe Hands tracks local frame landmark coordinates at high confidence thresholds[cite: 1]. Wrist positional data is mapped linearly across custom joint constraints to output safe target trajectories[cite: 1].
*   **Data Transport:** Communication is handled via local UDP socket serialization (`127.0.0.1:5005`) passing lightweight JSON packets[cite: 1, 2].
*   **Simulation Receiver (`rob_receiver.py`):** A non-blocking Webots robot controller parses incoming JSON packets, reads target angles, and applies linear interpolation for smooth joint transitions[cite: 2].

---

## 🎮 Gesture Mapping Matrix

| State / Motion | Gesture Input | Action Description |
| :--- | :--- | :--- |
| **System Enable** | 👍 Thumb Up | Sets system state to active[cite: 1]. |
| **System E-Stop** | ✊ Closed Fist | Halts movement, drops active status[cite: 1]. |
| **System Reset** | 🤙 Shaka / Sign | Resets joint positions back to home configurations[cite: 1]. |
| **Joint 1 (Base)** | ☝️ Index Finger Up | Maps Wrist X coordinate to Base angle bounds[cite: 1]. |
| **Joint 2 (Shoulder)** | ✌️ Victory Sign | Maps Wrist Y coordinate to Shoulder angle bounds[cite: 1]. |
| **Joint 3 (Elbow)** | 🤟 Three Fingers Up | Maps Wrist Y coordinate to Elbow angle bounds[cite: 1]. |
| **Joint 4 (Wrist)** | 🖐️ Pinky Finger Up | Maps Wrist Y coordinate to Wrist Pitch bounds[cite: 1]. |
| **End Effector** | Open Palm vs. Fist | Dynamically transitions the gripper states[cite: 1]. |

---

## 📁 Repository Structure

Organize your files like this inside the repository for Webots to automatically identify the project links:

```text
├── controllers/
│   └── rob_receiver/
│       └── rob_receiver.py       # The Webots robot controller script
├── worlds/
│   └── my_rob.wbt                # The Webots world environment file
├── gc_sender.py                  # The MediaPipe computer vision script
├── requirements.txt              # Python dependencies
└── .gitignore                    # Local cache/file ignore rules
