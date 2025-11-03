"""
Main Controller for OrangeBox Waste Sorting System
Finite State Machine implementation

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

import time
import cv2
from enum import Enum
from typing import Optional
import numpy as np
import config
from hardware.gpio_servo_hardware import GpioServoHardware
try:
    from hardware.five_servo_hardware import FiveServoHardware
except Exception:
    FiveServoHardware = None


class State(Enum):
    """Enum untuk state machine."""
    IDLE = "IDLE"
    INSPECTING = "INSPECTING"
    CLASSIFYING = "CLASSIFYING"
    SORTING_A = "SORTING_A"
    SORTING_B = "SORTING_B"


class MainController:
    """
    Main Controller dengan Finite State Machine.
    Kode ini 100% portabel - tidak ada perbedaan antara Mac dan RPi.
    """
    
    def __init__(self, classifier, hardware_interface):
        """
        Inisialisasi Main Controller.
        
        Args:
            classifier: Instance dari WasteClassifier
            hardware_interface: Instance dari HardwareInterface (Mock atau RPi)
        """
        self.classifier = classifier
        self.hw = hardware_interface
        # Integrasi controller servo untuk urutan sorting lengkap
        # Pilih 5-servo (ServoKit/PCA9685) jika dikonfigurasi, fallback ke 3-servo (GPIO)
        driver = getattr(config, 'SERVO_DRIVER', 'gpio').lower()
        if driver == 'servokit' and FiveServoHardware is not None:
            print("[MainController] Using 5-Servo hardware (ServoKit/PCA9685)")
            self.servo_hw = FiveServoHardware()
        else:
            print("[MainController] Using GPIO Servo hardware (PWM)")
            self.servo_hw = GpioServoHardware()
        self.current_state = State.IDLE
        self.running = False
        
        # Current frame and prediction storage
        self.current_frame = None
        self.current_prediction = None
        
        # Background subtraction for object detection
        self.background_frame = None
        # Optional: MOG2 background subtractor (better for shadows)
        self.use_mog2 = getattr(config, 'USE_MOG2', False)
        self.mog2 = None
        if self.use_mog2:
            self.mog2 = cv2.createBackgroundSubtractorMOG2(
                history=getattr(config, 'MOG2_HISTORY', 300),
                varThreshold=getattr(config, 'MOG2_VAR_THRESHOLD', 16),
                detectShadows=getattr(config, 'MOG2_DETECT_SHADOWS', True)
            )
        self.frame_buffer = []
        self.motion_threshold = getattr(config, 'MOTION_THRESHOLD', 1500)
        self.stabilization_frames = getattr(config, 'STABILIZATION_FRAMES', 5)
        self.frame_skip = 2  # Kurangi dari 3 ke 2 untuk lebih responsif
        self.frame_counter = 0
        # Edge-triggered motion detection dengan hysteresis
        self.motion_enter_threshold = getattr(config, 'MOTION_ENTER_THRESHOLD', self.motion_threshold)
        self.motion_exit_threshold = getattr(config, 'MOTION_EXIT_THRESHOLD', int(self.motion_enter_threshold * 0.5))
        self.motion_consecutive_required = getattr(config, 'MOTION_CONSECUTIVE_REQUIRED', self.stabilization_frames)
        self.still_frames_to_reset = getattr(config, 'MOTION_STILL_FRAMES_RESET', 8)
        self.cooldown_ms = getattr(config, 'COOLDOWN_MS', 1500)
        self.in_cooldown = False
        self.cooldown_until = 0
        self.consecutive_motion = 0
        self.consecutive_still = 0
        
        # Object stabilization timing
        self.object_stabilization_delay = getattr(config, 'OBJECT_STABILIZATION_DELAY', 3.0)
        self.stabilization_max_wait = getattr(config, 'STABILIZATION_MAX_WAIT', 5.0)
        self.object_detected_time = 0
        self.last_detection_print_time = 0  # Prevent spam
        
        # Processing lock - block new detection while processing current object
        self.is_processing = False
        self.last_roi_rect = None  # (x1,y1,x2,y2) pada frame asli saat trigger
        # Re-arm background after cooldown to avoid ghost re-triggers
        self.rearm_until_ms = 0
        # Keep a reference full-size frame for stable preview
        self.last_full_frame = None
        
        # Configuration
        self.stabilization_delay = 0.5  # Detik untuk stabilisasi objek
        self.sorting_duration = 2.0     # Detik untuk proses sorting
        self.confidence_threshold = getattr(config, 'CONFIDENCE_THRESHOLD', 0.6)
        # Distance/ROI gating
        self.min_roi_area_ratio = getattr(config, 'MIN_ROI_AREA_RATIO', 0.04)
        self.enable_distance_estimation = getattr(config, 'ENABLE_DISTANCE_ESTIMATION', False)
        self.focal_length_px = getattr(config, 'FOCAL_LENGTH_PX', 900.0)
        self.known_object_height_cm = getattr(config, 'KNOWN_OBJECT_HEIGHT_CM', 10.0)
        
        # Statistics
        self.stats = {
            'total_sorted': 0,
            'organic_count': 0,
            'anorganic_count': 0,
            'low_confidence_count': 0
        }
        
        # Location service (GPS/coordinates)
        self.location_service = None
        self.enable_gps = getattr(config, 'ENABLE_GPS', False)
        
        if self.enable_gps:
            try:
                from core.location_service import LocationService
                
                gps_interval = getattr(config, 'GPS_UPDATE_INTERVAL', 300)
                mock_location = getattr(config, 'GPS_MOCK_LOCATION', (-6.2088, 106.8456))
                
                self.location_service = LocationService(
                    platform=config.PLATFORM,
                    mock_location=mock_location
                )
                self.location_service.start_background_update(update_interval=gps_interval)
                
                # Optional: save history
                self.save_gps_history = getattr(config, 'GPS_SAVE_HISTORY', True)
                self.gps_history_file = getattr(config, 'GPS_HISTORY_FILE', 'location_history.jsonl')
                
                print("[MainController] ✓ GPS/Location service initialized")
            except Exception as e:
                print(f"[MainController] ⚠️  GPS initialization failed: {e}")
                print("[MainController] ℹ️  Continuing without GPS service...")
                self.location_service = None
                self.enable_gps = False
        else:
            print("[MainController] ℹ️  GPS disabled (ENABLE_GPS=False in config.py)")
            self.save_gps_history = False
        
        # Database service (MySQL RDS)
        self.database_service = None
        self.device_manager = None
        self.device_id = None
        self.enable_database = getattr(config, 'ENABLE_DATABASE', False)
        if self.enable_database:
            try:
                from src.core.database_service import DatabaseService
                from src.core.device_manager import DeviceManager
                
                # Initialize Device Manager
                self.device_manager = DeviceManager()
                self.device_manager.device_name = getattr(config, 'DEVICE_NAME', None)
                self.device_manager.device_location = getattr(config, 'DEVICE_LOCATION', None)
                
                # Get or generate device ID
                custom_id = getattr(config, 'DEVICE_ID', None)
                self.device_id = self.device_manager.get_device_id(custom_id)
                
                # Print device info
                print("\n" + "="*60)
                print("🔧 DEVICE IDENTIFICATION")
                print("="*60)
                print(f"Device ID:    {self.device_id}")
                print(f"Short ID:     {self.device_manager.generate_short_id()}")
                if self.device_manager.device_name:
                    print(f"Device Name:  {self.device_manager.device_name}")
                if self.device_manager.device_location:
                    print(f"Location:     {self.device_manager.device_location}")
                print("="*60 + "\n")
                
                # Initialize database
                self.database_service = DatabaseService(
                    host=getattr(config, 'DB_HOST'),
                    user=getattr(config, 'DB_USER'),
                    password=getattr(config, 'DB_PASSWORD'),
                    database=getattr(config, 'DB_NAME'),
                    port=getattr(config, 'DB_PORT', 3306)
                )
                
                print(f"[MainController] Database service initialized")
            except Exception as e:
                print(f"[MainController] Warning: Could not initialize database service: {e}")
                self.database_service = None
                self.device_manager = None
                self.device_id = None
                self.enable_database = False
        
        print("[MainController] Initialized")
        print(f"[MainController] Confidence threshold: {self.confidence_threshold}")
    
    def _get_location_info(self) -> Optional[str]:
        """
        Helper untuk mendapatkan string informasi lokasi.
        
        Returns:
            String informasi lokasi atau None jika GPS disabled
        """
        if not self.location_service:
            return None
        
        return self.location_service.get_location_info_string()
    
    def _print_state_transition(self, new_state: State):
        """Helper untuk print transisi state."""
        print(f"\n{'='*60}")
        print(f"STATE TRANSITION: {self.current_state.value} → {new_state.value}")
        print(f"{'='*60}")
        self.current_state = new_state
    
    def _state_idle(self) -> Optional[State]:
        """
        State: IDLE
        - Monitoring untuk OBJEK BARU dengan motion detection
        - Background kosong = TIDAK deteksi apapun
        - Objek masuk = Trigger inspeksi dan klasifikasi
        
        Returns:
            Next state atau None jika tetap di IDLE
        """
        if self.current_state != State.IDLE:
            self._print_state_transition(State.IDLE)
            # Pastikan sistem siap menerima objek berikutnya
            try:
                self.hw.reset_sorter()
            except Exception:
                pass
            try:
                self.servo_hw.reset_to_ready()
            except Exception:
                pass
            print("[IDLE] Standby - Menunggu objek masuk...")
        
        frame = self.hw.get_camera_frame()
        if frame is None:
            return None
        
        self.last_full_frame = frame.copy()
        # Always keep last full frame for stable preview size
        self.last_full_frame = frame.copy()
        
        # === FRAME SKIPPING UNTUK PERFORMA ===
        self.frame_counter += 1
        skip_detection = (self.frame_counter % self.frame_skip) != 0
        
        # === INISIALISASI BACKGROUND (untuk absdiff) ===
        if (not self.use_mog2) and self.background_frame is None:
            print("[IDLE] Initializing background reference...")
            # Resize ke resolusi kecil untuk speed
            small_frame = cv2.resize(frame, (160, 120))
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            self.background_frame = cv2.GaussianBlur(gray, (21, 21), 0)
            self.hw.display_frame(frame, "Initializing...", None)
            return None
        
        # === DETEKSI MOTION (dengan frame lebih kecil) ===
        if not skip_detection:
            small_frame = cv2.resize(frame, (160, 120))
            if self.use_mog2 and self.mog2 is not None:
                # Gunakan MOG2; bekukan model saat processing dengan learningRate=0
                lr = 0 if self.is_processing else -1
                fgmask = self.mog2.apply(small_frame, learningRate=lr)
                # Buang bayangan jika diaktifkan (nilai 127)
                if getattr(config, 'MOG2_DETECT_SHADOWS', True):
                    fgmask[fgmask == 127] = 0
                thresh = fgmask
            else:
                gray_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)
                # Hitung perbedaan dengan background
                frame_diff = cv2.absdiff(self.background_frame, gray_frame)
                # Binary threshold untuk deteksi perubahan - balance antara sensitif & noise
                diff_th = getattr(config, 'BINARY_DIFF_THRESHOLD', 20)
                _, thresh = cv2.threshold(frame_diff, diff_th, 255, cv2.THRESH_BINARY)
            
            # Terapkan ROI deteksi: abaikan area atas untuk mengurangi bayangan tangan
            y_start = int(thresh.shape[0] * getattr(config, 'DETECTION_ROI_Y_START_RATIO', 0.0))
            if y_start > 0:
                thresh[:y_start, :] = 0

            # MORPHOLOGICAL FILTERING: Hilangkan noise bayangan
            if config.ENABLE_MORPHOLOGICAL_FILTER:
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, 
                                                   (config.MORPH_KERNEL_SIZE, config.MORPH_KERNEL_SIZE))
                # Erosion 2x untuk hilangkan bayangan kecil lebih agresif
                thresh = cv2.erode(thresh, kernel, iterations=2)
                # Dilation 3x untuk kembalikan ukuran objek asli
                thresh = cv2.dilate(thresh, kernel, iterations=3)
            
            changed_pixels = cv2.countNonZero(thresh)
            
            # Update background hanya untuk mode absdiff dan saat tidak processing
            if (not self.use_mog2) and (not self.is_processing):
                self.background_frame = cv2.addWeighted(self.background_frame, 0.99, gray_frame, 0.01, 0)
            
            # Update counters (rising-edge detection)
            motion_detected = False
            if changed_pixels > self.motion_enter_threshold:
                self.consecutive_motion += 1
                self.consecutive_still = 0
                motion_detected = True
            elif changed_pixels < self.motion_exit_threshold:
                self.consecutive_still += 1
                self.consecutive_motion = 0
            # else: between thresholds → keep last trend

            # Handle cooldown window to avoid retriggering on same object
            now_ms = int(time.time() * 1000)
            if self.in_cooldown:
                fixed_only = getattr(config, 'FIXED_COOLDOWN_ONLY', False)
                ready = (now_ms >= self.cooldown_until) if fixed_only else (now_ms >= self.cooldown_until and self.consecutive_still >= self.still_frames_to_reset)
                if ready:
                    # Cooldown selesai
                    self.in_cooldown = False
                    self.is_processing = False  # RELEASE lock hanya setelah cooldown SELESAI
                    self.consecutive_motion = 0
                    self.consecutive_still = 0
                    # Set re-arm window to let background stabilize
                    self.rearm_until_ms = now_ms + getattr(config, 'REARM_MS', 600)
                    
                    # IMPORTANT: Force update MOG2/background untuk stabilkan after object lewat
                    # Ini mencegah ghost detection dari objek yang sudah lewat
                    if self.use_mog2 and self.mog2 is not None:
                        # Apply beberapa frame dengan learning rate tinggi untuk quick adapt
                        for _ in range(5):
                            self.mog2.apply(small_frame, learningRate=0.5)
                    elif self.background_frame is not None:
                        # Reset background reference untuk absdiff mode
                        gray_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                        self.background_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)
                    
                    print("\n✅ Cooldown complete - background reset - ready for next object")
                else:
                    # Tampilkan status cooldown dengan info (countdown jika fixed)
                    ttl_ms = max(0, self.cooldown_until - now_ms)
                    cooldown_info = {
                        'status': 'COOLDOWN',
                        'motion_pixels': changed_pixels,
                        'threshold': self.motion_enter_threshold,
                        'time_left_ms': ttl_ms
                    }
                    self.hw.display_frame(frame, "⏳ Cooldown...", cooldown_info)
                    return None

            # Re-arm background: skip detection for a brief period after cooldown
            if now_ms < getattr(self, 'rearm_until_ms', 0):
                info = {
                    'status': 'STANDBY',
                    'color': 'gray'
                }
                self.hw.display_frame(frame, "Stabilizing background...", info)
                return None

            # === TRIGGER PADA RISING EDGE ===
            # BLOCK detection if already processing an object
            if self.is_processing:
                # Display processing status
                status_info = {
                    'status': 'PROCESSING',
                    'color': 'cyan'
                }
                self.hw.display_frame(frame, "🔒 Processing... (blocked)", status_info)
                return None
            
            if not self.in_cooldown and self.consecutive_motion >= self.motion_consecutive_required:
                # Ekstrak ROI dari area bergerak
                roi, rect = self._extract_roi_from_thresh(frame, thresh, small_frame.shape[:2])
                if roi is None:
                    # Tidak ada ROI valid → standby saja
                    status_info = {
                        'status': 'NO OBJECT',
                        'motion_pixels': changed_pixels,
                        'threshold': self.motion_enter_threshold,
                        'color': 'red'
                    }
                    self.hw.display_frame(frame, "⚪ Standby - No Object", status_info)
                    return None
                # Gating berdasarkan besar ROI (approx jarak)
                H, W = frame.shape[:2]
                (x1, y1, x2, y2) = rect
                roi_area = (x2 - x1) * (y2 - y1)
                area_ratio = roi_area / float(W * H)
                if area_ratio < self.min_roi_area_ratio:
                    # Terlalu jauh, jangan klasifikasi
                    msg = f"📏 Objek terlalu jauh ({area_ratio*100:.1f}% area)"
                    if self.enable_distance_estimation:
                        approx_cm = self._approx_distance_cm(y2 - y1)
                        msg += f" ~{approx_cm:.0f}cm"
                    status_info = {
                        'status': 'TOO FAR',
                        'motion_pixels': changed_pixels,
                        'area_ratio': area_ratio,
                        'bbox': rect,
                        'color': 'yellow'
                    }
                    self.hw.display_frame(frame, msg, status_info)
                    # Jangan masuk cooldown, biar bisa trigger lagi saat mendekat
                    return None
                
                # Lolos gating → simpan ROI dan waktu deteksi
                self.current_frame = roi
                self.object_detected_time = time.time()
                self.last_roi_rect = rect
                # DON'T set cooldown here - will be set AFTER sorting completes
                self.consecutive_motion = 0
                self.consecutive_still = 0
                
                # SET PROCESSING LOCK - block new detections
                self.is_processing = True
                
                # FREEZE background - stop updating saat objek terdeteksi
                # Ini mencegah objek yang diam dianggap sebagai "motion" terus-menerus
                
                # Display dengan bbox hijau - SELALU tampilkan
                status_info = {
                    'status': 'DETECTED',
                    'motion_pixels': changed_pixels,
                    'area_ratio': area_ratio,
                    'bbox': rect,
                    'color': 'green'
                }
                
                if self.object_stabilization_delay > 0:
                    self.hw.display_frame(frame, "✅ Object Detected! Waiting to stabilize...", status_info)
                else:
                    self.hw.display_frame(frame, "⚡ Detecting... Quick Capture!", status_info)
                
                # Print hanya sekali (anti-spam)
                current_time = time.time()
                if current_time - self.last_detection_print_time > 2.0:  # Min 2 detik antara print
                    if self.object_stabilization_delay > 0:
                        print(f"\n🔍 OBJEK TERDETEKSI! ({changed_pixels} pixels berubah)")
                        print(f"   Menunggu objek stabil ({self.object_stabilization_delay} detik) sebelum klasifikasi...")
                    else:
                        print(f"\n⚡ OBJEK TERDETEKSI! ({changed_pixels} pixels) - Quick Capture Mode!")
                    self.last_detection_print_time = current_time
                
                return State.INSPECTING
            else:
                # Background kosong / belum cukup stabil
                if motion_detected:
                    status_info = {
                        'status': 'DETECTING',
                        'motion_pixels': changed_pixels,
                        'threshold': self.motion_enter_threshold,
                        'consecutive': self.consecutive_motion,
                        'required': self.motion_consecutive_required,
                        'color': 'orange',
                        'location': self._get_location_info()
                    }
                    self.hw.display_frame(frame, f"🔍 Detecting... ({self.consecutive_motion}/{self.motion_consecutive_required})", status_info)
                else:
                    status_info = {
                        'status': 'NO OBJECT',
                        'motion_pixels': changed_pixels,
                        'threshold': self.motion_enter_threshold,
                        'color': 'red',
                        'location': self._get_location_info()
                    }
                    self.hw.display_frame(frame, "⚪ Standby - No Object", status_info)
        else:
            # Skip detection, just display
            status_info = {
                'status': 'STANDBY',
                'color': 'gray'
            }
            self.hw.display_frame(frame, "⚪ Standby", status_info)
        
        return None

    def _extract_roi_from_thresh(self, frame, thresh_small, small_hw):
        """Ekstrak ROI (region of interest) dari mask perubahan kecil.
        - thresh_small: mask biner pada resolusi kecil (w=160, h=120)
        - small_hw: (h, w) dari frame kecil
        Return (roi_image, (x1,y1,x2,y2)) atau (None, None) jika tidak ada kontur.
        """
        h_small, w_small = small_hw
        contours, _ = cv2.findContours(thresh_small, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None
        # Ambil kontur terbesar
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        # Abaikan objek sangat kecil (filter ghost/noise)
        if w * h < 200:
            return None, None
        # Tambahkan margin
        margin = 10
        x1_s = max(0, x - margin)
        y1_s = max(0, y - margin)
        x2_s = min(w_small, x + w + margin)
        y2_s = min(h_small, y + h + margin)
        # Peta ke koordinat frame asli
        H, W = frame.shape[:2]
        scale_x = W / float(w_small)
        scale_y = H / float(h_small)
        x1 = int(x1_s * scale_x)
        y1 = int(y1_s * scale_y)
        x2 = int(x2_s * scale_x)
        y2 = int(y2_s * scale_y)
        # Clamp
        x1 = max(0, min(W - 1, x1))
        y1 = max(0, min(H - 1, y1))
        x2 = max(x1 + 1, min(W, x2))
        y2 = max(y1 + 1, min(H, y2))
        roi = frame[y1:y2, x1:x2]
        return roi, (x1, y1, x2, y2)

    def _approx_distance_cm(self, roi_h_px: int) -> float:
        """Estimasi jarak sederhana berdasarkan tinggi ROI dalam pixel.
        d = (H_k * f) / h_px
        - H_k: tinggi referensi objek (cm)
        - f: focal length (pixel)
        - h_px: tinggi bounding box (pixel)
        Catatan: sangat bergantung kalibrasi & ukuran objek.
        """
        if roi_h_px <= 0:
            return 0.0
        return (self.known_object_height_cm * self.focal_length_px) / float(roi_h_px)
    
    def _state_inspecting(self) -> State:
        """
        State: INSPECTING
        - Tunggu objek benar-benar DIAM dan stabil
        - Monitor apakah objek masih ada atau diangkat
        
        Returns:
            Next state (CLASSIFYING jika stabil, IDLE jika objek diangkat)
        """
        if self.current_state != State.INSPECTING:
            self._print_state_transition(State.INSPECTING)
        
        # Ambil frame untuk klasifikasi
        frame = self.hw.get_camera_frame()
        if frame is None:
            print("[ERROR] Failed to capture frame! Returning to IDLE")
            return State.IDLE
        # Keep full-size frame for display
        self.last_full_frame = frame.copy()
        # Use ROI/full frame only for inference; keep display on full-size frame
        self.current_frame = frame
        
        # QUICK CAPTURE MODE: Jika delay = 0, tampilkan sebentar lalu klasifikasi
        if self.object_stabilization_delay <= 0:
            # Tampilkan "Analyzing..." untuk visual feedback
            status_info = {
                'status': 'ANALYZING',
                'color': 'cyan'
            }
            self.hw.display_frame(frame, "🔍 Analyzing...", status_info)
            print(f"[INSPECTING] Quick capture! Langsung klasifikasi...")
            time.sleep(0.3)  # Brief pause untuk user bisa lihat
            self.current_frame = frame
            return State.CLASSIFYING
        
        # STABILIZATION MODE: Tunggu objek stabil jika delay > 0
        elapsed = time.time() - self.object_detected_time
        remaining = self.object_stabilization_delay - elapsed
        # Abort jika terlalu lama (orang belum keluar dari area)
        if elapsed > self.stabilization_max_wait:
            self.is_processing = False
            print("[INSPECTING] Timeout waiting for hand removal. Returning to IDLE.")
            return State.IDLE
        
        # Display countdown selama stabilisasi
        if remaining > 0:
            status_info = {
                'status': 'STABILIZING',
                'color': 'blue',
                'countdown': remaining
            }
            self.hw.display_frame(frame, f"⏱️  Stabilizing... {remaining:.1f}s", status_info)
            time.sleep(0.1)
            return State.INSPECTING
        
        # Setelah menunggu, verifikasi keberadaan objek sebelum klasifikasi
        # Hitung perubahan terhadap background yang di-freeze (MOG2 atau absdiff)
        small_frame = cv2.resize(frame, (160, 120))
        if self.use_mog2 and self.mog2 is not None:
            fgmask = self.mog2.apply(small_frame, learningRate=0)
            if getattr(config, 'MOG2_DETECT_SHADOWS', True):
                fgmask[fgmask == 127] = 0
            thresh = fgmask
        else:
            gray_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)
            frame_diff = cv2.absdiff(self.background_frame, gray_frame)
            diff_th = getattr(config, 'BINARY_DIFF_THRESHOLD', 20)
            _, thresh = cv2.threshold(frame_diff, diff_th, 255, cv2.THRESH_BINARY)
        # Apply ROI mask and morphological ops
        y_start = int(thresh.shape[0] * getattr(config, 'DETECTION_ROI_Y_START_RATIO', 0.0))
        if y_start > 0:
            thresh[:y_start, :] = 0
        if config.ENABLE_MORPHOLOGICAL_FILTER:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (config.MORPH_KERNEL_SIZE, config.MORPH_KERNEL_SIZE))
            thresh = cv2.erode(thresh, kernel, iterations=2)
            thresh = cv2.dilate(thresh, kernel, iterations=3)
        changed_pixels = cv2.countNonZero(thresh)
        # Area ratio dari ROI terakhir (fallback 0 jika tidak ada)
        area_ratio = 0.0
        if self.last_roi_rect is not None:
            H, W = frame.shape[:2]
            x1, y1, x2, y2 = self.last_roi_rect
            roi_area = max(1, (x2 - x1) * (y2 - y1))
            area_ratio = roi_area / float(W * H)
        # Keputusan presence: perlu area memadai ATAU changed_pixels masih signifikan
        if area_ratio < self.min_roi_area_ratio and changed_pixels < self.motion_exit_threshold:
            # Tidak ada objek yang tersisa di depan kamera
            info = {
                'status': 'NO OBJECT',
                'area_ratio': area_ratio,
                'changed_pixels': changed_pixels,
                'color': 'gray'
            }
            self.hw.display_frame(frame, "⚪ Standby - No Object to analyze", info)
            self.is_processing = False
            return State.IDLE
        # Ada objek → siapkan frame untuk klasifikasi (gunakan ROI jika ada)
        if self.last_roi_rect is not None:
            x1, y1, x2, y2 = self.last_roi_rect
            x1 = max(0, x1); y1 = max(0, y1)
            x2 = min(frame.shape[1], x2); y2 = min(frame.shape[0], y2)
            roi_now = frame[y1:y2, x1:x2]
            if roi_now.size > 0:
                self.current_frame = roi_now
            else:
                self.current_frame = frame
        else:
            self.current_frame = frame
        print(f"[INSPECTING] Object present (area={area_ratio*100:.1f}%, changed={changed_pixels}). Classifying...")
        return State.CLASSIFYING
    
    def _state_classifying(self) -> State:
        """
        State: CLASSIFYING
        - Jalankan classifier pada gambar
        - Evaluasi hasil prediksi
        - Tentukan bin tujuan
        
        Returns:
            Next state (SORTING_A, SORTING_B, atau IDLE jika confidence rendah)
        """
        self._print_state_transition(State.CLASSIFYING)
        
        print("[CLASSIFYING] Running AI inference...")
        
        # Run classifier
        prediction = self.classifier.predict_with_all_scores(self.current_frame)
        
        label = prediction['label']
        confidence = prediction['confidence']
        all_scores = prediction.get('all_scores', {})
        
        # Display hasil
        print(f"\n[CLASSIFYING] Results:")
        print(f"  Predicted Label: {label}")
        print(f"  Confidence: {confidence:.2%}")
        print(f"  All Scores: {all_scores}")
        
        # Save to database
        if self.database_service:
            try:
                location = self.location_service.get_location() if self.location_service else None
                
                # Insert location first
                location_id = None
                if location:
                    location_id = self.database_service.insert_location(
                        latitude=location['latitude'],
                        longitude=location['longitude'],
                        accuracy=location.get('accuracy'),
                        device_id=self.device_id,
                        source=location.get('source', 'unknown')
                    )
                
                # Determine bin assignment
                if label.upper() == 'ORGANIC':
                    bin_assignment = 'BIN A'
                    bin_angle = 0
                else:
                    bin_assignment = 'BIN B'
                    bin_angle = 90
                
                # Insert analysis result
                self.database_service.insert_analysis_result(
                    label=label,
                    confidence=confidence,
                    bin_assignment=bin_assignment,
                    bin_angle=bin_angle,
                    latitude=location['latitude'] if location else None,
                    longitude=location['longitude'] if location else None,
                    location_accuracy=location.get('accuracy') if location else None,
                    device_id=self.device_id,
                    location_id=location_id
                )
            except Exception as e:
                print(f"[MainController] Warning: Database insert failed: {e}")
        
        # Tampilkan hasil di frame (sebelum sorting)
        status_info = {
            'label': label,
            'confidence': confidence,
            'all_scores': all_scores,
            'bbox': self.last_roi_rect,
            'is_preview': False,  # Eksplisit: ini adalah hasil final
            'is_monitoring': False # Eksplisit: bukan lagi monitoring
        }
        
        # Simpan prediksi untuk ditampilkan di state berikutnya
        self.current_prediction = status_info
        
        # Langsung lanjutkan, jangan tunggu di sini.
        # Popup akan ditampilkan di state SORTING.

        # Berdasarkan label, tentukan state berikutnya
        label_upper = label.upper().strip()
        if label_upper == 'ORGANIC':
            decision = State.SORTING_A
        elif label_upper == 'ANORGANIC':
            decision = State.SORTING_B
        else:
            # Fallback: jika label tidak dikenali, cek substring (tapi ANORGANIC dulu)
            if 'ANORGANIC' in label_upper:
                decision = State.SORTING_B
            elif 'ORGANIC' in label_upper:
                decision = State.SORTING_A
            else:
                decision = State.SORTING_A  # Default safety
                
        print(f"[DEBUG] Decision: {decision} (Exact match: {label_upper})")

        return decision
    
    def _state_sorting_a(self) -> State:
        """
        State: SORTING_A (Organik)
        - Servo Layer 2 tilts to Bin A position (30°)
        - Then servo Layer 1 opens to drop waste (90° down)
        - Waste falls and slides to Bin A on Layer 2
        - Servos reset to ready position
        
        Cooldown includes SERVO_MOVEMENT_DURATION to ensure all servo
        movements complete before motion detection resumes.
        """
        if self.current_state != State.SORTING_A:
            self._print_state_transition(State.SORTING_A)
        
        # Urutan lengkap menggunakan controller servo yang aktif
        self.servo_hw.execute_sort('BIN A', getattr(config, 'SERVO_LAYER2_BIN_A', 60))
        
        print(f"[SORTING_A] Waiting for waste to fall ({self.sorting_duration}s)...")
        
        # Tampilkan popup hasil selama proses sorting
        start_time = time.time()
        while time.time() - start_time < self.sorting_duration:
            self.hw.display_frame(self.last_full_frame, "🌱 SORTING TO BIN A", self.current_prediction)
            if cv2.waitKey(20) & 0xFF == ord('q'):
                self.running = False
                return None
        
        # Update statistik
        self.stats['total_sorted'] += 1
        self.stats['organic_count'] += 1
        
        # Calculate total cooldown: base cooldown + servo movement duration
        # This ensures servo movements are NOT detected as new objects
        servo_duration_ms = int(getattr(config, 'SERVO_MOVEMENT_DURATION', 3.5) * 1000)
        total_cooldown_ms = self.cooldown_ms + servo_duration_ms
        
        print(f"[SORTING_A] Initiating cooldown ({total_cooldown_ms}ms): base {self.cooldown_ms}ms + servo {servo_duration_ms}ms")
        
        # DON'T release processing lock here - will be released after cooldown
        # ENABLE cooldown AFTER sorting - object must be removed before next trigger
        self.in_cooldown = True
        self.cooldown_until = int(time.time() * 1000) + total_cooldown_ms
        
        return State.IDLE

    def _state_sorting_b(self) -> State:
        """
        State: SORTING_B (Anorganik)
        - Servo Layer 2 tilts to Bin B position (30°)
        - Then servo Layer 1 opens to drop waste (90° down)
        - Waste falls and slides to Bin B on Layer 2
        - Servos reset to ready position
        
        Cooldown includes SERVO_MOVEMENT_DURATION to ensure all servo
        movements complete before motion detection resumes.
        """
        if self.current_state != State.SORTING_B:
            self._print_state_transition(State.SORTING_B)
        
        # Urutan lengkap menggunakan controller servo yang aktif
        self.servo_hw.execute_sort('BIN B', getattr(config, 'SERVO_LAYER2_BIN_B', 120))

        print(f"[SORTING_B] Waiting for waste to fall ({self.sorting_duration}s)...")

        # Tampilkan popup hasil selama proses sorting
        start_time = time.time()
        while time.time() - start_time < self.sorting_duration:
            self.hw.display_frame(self.last_full_frame, "♻️ SORTING TO BIN B", self.current_prediction)
            if cv2.waitKey(20) & 0xFF == ord('q'):
                self.running = False
                return None

        # Update statistik
        self.stats['total_sorted'] += 1
        self.stats['anorganic_count'] += 1
        
        # Calculate total cooldown: base cooldown + servo movement duration
        # This ensures servo movements are NOT detected as new objects
        servo_duration_ms = int(getattr(config, 'SERVO_MOVEMENT_DURATION', 3.5) * 1000)
        total_cooldown_ms = self.cooldown_ms + servo_duration_ms
        
        print(f"[SORTING_B] Initiating cooldown ({total_cooldown_ms}ms): base {self.cooldown_ms}ms + servo {servo_duration_ms}ms")
        
        # DON'T release processing lock here - will be released after cooldown
        # ENABLE cooldown AFTER sorting - object must be removed before next trigger
        self.in_cooldown = True
        self.cooldown_until = int(time.time() * 1000) + total_cooldown_ms
        
        return State.IDLE

    def run(self):
        """
        Main loop - menjalankan FSM.
        Loop akan terus berjalan sampai user menekan 'q'.
        """
        self.running = True
        self.current_state = State.IDLE
        
        print("\n" + "="*60)
        print("WASTE SORTER SYSTEM - STARTED")
        print("="*60)
        print("Instructions:")
        print("  - Press 't' to trigger sorting")
        print("  - Press 'q' to quit")
        print("="*60 + "\n")
        
        try:
            while self.running:
                # State machine
                next_state = None
                
                if self.current_state == State.IDLE:
                    next_state = self._state_idle()
                    
                elif self.current_state == State.INSPECTING:
                    next_state = self._state_inspecting()
                    
                elif self.current_state == State.CLASSIFYING:
                    next_state = self._state_classifying()
                    
                elif self.current_state == State.SORTING_A:
                    next_state = self._state_sorting_a()
                    
                elif self.current_state == State.SORTING_B:
                    next_state = self._state_sorting_b()
                
                # Transition ke state berikutnya
                if next_state is not None:
                    self.current_state = next_state
                
                # Check for quit command
                import cv2
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n[MainController] Quit command received")
                    self.running = False

                # Detect window closed via X button (macOS/Raspberry Pi)
                # If preview window is closed, gracefully stop the loop
                try:
                    if hasattr(self.hw, 'window_name'):
                        prop = cv2.getWindowProperty(self.hw.window_name, cv2.WND_PROP_VISIBLE)
                        if prop < 1:  # Window hidden/closed or not found
                            print("\n[MainController] Preview window closed. Exiting...")
                            self.running = False
                except Exception:
                    # If property read fails, ignore and continue
                    pass
                
                # Small delay untuk mencegah CPU overload
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\n[MainController] Interrupted by user (Ctrl+C)")
        
        finally:
            self._shutdown()
    
    def _shutdown(self):
        """Cleanup dan tampilkan statistik akhir."""
        print("\n" + "="*60)
        print("WASTE SORTER SYSTEM - SHUTTING DOWN")
        print("="*60)
        print("\nFinal Statistics:")
        print(f"  Total Sorted: {self.stats['total_sorted']}")
        print(f"  Organic: {self.stats['organic_count']}")
        print(f"  Anorganic: {self.stats['anorganic_count']}")
        print(f"  Low Confidence Rejections: {self.stats['low_confidence_count']}")
        
        # Save final location if GPS enabled
        if self.location_service and self.save_gps_history:
            print("\nFinal Location:")
            location = self.location_service.get_location()
            if location:
                print(f"  {self.location_service.get_location_info_string()}")
                self.location_service.save_location_to_file(self.gps_history_file)
        
        # Update database summary
        if self.database_service:
            try:
                location = self.location_service.get_location() if self.location_service else None
                self.database_service.update_session_summary(
                    device_id=self.device_id,
                    total_sorted=self.stats['total_sorted'],
                    organic_count=self.stats['organic_count'],
                    anorganic_count=self.stats['anorganic_count'],
                    latitude=location.get('latitude') if location else None,
                    longitude=location.get('longitude') if location else None
                )
                print("\nDatabase Summary Updated:")
                print(f"  Device ID: {self.device_id}")
                print(f"  Session saved to RDS")
            except Exception as e:
                print(f"[MainController] Warning: Database summary update failed: {e}")
        
        print("="*60 + "\n")
        
        # Cleanup GPS service
        if self.location_service:
            self.location_service.stop_background_update()
        
        # Cleanup servo controller first to stop PWM before any GPIO cleanup
        try:
            if hasattr(self, 'servo_hw') and self.servo_hw:
                self.servo_hw.cleanup()
        except Exception:
            pass

        # Then cleanup main hardware interface (may call GPIO.cleanup)
        self.hw.cleanup()


# Test function
def main():
    """
    Test function untuk MainController dengan mock data.
    """
    print("Testing MainController with mock components...\n")
    
    # Import mock classifier
    from .mock_classifier import MockClassifier
    
    # Mock hardware (minimal)
    class MockHW:
        def __init__(self):
            import cv2
            self.camera = cv2.VideoCapture(0)
        
        def check_trigger(self):
            import cv2
            key = cv2.waitKey(1) & 0xFF
            return key == ord('t')
        
        def get_camera_frame(self):
            ret, frame = self.camera.read()
            return frame if ret else None
        
        def display_frame(self, frame, text, prediction=None):
            import cv2
            if frame is not None:
                cv2.imshow("Test", frame)
        
        def reset_sorter(self):
            print("[Mock] Reset sorter")
        
        def sort_to_bin_A(self):
            print("[Mock] Sort to Bin A")
        
        def sort_to_bin_B(self):
            print("[Mock] Sort to Bin B")
        
        def cleanup(self):
            import cv2
            self.camera.release()
            cv2.destroyAllWindows()
    
    try:
        classifier = MockClassifier()
        hw = MockHW()
        controller = MainController(classifier, hw)
        controller.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
