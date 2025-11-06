#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🧡 ORANGE BOX - GUI INSTALLER 🧡                    ║
║        Interactive Setup for Raspberry Pi 5                 ║
║                                                              ║
╚═══════════════════════════════════════════════════════════════╝

Professional GUI installer untuk deployment Orange Box
Menggunakan dialog/whiptail untuk interface yang user-friendly
"""

import os
import sys
import subprocess
import time
import re
import shutil
import platform
from pathlib import Path

class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Installer:
    def __init__(self):
        self.project_dir = Path(__file__).parent.parent.absolute()  # Go up to orangebox root
        self.has_dialog = self.check_dialog()
        self.config = {
            'camera_index': 0,
            'confidence': 0.5,
            'auto_start': True,
            'platform': 'rpi',
            'has_gps': False,
            'device_id_mode': 'auto',
            'device_id': ''
        }
        
    def check_dialog(self):
        """Check if dialog/whiptail is available"""
        for cmd in ['dialog', 'whiptail']:
            if subprocess.run(['which', cmd], capture_output=True).returncode == 0:
                return cmd
        return None
    
    def show_banner(self):
        """Show ASCII art banner"""
        banner = f"""
{Colors.OKGREEN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🧡 ORANGE BOX - INTERACTIVE INSTALLER 🧡            ║
║        Intelligent Waste Classification System              ║
║                                                              ║
╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.OKCYAN}Version: 1.0.0
Platform: Raspberry Pi 5
Python: {sys.version.split()[0]}{Colors.ENDC}
"""
        print(banner)
    
    def dialog_msgbox(self, title, text, height=15, width=70):
        """Show message box"""
        if self.has_dialog:
            subprocess.run([
                self.has_dialog,
                '--title', title,
                '--msgbox', text,
                str(height), str(width)
            ])
        else:
            print(f"\n{Colors.BOLD}=== {title} ==={Colors.ENDC}")
            print(text)
            input("\nPress Enter to continue...")
    
    def dialog_yesno(self, title, text, height=10, width=70):
        """Show yes/no dialog"""
        if self.has_dialog:
            result = subprocess.run([
                self.has_dialog,
                '--title', title,
                '--yesno', text,
                str(height), str(width)
            ])
            return result.returncode == 0
        else:
            print(f"\n{Colors.BOLD}=== {title} ==={Colors.ENDC}")
            print(text)
            response = input("\nContinue? (y/n): ").lower()
            return response in ['y', 'yes']
    
    def dialog_menu(self, title, text, choices, height=20, width=70):
        """Show menu dialog"""
        if self.has_dialog:
            menu_items = []
            for i, choice in enumerate(choices, 1):
                menu_items.extend([str(i), choice])
            
            result = subprocess.run([
                self.has_dialog,
                '--title', title,
                '--menu', text,
                str(height), str(width), str(len(choices)),
                *menu_items
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                selected = int(result.stdout.strip())
                return choices[selected - 1]
            return None
        else:
            print(f"\n{Colors.BOLD}=== {title} ==={Colors.ENDC}")
            print(text)
            print()
            for i, choice in enumerate(choices, 1):
                print(f"  {i}. {choice}")
            
            try:
                choice = int(input("\nSelect option: "))
                if 1 <= choice <= len(choices):
                    return choices[choice - 1]
            except ValueError:
                pass
            return None
    
    def dialog_inputbox(self, title, text, init="", height=10, width=70):
        """Show input box"""
        if self.has_dialog:
            result = subprocess.run([
                self.has_dialog,
                '--title', title,
                '--inputbox', text,
                str(height), str(width), init
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout.strip()
            return init
        else:
            print(f"\n{Colors.BOLD}=== {title} ==={Colors.ENDC}")
            print(text)
            response = input(f"\n[{init}]: ").strip()
            return response if response else init
    
    def dialog_gauge(self, title, text, percent):
        """Show progress gauge (simplified)"""
        if not self.has_dialog:
            bar_length = 50
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r{text}: [{bar}] {percent}%", end='', flush=True)
    
    def run_command(self, cmd, title="Running Command"):
        """Run shell command with progress"""
        print(f"\n{Colors.OKCYAN}▶ {title}{Colors.ENDC}")
        print(f"  $ {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"{Colors.OKGREEN}  ✓ Success{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}  ✗ Failed{Colors.ENDC}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
    
    def welcome_screen(self):
        """Show welcome screen"""
        welcome_text = """Welcome to Orange Box Installer!

