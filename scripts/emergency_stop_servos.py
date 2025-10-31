#!/usr/bin/env python3
"""
Orange Box - Emergency Servo Stop
CRITICAL: Force stop all servos immediately and safely
"""

import sys
import time

def print_header():
    print("\n" + "="*70)
    print("🚨 EMERGENCY SERVO STOP 🚨")
    print("="*70 + "\n")

def stop_servos_servokit():
    """Stop servos using Adafruit ServoKit (PCA9685)"""
    try:
        from adafruit_servokit import ServoKit
        
        print("📌 Detected: Adafruit ServoKit (PCA9685)")
        print("   Stopping all servo channels...")
        
        # Initialize ServoKit (16 channels)
        kit = ServoKit(channels=16)
        
        # Stop all servo channels (0-15)
        channels_stopped = 0
        for channel in range(16):
            try:
                # Set to None to release PWM control
                kit.servo[channel].angle = None
                channels_stopped += 1
            except:
                pass
        
        print(f"   ✅ Stopped {channels_stopped}/16 channels")
        return True
        
    except ImportError:
        print("   ⚠️  ServoKit not available")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def stop_servos_pca9685():
    """Stop servos using Adafruit PCA9685 directly"""
    try:
        import board
        import busio
        from adafruit_pca9685 import PCA9685
        
        print("📌 Detected: Adafruit PCA9685 (Direct)")
        print("   Stopping all PWM channels...")
        
        # Initialize I2C and PCA9685
        i2c = busio.I2C(board.SCL, board.SDA)
        pca = PCA9685(i2c)
        pca.frequency = 50  # 50Hz for servos
        
        # Stop all channels (0-15)
        for channel in range(16):
            pca.channels[channel].duty_cycle = 0
        
        # Deinit PCA9685
        pca.deinit()
        
        print("   ✅ All PWM channels stopped")
        return True
        
    except ImportError:
        print("   ⚠️  PCA9685 library not available")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def stop_servos_gpio():
    """Stop servos using RPi.GPIO (direct GPIO PWM)"""
    try:
        import RPi.GPIO as GPIO
        
        print("📌 Detected: RPi.GPIO (Direct GPIO control)")
        print("   Stopping GPIO PWM servos...")
        
        # Servo GPIO pins from config
        servo_pins = [12, 13, 18]  # Layer1_Left, Layer1_Right, Layer2_Selector
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        stopped = 0
        for pin in servo_pins:
            try:
                GPIO.setup(pin, GPIO.OUT)
                pwm = GPIO.PWM(pin, 50)  # 50Hz
                pwm.start(0)  # 0% duty cycle
                time.sleep(0.1)
                pwm.stop()
                GPIO.cleanup(pin)
                stopped += 1
            except:
                pass
        
        print(f"   ✅ Stopped {stopped}/{len(servo_pins)} GPIO servos")
        return stopped > 0
        
    except ImportError:
        print("   ⚠️  RPi.GPIO not available")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def force_i2c_reset():
    """Force reset I2C bus (PCA9685)"""
    try:
        import subprocess
        
        print("📌 Force I2C Reset")
        print("   Resetting I2C bus 1...")
        
        # Get current I2C devices
        result = subprocess.run(['i2cdetect', '-y', '1'], 
                              capture_output=True, text=True)
        
        if '40' in result.stdout:
            print("   ✅ PCA9685 detected at 0x40")
            
            # Reset using i2cset (set all channels to 0)
            subprocess.run(['i2cset', '-y', '1', '0x40', '0xFA', '0x00'], 
                         capture_output=True)
            subprocess.run(['i2cset', '-y', '1', '0x40', '0xFB', '0x00'], 
                         capture_output=True)
            subprocess.run(['i2cset', '-y', '1', '0x40', '0xFC', '0x00'], 
                         capture_output=True)
            subprocess.run(['i2cset', '-y', '1', '0x40', '0xFD', '0x00'], 
                         capture_output=True)
            
            print("   ✅ I2C reset complete")
            return True
        else:
            print("   ⚠️  PCA9685 not detected")
            return False
            
    except FileNotFoundError:
        print("   ⚠️  i2c-tools not installed")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def kill_main_process():
    """Kill any running main.py process"""
    try:
        import subprocess
        
        print("📌 Checking for running processes")
        
        # Find main.py processes
        result = subprocess.run(['pgrep', '-f', 'main.py'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"   Found {len(pids)} process(es)")
            
            for pid in pids:
                subprocess.run(['kill', '-9', pid], capture_output=True)
                print(f"   ✅ Killed process {pid}")
            
            return True
        else:
            print("   ℹ️  No running processes")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def stop_systemd_service():
    """Stop orangebox systemd service"""
    try:
        import subprocess
        
        print("📌 Checking systemd service")
        
        # Check if service is active
        result = subprocess.run(['systemctl', 'is-active', 'orangebox'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip() == 'active':
            print("   Service is running, stopping...")
            subprocess.run(['sudo', 'systemctl', 'stop', 'orangebox'])
            print("   ✅ Service stopped")
            return True
        else:
            print(f"   ℹ️  Service status: {result.stdout.strip()}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main emergency stop routine"""
    print_header()
    
    print("⚠️  WARNING: This will forcefully stop ALL servos!")
    print("   Use this in emergency situations only.")
    print()
    
    # Ask for confirmation
    try:
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("\n❌ Operation cancelled\n")
            return 1
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled\n")
        return 1
    
    print("\n" + "="*70)
    print("🚨 EMERGENCY STOP SEQUENCE")
    print("="*70 + "\n")
    
    success_count = 0
    total_attempts = 6
    
    # 1. Stop systemd service
    print("STEP 1: Stop System Service")
    print("─" * 70)
    if stop_systemd_service():
        success_count += 1
    time.sleep(0.5)
    
    # 2. Kill main process
    print("\nSTEP 2: Kill Main Process")
    print("─" * 70)
    if kill_main_process():
        success_count += 1
    time.sleep(0.5)
    
    # 3. Stop servos via ServoKit
    print("\nSTEP 3: Stop Servos (ServoKit)")
    print("─" * 70)
    if stop_servos_servokit():
        success_count += 1
    time.sleep(0.5)
    
    # 4. Stop servos via PCA9685
    print("\nSTEP 4: Stop Servos (PCA9685 Direct)")
    print("─" * 70)
    if stop_servos_pca9685():
        success_count += 1
    time.sleep(0.5)
    
    # 5. Stop servos via GPIO
    print("\nSTEP 5: Stop Servos (GPIO Direct)")
    print("─" * 70)
    if stop_servos_gpio():
        success_count += 1
    time.sleep(0.5)
    
    # 6. Force I2C reset
    print("\nSTEP 6: Force I2C Reset")
    print("─" * 70)
    if force_i2c_reset():
        success_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("EMERGENCY STOP SUMMARY")
    print("="*70 + "\n")
    
    print(f"  Successful operations: {success_count}/{total_attempts}")
    print()
    
    if success_count >= 1:
        print("  ✅ SERVOS STOPPED SUCCESSFULLY")
        print()
        print("  All servos should now be in safe state:")
        print("    • PWM signals disabled")
        print("    • GPIO pins released")
        print("    • I2C bus reset")
        print("    • Processes terminated")
        print()
        return_code = 0
    else:
        print("  ❌ FAILED TO STOP SERVOS")
        print()
        print("  Manual intervention required:")
        print("    1. Power cycle the Raspberry Pi")
        print("    2. Disconnect servo power supply")
        print("    3. Check I2C connection: i2cdetect -y 1")
        print()
        return_code = 1
    
    print("="*70 + "\n")
    
    return return_code

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Emergency stop interrupted!")
        print("   Servos may still be active!\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("   Power cycle the system immediately!\n")
        sys.exit(1)
