#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

// -----------------------
// Adjust to your settings
// -----------------------
const char* ssid     = "UPCCF182B2";     // Home Wi-Fi SSID
const char* password = "pk2wdspN6sty";   // Home Wi-Fi Password

const char* apSSID     = "ESP32_Controller"; // AP fallback SSID
const char* apPassword = "12345678";

WiFiUDP udp;
const int udpPort = 4210; // UDP port

// Servo Setup
Servo servoX;
Servo servoY;

const int servoXPin = 19; // left-right
const int servoYPin = 18; // forward-backward

// Current servo positions
int servoXPos   = 90;   // current servo X position
int servoYPos   = 150;  // current servo Y position

// Movement parameters
int stepDelay   = 10;       // ms per 1-degree step
int rangeOffsetX = 30;      // ± degrees from X neutral
int rangeOffsetY = 30;      // ± degrees from Y neutral

// -----------------------------
// Incremental movement control
// -----------------------------
// Direction variables for each axis: 
//   -1 => move left/forward, 
//    0 => stop (return to neutral), 
//   +1 => move right/backward
int xDirection = 0;
int yDirection = 0;

// Keep track of when we last moved the servo (non-blocking)
unsigned long lastMoveTime = 0;

// Wi-Fi mode
bool apModeActive      = false;
unsigned long lastWiFiCheck   = 0;
const unsigned long wifiCheckPeriod = 10000;
int reconnectAttempts  = 0;

// ----------------------------------------------------
// Original function you wanted to keep (unused for w/s/a/d/x/y):
void moveServoSmooth(Servo &servo, int &currentPos, int targetPos) {
  Serial.printf("Moving servo from %d to %d\n", currentPos, targetPos);
  while (currentPos != targetPos) {
    if (currentPos < targetPos) {
      currentPos++;
    } else {
      currentPos--;
    }
    servo.write(currentPos);
    delay(stepDelay);
  }
  Serial.printf("Final position: %d\n", currentPos);
}

// ----------------------------------------------------
// Connect to Wi-Fi
bool connectToWiFi() {
  Serial.println("Trying to connect to home Wi-Fi...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 10) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to Home Wi-Fi!");
    Serial.print("ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
    return true;
  }
  return false;
}

// ----------------------------------------------------
void startHotspot() {
  Serial.println("\nStarting Hotspot...");
  WiFi.mode(WIFI_AP);
  WiFi.softAP(apSSID, apPassword);

  Serial.print("ESP32 Hotspot IP Address: ");
  Serial.println(WiFi.softAPIP());
  apModeActive = true;
}

// ----------------------------------------------------
// Non-blocking incremental movement: Called every loop
// Moves the servos step-by-step based on xDirection / yDirection
// and returns them to neutral (90 for X, 150 for Y) when direction = 0
void incrementalMove() {
  unsigned long now = millis();

  // Move only if enough time has passed
  if (now - lastMoveTime >= (unsigned long)stepDelay) {
    lastMoveTime = now;

    // --------------------------
    // X Axis
    // --------------------------
    if (xDirection == -1) {
      // Move left until we hit (90 - rangeOffsetX)
      if (servoXPos > (90 - rangeOffsetX)) {
        servoXPos--;
      }
      // else we are at limit
    }
    else if (xDirection == +1) {
      // Move right until we hit (90 + rangeOffsetX)
      if (servoXPos < (90 + rangeOffsetX)) {
        servoXPos++;
      }
      // else we are at limit
    }
    else {
      // xDirection == 0 => Move back to neutral (90)
      if (servoXPos < 90) {
        servoXPos++;
      } else if (servoXPos > 90) {
        servoXPos--;
      }
      // else at neutral
    }
    servoX.write(servoXPos);

    // --------------------------
    // Y Axis
    // --------------------------
    if (yDirection == -1) {
      // Move forward until (150 - rangeOffsetY)
      if (servoYPos > (150 - rangeOffsetY)) {
        servoYPos--;
      }
      // else we are at limit
    }
    else if (yDirection == +1) {
      // Move backward until (150 + rangeOffsetY)
      if (servoYPos < (150 + rangeOffsetY)) {
        servoYPos++;
      }
      // else we are at limit
    }
    else {
      // yDirection == 0 => Move back to neutral (150)
      if (servoYPos < 150) {
        servoYPos++;
      } else if (servoYPos > 150) {
        servoYPos--;
      }
      // else at neutral
    }
    servoY.write(servoYPos);
  }
}

