#!/usr/bin/env python3
"""
Test servo movement using Adafruit ServoKit (PCA9685) on Raspberry Pi.

Features:
- Auto-create venv, upgrade pip, and install missing Adafruit packages.
- Auto-install adafruit-circuitpython-servokit and adafruit-blinka when missing.
- Two-servo and single-servo modes with configurable channels and angles.
- Optional 0→180° sweep for diagnostics.
- I2C address selection for PCA9685.

Usage examples:
  python3 scripts/test_servo_servokit.py --ch1 2 --ch2 3 --sweep
  python3 scripts/test_servo_servokit.py --single --ch1 2 --open1 120 --close1 70
  python3 scripts/test_servo_servokit.py --address 0x40 --wait-open 1.5 --wait-close 1.0

Hardware notes:
- Power the servos from a stable 5–6V supply; DO NOT power servos from Pi 5V pin.
- Common ground between servo power supply, PCA9685, and Raspberry Pi.
- Signal wire to correct PCA9685 channel; verify I2C address via: i2cdetect -y 1
"""

import os
import sys
import time
import argparse
import subprocess


def is_raspberry_pi() -> bool:
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read().lower()
        return "raspberry pi" in cpuinfo or "rev" in cpuinfo
    except Exception:
        return False


def in_virtualenv() -> bool:
    return (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        or os.environ.get("VIRTUAL_ENV")
    )


def ensure_venv_and_reexec():
    """Create venv on Raspberry Pi and re-exec this script inside it."""
    if not is_raspberry_pi():
        return
    if in_virtualenv():
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
    venv_path = os.path.join(project_root, "venv")
    python_bin = sys.executable

    print("[setup] Raspberry Pi detected, preparing virtual environment...")
    if not os.path.exists(venv_path):
        print(f"[setup] Creating venv at: {venv_path}")
        subprocess.check_call([python_bin, "-m", "venv", venv_path])

    venv_python = os.path.join(venv_path, "bin", "python")
    pip_bin = os.path.join(venv_path, "bin", "pip")

    print("[setup] Upgrading pip tools in venv...")
    subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]) 

    # Install core Adafruit platform packages proactively
    print("[setup] Installing Adafruit core packages (blinka, servokit)...")
    subprocess.check_call([pip_bin, "install", "--upgrade", 
                           "adafruit-blinka", "adafruit-circuitpython-servokit"]) 

    # Re-exec script inside venv
    print("[setup] Relaunching script inside virtual environment...")
    os.execv(venv_python, [venv_python] + sys.argv)


def ensure_packages_when_in_venv():
    """If running inside venv on Raspberry Pi, ensure required Adafruit packages are present."""
    if not (is_raspberry_pi() and in_virtualenv()):
        return
    try:
        import adafruit_servokit  # noqa: F401
        import board  # noqa: F401
        import busio  # noqa: F401
    except Exception:
        print("[setup] Installing missing Adafruit packages (servokit, blinka)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade",
                               "adafruit-blinka", "adafruit-circuitpython-servokit"]) 


def parse_args():
    p = argparse.ArgumentParser(description="ServoKit-based servo tester for PCA9685")
    p.add_argument("--address", type=lambda x: int(x, 0), default=0x40,
                   help="I2C address of PCA9685 (e.g., 0x40)")
    p.add_argument("--single", action="store_true",
                   help="Use single-servo mode on --ch1 only")
    p.add_argument("--ch1", type=int, default=2, help="Servo channel 1 (default: 2)")
    p.add_argument("--ch2", type=int, default=3, help="Servo channel 2 (default: 3)")
    p.add_argument("--open1", type=float, default=120.0, help="Open angle for servo1")
    p.add_argument("--close1", type=float, default=70.0, help="Close angle for servo1")
    p.add_argument("--stop1", type=float, default=89.5, help="Stop/neutral angle for servo1")
    p.add_argument("--open2", type=float, default=None, help="Open angle for servo2 (default: mirrored)")
    p.add_argument("--close2", type=float, default=None, help="Close angle for servo2 (default: mirrored)")
    p.add_argument("--stop2", type=float, default=89.5, help="Stop/neutral angle for servo2")
    p.add_argument("--wait-open", type=float, default=1.5, help="Wait time after open movement")
    p.add_argument("--wait-close", type=float, default=1.0, help="Wait time after close movement")
    p.add_argument("--sweep", action="store_true", help="Perform 0→180° diagnostic sweep before moves")
    return p.parse_args()


