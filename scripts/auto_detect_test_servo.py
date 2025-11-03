#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║           AUTO DETECT & TEST SERVO - ORANGEBOX               ║
║     Deteksi servo otomatis dan test gerakan satu per satu   ║
╚═══════════════════════════════════════════════════════════════╝

🎯 FUNGSI:
   1. Deteksi apakah pakai GPIO atau PCA9685
   2. Scan servo yang terhubung
   3. Test gerakan tiap servo (0° → 90° → 180° → 90°)
   4. Rekomendasi setting untuk config.py

🚀 CARA PAKAI:
   python3 scripts/auto_detect_test_servo.py

⚠️  PERHATIAN:
   - Pastikan servo sudah terhubung dengan benar
   - Servo akan bergerak! Jauhkan tangan dari mekanik
   - Tekan Ctrl+C untuk berhenti kapan saja

Copyright (c) 2025 AF - OrangeBox Project
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Color codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def check_gpio():
    """Cek apakah RPi.GPIO tersedia"""
    try:
        import RPi.GPIO as GPIO
        print_success("RPi.GPIO tersedia")
        return True
    except ImportError:
        print_error("RPi.GPIO tidak ditemukan")
        print_info("Install dengan: sudo apt install python3-rpi.gpio")
        return False


def check_pca9685():
    """Cek apakah PCA9685 tersedia"""
    print_info("Mengecek PCA9685/ServoKit...")
    
    # Check library
    try:
        from adafruit_servokit import ServoKit
        print_success("Library ServoKit tersedia")
    except ImportError:
        print_error("Library ServoKit tidak ditemukan")
        print_info("Install dengan: pip install adafruit-servokit")
        return False
    
    # Check I2C device
    try:
        import subprocess
        result = subprocess.run(['i2cdetect', '-y', '1'], 
                              capture_output=True, text=True, timeout=5)
        
        if '40' in result.stdout or '0x40' in result.stdout:
            print_success("PCA9685 terdeteksi di alamat 0x40")
            return True
        else:
            print_warning("PCA9685 tidak terdeteksi di I2C")
            print_info("Pastikan board PCA9685 terhubung dengan benar")
            print_info("Cek dengan: i2cdetect -y 1")
            return False
    except FileNotFoundError:
        print_warning("Command i2cdetect tidak tersedia")
        print_info("Install dengan: sudo apt install i2c-tools")
        return False
    except Exception as e:
        print_warning(f"Tidak bisa cek I2C: {e}")
        return False


def test_gpio_servo(pin, name):
    """Test servo di GPIO pin tertentu"""
    try:
        import RPi.GPIO as GPIO
        
        print(f"\n{Colors.BOLD}Testing {name} (GPIO Pin {pin}):{Colors.END}")
        
        # Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, 50)  # 50Hz
        pwm.start(0)
        
        def set_angle(angle):
            """Convert angle to duty cycle"""
            duty = 2 + (angle / 18)
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.5)
            pwm.ChangeDutyCycle(0)  # Stop signal
        
        # Test sequence: 90° ↔ 0° sebanyak 3x
        print("  Test bolak-balik 90° ↔ 0° (3x):")
        for i in range(3):
            print(f"  [{i+1}] 90°", end='', flush=True)
            set_angle(90)
            time.sleep(0.6)
            print(" → 0°", end='', flush=True)
            set_angle(0)
            time.sleep(0.6)
            print(" ✓")
        
        # Cleanup
        pwm.stop()
        GPIO.cleanup(pin)
        
        print_success(f"{name} OK!")
        return True
        
    except Exception as e:
        print_error(f"Error: {e}")
        try:
            GPIO.cleanup(pin)
        except:
            pass
        return False