// ----------------------------------------------------
void setup() {
  Serial.begin(115200);

  // Try to connect to Wi-Fi first
  if (!connectToWiFi()) {
    startHotspot();
  } else {
    apModeActive = false;
  }

  udp.begin(udpPort);
  Serial.print("Listening on UDP port ");
  Serial.println(udpPort);

  servoX.attach(servoXPin);
  servoY.attach(servoYPin);
  servoX.write(servoXPos);
  servoY.write(servoYPos);
}

// ----------------------------------------------------
void loop() {
  // Check Wi-Fi periodically if in station mode
  if (!apModeActive && (millis() - lastWiFiCheck > wifiCheckPeriod)) {
    lastWiFiCheck = millis();

    if (WiFi.status() != WL_CONNECTED) {
      reconnectAttempts++;
      Serial.println("\nWi-Fi disconnected. Attempting reconnect...");
      if (!connectToWiFi()) {
        Serial.println("Failed to reconnect. Starting Hotspot.");
        startHotspot();
      } else {
        apModeActive = false;
        reconnectAttempts = 0;
      }
    }
  }

  // Perform the incremental servo movement each loop
  incrementalMove();

  // Check for incoming packets
  char packet[50];
  int packetSize = udp.parsePacket();
  if (packetSize > 0) {
    udp.read(packet, sizeof(packet) - 1);
    packet[packetSize] = '\0';
    String received = String(packet);

    Serial.print("Received: ");
    Serial.println(received);

    // -----------------------------
    // SPEED (SPD) and OFFSET (RNG)
    // -----------------------------
    if (received.startsWith("SPD:")) {
      int newSpeed = received.substring(4).toInt();
      if (newSpeed > 0 && newSpeed < 200) {
        stepDelay = newSpeed;
        Serial.print("Updated stepDelay to: ");
        Serial.println(stepDelay);
      }
      return;
    } 
    else if (received.startsWith("RNG:")) {
      // Retained for backward compatibility:
      // This sets both offsets at once
      int newRange = received.substring(4).toInt();
      if (newRange >= 10 && newRange <= 90) {
        rangeOffsetX = newRange;
        rangeOffsetY = newRange;
        Serial.print("Updated BOTH rangeOffsetX & rangeOffsetY to: ");
        Serial.println(newRange);
      }
      return;
    }
    else if (received.startsWith("RNX:")) {
      // New command to set X offset only
      int newRangeX = received.substring(4).toInt();
      if (newRangeX >= 10 && newRangeX <= 90) {
        rangeOffsetX = newRangeX;
        Serial.print("Updated rangeOffsetX to: ");
        Serial.println(rangeOffsetX);
      }
      return;
    }
    else if (received.startsWith("RNY:")) {
      // New command to set Y offset only
      int newRangeY = received.substring(4).toInt();
      if (newRangeY >= 10 && newRangeY <= 90) {
        rangeOffsetY = newRangeY;
        Serial.print("Updated rangeOffsetY to: ");
        Serial.println(rangeOffsetY);
      }
      return;
    }

    // ----------------------------------------------------------
    // MOVEMENT COMMANDS (Incremental Instead of moveServoSmooth)
    // ----------------------------------------------------------
    // Y-Axis
    if (received.indexOf('w') != -1) {
      Serial.println("Command: Forward (w)");
      // Move servo Y forward => direction = -1
      yDirection = -1;
    }
    else if (received.indexOf('s') != -1) {
      Serial.println("Command: Backward (s)");
      // Move servo Y backward => direction = +1
      yDirection = +1;
    }
    else if (received.indexOf('y') != -1) {
      Serial.println("Command: Stop Y (y) => return to neutral");
      // Stop Y => direction = 0 => servo returns to 150
      yDirection = 0;
    }

    // X-Axis
    if (received.indexOf('a') != -1) {
      Serial.println("Command: Left (a)");
      // Move servo X left => direction = -1
      xDirection = -1;
    }
    else if (received.indexOf('d') != -1) {
      Serial.println("Command: Right (d)");
      // Move servo X right => direction = +1
      xDirection = +1;
    }
    else if (received.indexOf('x') != -1) {
      Serial.println("Command: Stop X (x) => return to neutral");
      // Stop X => direction = 0 => servo returns to 90
      xDirection = 0;
    }
  }
}
