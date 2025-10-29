"""
Hardware Interface - Raspberry Pi Implementation
Implementasi untuk Raspberry Pi 5 dengan hardware sesungguhnya.

Hardware yang diperlukan:
- Raspberry Pi 5
- Pi Camera Module (atau USB Webcam)
- Proximity Sensor (HC-SR04 atau IR sensor)
- Servo Motor + PCA9685 Servo Driver
- Power supply yang memadai
"""

# PANDUAN SINGKAT (RPi5): KAMERA & SERVO DI FILE INI
# - Kamera: otomatis pilih PiCamera2 jika tersedia, kalau tidak pakai USB webcam (OpenCV).
#   Ubah manual via argumen: `python3 main.py --camera 0`.
#   Cek deteksi: `python3 -m src.core.camera_detector`.
# - Servo (opsi PCA9685): atur channel & sudut default di bagian "Servo Configuration"
#   → `self.SERVO_CHANNEL`, `self.SERVO_ANGLE_BIN_A/B/NEUTRAL` (legacy untuk mode PCA9685)
#   Untuk 3-servo (GPIO PWM langsung), gunakan `src/hardware/three_servo_hardware.py`
#   dan set derajat di `config.py` (lebih umum dipakai di proyek ini).

import time
import numpy as np
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# RPi GPIO Libraries (install: pip3 install RPi.GPIO)
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("WARNING: RPi.GPIO not found. This is expected on non-RPi systems.")
    GPIO = None

# PiCamera2 (install: pip3 install picamera2)
try:
    from picamera2 import Picamera2
except ImportError:
    print("WARNING: picamera2 not found. Falling back to OpenCV.")
    Picamera2 = None

# Servo Driver (install: pip3 install adafruit-circuitpython-pca9685)
try:
    from board import SCL, SDA
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo
except ImportError:
    print("WARNING: Adafruit libraries not found.")
    PCA9685 = None


