#!/usr/bin/env python3
"""
Servo Direct Test (PCA9685) — Tanpa Kamera, Tanpa Aplikasi Utama

Tujuan:
- Menguji gerak servo langsung via Adafruit ServoKit (PCA9685), tanpa lapisan controller lain.
- Dipakai untuk diagnosa awal: cek power, I2C, alamat PCA, dan pergerakan per channel.

Fitur:
- Auto-bootstrap venv jika ada .venv.
- Menu sederhana: set CHANNEL→ANGLE, preset Lock A/B, Corners UP/DOWN, Selector A/B/NEUTRAL, Emergency OFF.
- Opsi CLI cepat: --ch N --angle A untuk set satu channel langsung.

Panduan (Bahasa Indonesia):
- Nilai sudut servo adalah 0–180° (AMAN). Jangan paksa di luar rentang ini.
- Atur nilai default di file config.py:
    • Corner: SERVO_L1_CORNER_UP (default 0°), SERVO_L1_CORNER_DOWN (default 90°)
    • Lock A (kiri): SERVO_L1_LOCK_LEFT_LOCKED (90°), SERVO_L1_LOCK_LEFT_UNLOCKED (180°)
    • Lock B (kanan): SERVO_L1_LOCK_RIGHT_LOCKED (90°), SERVO_L1_LOCK_RIGHT_UNLOCKED (0°)
    • Selector: SERVO_L2_SELECTOR_NEUTRAL (90°), SERVO_L2_SELECTOR_BIN_A (60°), SERVO_L2_SELECTOR_BIN_B (120°)
- Jika horn tidak tepat 90°, gunakan offset di config.py:
    • SERVO_OFFSET_LOCK_LEFT/RIGHT, SERVO_OFFSET_CORNER_A/B/C/D, SERVO_OFFSET_SELECTOR
    • Nilai positif memutar searah jarum jam, negatif berlawanan (satuan derajat)
- Tips kalibrasi cepat:
    1) Gunakan opsi menu "1. Set CHANNEL → ANGLE" untuk cari posisi 90° (center) tiap servo
    2) Catat perbedaan dari 90° ideal, masukkan ke SERVO_OFFSET_*
    3) Simpan file, lalu test ulang
"""

import os
import sys
import time
import argparse


def _bootstrap_venv():
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


def _add_paths():
    here = os.path.abspath(os.path.dirname(__file__))
    root = os.path.abspath(os.path.join(here, '..'))
    src = os.path.join(root, 'src')
    if root not in sys.path:
        sys.path.insert(0, root)
    if src not in sys.path:
        sys.path.insert(0, src)


def clamp_angle(a):
    try:
        a = float(a)
    except Exception:
        raise ValueError("Angle must be a number")
    return max(0.0, min(180.0, a))


def init_servokit(cfg):
    from adafruit_servokit import ServoKit
    addr = getattr(cfg, 'PCA9685_I2C_ADDRESS', 0x40)
    kit = ServoKit(channels=16, address=addr)
    try:
        kit._pca.frequency = getattr(cfg, 'PCA9685_FREQUENCY', 50)
    except Exception:
        pass
    print(f"✓ ServoKit ready @ I2C 0x{addr:02X}, freq={getattr(cfg, 'PCA9685_FREQUENCY', 50)}Hz")
    return kit


def emergency_off(kit):
    print("⛔ PWM OFF (all channels)")
    for ch in range(16):
        try:
            kit.servo[ch].angle = None
        except Exception:
            pass


def print_tips(cfg):
    print("\n==== PANDUAN SINGKAT (DERAJAT & KALIBRASI) ====")
    print("- Rentang aman: 0–180°. Hindari di luar itu.")
    print("- Ubah default derajat di config.py sesuai kebutuhan:")
    print("  • Corner UP/DOWN   : SERVO_L1_CORNER_UP / SERVO_L1_CORNER_DOWN")
    print("  • Lock A/B         : SERVO_L1_LOCK_LEFT_* / SERVO_L1_LOCK_RIGHT_*")
    print("  • Selector A/B/NEU : SERVO_L2_SELECTOR_BIN_A / _BIN_B / _NEUTRAL")
    print("- Perbaikan sudut halus (horn tidak presisi 90°): SERVO_OFFSET_* di config.py")
    print("  • Nilai + = searah jarum jam, nilai - = berlawanan")
    print("- Tips: Pakai menu (1) untuk cari center (±90°), lalu set offset di config.py")
    print("- Waktu gerak dan anti-jitter pakai: SERVO_MOVEMENT_TIME, SERVO_STOP_JITTER")


def menu():
    print("\nMENU (Direct Test)")
    print("1. Set CHANNEL → ANGLE")
    print("2. Lock A UNLOCK then LOCK")
    print("3. Lock B UNLOCK then LOCK")
    print("4. Corners ALL UP (0°)")
    print("5. Corners ALL DOWN (90°)")
    print("6. Selector → BIN A then NEUTRAL")
    print("7. Selector → BIN B then NEUTRAL")
    print("8. Center mapped servos to 90° (raw)")
    print("0. Tampilkan konfigurasi saat ini")
    print("h. Bantuan (panduan derajat)")
    print("e. Emergency OFF (PWM none)")
    print("q. Quit")