This installer will:
• Install system dependencies (OpenCV, GPIO, Database, GPS)
• Setup Python environment
• Configure GPS Module (U-blox NEO-6M)
• Setup Device ID (Multi-device support)
• Verify ML Models
• Configure systemd service
• Enable auto-start on boot
• Test all hardware components

Database: AWS RDS (Pre-configured in config.py)

Estimated time: 10-15 minutes

Ready to begin?"""
        
        return self.dialog_yesno("Welcome to Orange Box", welcome_text)
    
    def configure_settings(self):
        """Interactive configuration"""
        self.dialog_msgbox("Configuration", 
            "Let's configure your Orange Box settings.\n\n"
            "You can change these later in config.py")
        
        # Camera selection
        camera_choice = self.dialog_menu(
            "Camera Selection",
            "Select your camera type:",
            ["Pi Camera Module (CSI)", "USB Webcam #0", "USB Webcam #1"],
            height=12
        )
        
        if camera_choice:
            if "USB Webcam #1" in camera_choice:
                self.config['camera_index'] = 1
            else:
                self.config['camera_index'] = 0
        
        # Confidence threshold
        confidence_choice = self.dialog_menu(
            "Confidence Threshold",
            "Select minimum confidence for classification:",
            ["50% - Balanced (Recommended)", "60% - More Accurate", "70% - Very Accurate", "40% - More Detections"],
            height=14
        )
        
        if confidence_choice:
            if "50%" in confidence_choice:
                self.config['confidence'] = 0.5
            elif "60%" in confidence_choice:
                self.config['confidence'] = 0.6
            elif "70%" in confidence_choice:
                self.config['confidence'] = 0.7
            else:
                self.config['confidence'] = 0.4
        
        # GPS Module
        has_gps = self.dialog_yesno(
            "GPS Module",
            "Do you have U-blox NEO-6M GPS module?\n\n"
            "If YES, installer will:\n"
            "• Enable UART on GPIO 14/15\n"
            "• Disable Bluetooth (uses same pins)\n"
            "• Install and configure GPSD\n\n"
            "You can add GPS later if needed."
        )
        self.config['has_gps'] = has_gps
        
        # Device ID Configuration
        device_id_choice = self.dialog_menu(
            "Device ID Configuration",
            "Choose Device ID mode:\n\n"
            "Auto-generate: Uses hostname + MAC address\n"
            "Manual input: You specify custom ID",
            ["Auto-generate (Recommended)", "Manual Input"],
            height=14
        )
        
        if device_id_choice and "Manual" in device_id_choice:
            self.config['device_id_mode'] = 'manual'
            device_id = self.dialog_inputbox(
                "Device ID",
                "Enter unique Device ID for this unit:\n\n"
                "(e.g., ORANGEBOX-001, CAMPUS-A-BIN1)",
                init="ORANGEBOX-001"
            )
            self.config['device_id'] = device_id
        else:
            self.config['device_id_mode'] = 'auto'
        
        # Auto-start
        auto_start = self.dialog_yesno(
            "Auto-Start",
            "Enable auto-start on boot?\n\n"
            "Orange Box will automatically start when\n"
            "Raspberry Pi powers on.\n\n"
            "Recommended: YES"
        )
        self.config['auto_start'] = auto_start
    
    def install_dependencies(self):
        """Install system and Python dependencies"""
        sysname = platform.system()
        steps = []
        if sysname == 'Linux':
            steps = [
                ("Updating package list", "sudo apt-get update", 10),
                ("Installing system packages",
                 "sudo apt-get install -y python3-pip python3-opencv python3-numpy python3-picamera2 "
                 "python3-rpi.gpio libopenblas-dev liblapack-dev libraspberrypi-dev "
                 "libcamera-dev libcamera-apps libmysqlclient-dev v4l-utils git dialog whiptail python3-venv "
                 "i2c-tools python3-smbus", 30),
                ("Creating Python venv", f"cd {self.project_dir} && python3 -m venv .venv", 40),
                ("Upgrading pip (venv)", f"{self.project_dir}/.venv/bin/pip install --upgrade pip", 50),
                ("Installing Python packages (venv)", f"{self.project_dir}/.venv/bin/pip install -r {self.project_dir}/requirements.txt", 70),
            ]
            if self.config['has_gps']:
                steps.append(("Installing GPS packages", "sudo apt-get install -y gpsd gpsd-clients python3-gps", 85))
            # Enable camera/SPI/I2C for hardware modules
            steps.append(("Enabling camera/SPI/I2C", "sudo raspi-config nonint do_camera 0 || true && sudo raspi-config nonint do_spi 0 || true && sudo raspi-config nonint do_i2c 0 || true", 90))
        else:
            # macOS atau platform lain: untuk simulasi, lewati instalasi berat
            steps = [
                ("Skipping system packages on non-Linux", f"echo 'Skip system packages for {sysname}'", 30),
                ("Installing Python deps (requirements)", f"pip3 install -r {self.project_dir}/requirements.txt", 60),
            ]
            print(f"\n{Colors.WARNING}⚠️  Non-Linux detected ({sysname}). Skipping heavy dependency installation for simulation.{Colors.ENDC}")

        self.dialog_msgbox("Installation",
            "Now installing dependencies...\n\n"
            "This may take 5-10 minutes.\n"
            "Please wait...")

        print(f"\n{Colors.HEADER}{'='*60}")
        print("INSTALLING DEPENDENCIES")
        print(f"{'='*60}{Colors.ENDC}\n")

        for title, cmd, progress in steps:
            self.dialog_gauge("Installing", title, progress)
            if not self.run_command(cmd, title):
                self.dialog_msgbox("Error",
                    f"Failed to execute: {title}\n\n"
                    f"Command: {cmd}\n\n"
                    "Check logs and try again.")
                return False

        steps.append(("Finalizing installation", "echo 'Dependencies installed'", 100))

        print(f"\n{Colors.OKGREEN}✓ All dependencies installed successfully!{Colors.ENDC}")
        return True

    def setup_gps(self):
        """Setup GPS module"""
        if not self.config['has_gps']:
            return True
        
        print(f"\n{Colors.OKCYAN}▶ Setting up GPS Module{Colors.ENDC}")
        
        # Enable UART
        print("  • Enabling UART on GPIO 14/15...")
        config_txt = "/boot/firmware/config.txt"
        
        commands = [
            f"sudo grep -q 'enable_uart=1' {config_txt} || echo 'enable_uart=1' | sudo tee -a {config_txt}",
            f"sudo grep -q 'dtoverlay=disable-bt' {config_txt} || echo 'dtoverlay=disable-bt' | sudo tee -a {config_txt}",
            "sudo systemctl disable hciuart 2>/dev/null || true",
            "sudo systemctl disable bluetooth 2>/dev/null || true"
        ]
        
        for cmd in commands:
            subprocess.run(cmd, shell=True, capture_output=True)
        
        # Configure GPSD
        print("  • Configuring GPSD...")
        gpsd_config = """# Orange Box GPS Configuration