def print_env_info(address: int):
    print("[env] Python:", sys.executable)
    print("[env] Virtualenv:", in_virtualenv())
    print("[env] Raspberry Pi:", is_raspberry_pi())
    print(f"[i2c] Target PCA9685 address: 0x{address:02X}")
    print("[hint] Ensure I2C enabled and address visible via 'i2cdetect -y 1'.")


def main():
    ensure_venv_and_reexec()
    ensure_packages_when_in_venv()

    args = parse_args()
    print_env_info(args.address)

    try:
        from adafruit_servokit import ServoKit
        import board
        import busio
    except Exception as e:
        print("[error] Missing Adafruit libraries for ServoKit:", e)
        print("[fix] Install inside venv: pip install adafruit-blinka adafruit-circuitpython-servokit")
        sys.exit(1)

    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        kit = ServoKit(channels=16, address=args.address, i2c=i2c)
    except Exception as e:
        print("[error] Failed to initialize PCA9685/ServoKit:", e)
        print("[hint] Check wiring, power, and I2C address; run 'i2cdetect -y 1'.")
        sys.exit(1)

    # Resolve angles for servo2 if not provided (mirror behavior)
    open2 = args.open2 if args.open2 is not None else max(0.0, min(180.0, 180.0 - args.open1))
    close2 = args.close2 if args.close2 is not None else max(0.0, min(180.0, 180.0 - args.close1))

    def clamp(a):
        return max(0.0, min(180.0, float(a)))

    stop1 = clamp(args.stop1)
    stop2 = clamp(args.stop2)
    open1 = clamp(args.open1)
    close1 = clamp(args.close1)
    open2 = clamp(open2)
    close2 = clamp(close2)

    def sweep_channel(ch: int, delay: float = 0.01):
        print(f"[diag] Sweeping channel {ch} 0→180°")
        for ang in range(0, 181, 5):
            try:
                kit.servo[ch].angle = ang
            except Exception:
                pass
            time.sleep(delay)
        time.sleep(0.3)

    def set_angle(ch: int, ang: float):
        try:
            kit.servo[ch].angle = clamp(ang)
        except Exception as e:
            print(f"[warn] Failed to set angle on ch{ch}: {e}")

    # Diagnostic sweep
    if args.sweep:
        if args.single:
            sweep_channel(args.ch1)
        else:
            sweep_channel(args.ch1)
            sweep_channel(args.ch2)

    if args.single:
        print(f"[move] Single-servo mode on ch{args.ch1}")
        print(f"[move] Close→Stop→Open sequence: close1={close1}, stop1={stop1}, open1={open1}")
        set_angle(args.ch1, close1)
        time.sleep(args.wait_close)
        set_angle(args.ch1, stop1)
        time.sleep(0.5)
        set_angle(args.ch1, open1)
        time.sleep(args.wait_open)
        set_angle(args.ch1, stop1)
        print("[done] Single-servo test complete.")
    else:
        print(f"[move] Dual-servo mode on ch{args.ch1} & ch{args.ch2}")
        print(f"[move] Close both: ch{args.ch1}={close1}, ch{args.ch2}={close2}")
        set_angle(args.ch1, close1)
        set_angle(args.ch2, close2)
        time.sleep(args.wait_close)

        print(f"[move] Stop both: ch{args.ch1}={stop1}, ch{args.ch2}={stop2}")
        set_angle(args.ch1, stop1)
        set_angle(args.ch2, stop2)
        time.sleep(0.5)

        print(f"[move] Open both: ch{args.ch1}={open1}, ch{args.ch2}={open2}")
        set_angle(args.ch1, open1)
        set_angle(args.ch2, open2)
        time.sleep(args.wait_open)

        print(f"[move] Return to stop: ch{args.ch1}={stop1}, ch{args.ch2}={stop2}")
        set_angle(args.ch1, stop1)
        set_angle(args.ch2, stop2)
        print("[done] Dual-servo test complete.")


if __name__ == "__main__":
    main()