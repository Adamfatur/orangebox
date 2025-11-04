"""
Camera Auto-Detection Module
Deteksi otomatis kamera yang tersedia di sistem (Mac/Raspberry Pi)

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

# CARA CEPAT PAKAI MODUL INI
# - Jalankan: `python3 -m src.core.camera_detector` untuk lihat daftar kamera & pilihan otomatis.
# - Di Raspberry Pi, modul mencoba PiCamera2 dulu, kalau gagal lanjut scan USB webcam via OpenCV.
# - Mau pilih kamera manual saat run app? Gunakan: `python3 main.py --camera 0`.
# - Kalau kamera USB tidak muncul di RPi: `sudo apt-get install v4l-utils` lalu `v4l2-ctl --list-devices`.

import cv2
import platform
import sys


class CameraDetector:
    """
    Auto-detect available cameras and select the best option.
    - Raspberry Pi: Detect Pi Camera Module (via picamera2) or USB webcam
    - Mac/Linux: Detect available USB cameras
    """
    
    def __init__(self):
        self.is_raspberry_pi = self._detect_raspberry_pi()
        self.has_picamera2 = False
        self.available_cameras = []
        
        if self.is_raspberry_pi:
            self._check_picamera2()
    
    def _detect_raspberry_pi(self) -> bool:
        """Detect if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                    return True
        except:
            pass
        return False
    
    def _check_picamera2(self) -> bool:
        """Check if picamera2 is available (Raspberry Pi Camera Module)"""
        try:
            from picamera2 import Picamera2
            
            # Method 1: Try to list cameras via global_camera_info
            try:
                cameras = Picamera2.global_camera_info()
                if cameras and len(cameras) > 0:
                    self.has_picamera2 = True
                    print(f"[CameraDetector] ✓ Raspberry Pi Camera Module detected")
                    return True
                else:
                    print("[CameraDetector] ⚠️  Picamera2 installed but no camera detected")
                    self._show_camera_help()
                    return False
            except Exception as e1:
                # Method 2: Try to create instance (fallback)
                try:
                    test_cam = Picamera2()
                    test_cam.close()
                    self.has_picamera2 = True
                    print("[CameraDetector] ✓ Raspberry Pi Camera Module detected")
                    return True
                except Exception as e2:
                    print(f"[CameraDetector] ⚠️  Camera detection failed: {e2}")
                    self._show_camera_help()
                    return False
                    
        except ImportError as e:
            print(f"[CameraDetector] ⚠️  picamera2 not installed")
            print("[CameraDetector] Installing picamera2...")
            try:
                import subprocess
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'python3-picamera2'], 
                             check=False, capture_output=True)
                print("[CameraDetector] ℹ️  Please restart the application")
            except:
                print("[CameraDetector] 💡 Install manually: sudo apt install python3-picamera2")
            return False
    
    def _show_camera_help(self):
        """Show helpful message when camera not detected"""
        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📷 Raspberry Pi Camera Module Not Detected")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")
        print("Quick Fix:")
        print("  1. Check physical connection (ribbon cable)")
        print("  2. Enable camera: sudo raspi-config")
        print("     → Interface Options → Camera → Enable")
        print("  3. Reboot: sudo reboot")
        print("  4. Test: libcamera-hello")
        print("")
        print("System will fallback to USB webcam if available...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")
    
    def detect_cameras(self, max_cameras: int = 5) -> list:
        """
        Detect all available USB/webcam cameras using OpenCV.
        
        Args:
            max_cameras: Maximum number of camera indices to check
            
        Returns:
            List of available camera indices
        """
        print(f"[CameraDetector] Scanning for cameras (0-{max_cameras-1})...")
        available = []
        
        for index in range(max_cameras):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # Try to read a frame to confirm camera is working
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Get camera info
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    
                    available.append({
                        'index': index,
                        'width': width,
                        'height': height,
                        'fps': fps
                    })
                    print(f"[CameraDetector] ✓ Camera {index}: {width}x{height} @ {fps}fps")
                cap.release()
        
        self.available_cameras = available
        return available
    
    def auto_select_camera(self) -> dict:
        """
        Automatically select the best camera option.
        
        Priority:
        1. Raspberry Pi Camera Module (if available)
        2. First available USB camera (index 0)
        3. Any other detected camera
        
        Returns:
            dict with 'type' and 'index' or None if no camera found
        """
        # Priority 1: Pi Camera Module (Raspberry Pi only)
        if self.is_raspberry_pi and self.has_picamera2:
            return {
                'type': 'picamera',
                'index': None,
                'name': 'Raspberry Pi Camera Module',
                'backend': 'picamera2'
            }
        
        # Priority 2: Detect USB cameras
        cameras = self.detect_cameras()
        
        if not cameras:
            print("[CameraDetector] ❌ No cameras detected!")
            if self.is_raspberry_pi:
                print("")
                print("💡 Troubleshooting:")
                print("   - Pi Camera: Check connection and run 'libcamera-hello'")
                print("   - USB Camera: Check with 'v4l2-ctl --list-devices'")
                print("   - Enable camera: sudo raspi-config → Interface → Camera")
                print("")
            return None
        
        # Select camera based on platform
        if self.is_raspberry_pi:
            # On RPi, prefer first camera (usually USB cam if no Pi Camera)
            selected = cameras[0]
            return {
                'type': 'usb',
                'index': selected['index'],
                'name': f"USB Camera {selected['index']}",
                'backend': 'opencv',
                'resolution': f"{selected['width']}x{selected['height']}"
            }
        else:
            # On Mac/PC, might have multiple cameras
            # Try to select the best one (higher resolution preferred)
            best = max(cameras, key=lambda c: c['width'] * c['height'])
            
            # Check if there are multiple cameras
            if len(cameras) > 1:
                print(f"[CameraDetector] Multiple cameras detected ({len(cameras)})")
                for i, cam in enumerate(cameras):
                    marker = "←" if cam['index'] == best['index'] else " "
                    print(f"  {marker} Camera {cam['index']}: {cam['width']}x{cam['height']}")
                print(f"[CameraDetector] Selected: Camera {best['index']} (best resolution)")
            
            return {
                'type': 'usb',
                'index': best['index'],
                'name': f"Camera {best['index']}",
                'backend': 'opencv',
                'resolution': f"{best['width']}x{best['height']}"
            }
    
    def get_camera_info(self) -> str:
        """Get formatted camera information string"""
        if self.is_raspberry_pi and self.has_picamera2:
            return "Raspberry Pi Camera Module (picamera2)"
        elif self.available_cameras:
            cam_list = ", ".join([f"Index {c['index']} ({c['width']}x{c['height']})" 
                                  for c in self.available_cameras])
            return f"USB Camera(s): {cam_list}"
        else:
            return "No camera detected"


