# Project-FaceDrive
Facial Gesture Wheelchair Controller This project enables hands-free control of a wheelchair using facial gestures detected through a camera. It was designed specifically to assist people with ALS or other mobility impairments.


This project uses a camera and an ESP32 to control a wheelchair using facial gestures.
The system detects eyebrow and mouth movements to send movement commands via Wi-Fi (UDP) to the ESP32, which controls two servos for directional movement.

Features
Facial gesture detection using Python and OpenCV.
I used 'playAbility' software.

Controls forward, backward, left, and right movement.

UDP communication with ESP32 microcontroller.

Smooth servo control for precise motion.

GUI interface for:

Setting detection thresholds.

Visualizing real-time gesture data.

Starting/stopping the serial link.

Exiting the program safely.

Supports dynamic IP (use address reservation on router for stability).

Requirements
Python 3.8+

OpenCV

dlib

Kivy (for GUI)

ESP32 (with custom firmware)

A webcam or Raspberry Pi camera




Gesture	Action
Raise eyebrows	Move forward
Mouth move left	Turn left
Mouth move right	Turn right
Open mouth	Move backward
Notes
No changes needed to ESP32 code if IP address is reserved.

Make sure your face is centered and well-lit for better detection.

For advanced settings, use the GUI sliders to adjust thresholds.