def run_interactive(cfg):
    try:
        kit = init_servokit(cfg)
    except Exception as e:
        print(f"❌ Cannot initialize ServoKit: {e}")
        print("💡 Cek: 'sudo raspi-config' → I2C Enable, 'i2cdetect -y 1' terlihat 0x40, dan paket Adafruit terpasang di venv.")
        return 2

    # Matikan PWM saat awal
    emergency_off(kit)

    mapping = {
        'lock_a': getattr(cfg, 'SERVO_L1_LOCK_LEFT_CHANNEL', None),
        'lock_b': getattr(cfg, 'SERVO_L1_LOCK_RIGHT_CHANNEL', None),
        'corner_a': getattr(cfg, 'SERVO_L1_CORNER_A_CHANNEL', None),
        'corner_b': getattr(cfg, 'SERVO_L1_CORNER_B_CHANNEL', None),
        'corner_c': getattr(cfg, 'SERVO_L1_CORNER_C_CHANNEL', None),
        'corner_d': getattr(cfg, 'SERVO_L1_CORNER_D_CHANNEL', None),
        'selector': getattr(cfg, 'SERVO_L2_SELECTOR_CHANNEL', None),
    }

    print("\nMapping (dari config.py):")
    for k, v in mapping.items():
        print(f"  {k}: {v}")

    print_tips(cfg)

    while True:
        menu()
        choice = input("Pilih: ").strip().lower()

        try:
            if choice == '1':
                ch = int(input("  Channel (0-15): ").strip())
                ang = clamp_angle(input("  Angle (0-180): ").strip())
                print(f"→ CH{ch} = {ang}°")
                kit.servo[ch].angle = ang
                time.sleep(getattr(cfg, 'SERVO_MOVEMENT_TIME', 0.2))
                if getattr(cfg, 'SERVO_STOP_JITTER', True):
                    kit.servo[ch].angle = None

            elif choice == '2':
                ch = mapping['lock_a']
                if ch is None:
                    print("⚠️  Lock A channel None")
                else:
                    a_lock = getattr(cfg, 'SERVO_L1_LOCK_LEFT_LOCKED', 90)
                    a_unlock = getattr(cfg, 'SERVO_L1_LOCK_LEFT_UNLOCKED', 180)
                    for a in (a_unlock, a_lock):
                        kit.servo[ch].angle = clamp_angle(a)
                        time.sleep(getattr(cfg, 'SERVO_MOVEMENT_TIME', 0.2))
                    if getattr(cfg, 'SERVO_STOP_JITTER', True):
                        kit.servo[ch].angle = None

            elif choice == '3':
                ch = mapping['lock_b']
                if ch is None:
                    print("⚠️  Lock B channel None")
                else:
                    a_lock = getattr(cfg, 'SERVO_L1_LOCK_RIGHT_LOCKED', 90)
                    a_unlock = getattr(cfg, 'SERVO_L1_LOCK_RIGHT_UNLOCKED', 0)
                    for a in (a_unlock, a_lock):
                        kit.servo[ch].angle = clamp_angle(a)
                        time.sleep(getattr(cfg, 'SERVO_MOVEMENT_TIME', 0.2))
                    if getattr(cfg, 'SERVO_STOP_JITTER', True):
                        kit.servo[ch].angle = None

            elif choice == '4':
                for n in ('corner_a','corner_b','corner_c','corner_d'):
                    ch = mapping[n]
                    if ch is not None:
                        kit.servo[ch].angle = clamp_angle(getattr(cfg, 'SERVO_L1_CORNER_UP', 0))
                time.sleep(getattr(cfg, 'SERVO_MOVEMENT_TIME', 0.2))
                if getattr(cfg, 'SERVO_STOP_JITTER', True):
                    for n in ('corner_a','corner_b','corner_c','corner_d'):
                        ch = mapping[n]
                        if ch is not None:
                            kit.servo[ch].angle = None

            elif choice == '5':
                for n in ('corner_a','corner_b','corner_c','corner_d'):
                    ch = mapping[n]
                    if ch is not None:
                        kit.servo[ch].angle = clamp_angle(getattr(cfg, 'SERVO_L1_CORNER_DOWN', 90))
                time.sleep(getattr(cfg, 'SERVO_MOVEMENT_TIME', 0.2))
                if getattr(cfg, 'SERVO_STOP_JITTER', True):
                    for n in ('corner_a','corner_b','corner_c','corner_d'):
                        ch = mapping[n]
                        if ch is not None:
                            kit.servo[ch].angle = None

            elif choice == '6':
                ch = mapping['selector']
                if ch is None:
                    print("⚠️  Selector channel None")
                else:
                    for a in (getattr(cfg,'SERVO_L2_SELECTOR_BIN_A',60), getattr(cfg,'SERVO_L2_SELECTOR_NEUTRAL',90)):
                        kit.servo[ch].angle = clamp_angle(a)
                        time.sleep(getattr(cfg, 'SERVO_MOVEMENT_TIME', 0.2))
                    if getattr(cfg, 'SERVO_STOP_JITTER', True):
                        kit.servo[ch].angle = None

            elif choice == '7':
                ch = mapping['selector']
                if ch is None:
                    print("⚠️  Selector channel None")
                else:
                    for a in (getattr(cfg,'SERVO_L2_SELECTOR_BIN_B',120), getattr(cfg,'SERVO_L2_SELECTOR_NEUTRAL',90)):
                        kit.servo[ch].angle = clamp_angle(a)
                        time.sleep(getattr(cfg, 'SERVO_MOVEMENT_TIME', 0.2))
                    if getattr(cfg, 'SERVO_STOP_JITTER', True):
                        kit.servo[ch].angle = None

            elif choice == '8':
                print("→ Center (raw 90°) untuk semua servo yang ter-mapping")
                for key in ('lock_a','lock_b','corner_a','corner_b','corner_c','corner_d','selector'):
                    ch = mapping[key]
                    if ch is not None:
                        try:
                            kit.servo[ch].angle = 90.0
                        except Exception:
                            pass
                time.sleep(getattr(cfg, 'SERVO_MOVEMENT_TIME', 0.2))
                if getattr(cfg, 'SERVO_STOP_JITTER', True):
                    for key in ('lock_a','lock_b','corner_a','corner_b','corner_c','corner_d','selector'):
                        ch = mapping[key]
                        if ch is not None:
                            kit.servo[ch].angle = None

            elif choice == '0':
                print("\nKonfigurasi aktif (config.py):")
                print(f"  Corner UP/DOWN  : {getattr(cfg,'SERVO_L1_CORNER_UP',0)} / {getattr(cfg,'SERVO_L1_CORNER_DOWN',90)}")
                print(f"  Lock A (L) L/U  : {getattr(cfg,'SERVO_L1_LOCK_LEFT_LOCKED',90)} / {getattr(cfg,'SERVO_L1_LOCK_LEFT_UNLOCKED',180)}")
                print(f"  Lock B (R) L/U  : {getattr(cfg,'SERVO_L1_LOCK_RIGHT_LOCKED',90)} / {getattr(cfg,'SERVO_L1_LOCK_RIGHT_UNLOCKED',0)}")
                print(f"  Selector N/A/B  : {getattr(cfg,'SERVO_L2_SELECTOR_NEUTRAL',90)} / {getattr(cfg,'SERVO_L2_SELECTOR_BIN_A',60)} / {getattr(cfg,'SERVO_L2_SELECTOR_BIN_B',120)}")
                print("  Offsets:")
                print(f"    LOCK L/R      : {getattr(cfg,'SERVO_OFFSET_LOCK_LEFT',0)} / {getattr(cfg,'SERVO_OFFSET_LOCK_RIGHT',0)}")
                print(f"    CORNER A-D    : {getattr(cfg,'SERVO_OFFSET_CORNER_A',0)}, {getattr(cfg,'SERVO_OFFSET_CORNER_B',0)}, {getattr(cfg,'SERVO_OFFSET_CORNER_C',0)}, {getattr(cfg,'SERVO_OFFSET_CORNER_D',0)}")
                print(f"    SELECTOR      : {getattr(cfg,'SERVO_OFFSET_SELECTOR',0)}")

            elif choice == 'h':
                print_tips(cfg)

            elif choice == 'e':
                emergency_off(kit)

            elif choice == 'q':
                break

            else:
                print("❌ Pilihan tidak dikenal")

        except KeyboardInterrupt:
            print("\n⚠️  Dibreak oleh user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

    emergency_off(kit)
    print("✅ Selesai")
    return 0


def run_cli(cfg, ch, angle):
    try:
        kit = init_servokit(cfg)
    except Exception as e:
        print(f"❌ Cannot initialize ServoKit: {e}")
        return 2
    angle = clamp_angle(angle)
    print(f"→ CH{ch} = {angle}°")
    kit.servo[ch].angle = angle
    time.sleep(getattr(cfg, 'SERVO_MOVEMENT_TIME', 0.2))
    if getattr(cfg, 'SERVO_STOP_JITTER', True):
        kit.servo[ch].angle = None
    print("✅ Done")
    return 0


def main():
    _bootstrap_venv()
    _add_paths()
    import config

    parser = argparse.ArgumentParser(description='Servo Direct Test (PCA9685)')
    parser.add_argument('--ch', type=int, help='Channel (0-15)')
    parser.add_argument('--angle', type=float, help='Angle (0-180)')
    args = parser.parse_args()

    if args.ch is not None and args.angle is not None:
        return run_cli(config, args.ch, args.angle)
    else:
        return run_interactive(config)


if __name__ == '__main__':
    sys.exit(main())