class HardwareInterface:
    """
    Hardware interface implementation untuk Raspberry Pi.
    Mengontrol sensor proximity, Pi Camera, dan servo motor.
    """
    
    def __init__(self, camera_index: int = None):
        """
        Inisialisasi hardware interface untuk Raspberry Pi.
        
        Args:
            camera_index: Index kamera (None = auto-detect, 0-4 untuk manual selection)
        """
        # GPIO Pin Configuration
        self.PROXIMITY_SENSOR_PIN = 17  # GPIO pin untuk proximity sensor (sesuaikan!)
        
        # Servo Configuration
        self.SERVO_CHANNEL = 0  # Channel servo di PCA9685
        self.SERVO_ANGLE_BIN_A = 0      # Sudut servo untuk Bin A (Organic)
        self.SERVO_ANGLE_BIN_B = 90     # Sudut servo untuk Bin B (Anorganic)
        self.SERVO_ANGLE_NEUTRAL = 45   # Sudut servo posisi netral
        # CATATAN: Jika kamu memakai 3-servo GPIO (tanpa PCA9685), abaikan pengaturan di atas
        # dan gunakan nilai dari config.py melalui ThreeServoHardware.
        
        # Camera
        self.camera = None
        self.camera_index = camera_index
        self.camera_config = None
        
        # Servo driver
        self.pca = None
        self.servo_motor = None
        
        # State
        self.last_trigger_time = 0
        self.trigger_cooldown = 1.0
        
        # Auto-detect camera if not specified
        if camera_index is None:
            self._auto_detect_camera()
        
        # Initialize components
        self._initialize_gpio()
        self._initialize_camera()
        self._initialize_servo()
        
        print("[HardwareInterface] Raspberry Pi hardware initialized")
    
    def _auto_detect_camera(self):
        """Auto-detect available camera and set camera_index"""
        try:
            from src.core.camera_detector import detect_camera_auto
            
            print("[HardwareInterface] Auto-detecting camera...")
            camera_info = detect_camera_auto()
            
            if camera_info:
                if camera_info['type'] == 'picamera':
                    self.camera_config = camera_info
                    self.camera_index = None  # Use Pi Camera
                    print(f"[HardwareInterface] ✓ Selected: {camera_info['name']}")
                else:
                    self.camera_config = camera_info
                    self.camera_index = camera_info['index']
                    print(f"[HardwareInterface] ✓ Selected: {camera_info['name']} (index {self.camera_index})")
            else:
                print("[HardwareInterface] ⚠ No camera detected, defaulting to index 0")
                self.camera_index = 0
                
        except Exception as e:
            print(f"[HardwareInterface] Camera auto-detection failed: {e}")
            print("[HardwareInterface] Defaulting to camera index 0")
            self.camera_index = 0

    
    def _initialize_gpio(self):
        """Initialize GPIO untuk proximity sensor."""
        if GPIO is None:
            print("[ERROR] RPi.GPIO not available!")
            return
        
        # Setup GPIO mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup proximity sensor pin sebagai input dengan pull-down
        GPIO.setup(self.PROXIMITY_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        print(f"[HardwareInterface] GPIO initialized (Proximity sensor: GPIO{self.PROXIMITY_SENSOR_PIN})")
    
    def _initialize_camera(self):
        """Initialize Pi Camera atau fallback ke USB webcam."""
        
        # Try Pi Camera first
        if Picamera2 is not None:
            try:
                self.camera = Picamera2()
                
                # Configure camera
                camera_config = self.camera.create_still_configuration(
                    main={"size": (640, 480), "format": "RGB888"}
                )
                self.camera.configure(camera_config)
                self.camera.start()
                
                # Warm up camera
                time.sleep(2)
                
                print("[HardwareInterface] Pi Camera initialized (640x480)")
                self.camera_type = "picamera"
                return
            except Exception as e:
                print(f"[WARNING] Failed to initialize Pi Camera: {e}")
                print("[INFO] Falling back to USB webcam...")
        
        # Fallback to OpenCV for USB webcam
        try:
            import cv2
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                raise RuntimeError(f"Cannot open camera {self.camera_index}")
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            print(f"[HardwareInterface] USB Webcam initialized (index: {self.camera_index})")
            self.camera_type = "opencv"
        except Exception as e:
            print(f"[ERROR] Failed to initialize camera: {e}")
            raise
    
    def _initialize_servo(self):
        """Initialize PCA9685 servo driver."""
        if PCA9685 is None:
            print("[ERROR] Adafruit PCA9685 library not available!")
            return
        
        try:
            # Initialize I2C bus
            i2c = busio.I2C(SCL, SDA)
            
            # Initialize PCA9685
            self.pca = PCA9685(i2c)
            self.pca.frequency = 50  # 50Hz untuk servo
            
            # Initialize servo motor
            self.servo_motor = servo.Servo(
                self.pca.channels[self.SERVO_CHANNEL],
                min_pulse=500,
                max_pulse=2500
            )
            
            # Set ke posisi netral
            self.servo_motor.angle = self.SERVO_ANGLE_NEUTRAL
            
            print(f"[HardwareInterface] Servo initialized (Channel {self.SERVO_CHANNEL}, Neutral: {self.SERVO_ANGLE_NEUTRAL}°)")
        
        except Exception as e:
            print(f"[ERROR] Failed to initialize servo: {e}")
            raise
    
    def check_trigger(self) -> bool:
        """
        Baca status proximity sensor.
        
        Returns:
            True jika sensor mendeteksi objek, False jika tidak
        """
        if GPIO is None:
            print("[ERROR] GPIO not available")
            return False
        
        # Implementasi cooldown
        current_time = time.time()
        if current_time - self.last_trigger_time < self.trigger_cooldown:
            return False
        
        # Baca status sensor (HIGH = object detected)
        sensor_state = GPIO.input(self.PROXIMITY_SENSOR_PIN)
        
        if sensor_state == GPIO.HIGH:
            self.last_trigger_time = current_time
            print("[HardwareInterface] ⚡ TRIGGER DETECTED (Proximity sensor)")
            return True
        
        return False
    
    def get_camera_frame(self) -> Optional[np.ndarray]:
        """
        Capture frame dari kamera.
        
        Returns:
            Frame gambar (numpy array BGR format) atau None jika gagal
        """
        if self.camera is None:
            print("[ERROR] Camera not initialized")
            return None
        
        try:
            if self.camera_type == "picamera":
                # Capture dari Pi Camera
                frame = self.camera.capture_array()
                
                # Convert RGB to BGR (OpenCV format)
                import cv2
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
            else:  # opencv
                # Capture dari USB webcam
                ret, frame = self.camera.read()
                
                if not ret or frame is None:
                    print("[ERROR] Failed to capture frame")
                    return None
            
            print(f"[HardwareInterface] 📸 Frame captured ({frame.shape[1]}x{frame.shape[0]})")
            return frame
        
        except Exception as e:
            print(f"[ERROR] Camera capture failed: {e}")
            return None
    
    def sort_to_bin_A(self):
        """
        Gerakkan servo ke Bin A (Organic).
        Servo bergerak ke sudut yang ditentukan (default: 0°).
        """
        if self.servo_motor is None:
            print("[ERROR] Servo not initialized")
            return
        
        try:
            print("╔════════════════════════════════════════╗")
            print("║  🌱 SORTING TO BIN A (ORGANIC)        ║")
            print(f"║  Servo bergerak ke {self.SERVO_ANGLE_BIN_A}°                ║")
            print("╚════════════════════════════════════════╝")
            
            self.servo_motor.angle = self.SERVO_ANGLE_BIN_A
            time.sleep(0.5)  # Tunggu servo selesai bergerak
            
        except Exception as e:
            print(f"[ERROR] Servo movement failed: {e}")
    
    def sort_to_bin_B(self):
        """
        Gerakkan servo ke Bin B (Anorganic).
        Servo bergerak ke sudut yang ditentukan (default: 90°).
        """
        if self.servo_motor is None:
            print("[ERROR] Servo not initialized")
            return
        
        try:
            print("╔════════════════════════════════════════╗")
            print("║  ♻️  SORTING TO BIN B (ANORGANIC)      ║")
            print(f"║  Servo bergerak ke {self.SERVO_ANGLE_BIN_B}°               ║")
            print("╚════════════════════════════════════════╝")
            
            self.servo_motor.angle = self.SERVO_ANGLE_BIN_B
            time.sleep(0.5)  # Tunggu servo selesai bergerak
            
        except Exception as e:
            print(f"[ERROR] Servo movement failed: {e}")
    
    def reset_sorter(self):
        """
        Kembalikan servo ke posisi netral.
        Servo bergerak ke sudut netral (default: 45°).
        """
        if self.servo_motor is None:
            print("[ERROR] Servo not initialized")
            return
        
        try:
            print(f"[HardwareInterface] 🔄 Sorter reset ke posisi netral ({self.SERVO_ANGLE_NEUTRAL}°)")
            self.servo_motor.angle = self.SERVO_ANGLE_NEUTRAL
            time.sleep(0.3)
            
        except Exception as e:
            print(f"[ERROR] Servo reset failed: {e}")
    
    def cleanup(self):
        """Cleanup resources."""
        print("[HardwareInterface] Cleaning up resources...")
        
        # Reset servo to neutral
        if self.servo_motor is not None:
            try:
                self.servo_motor.angle = self.SERVO_ANGLE_NEUTRAL
            except:
                pass
        
        # Cleanup camera
        if self.camera is not None:
            if self.camera_type == "picamera":
                self.camera.stop()
                self.camera.close()
            else:  # opencv
                self.camera.release()
        
        # Cleanup servo driver
        if self.pca is not None:
            try:
                self.pca.deinit()
            except:
                pass
        
        # Cleanup GPIO
        if GPIO is not None:
            GPIO.cleanup()
        
        print("[HardwareInterface] Cleanup complete")


# Configuration helper
def configure_hardware():
    """
    Helper function untuk konfigurasi hardware.
    Edit nilai-nilai di sini sesuai dengan setup hardware Anda.
    """
    config = {
        'proximity_sensor_pin': 17,     # GPIO pin untuk proximity sensor
        'servo_channel': 0,              # Channel servo di PCA9685 (0-15)
        'servo_angle_bin_a': 0,          # Sudut servo untuk Bin A (Organic)
        'servo_angle_bin_b': 90,         # Sudut servo untuk Bin B (Anorganic)
        'servo_angle_neutral': 45,       # Sudut servo posisi netral
        'camera_index': 0,               # 0 untuk Pi Camera, atau index USB webcam
    }
    
    print("Hardware Configuration:")
    print(f"  Proximity Sensor: GPIO{config['proximity_sensor_pin']}")
    print(f"  Servo Channel: {config['servo_channel']}")
    print(f"  Servo Angles: Bin A={config['servo_angle_bin_a']}°, "
          f"Bin B={config['servo_angle_bin_b']}°, Neutral={config['servo_angle_neutral']}°")
    print(f"  Camera Index: {config['camera_index']}")
    
    return config


# Test function
def main():
    """
    Test function untuk hardware interface RPi.
    """
    print("="*60)
    print("Hardware Interface Test (Raspberry Pi)")
    print("="*60)
    print("\nWARNING: This test should only be run on Raspberry Pi!")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Show configuration
        config = configure_hardware()
        print()
        
        # Initialize hardware
        hw = HardwareInterface()
        
        print("\nTesting servo movements...")
        hw.reset_sorter()
        time.sleep(2)
        
        hw.sort_to_bin_A()
        time.sleep(2)
        
        hw.sort_to_bin_B()
        time.sleep(2)
        
        hw.reset_sorter()
        time.sleep(1)
        
        print("\nTesting camera...")
        frame = hw.get_camera_frame()
        if frame is not None:
            print(f"✓ Camera working! Frame shape: {frame.shape}")
        
        print("\nTesting proximity sensor...")
        print("Trigger the proximity sensor to test...")
        
        for i in range(50):
            if hw.check_trigger():
                print("✓ Proximity sensor triggered!")
                break
            time.sleep(0.1)
        
        print("\n✓ All tests completed!")
        
        hw.cleanup()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        if 'hw' in locals():
            hw.cleanup()
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        if 'hw' in locals():
            hw.cleanup()


if __name__ == "__main__":
    main()
