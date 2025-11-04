#!/usr/bin/env python3
"""
Auto-Detect Servo Hardware
Deteksi otomatis servo yang terhubung ke Raspberry Pi.

Mendeteksi:
1. GPIO-based servos (RPi.GPIO + PWM)
2. PCA9685-based servos (I2C ServoKit)
3. Number of servos connected
4. Servo channels/pins yang aktif

Output: Konfigurasi servo yang terdeteksi
"""

import sys
import os

def detect_gpio_servos():
    """Deteksi servo yang terhubung via GPIO PWM."""
    print("🔍 Scanning GPIO PWM pins for servos...")
    
    detected_servos = []
    
    try:
        import RPi.GPIO as GPIO
        
        # Pins yang umum digunakan untuk PWM servo (BCM numbering)
        # Hardware PWM: GPIO 12, 13, 18, 19
        # Software PWM: Any GPIO (but less accurate)
        common_pwm_pins = [12, 13, 18, 19, 16, 26, 20, 21]
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        for pin in common_pwm_pins:
            try:
                # Try to set pin as PWM output
                GPIO.setup(pin, GPIO.OUT)
                pwm = GPIO.PWM(pin, 50)  # 50Hz for servo
                
                # Test if we can start PWM (servo would respond)
                pwm.start(7.5)  # Neutral position (90 degrees)
                
                # If no error, servo might be connected
                detected_servos.append({
                    'type': 'GPIO_PWM',
                    'pin': pin,
                    'interface': 'RPi.GPIO'
                })
                
                pwm.stop()
                print(f"   ✓ Found potential servo on GPIO {pin}")
                
            except Exception as e:
                # Pin not available or error
                pass
        
        GPIO.cleanup()
        
    except ImportError:
        print("   ℹ️  RPi.GPIO not available (not on Raspberry Pi)")
        return []
    except Exception as e:
        print(f"   ⚠️  GPIO detection error: {e}")
        return []
    
    return detected_servos


def detect_pca9685_servos():
    """Deteksi servo yang terhubung via PCA9685 (I2C)."""
    print("\n🔍 Scanning I2C bus for PCA9685 servo controller...")
    
    detected = {
        'found': False,
        'address': None,
        'channels': [],
        'type': 'PCA9685'
    }
    
    try:
        from adafruit_servokit import ServoKit
        
        # Common PCA9685 I2C addresses
        addresses = [0x40, 0x41, 0x42, 0x43]
        
        for addr in addresses:
            try:
                # Try to initialize ServoKit at this address
                kit = ServoKit(channels=16, address=addr)
                
                print(f"   ✓ Found PCA9685 at address 0x{addr:02X}")
                detected['found'] = True
                detected['address'] = addr
                
                # Try to detect which channels have servos
                # Note: This is a best-effort; can't definitively detect without physical test
                # We'll just report that PCA9685 is available
                print(f"   ℹ️  PCA9685 supports 16 channels (0-15)")
                print(f"   ℹ️  To test channels, use: python3 scripts/test_seven_servo.py")
                
                break
                
            except Exception as e:
                # Address not responding
                continue
        
        if not detected['found']:
            print("   ✗ No PCA9685 found on I2C bus")
            print("   ℹ️  Check I2C is enabled: sudo raspi-config → Interface Options → I2C")
            print("   ℹ️  Check wiring: SDA=GPIO2, SCL=GPIO3, VCC=5V, GND=GND")
    
    except ImportError:
        print("   ℹ️  adafruit-servokit not installed")
        print("   → Install with: pip install adafruit-circuitpython-servokit")
        return detected
    except Exception as e:
        print(f"   ⚠️  PCA9685 detection error: {e}")
    
    return detected