def test_pca9685_servo(channel, name):
    """Test servo di PCA9685 channel tertentu"""
    try:
        from adafruit_servokit import ServoKit
        
        print(f"\n{Colors.BOLD}Testing {name} (PCA9685 Channel {channel}):{Colors.END}")
        
        # Initialize
        kit = ServoKit(channels=16, address=0x40)
        
        # Test sequence: 90° ↔ 0° sebanyak 3x
        print("  Test bolak-balik 90° ↔ 0° (3x):")
        for i in range(3):
            print(f"  [{i+1}] 90°", end='', flush=True)
            kit.servo[channel].angle = 90
            time.sleep(0.6)
            print(" → 0°", end='', flush=True)
            kit.servo[channel].angle = 0
            time.sleep(0.6)
            print(" ✓")
        
        print_success(f"{name} OK!")
        return True
        
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def scan_gpio_servos():
    """Scan dan test servo di GPIO"""
    print_header("SCAN GPIO SERVOS")
    
    if not check_gpio():
        return []
    
    # GPIO pins yang umum dipakai untuk servo
    common_pins = [12, 13, 18, 19, 16, 26, 20, 21]
    
    print_info("Scanning GPIO pins: " + ", ".join(map(str, common_pins)))
    print_warning("Servo akan bergerak! Pastikan aman.")
    
    input("\nTekan ENTER untuk mulai test GPIO...")
    
    working_servos = []
    
    for pin in common_pins:
        if test_gpio_servo(pin, f"GPIO{pin}"):
            working_servos.append(('gpio', pin))
            time.sleep(1)
    
    return working_servos


def scan_pca9685_servos():
    """Scan dan test servo di PCA9685"""
    print_header("SCAN PCA9685 SERVOS")
    
    if not check_pca9685():
        return []
    
    print_info("Scanning PCA9685 channels 0-15")
    print_warning("Servo akan bergerak! Pastikan aman.")
    
    input("\nTekan ENTER untuk mulai test PCA9685...")
    
    working_servos = []
    
    for channel in range(16):
        if test_pca9685_servo(channel, f"CH{channel}"):
            working_servos.append(('pca9685', channel))
            time.sleep(1)
    
    return working_servos


def generate_config_recommendation(servos):
    """Generate rekomendasi config berdasarkan servo yang terdeteksi"""
    print_header("REKOMENDASI CONFIG.PY")
    
    if not servos:
        print_error("Tidak ada servo terdeteksi!")
        return
    
    # Group by type
    gpio_servos = [s[1] for s in servos if s[0] == 'gpio']
    pca_servos = [s[1] for s in servos if s[0] == 'pca9685']
    
    print(f"Terdeteksi: {len(gpio_servos)} servo GPIO, {len(pca_servos)} servo PCA9685\n")
    
    # Determine driver
    if pca_servos and len(pca_servos) >= 3:
        print(f"{Colors.GREEN}Rekomendasi: Gunakan PCA9685 (ServoKit){Colors.END}")
        print(f"\nTambahkan ke config.py:")
        print(f"{Colors.CYAN}─────────────────────────────────────{Colors.END}")
        print(f"SERVO_DRIVER = 'servokit'\n")
        
        if len(pca_servos) >= 5:
            print("# 5-Servo Setup (PCA9685)")
            if len(pca_servos) >= 1:
                print(f"SERVO_LAYER2_SELECTOR_CHANNEL = {pca_servos[0]}  # Pemilah")
            if len(pca_servos) >= 3:
                print(f"SERVO_LAYER1_LEFT_CHANNEL = {pca_servos[1]}      # Pintu Kiri A")
                print(f"SERVO_LAYER1_RIGHT_CHANNEL = {pca_servos[2]}     # Pintu Kanan A")
            if len(pca_servos) >= 5:
                print(f"SERVO_LAYER1_LEFT2_CHANNEL = {pca_servos[3]}     # Pintu Kiri B")
                print(f"SERVO_LAYER1_RIGHT2_CHANNEL = {pca_servos[4]}    # Pintu Kanan B")
        else:
            print("# 3-Servo Setup (PCA9685)")
            if len(pca_servos) >= 1:
                print(f"SERVO_LAYER2_SELECTOR_CHANNEL = {pca_servos[0]}  # Pemilah")
            if len(pca_servos) >= 3:
                print(f"SERVO_LAYER1_LEFT_CHANNEL = {pca_servos[1]}      # Pintu Kiri")
                print(f"SERVO_LAYER1_RIGHT_CHANNEL = {pca_servos[2]}     # Pintu Kanan")
        
        print(f"{Colors.CYAN}─────────────────────────────────────{Colors.END}")
        
    elif gpio_servos and len(gpio_servos) >= 3:
        print(f"{Colors.GREEN}Rekomendasi: Gunakan GPIO{Colors.END}")
        print(f"\nTambahkan ke config.py:")
        print(f"{Colors.CYAN}─────────────────────────────────────{Colors.END}")
        print(f"SERVO_DRIVER = 'gpio'\n")
        print("# 3-Servo Setup (GPIO)")
        if len(gpio_servos) >= 1:
            print(f"SERVO_LAYER2_SELECTOR_PIN = {gpio_servos[0]}  # Pemilah")
        if len(gpio_servos) >= 3:
            print(f"SERVO_LAYER1_LEFT_PIN = {gpio_servos[1]}      # Pintu Kiri")
            print(f"SERVO_LAYER1_RIGHT_PIN = {gpio_servos[2]}     # Pintu Kanan")
        if len(gpio_servos) >= 5:
            print(f"SERVO_LAYER1_LEFT2_PIN = {gpio_servos[3]}     # Pintu Kiri 2 (opsional)")
            print(f"SERVO_LAYER1_RIGHT2_PIN = {gpio_servos[4]}    # Pintu Kanan 2 (opsional)")
        print(f"{Colors.CYAN}─────────────────────────────────────{Colors.END}")
    
    else:
        print_warning(f"Hanya terdeteksi {len(servos)} servo. Minimal butuh 3 servo.")
    
    # Catatan derajat
    print(f"\n{Colors.YELLOW}📝 CATATAN DERAJAT:{Colors.END}")
    print("   Servo di-test dengan gerakan bolak-balik: 90° ↔ 0° (3x)")
    print("   Jika servo bergerak terbalik, tukar nilai CLOSED/OPEN")
    print("   di config.py sesuai dengan posisi fisik servo Anda.")


