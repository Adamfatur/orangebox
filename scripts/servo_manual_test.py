#!/usr/bin/env python3
"""
Servo Manual Test (No Camera)

Tujuan:
- Menjalankan test pergerakan servo TANPA kamera.
- Menggunakan venv (.venv) otomatis kalau ada.
- Menu interaktif untuk: center semua servo, lock/unlock A/B, corner UP/DOWN,
  selector ke BIN A/B/NEUTRAL, emergency stop, dan full sort sequence.

Catatan:
- Mapping channel dan derajat diambil dari config.py.
- Safety: semua perintah sudut di clamp 0–180° di driver; PWM dimatikan saat stop.
"""

import os
import sys
import time


def _ensure_project_root_on_path():
    here = os.path.abspath(os.path.dirname(__file__))
    root = os.path.abspath(os.path.join(here, '..'))
    if root not in sys.path:
        sys.path.insert(0, root)
    # also add src for absolute imports
    src = os.path.join(root, 'src')
    if src not in sys.path:
        sys.path.insert(0, src)


def _bootstrap_venv():
    """If .venv exists and not using it, relaunch with .venv/bin/python3."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    venv_py = os.path.join(root, '.venv', 'bin', 'python3')
    try:
        if os.path.exists(venv_py):
            current = os.path.abspath(sys.executable)
            if not current.startswith(os.path.join(root, '.venv')):
                print(f"🔄 Relaunching inside venv: {venv_py}")
                os.execv(venv_py, [venv_py, os.path.abspath(__file__)] + sys.argv[1:])
    except Exception as e:
        print(f"⚠️  Venv bootstrap warning: {e}")


def banner():
    print("\n" + "=" * 70)
    print("🛠  SERVO MANUAL TEST - OrangeBox (No Camera)")
    print("=" * 70)


def menu():
    print("\nMENU")
    print("1. Show mapping & config summary")
    print("2. Center ALL servos to 90°")
    print("3. Lock A → UNLOCK (90°→180°), then back to LOCK (180°→90°)")
    print("4. Lock B → UNLOCK (90°→0°), then back to LOCK (0°→90°)")
    print("5. Corners ALL UP (0°)")
    print("6. Corners ALL DOWN (90°)")
    print("7. Selector → BIN A (then NEUTRAL)")
    print("8. Selector → BIN B (then NEUTRAL)")
    print("9. Run FULL sort sequence to BIN A")
    print("10. Run FULL sort sequence to BIN B")
    print("e. Emergency STOP (PWM off)")
    print("q. Quit")


def print_config_summary(config):
    print("\nCONFIG SUMMARY")
    print(f"  SERVO_DRIVER: {getattr(config, 'SERVO_DRIVER', 'unknown')}")
    print(f"  PCA I2C: 0x{getattr(config, 'PCA9685_I2C_ADDRESS', 0x40):02X}, Freq={getattr(config, 'PCA9685_FREQUENCY', 50)}Hz")
    print("  Channels:")
    print(f"    Lock A (left):  {getattr(config, 'SERVO_L1_LOCK_LEFT_CHANNEL', 'N/A')}")
    print(f"    Lock B (right): {getattr(config, 'SERVO_L1_LOCK_RIGHT_CHANNEL', 'N/A')}")
    print(f"    Corner A:       {getattr(config, 'SERVO_L1_CORNER_A_CHANNEL', 'N/A')}")
    print(f"    Corner B:       {getattr(config, 'SERVO_L1_CORNER_B_CHANNEL', 'N/A')}")
    print(f"    Corner C:       {getattr(config, 'SERVO_L1_CORNER_C_CHANNEL', 'N/A')}")
    print(f"    Corner D:       {getattr(config, 'SERVO_L1_CORNER_D_CHANNEL', 'N/A')}")
    print(f"    Selector:       {getattr(config, 'SERVO_L2_SELECTOR_CHANNEL', 'N/A')}")
    print("  Angles:")
    print(f"    Lock (global):  LOCKED={getattr(config, 'SERVO_L1_LOCK_LOCKED', 'N/A')}°, UNLOCKED={getattr(config, 'SERVO_L1_LOCK_UNLOCKED', 'N/A')}°")
    print(f"    Lock A custom:  LOCKED={getattr(config, 'SERVO_L1_LOCK_LEFT_LOCKED', 'N/A')}°, UNLOCKED={getattr(config, 'SERVO_L1_LOCK_LEFT_UNLOCKED', 'N/A')}°")
    print(f"    Lock B custom:  LOCKED={getattr(config, 'SERVO_L1_LOCK_RIGHT_LOCKED', 'N/A')}°, UNLOCKED={getattr(config, 'SERVO_L1_LOCK_RIGHT_UNLOCKED', 'N/A')}°")
    print(f"    Corner:         UP={getattr(config, 'SERVO_L1_CORNER_UP', 'N/A')}°, DOWN={getattr(config, 'SERVO_L1_CORNER_DOWN', 'N/A')}°")
    print(f"    Selector:       NEUTRAL={getattr(config, 'SERVO_L2_SELECTOR_NEUTRAL', 'N/A')}°, A={getattr(config, 'SERVO_L2_SELECTOR_BIN_A', 'N/A')}°, B={getattr(config, 'SERVO_L2_SELECTOR_BIN_B', 'N/A')}°")
    print("  Safety:")
    print(f"    Max swing lock:   {getattr(config, 'SERVO_MAX_SWING_LOCK_DEG', 'N/A')}°")
    print(f"    Max swing corner: {getattr(config, 'SERVO_MAX_SWING_CORNER_DEG', 'N/A')}°")


def main():
    _bootstrap_venv()
    _ensure_project_root_on_path()

    import config
    from src.hardware.seven_servo_hardware import SevenServoHardware

    banner()
    hw = SevenServoHardware()

    try:
        while True:
            menu()
            choice = input("\nPilih menu: ").strip().lower()

            if choice == '1':
                print_config_summary(config)

            elif choice == '2':
                center = input("Center angle [90]: ").strip()
                center = float(center) if center else 90.0
                hw.center_all_servos(center)

            elif choice == '3':
                # Lock A: 90 → 180, then back to 90
                if 'lock_left' in hw.servos:
                    hw._move_servo('lock_left', hw.servos['lock_left']['unlocked'])
                    time.sleep(0.5)
                    hw._move_servo('lock_left', hw.servos['lock_left']['locked'])
                else:
                    print("⚠️  Lock A tidak terkonfigurasi")

            elif choice == '4':
                # Lock B: 90 → 0, then back to 90
                if 'lock_right' in hw.servos:
                    hw._move_servo('lock_right', hw.servos['lock_right']['unlocked'])
                    time.sleep(0.5)
                    hw._move_servo('lock_right', hw.servos['lock_right']['locked'])
                else:
                    print("⚠️  Lock B tidak terkonfigurasi")

            elif choice == '5':
                moves = []
                for c in ['corner_a','corner_b','corner_c','corner_d']:
                    if c in hw.servos:
                        moves.append((c, hw.servos[c]['up']))
                if moves:
                    hw._move_multiple_servos_parallel(moves)
                else:
                    print("⚠️  Corner tidak terkonfigurasi")

            elif choice == '6':
                moves = []
                for c in ['corner_a','corner_b','corner_c','corner_d']:
                    if c in hw.servos:
                        moves.append((c, hw.servos[c]['down']))
                if moves:
                    hw._move_multiple_servos_parallel(moves)
                else:
                    print("⚠️  Corner tidak terkonfigurasi")

            elif choice == '7':
                if 'selector' in hw.servos:
                    hw._move_servo('selector', hw.servos['selector']['bin_a'])
                    time.sleep(0.6)
                    hw._move_servo('selector', hw.servos['selector']['neutral'])
                else:
                    print("⚠️  Selector tidak terkonfigurasi")

            elif choice == '8':
                if 'selector' in hw.servos:
                    hw._move_servo('selector', hw.servos['selector']['bin_b'])
                    time.sleep(0.6)
                    hw._move_servo('selector', hw.servos['selector']['neutral'])
                else:
                    print("⚠️  Selector tidak terkonfigurasi")

            elif choice == '9':
                hw.sort_to_bin_a()

            elif choice == '10':
                hw.sort_to_bin_b()

            elif choice == 'e':
                print("\n⛔ Emergency STOP: PWM OFF for all channels")
                try:
                    if hw.kit is not None:
                        for sid, cfg in hw.servos.items():
                            hw.kit.servo[cfg['channel']].angle = None
                    print("✓ PWM disabled")
                except Exception as e:
                    print(f"⚠️  Emergency stop warning: {e}")

            elif choice == 'q':
                break

            else:
                print("❌ Pilihan tidak valid")

    except KeyboardInterrupt:
        print("\n⚠️  Dihentikan oleh pengguna")
    finally:
        try:
            hw.cleanup()
        except Exception:
            pass
        print("\n✅ Selesai")


if __name__ == '__main__':
    main()
