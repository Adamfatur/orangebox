"""
Test: Move all four Layer-1 servos IN SYNC using FiveServoHardware
- Requires PCA9685 + Adafruit ServoKit available
- Uses burst-write to PCA9685 registers for minimal I2C overhead
- Config channels and angles from config.py (OPEN/CLOSED)

Usage:
  source .venv/bin/activate
  python3 scripts/test_servo_all_sync.py

Expected:
- All 4 servos start moving within <10ms (appears simultaneous)
- No more "left first, then right" sequential motion
"""
import sys, os, time
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
from src.hardware.five_servo_hardware import FiveServoHardware


def main():
    print("=== Test: All-Sync Layer-1 Servos (Staggered Start) ===")
    print(f"SERVO_LAYER1_OPEN_BOTH_SIDES={getattr(config, 'SERVO_LAYER1_OPEN_BOTH_SIDES', False)}")
    print(f"SERVO_STAGGER_DELAY_MS={getattr(config, 'SERVO_STAGGER_DELAY_MS', 10)}ms")
    hw = FiveServoHardware()
    status = hw.get_status()
    print("Status:")
    print(f"  Active: {status['active']}")

    # Build list to ensure 4 channels detected
    channels = []
    for sid in ('layer1_left', 'layer1_left2', 'layer1_right', 'layer1_right2'):
        if sid in [*status['servos'].keys()]:
            channels.append(status['servos'][sid]['channel'])
    print(f"  Channels detected: {channels}")
    
    if len(channels) < 4:
        print(f"  WARNING: Only {len(channels)} servos configured. Expected 4.")

    print("\n--- Test 1: Open ALL (staggered start) ---")
    print("Servos should start moving with small delay (~10ms between each)")
    print("Still appears nearly simultaneous, but more stable on limited PSU")
    ok1 = hw.open_all_sync()
    print(f"open_all_sync() → {ok1}")
    time.sleep(2.0)

    print("\n--- Test 2: Close ALL (staggered start) ---")
    ok2 = hw.close_all_sync()
    print(f"close_all_sync() → {ok2}")
    time.sleep(1.0)

    print("\n--- Test 3: Repeat 3x for consistency check ---")
    for i in range(3):
        print(f"  Round {i+1}/3: open...")
        hw.open_all_sync()
        time.sleep(1.0)
        print(f"  Round {i+1}/3: close...")
        hw.close_all_sync()
        time.sleep(0.5)

    print("\nDone. Cleaning up...")
    hw.cleanup()
    print("✓ All done.")
    print("\n=== Troubleshooting ===")
    print("If servos still inconsistent (sometimes 2, sometimes 3-4 move):")
    print("  1. ⚡ POWER SUPPLY: Use 5V/5-10A PSU with thick wires (16-18 AWG)")
    print("  2. 🔌 COMMON GROUND: Ensure RPi, PCA9685, and servo GND all connected")
    print("  3. 📏 WIRE LENGTH: Keep servo wires <30cm to reduce voltage drop")
    print("  4. 🔧 STAGGER DELAY: Increase SERVO_STAGGER_DELAY_MS (try 15-20ms)")
    print("  5. 🧪 TEST ONE-BY-ONE: Comment out 2 servos in config to isolate issue")


if __name__ == "__main__":
    main()