def main():
    """Main function"""
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║           AUTO DETECT & TEST SERVO - ORANGEBOX               ║
║     Deteksi servo otomatis dan test gerakan satu per satu   ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print_info("Script ini akan:")
    print("  1. Deteksi hardware (GPIO/PCA9685)")
    print("  2. Test gerakan tiap servo yang terdeteksi")
    print("  3. Beri rekomendasi config.py\n")
    
    print_warning("PASTIKAN:")
    print("  - Servo sudah terhubung dengan benar")
    print("  - Power supply 5V mencukupi")
    print("  - Tidak ada yang menghalangi gerakan servo\n")
    
    try:
        # Pilihan mode
        print(f"{Colors.BOLD}Pilih mode deteksi:{Colors.END}")
        print("  1. GPIO only")
        print("  2. PCA9685 only")
        print("  3. Both (GPIO + PCA9685)")
        
        choice = input("\nPilihan (1/2/3): ").strip()
        
        all_servos = []
        
        if choice in ['1', '3']:
            servos = scan_gpio_servos()
            all_servos.extend(servos)
        
        if choice in ['2', '3']:
            servos = scan_pca9685_servos()
            all_servos.extend(servos)
        
        # Generate recommendation
        if all_servos:
            generate_config_recommendation(all_servos)
        else:
            print_header("HASIL")
            print_error("Tidak ada servo yang terdeteksi!")
            print_info("\nPossible issues:")
            print("  - Servo tidak terhubung dengan benar")
            print("  - Power supply tidak mencukupi")
            print("  - Pin/channel salah")
            print("  - Driver tidak terinstall")
        
        print(f"\n{Colors.GREEN}{'='*70}{Colors.END}")
        print(f"{Colors.GREEN}Deteksi selesai!{Colors.END}")
        print(f"{Colors.GREEN}{'='*70}{Colors.END}\n")
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Program dihentikan oleh user.{Colors.END}")
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