START_DAEMON="true"
GPSD_OPTIONS="-n"
DEVICES="/dev/serial0"
USBAUTO="true"
GPSD_SOCKET="/var/run/gpsd.sock"
"""
        
        with open('/tmp/gpsd', 'w') as f:
            f.write(gpsd_config)
        
        subprocess.run("sudo cp /tmp/gpsd /etc/default/gpsd", shell=True)
        subprocess.run("sudo systemctl enable gpsd", shell=True, capture_output=True)
        
        print(f"{Colors.OKGREEN}  ✓ GPS configured (requires reboot){Colors.ENDC}")
        return True
    
    def setup_device_id(self):
        """Setup Device ID"""
        print(f"\n{Colors.OKCYAN}▶ Configuring Device ID{Colors.ENDC}")
        
        if self.config['device_id_mode'] == 'auto':
            # Auto-generate from hostname + MAC
            result = subprocess.run("hostname", shell=True, capture_output=True, text=True)
            hostname = result.stdout.strip()
            
            result = subprocess.run("cat /sys/class/net/eth0/address 2>/dev/null || cat /sys/class/net/wlan0/address", 
                                  shell=True, capture_output=True, text=True)
            mac = result.stdout.strip().replace(':', '')[-6:].upper()
            
            device_id = f"{hostname}-{mac}"
            print(f"  • Auto-generated: {device_id}")
        else:
            device_id = self.config['device_id']
            print(f"  • Manual ID: {device_id}")
        
        # Save to device_config.txt
        config_file = self.project_dir / 'device_config.txt'
        with open(config_file, 'w') as f:
            f.write(f"DEVICE_ID={device_id}\n")
        
        self.config['device_id'] = device_id
        print(f"{Colors.OKGREEN}  ✓ Device ID saved{Colors.ENDC}")
        return True
    
    def update_config(self):
        """Update config.py with user settings (robust regex replacements)"""
        config_file = self.project_dir / 'config.py'
        
        try:
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Update platform line to selected platform
            platform_value = self.config.get('platform', 'rpi')
            content = re.sub(r"PLATFORM\s*=\s*['\"][^'\"]+['\"]", f"PLATFORM = '{platform_value}'", content)
            
            # Update camera index (replace any integer assignment)
            content = re.sub(r"CAMERA_INDEX\s*=\s*\d+", f"CAMERA_INDEX = {self.config['camera_index']}", content)
            
            # Update confidence threshold (replace any numeric assignment)
            content = re.sub(r"CONFIDENCE_THRESHOLD\s*=\s*[0-9.]+", f"CONFIDENCE_THRESHOLD = {self.config['confidence']}", content)
            
            # Update GPS setting (force True only if GPS selected)
            if self.config['has_gps']:
                content = re.sub(r"GPS_USE_GPSD\s*=\s*(True|False)", "GPS_USE_GPSD = True", content)
            else:
                content = re.sub(r"GPS_USE_GPSD\s*=\s*(True|False)", "GPS_USE_GPSD = False", content)
            
            with open(config_file, 'w') as f:
                f.write(content)
            
            print(f"{Colors.OKGREEN}✓ Configuration updated{Colors.ENDC}")
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}✗ Failed to update config: {e}{Colors.ENDC}")
            return False
    
    def setup_service(self):
        """Setup systemd service"""
        if not self.config['auto_start']:
            return True
        
        service_content = f"""[Unit]