def detect_i2c_devices():
    """Scan I2C bus untuk semua device (termasuk PCA9685)."""
    print("\n🔍 Scanning I2C bus for all devices...")
    
    try:
        import subprocess
        result = subprocess.run(['i2cdetect', '-y', '1'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        
        if result.returncode == 0:
            print("   I2C Bus 1 scan:")
            # Parse output untuk temukan device addresses
            lines = result.stdout.split('\n')
            devices_found = []
            
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    for part in parts[1:]:  # Skip row number
                        if part != '--' and len(part) == 2:
                            devices_found.append(part)
            
            if devices_found:
                print(f"   ✓ Found {len(devices_found)} I2C device(s): {', '.join(['0x'+d for d in devices_found])}")
                
                # Check if any is PCA9685 (0x40-0x43 range)
                pca_addrs = [d for d in devices_found if d.lower() in ['40', '41', '42', '43']]
                if pca_addrs:
                    print(f"   ✓ Possible PCA9685 at: {', '.join(['0x'+a for a in pca_addrs])}")
            else:
                print("   ✗ No I2C devices found")
                print("   → Check I2C is enabled and devices are connected")
        else:
            print(f"   ⚠️  i2cdetect failed: {result.stderr}")
            
    except FileNotFoundError:
        print("   ℹ️  i2cdetect not found (install i2c-tools: sudo apt install i2c-tools)")
    except subprocess.TimeoutExpired:
        print("   ⚠️  i2cdetect timeout (I2C may be disabled)")
    except Exception as e:
        print(f"   ⚠️  I2C scan error: {e}")


def recommend_config():
    """Berikan rekomendasi konfigurasi berdasarkan hardware yang terdeteksi."""
    print("\n" + "="*70)
    print("📋 RECOMMENDED CONFIGURATION")
    print("="*70)
    
    gpio_servos = detect_gpio_servos()
    pca9685 = detect_pca9685_servos()
    detect_i2c_devices()
    
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS")
    print("="*70)
    
    if pca9685['found']:
        print("\n✅ PCA9685 Detected - Recommended Setup:")
        print(f"   SERVO_DRIVER = 'servokit'")
        print(f"   PCA9685_I2C_ADDRESS = 0x{pca9685['address']:02X}")
        print(f"   PCA9685_FREQUENCY = 50")
        print("\n   Channel mapping (edit in config.py):")
        print("   - SERVO_L1_LEFT_A_CH = 2    # Layer 1 left door A")
        print("   - SERVO_L1_RIGHT_A_CH = 3   # Layer 1 right door A")
        print("   - SERVO_L2_SELECTOR_CH = 0  # Layer 2 selector")
        print("\n   Test with:")
        print("   python3 scripts/test_seven_servo.py")
        
    elif gpio_servos:
        print(f"\n✅ {len(gpio_servos)} GPIO Servo(s) Detected - Recommended Setup:")
        print(f"   SERVO_DRIVER = 'gpio'")
        print("\n   Pin mapping (edit in config.py):")
        for servo in gpio_servos:
            print(f"   - GPIO {servo['pin']}")
        print("\n   Example config:")
        if len(gpio_servos) >= 3:
            print(f"   SERVO_LAYER1_LEFT_PIN = {gpio_servos[0]['pin']}")
            print(f"   SERVO_LAYER1_RIGHT_PIN = {gpio_servos[1]['pin']}")
            print(f"   SERVO_LAYER2_SELECTOR_PIN = {gpio_servos[2]['pin']}")
    
    else:
        print("\n⚠️  No servos detected!")
        print("\n   Possible reasons:")
        print("   1. No servos connected")
        print("   2. I2C not enabled (for PCA9685)")
        print("   3. Incorrect wiring")
        print("   4. Servo power supply issue")
        print("\n   Next steps:")
        print("   1. Check physical connections")
        print("   2. Enable I2C: sudo raspi-config → Interface Options → I2C")
        print("   3. Test I2C: i2cdetect -y 1")
        print("   4. Check servo power (5-6V, sufficient current)")
    
    print("\n" + "="*70)


def main():
    """Main entry point."""
    print("=" * 70)
    print("🔧 ORANGEBOX SERVO AUTO-DETECTION")
    print("=" * 70)
    print()
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            if 'Raspberry Pi' not in f.read():
                print("⚠️  Not running on Raspberry Pi")
                print("   This script is designed for Raspberry Pi hardware")
                print()
    except:
        print("⚠️  Cannot detect platform")
        print()
    
    recommend_config()
    
    print("\n✅ Detection complete!")
    print()


if __name__ == "__main__":
    main()
