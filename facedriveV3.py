import socket
import keyboard
import tkinter as tk
from tkinter import ttk
import subprocess
import time
import platform

# ---------------------------
# ADJUST THESE TO MATCH YOUR SETUP
STATION_IP = "192.168.68.113"     # Normal IP when ESP32 is on your home router
AP_IP      = "192.168.4.1"        # Default IP for ESP32 in AP mode
ESP32_PORT = 4210                 # Same UDP port as ESP32
WIFI_PROFILE_NAME = "ESP32_Controller"  # The Wi-Fi SSID or profile name on Windows
# ---------------------------

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

current_esp_ip = STATION_IP   # We'll start by assuming station IP

# -----------------
# Tkinter GUI Setup
# -----------------
root = tk.Tk()
root.title("Wi-Fi Keyboard Controller")
root.geometry("400x600")  # Increase size for new offset widgets

BIG_FONT = ("Arial", 14, "bold")
MED_FONT = ("Arial", 12)

status_label = ttk.Label(root, text="Connecting...", foreground="green", font=MED_FONT)
status_label.pack(pady=5)

key_label = ttk.Label(root, text="Press W/A/S/D", font=BIG_FONT)
key_label.pack(pady=10)

lock_label = ttk.Label(root, text="", font=MED_FONT, foreground="red")
lock_label.pack(pady=5)

countdown_label = ttk.Label(root, text="", font=MED_FONT)
countdown_label.pack(pady=5)

# -------------------------
# SPEED & OFFSET CONTROLS
# -------------------------
control_frame = ttk.Frame(root)
control_frame.pack(pady=10)

# SPEED
speed_var = tk.IntVar(value=10)

speed_value_label = ttk.Label(
    control_frame, text=f"Speed: {speed_var.get()} ms/°", font=MED_FONT
)
speed_value_label.grid(row=0, column=0, columnspan=3, pady=5, sticky="w")

def increase_speed():
    new_speed = min(speed_var.get() + 1, 200)  # clamp at 200
    speed_var.set(new_speed)

def decrease_speed():
    new_speed = max(speed_var.get() - 1, 1)  # clamp at 1
    speed_var.set(new_speed)

minus_speed_btn = ttk.Button(control_frame, text="-", command=decrease_speed)
minus_speed_btn.grid(row=0, column=3, padx=(10,0), sticky="e")

plus_speed_btn = ttk.Button(control_frame, text="+", command=increase_speed)
plus_speed_btn.grid(row=0, column=4, padx=(2,0), sticky="e")

# -------------------------
# OFFSETS FOR X AND Y
# -------------------------
# We'll use two separate IntVars: rangeX_var, rangeY_var
rangeX_var = tk.IntVar(value=30)
rangeY_var = tk.IntVar(value=30)

rangeX_value_label = ttk.Label(
    control_frame, text=f"X Offset: {rangeX_var.get()}°", font=MED_FONT
)
rangeX_value_label.grid(row=1, column=0, columnspan=3, pady=5, sticky="w")

def increase_range_x():
    new_range_x = min(rangeX_var.get() + 1, 90)
    rangeX_var.set(new_range_x)

def decrease_range_x():
    new_range_x = max(rangeX_var.get() - 1, 0)
    rangeX_var.set(new_range_x)

minus_range_x_btn = ttk.Button(control_frame, text="-", command=decrease_range_x)
minus_range_x_btn.grid(row=1, column=3, padx=(10,0), sticky="e")

plus_range_x_btn = ttk.Button(control_frame, text="+", command=increase_range_x)
plus_range_x_btn.grid(row=1, column=4, padx=(2,0), sticky="e")


rangeY_value_label = ttk.Label(
    control_frame, text=f"Y Offset: {rangeY_var.get()}°", font=MED_FONT
)
rangeY_value_label.grid(row=2, column=0, columnspan=3, pady=5, sticky="w")

def increase_range_y():
    new_range_y = min(rangeY_var.get() + 1, 90)
    rangeY_var.set(new_range_y)