Description=Orange Box - Intelligent Waste Classification System
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'pi')}
WorkingDirectory={self.project_dir}
Environment="DISPLAY=:0"
Environment="PYTHONUNBUFFERED=1"
ExecStart={self.project_dir}/.venv/bin/python3 {self.project_dir}/main.py --model {self.project_dir}/models/model_quant_infer.tflite --camera {self.config['camera_index']}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        service_file = '/tmp/orangebox.service'
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        commands = [
            f"sudo cp {service_file} /etc/systemd/system/orangebox.service",
            "sudo systemctl daemon-reload",
            "sudo systemctl enable orangebox.service"
        ]
        
        for cmd in commands:
            if not self.run_command(cmd, "Setting up service"):
                return False
        
        return True
    
    def verify_models(self):
        """Verify ML models exist"""
        print(f"\n{Colors.OKCYAN}▶ Verifying ML Models{Colors.ENDC}")
        
        models = [
            self.project_dir / "models" / "model_quant_infer.tflite",
            self.project_dir / "models" / "model_float32_infer.tflite"
        ]
        
        all_found = True
        for model in models:
            if model.exists():
                size = model.stat().st_size / (1024*1024)
                print(f"  ✓ {model.name} ({size:.1f} MB)")
            else:
                print(f"  ✗ {model.name} - NOT FOUND")
                all_found = False
        
        if not all_found:
            print(f"\n{Colors.WARNING}⚠️  Some models missing. System may not work properly.{Colors.ENDC}")
        
        return all_found
    
    def test_installation(self):
        """Test if installation is successful"""
        tests = [
            ("Camera detection (USB/libcamera)", "v4l2-ctl --list-devices || libcamera-hello --list-cameras"),
            ("Python imports", f"{self.project_dir}/.venv/bin/python3 -c 'import cv2, numpy, tflite_runtime, RPi.GPIO' || {self.project_dir}/.venv/bin/python3 -c 'import cv2, numpy, tflite_runtime'"),
            ("Model file", f"test -f {self.project_dir}/models/model_quant_infer.tflite && echo OK"),
            ("Config file", f"test -f {self.project_dir}/config.py && echo OK"),
            ("Device ID", f"test -f {self.project_dir}/device_config.txt && echo OK")
        ]
        
        # Add GPS test if configured
        if self.config['has_gps']:
            tests.append(("GPS daemon", "systemctl is-enabled gpsd 2>/dev/null && echo OK || echo DISABLED"))
        
        # Optional: Servo test (simulasi di non-RPi)
        tests.append(("Servo test", f"{self.project_dir}/.venv/bin/python3 {self.project_dir}/scripts/test_servo_simple.py || true"))
        
        print(f"\n{Colors.HEADER}{'='*60}")
        print("RUNNING TESTS")
        print(f"{'='*60}{Colors.ENDC}\n")
        
        all_passed = True
        for title, cmd in tests:
            result = self.run_command(cmd, title)
            if not result:
                all_passed = False
        
        return all_passed

    def detect_camera_devices(self):
        """Cross-platform camera detection.
        - Linux: v4l2/libcamera
        - macOS: system_profiler, ffmpeg avfoundation, OpenCV fallback
        Returns summary string.
        """
        sysname = platform.system()
        summaries = []

        if sysname == 'Linux':
            if shutil.which('v4l2-ctl'):
                res = subprocess.run(['v4l2-ctl', '--list-devices'], capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    summaries.append(res.stdout.strip())
            if shutil.which('libcamera-hello'):
                res2 = subprocess.run(['libcamera-hello', '--list-cameras'], capture_output=True, text=True)
                if res2.returncode == 0 and res2.stdout.strip():
                    summaries.append(res2.stdout.strip())
        elif sysname == 'Darwin':  # macOS
            # 1) system_profiler (built-in)
            if shutil.which('system_profiler'):
                sp = subprocess.run(['system_profiler', 'SPCameraDataType'], capture_output=True, text=True)
                names = []
                for line in sp.stdout.splitlines():
                    s = line.strip()
                    if s.endswith(':') and s and s != 'Camera:':
                        # Example: 'FaceTime HD Camera (Built-in):'
                        names.append(s[:-1])
                if names:
                    summaries.append('macOS cameras (system_profiler):\n' + '\n'.join(f'- {n}' for n in names))
            # 2) ffmpeg avfoundation (if available)
            if shutil.which('ffmpeg'):
                ff = subprocess.run(['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''], capture_output=True, text=True)
                devices = []
                for line in (ff.stderr or '').splitlines():
                    if 'AVFoundation video devices' in line:
                        continue
                    m = re.search(r'\[(\d+)\]\s*(.+)$', line)
                    if m:
                        devices.append(f"[{m.group(1)}] {m.group(2).strip()}")
                if devices:
                    summaries.append('AVFoundation video devices (ffmpeg):\n' + '\n'.join(f'- {d}' for d in devices))
            # 3) OpenCV fallback (optional)
            try:
                import cv2
                found = []
                for idx in range(0, 3):
                    cap = cv2.VideoCapture(idx, cv2.CAP_AVFOUNDATION)
                    if cap is not None and cap.isOpened():
                        found.append(f'Index {idx} (OpenCV)')
                        cap.release()
                if found:
                    summaries.append('OpenCV detected devices:\n' + '\n'.join(f'- {x}' for x in found))
            except Exception:
                pass
        else:
            # Generic OpenCV fallback on other OS
            try:
                import cv2
                found = []
                for idx in range(0, 3):
                    cap = cv2.VideoCapture(idx)
                    if cap is not None and cap.isOpened():
                        found.append(f'Index {idx} (OpenCV)')
                        cap.release()
                if found:
                    summaries.append('OpenCV detected devices:\n' + '\n'.join(f'- {x}' for x in found))
            except Exception:
                pass

        if not summaries:
            return 'No camera devices found or tools unavailable on this OS.'
        joined = '\n---\n'.join(summaries)
        return joined[:1200]

    def quick_tests(self):
        """Offer quick tests: camera detection and servo simulation. Safe to skip."""
        should = self.dialog_yesno(
            "Quick Hardware Tests",
            "Run quick tests before installation?\n\n"
            "• Detect cameras (USB/libcamera)\n"
            "• Simulate 3-servo sorting sequence\n\n"
            "Recommended: YES (helps verify setup)")
        if not should:
            return
        cam_info = self.detect_camera_devices()
        self.camera_devices = cam_info
        self.dialog_msgbox("Camera Detection", cam_info[:1200], height=20, width=80)
        self.dialog_msgbox(
            "Servo Test",
            "Starting servo simulation test...\n\n"
            "This will execute tilt → open doors → reset for Bin A & B.\n"
            "If running on non-RPi, movements are simulated.",
            height=12, width=70
        )
        res = subprocess.run(
            ['python3', str(self.project_dir / 'src' / 'hardware' / 'gpio_servo_hardware.py')],
            capture_output=True, text=True
        )
        if res.returncode == 0:
            out = res.stdout[-1200:] if res.stdout else 'OK'
            self.dialog_msgbox("Servo Test Result", out, height=25, width=80)
        else:
            err = (res.stderr or 'Failed').strip()[:800]
            self.dialog_msgbox("Servo Test Error", err, height=20, width=80)
    
    def completion_screen(self):
        """Show completion screen"""
        service_status = "ENABLED" if self.config['auto_start'] else "DISABLED"
        gps_status = "CONFIGURED" if self.config['has_gps'] else "NOT CONFIGURED"
        camera_detected = getattr(self, 'camera_devices', None)
        camera_summary = camera_detected if camera_detected else 'Not tested'
        
        completion_text = f"""
Installation Complete! 🎉

Configuration Summary:
• Platform: Raspberry Pi 5
• Device ID: {self.config.get('device_id', 'Not set')}
• Camera: Index {self.config['camera_index']}
• Detected Cameras: {camera_summary}
• Confidence: {self.config['confidence']*100:.0f}%
• GPS Module: {gps_status}
• Database: AWS RDS (Pre-configured)
• Auto-Start: {service_status}

Hardware Connections:
• GPS: VCC→5V, GND→GND, TX→GPIO15, RX→GPIO14
• Servo 1: GPIO 12 (Layer 1 Left)
• Servo 2: GPIO 13 (Layer 1 Right)
• Servo 3: GPIO 18 (Layer 2 Selector)

Quick Commands:
• Start:    sudo systemctl start orangebox
• Stop:     sudo systemctl stop orangebox
• Logs:     sudo journalctl -u orangebox -f
• Status:   sudo systemctl status orangebox

Next Steps:
1. REBOOT system (required for GPS/UART)
2. Connect hardware (GPS, Servos, Camera)
3. Test GPS: bash scripts/test_gps.sh
4. Test system: python3 main.py
5. Check service: sudo systemctl status orangebox

Orange Box is ready to use!
"""
        
        self.dialog_msgbox("Installation Complete!", completion_text, height=30, width=75)
    
    def run(self):
        """Main installation flow"""
        self.show_banner()
        
        # Check if running on Raspberry Pi
        if not os.path.exists('/proc/cpuinfo'):
            print(f"{Colors.WARNING}⚠️  Not running on Raspberry Pi{Colors.ENDC}")
        else:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' not in f.read():
                    if not self.dialog_yesno("Warning", 
                        "This doesn't appear to be a Raspberry Pi.\n\n"
                        "Continue anyway?"):
                        return False
        
        # Welcome
        if not self.welcome_screen():
            print(f"\n{Colors.WARNING}Installation cancelled.{Colors.ENDC}\n")
            return False
        
        # Configure
        self.configure_settings()
        
        # Optional quick hardware tests (camera & servo)
        self.quick_tests()
        
        # Confirm
        gps_status = "Yes" if self.config['has_gps'] else "No"
        device_id_preview = self.config.get('device_id', 'Auto-generate')
        
        confirm_text = f"""
Ready to install with these settings:

Camera Index: {self.config['camera_index']}
Confidence: {self.config['confidence']*100:.0f}%
GPS Module: {gps_status}
Device ID: {device_id_preview}
Database: AWS RDS (Pre-configured)
Auto-Start: {'Yes' if self.config['auto_start'] else 'No'}

Proceed with installation?"""
        
        if not self.dialog_yesno("Confirm Installation", confirm_text, height=15):
            print(f"\n{Colors.WARNING}Installation cancelled.{Colors.ENDC}\n")
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            return False
        
        # Setup GPS
        self.setup_gps()
        
        # Setup Device ID
        self.setup_device_id()
        
        # Update config
        self.update_config()
        
        # Verify models
        self.verify_models()
        
        # Setup service
        if self.config['auto_start']:
            self.setup_service()
        
        # Test
        self.test_installation()
        
        # Complete
        self.completion_screen()
        
        print(f"\n{Colors.OKGREEN}{'='*60}")
        print("✓ INSTALLATION SUCCESSFUL!")
        print(f"{'='*60}{Colors.ENDC}\n")
        
        return True

def main():
    """Main entry point"""
    if os.geteuid() == 0:
        print(f"{Colors.FAIL}❌ Don't run this script as root/sudo{Colors.ENDC}")
        print("   The script will ask for sudo when needed.")
        sys.exit(1)
    
    installer = Installer()
    
    try:
        success = installer.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Installation interrupted by user.{Colors.ENDC}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
