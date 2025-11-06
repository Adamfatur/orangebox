"""
Hardware Interface - Raspberry Pi Implementation
Implementasi untuk Raspberry Pi 5 dengan hardware sesungguhnya.

Hardware yang diperlukan:
- Raspberry Pi 5
- Pi Camera Module (atau USB Webcam)
- 7x Servo Motor MG996R + PCA9685 I2C Servo Driver
- Power supply yang memadai (5V 3A untuk Pi, 5V 10A untuk servo)
"""

# PANDUAN SINGKAT (RPi5): KAMERA & SERVO DI FILE INI
# - Kamera: otomatis pilih PiCamera2 jika tersedia, kalau tidak pakai USB webcam (OpenCV).
#   Ubah manual via argumen: `python3 main.py --camera 0`.
#   Cek deteksi: `python3 -m src.core.camera_detector`.
# - Servo: Sistem menggunakan 7-servo dengan PCA9685 I2C driver
#   Konfigurasi ada di config.py (SERVO_DRIVER = 'seven_servo')
#   Channel mapping: CH0-6 untuk 4 corners, 2 locks, 1 selector

# CRITICAL: Fix Qt platform plugin error on Raspberry Pi
# OpenCV tries to use Wayland but it's not available in venv
# Force X11 backend or headless mode
import os
if 'QT_QPA_PLATFORM' not in os.environ:
    # Try X11 first (most common on Raspberry Pi Desktop)
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    # If xcb fails, OpenCV will auto-fallback to offscreen mode

import time
import numpy as np
from typing import Optional
import sys
import cv2
import config

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# PiCamera2 (install: sudo apt install python3-picamera2)
try:
    from picamera2 import Picamera2
except ImportError:
    print("WARNING: picamera2 not found. Falling back to OpenCV.")
    Picamera2 = None