def decrease_range_y():
    new_range_y = max(rangeY_var.get() - 1, 0)
    rangeY_var.set(new_range_y)

minus_range_y_btn = ttk.Button(control_frame, text="-", command=decrease_range_y)
minus_range_y_btn.grid(row=2, column=3, padx=(10,0), sticky="e")

plus_range_y_btn = ttk.Button(control_frame, text="+", command=increase_range_y)
plus_range_y_btn.grid(row=2, column=4, padx=(2,0), sticky="e")


# Optionally, we can keep or remove the sliders. Let's keep them for finer control:
slider_frame = ttk.Frame(root)
slider_frame.pack(pady=10, fill='x')

# Speed Slider
speed_label = ttk.Label(slider_frame, text="Servo Speed (ms/°):", font=MED_FONT)
speed_label.pack()
speed_slider = ttk.Scale(slider_frame, from_=1, to=100, orient=tk.HORIZONTAL, variable=speed_var)
speed_slider.pack(fill='x', padx=30)

# X Offset Slider
rangeX_label = ttk.Label(slider_frame, text="X Offset (degrees):", font=MED_FONT)
rangeX_label.pack()
rangeX_slider = ttk.Scale(slider_frame, from_=0, to=90, orient=tk.HORIZONTAL, variable=rangeX_var)
rangeX_slider.pack(fill='x', padx=30)

# Y Offset Slider
rangeY_label = ttk.Label(slider_frame, text="Y Offset (degrees):", font=MED_FONT)
rangeY_label.pack()
rangeY_slider = ttk.Scale(slider_frame, from_=0, to=90, orient=tk.HORIZONTAL, variable=rangeY_var)
rangeY_slider.pack(fill='x', padx=30)


# -------------------------------------
# Fallback Logic (Station -> AP switch)
# -------------------------------------
def ping_device(ip_address, timeout=3):
    """Returns True if ping to `ip_address` is successful, False otherwise."""
    if platform.system().lower().startswith("win"):
        cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip_address]
    else:
        cmd = ["ping", "-c", "1", "-W", str(timeout), ip_address]

    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return (result.returncode == 0)
    except Exception:
        return False

def ensure_connection():
    """Checks if the station IP is reachable; if not, attempts to connect to AP."""
    global current_esp_ip

    # 1) Try station IP first
    if ping_device(STATION_IP):
        current_esp_ip = STATION_IP
        status_label.config(text="Using Station IP", foreground="green")
        return

    # 2) If station IP fails, try to switch Wi-Fi to the ESP32 AP (Windows example)
    if platform.system().lower().startswith("win"):
        try:
            subprocess.run(["netsh", "wlan", "connect", f"name={WIFI_PROFILE_NAME}"],
                           check=True)
            time.sleep(5)  # Wait a few seconds for Wi-Fi to connect
        except subprocess.CalledProcessError:
            pass

    # 3) Check if the AP IP is now reachable
    if ping_device(AP_IP):
        current_esp_ip = AP_IP
        status_label.config(text="Using ESP32 AP", foreground="orange")
    else:
        status_label.config(text="ESP32 Not Found!", foreground="red")


# -------------------------------------------
# Send updated speed, plus X/Y offsets
# -------------------------------------------
def send_all_updates(*_args):
    """
    Sends SPD:<value>, RNX:<value>, RNY:<value> to the ESP32 whenever
    speed or offset changes.
    """
    # Grab current values
    speed_value = speed_var.get()
    rangeX_value = rangeX_var.get()
    rangeY_value = rangeY_var.get()

    # Update numeric labels
    speed_value_label.config(text=f"Speed: {speed_value} ms/°")
    rangeX_value_label.config(text=f"X Offset: {rangeX_value}°")
    rangeY_value_label.config(text=f"Y Offset: {rangeY_value}°")

    # Send SPD:<speed_value>
    speed_msg = f"SPD:{speed_value}"
    sock.sendto(speed_msg.encode(), (current_esp_ip, ESP32_PORT))

    # Send RNX:<rangeX_value>
    rnx_msg = f"RNX:{rangeX_value}"
    sock.sendto(rnx_msg.encode(), (current_esp_ip, ESP32_PORT))

    # Send RNY:<rangeY_value>
    rny_msg = f"RNY:{rangeY_value}"
    sock.sendto(rny_msg.encode(), (current_esp_ip, ESP32_PORT))


