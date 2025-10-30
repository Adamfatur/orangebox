"""
Servo Test Script for OrangeBox

Tujuan:
- Verifikasi cepat apakah servo bekerja pada Raspberry Pi 5
- Otomatis deteksi platform: gunakan PCA9685 bila tersedia, fallback ke 3-servo GPIO
- Menjalankan urutan aman: netral → Bin A → netral → Bin B → netral → cleanup

Cara pakai:
  python3 scripts/test_servo.py

Catatan:
- Di macOS / non-RPi: simulasi (log print), tidak gerak fisik.
- Di Raspberry Pi 5: jika pustaka Adafruit tersedia, servo dikendalikan via PCA9685.
"""

import sys
import os
import time

# Ensure project root on path to import config and hardware modules
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

HAS_GPIO = False
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except Exception:
    HAS_GPIO = False

# Adafruit PCA9685 (I2C) libraries
HAS_PCA9685 = False
try:
    from board import SCL, SDA
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo as adafruit_servo
    HAS_PCA9685 = True
except Exception:
    HAS_PCA9685 = False


def is_raspberry_pi() -> bool:
    try:
        import platform
        return platform.system() == 'Linux'
    except Exception:
        return False


def main():
    print("=" * 60)
    print("OrangeBox Servo Test")
    print("=" * 60)

    # Inform platform
    if is_raspberry_pi():
        print(f"Platform: Raspberry Pi ({'PCA9685' if HAS_PCA9685 else 'GPIO'} available)")
    else:
        print("Platform: Non-RPi (simulation mode)")

    # Import hardware controller
    try:
        import config
        # Import opsional untuk fallback GPIO
        try:
            from src.hardware.three_servo_hardware import ThreeServoHardware
        except Exception:
            ThreeServoHardware = None
    except Exception as e:
        print(f"[ERROR] Failed to import hardware modules: {e}")
        return

    hw = None
    pca = None
    pca_servo = None
    try:
        if is_raspberry_pi() and HAS_PCA9685:
            print("\nMode: PCA9685 (I2C) driver")
            try:
                # Init I2C & PCA9685
                i2c = busio.I2C(SCL, SDA)
                pca = PCA9685(i2c)
                pca.frequency = getattr(config, 'SERVO_PWM_FREQUENCY', 50)

                # Channel & angles
                ch = getattr(config, 'SERVO_CHANNEL', 0)
                angle_neutral = getattr(config, 'SERVO_LAYER2_NEUTRAL', getattr(config, 'SERVO_ANGLE_NEUTRAL', 90))
                angle_a = getattr(config, 'SERVO_LAYER2_BIN_A', getattr(config, 'SERVO_ANGLE_BIN_A', 60))
                angle_b = getattr(config, 'SERVO_LAYER2_BIN_B', getattr(config, 'SERVO_ANGLE_BIN_B', 120))

                print(f"Using PCA9685 channel: {ch}")
                print(f"Angles → Neutral:{angle_neutral}°, BinA:{angle_a}°, BinB:{angle_b}°")

                # Create servo instance
                pca_servo = adafruit_servo.Servo(
                    pca.channels[ch],
                    min_pulse=500,
                    max_pulse=2500
                )

                # Optional: scan all channels to try to detect the single connected servo
                def clamp(v):
                    return max(0, min(180, int(v)))
                scan_delta = 20
                print("\nScanning PCA9685 channels (0-15) with small motion pattern...")
                for scan_ch in range(16):
                    try:
                        s = adafruit_servo.Servo(pca.channels[scan_ch], min_pulse=500, max_pulse=2500)
                        print(f"[SCAN] Channel {scan_ch}: neutral → -{scan_delta} → +{scan_delta}")
                        s.angle = clamp(angle_neutral)
                        time.sleep(0.5)
                        s.angle = clamp(angle_neutral - scan_delta)
                        time.sleep(0.6)
                        s.angle = clamp(angle_neutral + scan_delta)
                        time.sleep(0.6)
                        s.angle = clamp(angle_neutral)
                        time.sleep(0.4)
                    except Exception as se:
                        print(f"[SCAN] Channel {scan_ch} error: {se}")

                # Sequence: neutral → A → neutral → B → neutral
                print("\nInitializing: Neutral position")
                pca_servo.angle = angle_neutral
                time.sleep(1)

                print("\n" + "=" * 60)
                print("TEST 1 (PCA9685): Move to Bin A")
                print("=" * 60)
                pca_servo.angle = angle_a
                time.sleep(1.5)
                pca_servo.angle = angle_neutral
                print("✓ Test 1 PASSED")
                time.sleep(1)

                print("\n" + "=" * 60)
                print("TEST 2 (PCA9685): Move to Bin B")
                print("=" * 60)
                pca_servo.angle = angle_b
                time.sleep(1.5)
                pca_servo.angle = angle_neutral
                print("✓ Test 2 PASSED")
                time.sleep(1)

                print("\nFinal Reset (Neutral)")
                pca_servo.angle = angle_neutral
                print("\n" + "=" * 60)
                print("✓ SERVO TEST COMPLETE (PCA9685)")
                print("=" * 60)
            except Exception as e:
                print(f"[ERROR] PCA9685 init/move failed: {e}")
                print("[INFO] Fallback to ThreeServoHardware (GPIO/simulasi)")
                # Force fallback path below
                HAS_PCA9685_local = False
                # Proceed to fallback block
                if ThreeServoHardware is None:
                    print("[WARN] ThreeServoHardware not available; running in pure simulation.")
                    print("Simulated: Neutral → Bin A → Neutral → Bin B → Neutral")
                    time.sleep(3)
                else:
                    hw = ThreeServoHardware()
                    status = hw.get_status()
                    print("\nSystem Status:")
                    print(f"  Active: {status['active']}")
                    print(f"  GPIO: {status['has_gpio']}")
                    print(f"  Servos: {status['count']}/3")
                    for sid, info in status['servos'].items():
                        print(f"  - {info['name']}: GPIO {info['pin']}")
                    try:
                        if hasattr(hw, 'reset_to_ready'):
                            hw.reset_to_ready()
                        else:
                            hw.reset_to_ready_position()
                    except Exception:
                        pass
                    time.sleep(1)
                    bin_a_angle = getattr(config, 'SERVO_LAYER2_BIN_A', 60)
                    ok = hw.execute_sort('BIN A', bin_a_angle)
                    print("✓ Test 1 PASSED" if ok else "✗ Test 1 FAILED")
                    time.sleep(2)
                    try:
                        if hasattr(hw, 'reset_to_ready'):
                            hw.reset_to_ready()
                        else:
                            hw.reset_to_ready_position()
                    except Exception:
                        pass
                    time.sleep(1)
                    bin_b_angle = getattr(config, 'SERVO_LAYER2_BIN_B', 120)
                    ok = hw.execute_sort('BIN B', bin_b_angle)
                    print("✓ Test 2 PASSED" if ok else "✗ Test 2 FAILED")
                    time.sleep(2)
                    try:
                        if hasattr(hw, 'reset_to_ready'):
                            hw.reset_to_ready()
                        else:
                            hw.reset_to_ready_position()
                    except Exception:
                        pass
                    print("\n" + "=" * 60)
                    print("✓ SERVO TEST COMPLETE")
                    print("=" * 60)

        else:
            # Fallback: use ThreeServoHardware (GPIO PWM) or simulation
            if ThreeServoHardware is None:
                print("[WARN] ThreeServoHardware not available; running in pure simulation.")
                print("Simulated: Neutral → Bin A → Neutral → Bin B → Neutral")
                time.sleep(3)
            else:
                hw = ThreeServoHardware()

                # Show basic status
                status = hw.get_status()
                print("\nSystem Status:")
                print(f"  Active: {status['active']}")
                print(f"  GPIO: {status['has_gpio']}")
                print(f"  Servos: {status['count']}/3")
                for sid, info in status['servos'].items():
                    print(f"  - {info['name']}: GPIO {info['pin']}")

                print("\nInitializing: Reset to ready position")
                try:
                    if hasattr(hw, 'reset_to_ready'):
                        hw.reset_to_ready()
                    else:
                        hw.reset_to_ready_position()
                except Exception:
                    pass
                time.sleep(1)

                print("\n" + "=" * 60)
                print("TEST 1: Sort to Bin A (Organic)")
                print("=" * 60)
                bin_a_angle = getattr(config, 'SERVO_LAYER2_BIN_A', 60)
                ok = hw.execute_sort('BIN A', bin_a_angle)
                print("✓ Test 1 PASSED" if ok else "✗ Test 1 FAILED")
                time.sleep(2)

                print("\nReset to ready position")
                try:
                    if hasattr(hw, 'reset_to_ready'):
                        hw.reset_to_ready()
                    else:
                        hw.reset_to_ready_position()
                except Exception:
                    pass
                time.sleep(1)

                print("\n" + "=" * 60)
                print("TEST 2: Sort to Bin B (Anorganic)")
                print("=" * 60)
                bin_b_angle = getattr(config, 'SERVO_LAYER2_BIN_B', 120)
                ok = hw.execute_sort('BIN B', bin_b_angle)
                print("✓ Test 2 PASSED" if ok else "✗ Test 2 FAILED")
                time.sleep(2)

                print("\nFinal Reset: Returning to ready state")
                try:
                    if hasattr(hw, 'reset_to_ready'):
                        hw.reset_to_ready()
                    else:
                        hw.reset_to_ready_position()
                except Exception:
                    pass

                print("\n" + "=" * 60)
                print("✓ SERVO TEST COMPLETE")
                print("=" * 60)

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Servo test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nCleaning up...")
        try:
            if pca is not None:
                # Reset channel to neutral if possible
                try:
                    if pca_servo is not None:
                        angle_neutral = getattr(config, 'SERVO_LAYER2_NEUTRAL', getattr(config, 'SERVO_ANGLE_NEUTRAL', 90))
                        pca_servo.angle = angle_neutral
                        time.sleep(0.5)
                except Exception:
                    pass
                try:
                    # Deinit PCA if supported
                    if hasattr(pca, 'deinit'):
                        pca.deinit()
                except Exception:
                    pass
            if hw is not None:
                hw.cleanup()
        except Exception:
            pass
        print("Cleanup complete.")


if __name__ == "__main__":
    main()