# Servo Driver - NOT USED in hardware_interface_rpi.py
# Servo control is handled by seven_servo_hardware.py via MainController
# This file only handles camera operations
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
    Mengontrol Pi Camera dan servo motor.
    """
    
    def __init__(self, camera_index: Optional[int] = None):
        """
        Initialize hardware interface.
        
        Args:
            camera_index: Index kamera (0, 1, 2...). None = auto-detect
        """
        print("[HardwareInterface] Initializing...")
        
        # Camera
        self.camera = None
        self.camera_index = camera_index
        self.camera_config = None
        
        # State
        self.last_trigger_time = 0
        self.trigger_cooldown = 1.0
        # Preview window name (for OpenCV display)
        self.window_name = "Orange Box - Camera View"
        # Logo (untuk fancy UI)
        self._logo = None
        # Camera logging control (avoid spam)
        self._last_frame_log_time = 0
        self._frame_log_interval = 5.0  # seconds
        
        # Auto-detect camera if not specified
        if camera_index is None:
            self._auto_detect_camera()
        
        # Initialize hardware components
        self._initialize_camera()
        
        print("[HardwareInterface] ✓ Hardware initialization complete")
    
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
                print("[HardwareInterface] ⚠️  No camera detected")
                print("[HardwareInterface] System will attempt to use index 0")
                print("[HardwareInterface] If camera fails, check connection and reboot")
                self.camera_index = 0
                
        except Exception as e:
            print(f"[HardwareInterface] ⚠️  Camera auto-detection error: {e}")
            print("[HardwareInterface] Attempting fallback to index 0")
            self.camera_index = 0

    
    
    def _initialize_camera(self):
        """
        Initialize Pi Camera atau fallback ke USB webcam.
        
        CRITICAL: PiCamera2 can segfault on some systems.
        Using OpenCV fallback for stability.
        """
        
        # Decide backend based on detection result
        use_picamera = False
        try:
            if getattr(self, 'camera_config', None) and self.camera_config.get('type') == 'picamera' and Picamera2 is not None:
                use_picamera = True
        except Exception:
            use_picamera = False

        if use_picamera:
            try:
                print("[HardwareInterface] Initializing PiCamera2...")
                self.camera = Picamera2()
                
                # Configure camera
                camera_config = self.camera.create_still_configuration(
                    main={"size": (640, 480), "format": "RGB888"}
                )
                self.camera.configure(camera_config)
                
                # Start camera
                print("[HardwareInterface] Starting camera...")
                self.camera.start()
                
                # CRITICAL: Camera warm-up with retry
                print("[HardwareInterface] Warming up Pi Camera...")
                frame_ok = False
                max_attempts = 10
                
                for attempt in range(max_attempts):
                    try:
                        test_frame = self.camera.capture_array()
                        if test_frame is not None and test_frame.size > 0:
                            frame_ok = True
                            print(f"[HardwareInterface] ✓ Pi Camera ready after {attempt + 1} attempts")
                            break
                        time.sleep(0.2)
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            time.sleep(0.2)
                            continue
                        else:
                            raise RuntimeError(f"Pi Camera failed to capture: {e}")
                
                if not frame_ok:
                    raise RuntimeError("Pi Camera cannot capture frames")
                
                print("[HardwareInterface] ✓ Pi Camera initialized (640x480)")
                self.camera_type = "picamera"
                return
                
            except Exception as e:
                print(f"[HardwareInterface] ⚠️  PiCamera2 failed: {e}")
                print("[HardwareInterface] Falling back to OpenCV USB webcam...")
                # Clean up failed picamera
                try:
                    if hasattr(self, 'camera') and self.camera:
                        self.camera.close()
                except:
                    pass
        else:
            print("[HardwareInterface] Using OpenCV (USB/V4L2) for camera")
        
        # Use OpenCV for USB webcam (more stable)
        try:
            import cv2
            
            # Try camera index
            cam_idx = self.camera_index if self.camera_index is not None else 0
            
            print(f"[HardwareInterface] Opening camera at index {cam_idx}...")
            # Prefer V4L2 backend to avoid GStreamer issues on RPi
            self.camera = cv2.VideoCapture(cam_idx, cv2.CAP_V4L2)
            if not self.camera.isOpened():
                # Fallback to default backend
                self.camera = cv2.VideoCapture(cam_idx)
            
            if not self.camera.isOpened():
                # Try other indices
                print(f"[HardwareInterface] Camera {cam_idx} failed, trying alternatives...")
                for idx in range(0, 4):
                    if idx == cam_idx:
                        continue
                    print(f"[HardwareInterface]   Trying index {idx}...")
                    self.camera = cv2.VideoCapture(idx, cv2.CAP_V4L2)
                    if not self.camera.isOpened():
                        self.camera = cv2.VideoCapture(idx)
                    if self.camera.isOpened():
                        cam_idx = idx
                        break
                
                if not self.camera.isOpened():
                    raise RuntimeError(f"Cannot open any camera (tried 0-3)")
            
            # Set resolution and preferred MJPG format for stability/perf on RPi
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Try MJPG format for better performance (optional - may not work on all cameras)
            try:
                self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.camera.set(cv2.CAP_PROP_FPS, 30)
            except Exception:
                pass  # Ignore if not supported
            
            # CRITICAL: Camera warm-up with retry mechanism
            # Some cameras (especially on RPi5) need multiple reads before working
            print("[HardwareInterface] Warming up camera...")
            frame_ok = False
            max_warmup_attempts = 20  # Try up to 20 times
            
            for attempt in range(max_warmup_attempts):
                try:
                    ret, test_frame = self.camera.read()
                    if ret and test_frame is not None and test_frame.size > 0:
                        frame_ok = True
                        print(f"[HardwareInterface] ✓ Camera ready after {attempt + 1} attempts")
                        break
                    time.sleep(0.1)  # Wait between attempts
                except Exception as e:
                    if attempt < max_warmup_attempts - 1:
                        time.sleep(0.1)
                        continue
                    else:
                        raise
            
            if not frame_ok:
                raise RuntimeError(
                    f"Camera at index {cam_idx} opened but cannot read frames.\n"
                    f"Possible causes:\n"
                    f"  - Camera needs more initialization time\n"
                    f"  - Driver issue (try different camera)\n"
                    f"  - Permission issue (add user to 'video' group)\n"
                    f"  - For Pi Camera: use 'libcamera-hello' to test\n"
                    f"  - For USB Camera: check 'v4l2-ctl --list-devices'"
                )
            
            # Get final frame info
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"[HardwareInterface] ✓ USB Webcam initialized")
            print(f"[HardwareInterface]   Index: {cam_idx}")
            print(f"[HardwareInterface]   Resolution: {actual_width}x{actual_height}")
            self.camera_type = "opencv"
            
        except Exception as e:
            print(f"[HardwareInterface] ❌ Camera initialization failed: {e}")
            print("[HardwareInterface] System cannot run without camera!")
            self.camera = None
            self.camera_type = None
            raise
    
    def _initialize_servo(self):
        """
        Initialize PCA9685 servo driver.
        
        CRITICAL: Servo should NOT move during initialization!
        Only prepare the driver, do NOT set any angles yet.
        """
        if PCA9685 is None:
            print("[HardwareInterface] PCA9685 library not available - servo disabled")
            self.servo_motor = None
            self.pca = None
            return
        
        try:
            # Initialize I2C bus
            i2c = busio.I2C(SCL, SDA)
            
            # Initialize PCA9685
            self.pca = PCA9685(i2c)
            self.pca.frequency = 50  # 50Hz untuk servo
            
            # Initialize servo motor object (but do NOT move it yet!)
            self.servo_motor = servo.Servo(
                self.pca.channels[self.SERVO_CHANNEL],
                min_pulse=500,
                max_pulse=2500
            )
            
            # CRITICAL: DO NOT set servo angle during init!
            # Servo will move only when explicitly commanded by sorting logic
            # Old buggy code: self.servo_motor.angle = self.SERVO_ANGLE_NEUTRAL  # ← REMOVED!
            
            print(f"[HardwareInterface] Servo driver initialized (Channel {self.SERVO_CHANNEL})")
            print(f"[HardwareInterface] ⚠️  Servo will move ONLY after classification")
        
        except Exception as e:
            print(f"[HardwareInterface] Failed to initialize servo: {e}")
            print(f"[HardwareInterface] Servo functionality disabled")
            self.servo_motor = None
            self.pca = None
    
    def check_trigger(self) -> bool:
        """
        Check for trigger event.
        
        Note: Trigger logic is handled by MainController's motion detection.
        This method is deprecated and always returns False.
        
        Returns:
            False (trigger via motion detection)
        """
        return False
    
    def get_camera_frame(self) -> Optional[np.ndarray]:
        """
        Capture frame dari kamera.
        
        Returns:
            Frame gambar (numpy array BGR format) atau None jika gagal
        """
        if self.camera is None:
            print("[HardwareInterface] ❌ Camera not initialized")
            return None
            
        try:
            if self.camera_type == "picamera":
                # Capture dari Pi Camera
                frame = self.camera.capture_array()
                if frame is None or frame.size == 0:
                    print("[HardwareInterface] ⚠️  Pi Camera returned empty frame")
                    return None
                # Convert RGB to BGR (OpenCV format)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
            else:
                # Capture dari USB webcam
                ret, frame = self.camera.read()
                if not ret or frame is None or frame.size == 0:
                    print("[HardwareInterface] ⚠️  Camera read failed (empty frame)")
                    print("[HardwareInterface] 💡 Try: restart camera or reboot system")
                    return None
                    
            # Rate-limit camera capture logs to avoid spam
            try:
                now = time.time()
                if (now - self._last_frame_log_time) >= self._frame_log_interval:
                    print(f"[HardwareInterface] 📸 Frame captured ({frame.shape[1]}x{frame.shape[0]})")
                    self._last_frame_log_time = now
            except Exception:
                pass
                
            return frame
            
        except Exception as e:
            print(f"[HardwareInterface] ❌ Camera capture error: {e}")
            print(f"[HardwareInterface] 💡 Camera may have disconnected or need restart")
            return None

    # ====== UI Helpers (ported minimal dari mock untuk selaraskan gaya) ======
    def _load_logo(self):
        """Muat logo dari assets jika tersedia (opsional)."""
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'logo-orangebox.png')
            if os.path.exists(logo_path):
                logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
                if logo is not None and logo.shape[2] == 4:
                    # Convert RGBA to BGR (drop alpha for simple overlay)
                    self._logo = cv2.cvtColor(logo, cv2.COLOR_BGRA2BGR)
                else:
                    self._logo = logo
        except Exception:
            self._logo = None

    def _overlay_logo(self, img, logo, x, y):
        try:
            if logo is None:
                return
            h, w = logo.shape[:2]
            roi = img[y:y+h, x:x+w]
            if roi.shape[:2] != (h, w):
                return
            # Simple paste (no alpha blending for performance)
            img[y:y+h, x:x+w] = logo
        except Exception:
            pass

    def _draw_filled_rounded_rect(self, img, x, y, w, h, color, radius=10):
        try:
            radius = max(0, min(radius, min(w, h)//2))
            # Center rectangle
            cv2.rectangle(img, (x+radius, y), (x+w-radius, y+h), color, -1)
            # Side rectangles
            cv2.rectangle(img, (x, y+radius), (x+w, y+h-radius), color, -1)
            # Corners
            cv2.circle(img, (x+radius, y+radius), radius, color, -1)
            cv2.circle(img, (x+w-radius-1, y+radius), radius, color, -1)
            cv2.circle(img, (x+radius, y+h-radius-1), radius, color, -1)
            cv2.circle(img, (x+w-radius-1, y+h-radius-1), radius, color, -1)
        except Exception:
            pass

    def _put_text_with_shadow(self, img, text, org, font, scale, color, thickness=1, shadow_color=(0,0,0)):
        try:
            x, y = org
            cv2.putText(img, text, (x+1, y+1), font, scale, shadow_color, thickness+2, cv2.LINE_AA)
            cv2.putText(img, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)
        except Exception:
            pass

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

    def display_frame(self, frame: np.ndarray, text: str = "",
                      prediction: Optional[dict] = None):
        """
        Tampilkan frame kamera dengan overlay informasi sederhana menggunakan OpenCV.
        
        CRITICAL: Handle headless mode (SSH/no DISPLAY) gracefully.
        
        Args:
            frame: Frame gambar (numpy array, BGR)
            text: Teks status utama
            prediction: Info status/prediksi (opsional)
        """
        try:
            if frame is None:
                return
            
            # Check if we can display (not headless/SSH)
            can_display = True
            if os.environ.get('DISPLAY') is None or os.environ.get('DISPLAY') == '':
                can_display = False
            
            if not can_display:
                # Headless mode - just log status, no display
                if prediction:
                    print(f"[Camera] Status: {text} | Prediction: {prediction.get('label', 'N/A')} ({prediction.get('confidence', 0):.1%})")
                else:
                    print(f"[Camera] Status: {text}")
                return
            
            display = frame.copy()
            h, w = display.shape[:2]
            font = cv2.FONT_HERSHEY_SIMPLEX

            if getattr(config, 'FANCY_UI', False):
                # Fancy top bar
                bar_h = 70
                self._draw_filled_rounded_rect(display, 6, 6, w-12, bar_h, (28,28,32), radius=12)
                # Logo dan judul
                logo_x, logo_y = 16, 15
                if self._logo is not None:
                    self._overlay_logo(display, self._logo, logo_x, logo_y)
                    text_x = logo_x + self._logo.shape[1] + 12
                else:
                    text_x = logo_x + 4
                self._put_text_with_shadow(display, "Orange Box", (text_x, 30), font, 0.75, (230,230,235), thickness=2)
            else:
                # Minimal top bar
                cv2.rectangle(display, (0, 0), (w, 60), (40, 40, 45), -1)
                cv2.putText(display, "Orange Box", (12, 28), font, 0.8, (235,235,240), 2, cv2.LINE_AA)

            # Determine status text
            status_text = text.strip() if text else ""
            if not status_text and prediction and isinstance(prediction, dict):
                status_text = str(prediction.get("status", ""))
            if status_text:
                if getattr(config, 'FANCY_UI', False):
                    cv2.circle(display, (14, 46), 5, (0, 200, 255), -1)
                    self._put_text_with_shadow(display, status_text, (26, 50), font, 0.55, (210,210,215), thickness=1)
                else:
                    cv2.circle(display, (14, 46), 5, (0, 200, 255), -1)
                    cv2.putText(display, status_text, (26, 50), font, 0.55, (210,210,215), 1, cv2.LINE_AA)

            # Draw bbox if provided
            if prediction and isinstance(prediction, dict) and prediction.get("bbox"):
                x1, y1, x2, y2 = prediction["bbox"]
                if getattr(config, 'FANCY_UI', False):
                    corner_len = max(12, (x2-x1)//7)
                    color = (0, 200, 255)
                    cv2.line(display, (x1, y1), (x1+corner_len, y1), color, 2)
                    cv2.line(display, (x1, y1), (x1, y1+corner_len), color, 2)
                    cv2.line(display, (x2, y1), (x2-corner_len, y1), color, 2)
                    cv2.line(display, (x2, y1), (x2, y1+corner_len), color, 2)
                    cv2.line(display, (x1, y2), (x1+corner_len, y2), color, 2)
                    cv2.line(display, (x1, y2), (x1, y2-corner_len), color, 2)
                    cv2.line(display, (x2, y2), (x2-corner_len, y2), color, 2)
                    cv2.line(display, (x2, y2), (x2, y2-corner_len), color, 2)
                else:
                    cv2.rectangle(display, (x1, y1), (x2, y2), (0, 200, 255), 2)

            # Show label & confidence (simple badge)
            if prediction and isinstance(prediction, dict) and prediction.get("label"):
                label = str(prediction.get("label", "")).upper()
                conf = float(prediction.get("confidence", 0.0))
                badge = f"{label}  {conf*100:.1f}%"
                # Badge background
                size, _ = cv2.getTextSize(badge, font, 0.6, 2)
                bx, by = 12, 68
                bw, bh = size[0] + 16, size[1] + 14
                if getattr(config, 'FANCY_UI', False):
                    self._draw_filled_rounded_rect(display, bx, by, bw, bh, (32,34,38), radius=8)
                    self._put_text_with_shadow(display, badge, (bx+10, by+bh-8), font, 0.6, (240,240,240), thickness=2)
                else:
                    cv2.rectangle(display, (bx, by), (bx+bw, by+bh), (32, 34, 38), -1)
                    cv2.putText(display, badge, (bx+10, by+bh-8), font, 0.6, (240,240,240), 2, cv2.LINE_AA)

            # Location chip (bottom-left)
            if prediction and isinstance(prediction, dict) and prediction.get("location"):
                loc = str(prediction["location"])[:64]
                size, _ = cv2.getTextSize(loc, font, 0.5, 1)
                lx, ly = 10, h - 18
                if getattr(config, 'FANCY_UI', False):
                    self._draw_filled_rounded_rect(display, lx-4, ly-size[1]-10, size[0]+12, size[1]+16, (30,35,40), radius=10)
                    self._put_text_with_shadow(display, loc, (lx, ly), font, 0.5, (100,200,255), thickness=1)
                else:
                    cv2.rectangle(display, (lx-4, ly-size[1]-10), (lx+size[0]+8, ly+6), (30, 35, 40), -1)
                    cv2.putText(display, loc, (lx, ly), font, 0.5, (100, 200, 255), 1, cv2.LINE_AA)

            # Instruction pill (bottom-right)
            instr = "Tekan 'q' untuk keluar"
            size, _ = cv2.getTextSize(instr, font, 0.5, 1)
            px, py = w - size[0] - 20, h - 18
            if getattr(config, 'FANCY_UI', False):
                self._draw_filled_rounded_rect(display, px-10, py-size[1]-10, size[0]+20, size[1]+16, (30,30,34), radius=14)
                self._put_text_with_shadow(display, instr, (px, py), font, 0.5, (245,245,245), thickness=1)
            else:
                cv2.rectangle(display, (px-10, py-size[1]-10), (px+size[0]+10, py+6), (30, 30, 34), -1)
                cv2.putText(display, instr, (px, py), font, 0.5, (245, 245, 245), 1, cv2.LINE_AA)

            # Render dengan ukuran konsisten agar teks tajam
            try:
                base_w, base_h = 1280, 720
                if display.shape[1] != base_w or display.shape[0] != base_h:
                    display = cv2.resize(display, (base_w, base_h), interpolation=cv2.INTER_LINEAR)
            except Exception:
                pass
            
            # Try to display frame
            try:
                cv2.imshow(self.window_name, display)
                cv2.waitKey(1)
            except cv2.error as e:
                # Display failed (headless/SSH mode likely)
                if 'DISPLAY' not in os.environ or os.environ.get('DISPLAY') == '':
                    # Silent fail - headless mode
                    pass
                else:
                    print(f"[WARNING] Display error (headless mode?): {e}")
                    print(f"[INFO] Running in headless mode - camera feed disabled")
                    # Set env to prevent further attempts
                    os.environ['DISPLAY'] = ''
                    
        except Exception as e:
            # Jangan ganggu alur utama jika preview gagal
            print(f"[WARNING] Display frame error: {e}")
            pass

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
        
        # Close preview windows (if any)
        try:
            import cv2
            cv2.destroyAllWindows()
        except Exception:
            pass

        print("[HardwareInterface] Cleanup complete")


# Configuration helper
def configure_hardware():
    """
    Helper function untuk konfigurasi hardware.
    Edit nilai-nilai di sini sesuai dengan setup hardware Anda.
    """
    config = {
        'servo_channel': 0,              # Channel servo di PCA9685 (0-15)
        'servo_angle_bin_a': 0,          # Sudut servo untuk Bin A (Organic)
        'servo_angle_bin_b': 90,         # Sudut servo untuk Bin B (Anorganic)
        'servo_angle_neutral': 45,       # Sudut servo posisi netral
        'camera_index': 0,               # 0 untuk Pi Camera, atau index USB webcam
    }
    
    print("Hardware Configuration:")
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