# Lock/Key logic
keys_pressed = {"w": False, "a": False, "s": False, "d": False}
lock_active = False
lock_start_time = None
lock_release_time = None

def send_key_state(active_keys):
    """Sends the current movement command to the ESP32."""
    if active_keys:
        sock.sendto(active_keys.encode(), (current_esp_ip, ESP32_PORT))
        key_label.config(text=f"Sent: {active_keys.upper()}")
    else:
        # No movement => stop both axes
        sock.sendto(b"x", (current_esp_ip, ESP32_PORT))  # stop horizontal
        sock.sendto(b"y", (current_esp_ip, ESP32_PORT))  # stop vertical
        key_label.config(text="Keys Released")

def check_keys():
    """Main loop that checks keyboard state and handles lock logic."""
    global lock_active, lock_start_time, lock_release_time
    previous_keys = keys_pressed.copy()
    current_time = time.time()

    # Update which keys are pressed
    for key in keys_pressed:
        if keyboard.is_pressed(key):
            keys_pressed[key] = True
        else:
            keys_pressed[key] = False

    # Lock logic: hold 'w' for 5 seconds
    if keys_pressed["w"] and not lock_active:
        if lock_start_time is None:
            lock_start_time = current_time
        countdown_time = 5 - (current_time - lock_start_time)
        if countdown_time < 0:
            countdown_time = 0
        countdown_label.config(text=f"Lock in: {countdown_time:.1f}s")

        if countdown_time <= 0:
            lock_active = True
            lock_label.config(text="Lock Active: Adjust with A/D")
            countdown_label.config(text="")
            lock_release_time = time.time()
    else:
        lock_start_time = None
        countdown_label.config(text="")

    # Break lock if 'w' or 's' is pressed again, 1s after lock
    if lock_active and (keyboard.is_pressed("w") or keyboard.is_pressed("s")):
        if lock_release_time and (current_time - lock_release_time > 1):
            lock_active = False
            lock_label.config(text="")
            countdown_label.config(text="")
            lock_release_time = None

    # Determine movement commands
    if lock_active:
        # Force 'w' if locked
        active_keys = "w"
        if keys_pressed["a"]:
            active_keys += "a"
        if keys_pressed["d"]:
            active_keys += "d"
    else:
        vertical_keys = []
        horizontal_keys = []
        if keys_pressed["w"]:
            vertical_keys.append("w")
        if keys_pressed["s"]:
            vertical_keys.append("s")
        if keys_pressed["a"]:
            horizontal_keys.append("a")
        if keys_pressed["d"]:
            horizontal_keys.append("d")

        # Remove conflicting vertical/horizontal commands
        if len(vertical_keys) > 1:
            vertical_keys = []
        if len(horizontal_keys) > 1:
            horizontal_keys = []

        active_keys = "".join(vertical_keys + horizontal_keys)

    # Send if keys changed or we are locked
    if keys_pressed != previous_keys or lock_active:
        send_key_state(active_keys)

    # If locked and neither A nor D is pressed, send neutral for X
    if lock_active and not (keys_pressed["a"] or keys_pressed["d"]):
        sock.sendto(b"x", (current_esp_ip, ESP32_PORT))

    root.after(50, check_keys)

# Exit Button
exit_button = ttk.Button(root, text="Exit", command=root.quit, style="TButton")
exit_button.pack(pady=10)

# ----------
# TRIGGERS:
# Whenever speed or offsets change, send updates
# ----------
speed_var.trace("w", send_all_updates)
rangeX_var.trace("w", send_all_updates)
rangeY_var.trace("w", send_all_updates)

# -----------------------
# Initialize the GUI Flow
# -----------------------
ensure_connection()       # Attempt to connect station -> AP
root.after(50, check_keys)
root.mainloop()