def detect_camera_auto():
    """
    Convenience function for quick camera detection.
    
    Returns:
        Camera config dict or None if no camera found
    """
    detector = CameraDetector()
    return detector.auto_select_camera()


def print_camera_info():
    """Print detailed camera information for debugging"""
    detector = CameraDetector()
    
    print("\n" + "="*60)
    print("CAMERA DETECTION REPORT")
    print("="*60)
    
    print(f"Platform: {platform.system()} ({platform.machine()})")
    print(f"Raspberry Pi: {'Yes' if detector.is_raspberry_pi else 'No'}")
    
    if detector.is_raspberry_pi:
        print(f"Pi Camera Module: {'Available' if detector.has_picamera2 else 'Not detected'}")
    
    cameras = detector.detect_cameras()
    print(f"\nUSB/Webcam Cameras: {len(cameras)} found")
    
    if cameras:
        for cam in cameras:
            print(f"  - Index {cam['index']}: {cam['width']}x{cam['height']} @ {cam['fps']}fps")
    
    print("\n" + "-"*60)
    selected = detector.auto_select_camera()
    
    if selected:
        print("AUTO-SELECTED CAMERA:")
        print(f"  Type: {selected['type']}")
        print(f"  Name: {selected['name']}")
        print(f"  Backend: {selected['backend']}")
        if selected['index'] is not None:
            print(f"  Index: {selected['index']}")
        if 'resolution' in selected:
            print(f"  Resolution: {selected['resolution']}")
    else:
        print("NO CAMERA AVAILABLE!")
    
    print("="*60 + "\n")
    
    return selected


# Test program
if __name__ == "__main__":
    print("Testing Camera Auto-Detection...\n")
    result = print_camera_info()
    
    if result:
        print("✅ Camera detection successful!")
        sys.exit(0)
    else:
        print("❌ No camera detected!")
        sys.exit(1)
