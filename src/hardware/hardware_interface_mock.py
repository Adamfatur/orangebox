"""
Hardware Interface - Mock Implementation untuk macOS
Implementasi simulasi untuk testing di macOS sebelum deployment ke Raspberry Pi.
"""

import cv2
import time
import numpy as np
from typing import Optional
import config


# ===== UI helpers (rounded shapes, chips, progress bars) =====
def _draw_filled_rounded_rect(img, x, y, w, h, color, radius=10, alpha=1.0):
    """Draw a filled rounded rectangle with optional translucency."""
    radius = max(0, min(radius, min(w, h)//2))
    overlay = img.copy()
    # Center rectangle
    cv2.rectangle(overlay, (x+radius, y), (x+w-radius, y+h), color, -1)
    # Side rectangles
    cv2.rectangle(overlay, (x, y+radius), (x+w, y+h-radius), color, -1)
    # Corners
    cv2.circle(overlay, (x+radius, y+radius), radius, color, -1)
    cv2.circle(overlay, (x+w-radius-1, y+radius), radius, color, -1)
    cv2.circle(overlay, (x+radius, y+h-radius-1), radius, color, -1)
    cv2.circle(overlay, (x+w-radius-1, y+h-radius-1), radius, color, -1)
    if alpha >= 1.0:
        img[y:y+h, x:x+w] = overlay[y:y+h, x:x+w]
    else:
        cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)


def _put_text_with_shadow(img, text, org, font, scale, color, thickness=1, shadow_color=(0,0,0)):
    x, y = org
    # Shadow
    cv2.putText(img, text, (x+1, y+1), font, scale, shadow_color, thickness+2, cv2.LINE_AA)
    # Text
    cv2.putText(img, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)


def _sanitize_text(text: str) -> str:
    """Replace or strip emojis/unrenderable glyphs for OpenCV fonts.

    Map a few common emojis to ASCII words, otherwise remove non-ASCII
    characters so OpenCV text won't draw question marks.
    """
    if not text:
        return ""
    # common replacements
    replacements = {
        '🔍': 'Scan',
        '⏱': 'Timer',
        '⏳': 'Timer',
        '⚡': 'Quick',
        '🌱': '',
        '♻': '',
        '✅': 'OK',
        '✓': '✓',
        '➡': '->',
        '➔': '->',
        '\uFE0F': ''  # remove variation selectors
    }
    s = str(text)
    for k, v in replacements.items():
        s = s.replace(k, v)
    # remove high-unicode chars not typically supported by Hershey fonts
    s = ''.join(ch for ch in s if ord(ch) < 0x100 or ch in ['✓'])
    return s


def _draw_chip(img, text, x, y, bg=(60,60,60), fg=(255,255,255), pad_x=10, pad_y=6, radius=12):
    font = cv2.FONT_HERSHEY_SIMPLEX
    size, _ = cv2.getTextSize(text, font, 0.5, 1)
    w = size[0] + pad_x*2
    h = size[1] + pad_y*2
    _draw_filled_rounded_rect(img, x, y-h+pad_y, w, h, bg, radius, alpha=0.9)
    cv2.putText(img, text, (x+pad_x, y), font, 0.5, fg, 1, cv2.LINE_AA)
    return w, h


def _draw_progress_bar(img, x, y, w, h, pct, bg=(50,50,50), fg=(0,200,255), border=(120,120,120), radius=8):
    pct = max(0.0, min(1.0, float(pct)))
    _draw_filled_rounded_rect(img, x, y, w, h, bg, radius, alpha=0.85)
    fill_w = int(w * pct)
    if fill_w > 0:
        _draw_filled_rounded_rect(img, x, y, fill_w, h, fg, radius, alpha=0.95)
    cv2.rectangle(img, (x, y), (x+w, y+h), border, 1, cv2.LINE_AA)


def _draw_score_bars(img, x, y, width, scores: dict):
    """Draw labeled score bars for classes with percentages."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    bar_h = 18
    gap = 10
    y_cur = y
    # Stable order if only two classes
    ordered = list(scores.items())
    if set(k.upper().strip() for k in scores.keys()) == {"ORGANIC", "ANORGANIC"}:
        ordered = [("ORGANIC", scores.get("ORGANIC", 0.0)), ("ANORGANIC", scores.get("ANORGANIC", 0.0))]
    for name, score in ordered:
        name_clean = str(name).upper().strip()
        if name_clean == "ORGANIC":
            col = (0, 200, 0)
        elif name_clean == "ANORGANIC":
            col = (0, 140, 255)
        else:
            col = (180, 180, 180)

        # Draw a colored dot
        cv2.circle(img, (x+8, y_cur+12), 6, col, -1)
        label = f"{name_clean.title()}"
        cv2.putText(img, label, (x+20, y_cur+14), font, 0.5, (220,220,220), 1, cv2.LINE_AA)
        _draw_progress_bar(img, x, y_cur+22, width, bar_h, score, bg=(45,45,55), fg=col, border=(80,80,90), radius=6)
        cv2.putText(img, f"{score:.1%}", (x+width-60, y_cur+36), font, 0.5, (240,240,240), 1, cv2.LINE_AA)
        y_cur += 22 + bar_h + gap
    return y_cur


class HardwareInterface:
    """
    Mock implementation dari hardware interface untuk testing di macOS.
    Interface ini mensimulasikan:
    - Proximity sensor (trigger dengan keyboard 't')
    - Webcam capture
    - Servo movement (print ke console)
    """
    
    def __init__(self, camera_index: int = None):
        """
        Inisialisasi hardware interface.
        
        Args:
            camera_index: Index kamera (None = auto-detect, 0-4 untuk manual selection)
        """
        self.camera_index = camera_index
        self.camera_config = None
        self.camera = None
        self.last_trigger_time = 0
        self.trigger_cooldown = 1.0  # Cooldown 1 detik antara trigger
        self.window_name = "Orange Box - Camera View"
        # FPS monitoring
        self._fps_last_time = time.time()
        self._fps_counter = 0
        self._fps = 0.0
        
        # Text stabilization to prevent flicker
        self._stable_status_text = ""
        self._stable_status_time = 0
        self._status_debounce = 0.3  # seconds
        
        # Motion smoothing to prevent rapid flicker
        
        # Auto-detect camera if not specified
        if camera_index is None:
            self._auto_detect_camera()

        self._motion_history = []
        self._motion_history_max = 5  # Average over last N frames
        self._smoothed_motion = 0
        
        # Load logo
        self._logo = None
        self._load_logo()
        
        self._initialize_camera()
    
    def _auto_detect_camera(self):
        """Auto-detect available camera and set camera_index"""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
            from src.core.camera_detector import detect_camera_auto
            
            print("[HardwareInterface] Auto-detecting camera...")
            camera_info = detect_camera_auto()
            
            if camera_info:
                self.camera_config = camera_info
                idx = camera_info.get('index')
                if idx is None:
                    # If detector returns None (e.g., PiCamera path), default to 0 for OpenCV
                    print("[HardwareInterface] ℹ️ Index None from detector; defaulting to 0 for OpenCV")
                    idx = 0
                self.camera_index = idx
                print(f"[HardwareInterface] ✓ Selected: {camera_info['name']} (index {self.camera_index})")
            else:
                print("[HardwareInterface] ⚠ No camera detected, defaulting to index 0")
                self.camera_index = 0
                
        except Exception as e:
            print(f"[HardwareInterface] Camera auto-detection failed: {e}")
            print("[HardwareInterface] Defaulting to camera index 0")
            self.camera_index = 0
        
    def _load_logo(self):
        """Load logo image from project root."""
        import os
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'logo-orangebox.png')
        try:
            if os.path.exists(logo_path):
                self._logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
                if self._logo is not None:
                    # Resize logo to fit top bar (height ~40px)
                    h, w = self._logo.shape[:2]
                    target_h = 40
                    target_w = int(w * target_h / h)
                    self._logo = cv2.resize(self._logo, (target_w, target_h), interpolation=cv2.INTER_AREA)
                    print(f"[HardwareInterface] ✅ Logo loaded: {target_w}x{target_h}px")
                else:
                    print(f"[HardwareInterface] ⚠️ Logo file found but failed to load: {logo_path}")
            else:
                print(f"[HardwareInterface] ⚠️ Logo not found: {logo_path}")
        except Exception as e:
            print(f"[HardwareInterface] ⚠️ Error loading logo: {e}")
            self._logo = None
    
    def _overlay_logo(self, background, logo, x, y):
        """Overlay logo with alpha channel onto background."""
        try:
            h, w = logo.shape[:2]
            # Check bounds
            if y + h > background.shape[0] or x + w > background.shape[1]:
                return
            
            roi = background[y:y+h, x:x+w]
            
            # Check if logo has alpha channel
            if logo.shape[2] == 4:
                # Extract alpha channel and normalize
                alpha = logo[:, :, 3] / 255.0
                alpha = alpha[:, :, np.newaxis]
                
                # Blend logo with background using alpha
                logo_rgb = logo[:, :, :3]
                blended = (alpha * logo_rgb + (1 - alpha) * roi).astype(np.uint8)
                background[y:y+h, x:x+w] = blended
            else:
                # No alpha channel, just copy
                background[y:y+h, x:x+w] = logo
        except Exception as e:
            pass  # Silently ignore overlay errors
        
    def _initialize_camera(self):
        """Inisialisasi koneksi ke webcam."""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                print("\n" + "="*60)
                print("⚠️  CAMERA PERMISSION REQUIRED")
                print("="*60)
                print("macOS memerlukan permission untuk akses kamera.")
                print("\nLangkah-langkah:")
                print("1. Buka System Preferences (System Settings)")
                print("2. Pilih Security & Privacy → Privacy")
                print("3. Pilih Camera di sidebar")
                print("4. Centang 'Terminal' atau aplikasi yang menjalankan script")
                print("5. Restart Terminal dan run lagi")
                print("\nAtau coba kamera lain dengan: python3 run.py --camera 1")
                print("="*60 + "\n")
                raise RuntimeError(f"Tidak dapat membuka kamera dengan index {self.camera_index}")
            
            # Set resolusi kamera untuk 720p @ 30 FPS
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            # Test capture
            ret, test_frame = self.camera.read()
            if not ret or test_frame is None:
                raise RuntimeError("Kamera terbuka tapi tidak bisa capture frame")
            
            # Get actual resolution (might differ from requested)
            actual_w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.camera.get(cv2.CAP_PROP_FPS))
            
            print(f"[HardwareInterface] ✅ Kamera berhasil diinisialisasi (index: {self.camera_index})")
            print(f"[HardwareInterface] 📸 Resolution: {actual_w}x{actual_h} @ {actual_fps} FPS")
            # Base display size to keep preview constant
            self._base_w = actual_w or 1280
            self._base_h = actual_h or 720
        except Exception as e:
            print(f"[ERROR] Gagal menginisialisasi kamera: {e}")
            raise
    
    def check_trigger(self) -> bool:
        """
        Simulasi proximity sensor.
        Mendeteksi trigger dengan menekan tombol 't' pada keyboard.
        
        Returns:
            True jika trigger terdeteksi (tombol 't' ditekan), False jika tidak
        """
        # Implementasi cooldown agar tidak trigger berulang kali
        current_time = time.time()
        if current_time - self.last_trigger_time < self.trigger_cooldown:
            return False
        
        # Check keyboard input
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('t'):
            self.last_trigger_time = current_time
            print("[HardwareInterface] ⚡ TRIGGER DETECTED (tombol 't' ditekan)")
            return True
        elif key == ord('q'):
            print("[HardwareInterface] Tombol 'q' ditekan - akan keluar...")
            return False
        
        return False
    
    def get_camera_frame(self) -> Optional[np.ndarray]:
        """
        Mengambil frame gambar dari webcam.
        
        Returns:
            Frame gambar (numpy array) atau None jika gagal
        """
        if self.camera is None or not self.camera.isOpened():
            print("[ERROR] Kamera tidak tersedia")
            return None
        
        ret, frame = self.camera.read()
        
        if not ret or frame is None:
            print("[ERROR] Gagal mengambil frame dari kamera")
            return None
        
        # Reduced logging - only log errors, not every frame
        # print(f"[HardwareInterface] 📸 Frame captured ({frame.shape[1]}x{frame.shape[0]})")
        return frame
    
    def sort_to_bin_A(self):
        """
        Simulasi menggerakkan servo ke Bin A (Organik).
        Di RPi: Servo bergerak ke sudut 0°
        """
        print("╔════════════════════════════════════════╗")
        print("║  SORTING TO BIN A (ORGANIC)           ║")
        print("║  [SIMULASI] Servo bergerak ke 0°      ║")
        print("╚════════════════════════════════════════╝")
        time.sleep(0.5)  # Simulasi waktu gerakan servo
    
    def sort_to_bin_B(self):
        """
        Simulasi menggerakkan servo ke Bin B (Anorganik).
        Di RPi: Servo bergerak ke sudut 90°
        """
        print("╔════════════════════════════════════════╗")
        print("║  SORTING TO BIN B (ANORGANIC)         ║")
        print("║  [SIMULASI] Servo bergerak ke 90°     ║")
        print("╚════════════════════════════════════════╝")
        time.sleep(0.5)  # Simulasi waktu gerakan servo
    
    def reset_sorter(self):
        """
        Mengembalikan servo ke posisi default/netral.
        Di RPi: Servo bergerak ke sudut 45°
        """
        print("[HardwareInterface] 🔄 Sorter reset ke posisi netral (45°)")
        time.sleep(0.3)  # Simulasi waktu gerakan servo
    
    def display_frame(self, frame: np.ndarray, text: str = "", 
                     prediction: Optional[dict] = None):
        """
        Menampilkan frame dengan informasi tambahan di jendela OpenCV.
        
        Args:
            frame: Frame gambar untuk ditampilkan
            text: Teks status untuk ditampilkan
            prediction: Dictionary hasil prediksi atau status info
        """
        if frame is None:
            return
        
        # Buat copy frame untuk annotasi
        display_frame = frame.copy()
        h, w = display_frame.shape[:2]
        # Keep constant preview size (avoid flicker when ROI used elsewhere)
        base_w = getattr(self, '_base_w', w)
        base_h = getattr(self, '_base_h', h)
        
        font = cv2.FONT_HERSHEY_SIMPLEX

        # === FPS calculation ===
        now = time.time()
        self._fps_counter += 1
        if now - self._fps_last_time >= 1.0:
            self._fps = self._fps_counter / (now - self._fps_last_time)
            self._fps_counter = 0
            self._fps_last_time = now
        
        # === Text stabilization (debounce to prevent flicker) ===
        def _get_stable_text(new_text):
            """Return stabilized text to prevent flicker."""
            if new_text != self._stable_status_text:
                # Only update if enough time passed or significantly different
                if (now - self._stable_status_time) > self._status_debounce:
                    self._stable_status_text = new_text
                    self._stable_status_time = now
            return self._stable_status_text
        
        # === Motion smoothing ===
        def _get_smoothed_motion(new_motion):
            """Return smoothed motion value to prevent flicker."""
            self._motion_history.append(new_motion)
            if len(self._motion_history) > self._motion_history_max:
                self._motion_history.pop(0)
            # Return average
            return int(sum(self._motion_history) / len(self._motion_history))
        
        # === HANDLE STATUS INFO (motion detection) ===
        if prediction and 'status' in prediction:
            status = prediction.get('status', 'STANDBY')
            motion_pixels = prediction.get('motion_pixels', 0)
            threshold = prediction.get('threshold', 0)
            bbox = prediction.get('bbox', None)
            color_name = prediction.get('color', 'gray')
            
            # Smooth motion pixel value
            smoothed_motion = _get_smoothed_motion(motion_pixels)
            
            # Color mapping
            color_map = {
                'green': (0, 255, 0),
                'red': (0, 0, 255),
                'yellow': (0, 255, 255),
                'orange': (0, 165, 255),
                'cyan': (255, 255, 0),
                'gray': (128, 128, 128)
            }
            color = color_map.get(color_name, (128, 128, 128))
            
            # Draw bounding box if available (stylized corners)
            if bbox:
                x1, y1, x2, y2 = bbox
                # Corner accents
                corner_len = max(12, (x2-x1)//7)
                thickness = 3
                # Top-left
                cv2.line(display_frame, (x1, y1), (x1+corner_len, y1), color, thickness)
                cv2.line(display_frame, (x1, y1), (x1, y1+corner_len), color, thickness)
                # Top-right
                cv2.line(display_frame, (x2, y1), (x2-corner_len, y1), color, thickness)
                cv2.line(display_frame, (x2, y1), (x2, y1+corner_len), color, thickness)
                # Bottom-left
                cv2.line(display_frame, (x1, y2), (x1+corner_len, y2), color, thickness)
                cv2.line(display_frame, (x1, y2), (x1, y2-corner_len), color, thickness)
                # Bottom-right
                cv2.line(display_frame, (x2, y2), (x2-corner_len, y2), color, thickness)
                cv2.line(display_frame, (x2, y2), (x2, y2-corner_len), color, thickness)
                _put_text_with_shadow(display_frame, "OBJECT", (x1, max(18, y1-8)), font, 0.5, color)
            
            # Top app bar
            bar_height = 70
            _draw_filled_rounded_rect(display_frame, 6, 6, w-12, bar_height, (28,28,32), radius=12, alpha=0.85)
            
            # Logo (if available) - centered vertically in bar
            logo_x = 16
            logo_y = 15
            if self._logo is not None:
                self._overlay_logo(display_frame, self._logo, logo_x, logo_y)
                # Text position after logo
                text_x = logo_x + self._logo.shape[1] + 12
            else:
                text_x = logo_x + 4
            
            # App title (top line)
            _put_text_with_shadow(display_frame, "Orange Box", (text_x, 30), font, 0.75, (230,230,235), thickness=2)
            
            # Status: Gunakan teks utama yang di-pass dari controller (bottom line)
            status_text = text if text and text.strip() else status
            status_text = _sanitize_text(status_text)
            if status_text:
                stable_status = _get_stable_text(status_text)
                # Gambar lingkaran status dan teksnya di baris bawah
                cv2.circle(display_frame, (text_x + 4, 52), 5, color, -1)
                _put_text_with_shadow(display_frame, stable_status, (text_x + 16, 56), font, 0.5, (210,210,215))

            # Right side info panel - aligned and organized
            right_margin = 16
            right_x = w - right_margin
            
            # FPS chip (top-right, first row)
            fps_text = f"{self._fps:4.1f} FPS"
            fps_chip_w, fps_chip_h = _draw_chip(display_frame, fps_text, right_x - 100, 16, bg=(55,55,60), fg=(220,220,220))
            
            # Motion progress bar (second row, aligned with FPS)
            if threshold > 0:
                pct = smoothed_motion/float(threshold) if threshold>0 else 0
                bar_w = 160
                bar_x = right_x - bar_w
                _draw_progress_bar(display_frame, bar_x, 48, bar_w, 10, pct, bg=(45,45,50), fg=(0,200,255), border=(80,80,90), radius=5)
            
            # Countdown timer if available
            if 'countdown' in prediction:
                countdown = prediction['countdown']
                # Large countdown in center with shadow
                countdown_text = f"{countdown:.1f}"
                text_size = cv2.getTextSize(countdown_text, font, 3.2, 6)[0]
                text_x_center = (w - text_size[0]) // 2
                text_y_center = (h + text_size[1]) // 2
                _put_text_with_shadow(display_frame, countdown_text, (text_x_center, text_y_center), font, 3.2, (0, 255, 255), thickness=6)
            
            # Consecutive counter if detecting (simplified)
            if 'consecutive' in prediction and 'required' in prediction:
                consecutive = prediction['consecutive']
                required = prediction['required']
                pct = consecutive / float(required)
                bar_w = int(w * 0.3)
                _draw_progress_bar(display_frame, 20, h-40, bar_w, 8, pct, bg=(45,45,50), fg=(0,200,255), border=(80,80,90), radius=4)
            
            # Area ratio if available (simplified)
            if 'area_ratio' in prediction:
                area_ratio = prediction['area_ratio']
                area_pct = area_ratio * 100
                bar_w = int(w * 0.2)
                _draw_progress_bar(display_frame, w - bar_w - 20, h-40, bar_w, 8, area_ratio, bg=(45,45,50), fg=(100,200,100), border=(80,80,90), radius=4)

            # Cooldown progress bar (rounded)
            if status == 'COOLDOWN':
                total_ms = getattr(config, 'COOLDOWN_MS', 1500)
                time_left = int(prediction.get('time_left_ms', 0))
                time_left = max(0, min(time_left, total_ms))
                done = total_ms - time_left
                pct = done / float(total_ms) if total_ms > 0 else 1.0
                # Draw progress bar at bottom
                bar_w = int(w * 0.6)
                bar_h = 18
                bar_x = (w - bar_w) // 2
                bar_y = h - 36
                _draw_progress_bar(display_frame, bar_x, bar_y, bar_w, bar_h, pct, bg=(60,60,65), fg=(0,210,255), border=(120,120,120), radius=10)
                ms_text = f"Cooldown {time_left/1000:.1f}s"
                _put_text_with_shadow(display_frame, ms_text, (bar_x, bar_y-6), font, 0.55, (220, 220, 220))
        
        # === HANDLE PREDICTION RESULT ===
        elif prediction and 'label' in prediction:
            label = prediction.get('label', 'Unknown')
            confidence = prediction.get('confidence', 0.0)
            all_scores = prediction.get('all_scores', {})
            is_preview = prediction.get('is_preview', False)
            is_monitoring = prediction.get('is_monitoring', False)
            bbox = prediction.get('bbox', None)
            
            # Tentukan warna berdasarkan label - EXACT MATCH!
            label_clean = label.upper().strip()
            if label_clean == 'ORGANIC':
                color = (0, 255, 0)  # Green
                bin_name = "BIN A"
                bin_desc = "ORGANIK"
                decision_bg = (20, 100, 30)
            elif label_clean == 'ANORGANIC':
                color = (0, 140, 255)  # Orange
                bin_name = "BIN B"
                bin_desc = "ANORGANIK"
                decision_bg = (60, 70, 20)
            else:
                # Jika label tidak dikenali, jangan tampilkan popup
                return
            
            # === CENTER POPUP FOR FINAL RESULT (not preview/monitoring) ===
            if not is_monitoring and not is_preview:
                # Large center popup
                popup_w = int(w * 0.5)
                popup_h = int(h * 0.55)
                popup_x = (w - popup_w) // 2
                popup_y = (h - popup_h) // 2
                
                # Draw popup background with shadow
                shadow_offset = 8
                _draw_filled_rounded_rect(display_frame, popup_x+shadow_offset, popup_y+shadow_offset, popup_w, popup_h, (0,0,0), radius=22, alpha=0.4)
                _draw_filled_rounded_rect(display_frame, popup_x, popup_y, popup_w, popup_h, (38, 40, 45), radius=22, alpha=0.96)
                
                # Header with result color
                header_h = 50
                _draw_filled_rounded_rect(display_frame, popup_x, popup_y, popup_w, header_h, decision_bg, radius=22, alpha=1.0)
                cv2.rectangle(display_frame, (popup_x, popup_y+header_h-22), (popup_x+popup_w, popup_y+header_h), decision_bg, -1)
                
                # Title in header (centered)
                title_text = _sanitize_text("KLASIFIKASI SELESAI")
                title_size = cv2.getTextSize(title_text, font, 0.7, 2)[0]
                _put_text_with_shadow(display_frame, title_text, (popup_x + (popup_w - title_size[0])//2, popup_y+33), font, 0.7, (255,255,255), thickness=2)
                
                # Main content area (centered)
                content_y = popup_y + header_h + 45
                
                # Draw a large colored circle instead of emoji
                cv2.circle(display_frame, (popup_x + popup_w//2, content_y + 60), 32, color, -1)
                # Label text (sanitized & title-cased)
                label_clean_s = _sanitize_text(label_clean.title())
                label_size = cv2.getTextSize(label_clean_s, font, 1.2, 3)[0]
                _put_text_with_shadow(display_frame, label_clean_s, (popup_x + (popup_w - label_size[0])//2, content_y + 140), font, 1.2, (255,255,255), thickness=3)

                # Confidence text
                conf_text = f"{confidence*100:.1f}%"
                conf_size = cv2.getTextSize(conf_text, font, 0.8, 2)[0]
                _put_text_with_shadow(display_frame, conf_text, (popup_x + (popup_w - conf_size[0])//2, content_y + 165), font, 0.8, (220,220,220), thickness=2)

                # Divider line
                line_y = popup_y + popup_h - 90
                cv2.line(display_frame, (popup_x + 30, line_y), (popup_x + popup_w - 30, line_y), (60, 60, 65), 1)

                # Decision text (centered)
                decision_y = line_y + 45
                decision_main = f"SORTIR KE {bin_name} ({bin_desc})"
                decision_size = cv2.getTextSize(decision_main, font, 0.8, 2)[0]
                _put_text_with_shadow(display_frame, decision_main, (popup_x + (popup_w - decision_size[0])//2, decision_y), font, 0.8, color, thickness=2)

            else:
                # Small side card for monitoring/preview
                card_w = int(w*0.32)
                card_x = w - card_w - 12
                card_y = 78
                card_h = min(int(h*0.45), h - card_y - 50)
                base_card_color = (32, 34, 38)
                _draw_filled_rounded_rect(display_frame, card_x, card_y, card_w, card_h, base_card_color, radius=14, alpha=0.88)
                
                if is_monitoring:
                    title = _sanitize_text("Scanning...")
                    title_color = (100, 200, 255)
                else:
                    title = ""
                    title_color = (200, 200, 200)
                
                if title:
                    _put_text_with_shadow(display_frame, title, (card_x+16, card_y+28), font, 0.65, title_color, thickness=1)
                
                # Small score display
                bars_x = card_x + 16
                bars_y = card_y + 50
                bars_w = card_w - 32
                _draw_score_bars(display_frame, bars_x, bars_y, bars_w, all_scores)
            
            # Draw ROI bbox if provided (on original frame, not inside popup)
            if bbox:
                x1, y1, x2, y2 = bbox
                corner_len = max(12, (x2-x1)//7)
                bbox_color = (160,160,160)
                # Stylized corners
                cv2.line(display_frame, (x1, y1), (x1+corner_len, y1), bbox_color, 2)
                cv2.line(display_frame, (x1, y1), (x1, y1+corner_len), bbox_color, 2)
                cv2.line(display_frame, (x2, y1), (x2-corner_len, y1), bbox_color, 2)
                cv2.line(display_frame, (x2, y1), (x2, y1+corner_len), bbox_color, 2)
                cv2.line(display_frame, (x1, y2), (x1+corner_len, y2), bbox_color, 2)
                cv2.line(display_frame, (x1, y2), (x1, y2-corner_len), bbox_color, 2)
                cv2.line(display_frame, (x2, y2), (x2-corner_len, y2), bbox_color, 2)
                cv2.line(display_frame, (x2, y2), (x2, y2-corner_len), bbox_color, 2)
                _put_text_with_shadow(display_frame, "ROI", (x1, max(18, y1-8)), font, 0.5, (220, 220, 220))
        
        # === DISPLAY LOCATION INFO (GPS) ===
        if prediction and 'location' in prediction and prediction['location']:
            location_str = prediction['location']
            loc_size = cv2.getTextSize(location_str, font, 0.45, 1)[0]
            # Display di bottom-left, above instruction pill
            loc_x = 10
            loc_y = h - 42
            _draw_filled_rounded_rect(display_frame, loc_x-2, loc_y-loc_size[1]-6, loc_size[0]+12, loc_size[1]+10, (30,35,40), radius=8, alpha=0.8)
            _put_text_with_shadow(display_frame, location_str, (loc_x+4, loc_y), font, 0.45, (100, 200, 255), thickness=1)
        
        # Bottom instruction pill
        instr_text = "Auto-detection aktif  •  Tekan 'q' untuk keluar"
        size, _ = cv2.getTextSize(instr_text, font, 0.55, 1)
        pill_w = size[0] + 24
        pill_h = size[1] + 16
        pill_x = 10
        pill_y = h - 12
        _draw_filled_rounded_rect(display_frame, pill_x, pill_y-pill_h+6, pill_w, pill_h, (30,30,34), radius=14, alpha=0.8)
        cv2.putText(display_frame, instr_text, (pill_x+12, h-12), font, 0.55, (245, 245, 245), 1, cv2.LINE_AA)
        
        # Resize to constant base size if needed
        if display_frame.shape[1] != base_w or display_frame.shape[0] != base_h:
            display_frame = cv2.resize(display_frame, (base_w, base_h), interpolation=cv2.INTER_LINEAR)
        # Show frame
        cv2.imshow(self.window_name, display_frame)
    
    def cleanup(self):
        """Cleanup resources (kamera dan windows)."""
        print("[HardwareInterface] Cleaning up resources...")
        
        if self.camera is not None:
            self.camera.release()
        
        cv2.destroyAllWindows()
        print("[HardwareInterface] Cleanup complete")


# Test function
def main():
    """
    Test function untuk memverifikasi HardwareInterface berfungsi dengan baik.
    """
    print("Testing HardwareInterface (Mock for macOS)...\n")
    print("Instruksi:")
    print("- Tekan 't' untuk trigger (simulasi sensor proximity)")
    print("- Tekan 'q' untuk quit")
    print("-" * 50)
    
    try:
        hw = HardwareInterface()
        
        print("\nTesting camera capture...")
        frame = hw.get_camera_frame()
        
        if frame is not None:
            print(f"✓ Camera working! Frame shape: {frame.shape}")
            
            print("\nTesting display...")
            hw.display_frame(frame, "TEST MODE", {"label": "ORGANIC", "confidence": 0.95})
            
            print("\nTesting servo movements...")
            hw.reset_sorter()
            time.sleep(1)
            hw.sort_to_bin_A()
            time.sleep(1)
            hw.sort_to_bin_B()
            time.sleep(1)
            hw.reset_sorter()
            
            print("\n✓ All tests passed!")
            print("\nTekan tombol apapun pada jendela kamera untuk keluar...")
            cv2.waitKey(0)
        else:
            print("✗ Camera test failed!")
        
        hw.cleanup()
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
