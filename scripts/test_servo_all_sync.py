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
    print("=== Test: All-Sync Layer-1 Servos (Burst-Write) ===")
    print(f"SERVO_LAYER1_OPEN_BOTH_SIDES={getattr(config, 'SERVO_LAYER1_OPEN_BOTH_SIDES', False)}")
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

    print("\n--- Test 1: Open ALL (sync) ---")
    print("Servos should start moving together (within <10ms)")
    ok1 = hw.open_all_sync()
    print(f"open_all_sync() → {ok1}")
    time.sleep(2.0)

    print("\n--- Test 2: Close ALL (sync) ---")
    print("Servos should start moving together (within <10ms)")
    ok2 = hw.close_all_sync()
    print(f"close_all_sync() → {ok2}")
    time.sleep(1.0)

    print("\n--- Test 3: Repeat for confirmation ---")
    hw.open_all_sync()
    time.sleep(1.5)
    hw.close_all_sync()

    print("\nDone. Cleaning up...")
    hw.cleanup()
    print("✓ All done.")
    print("\nIf servos moved in sequence (not together), possible causes:")
    print("  1. Power supply not strong enough (use 5V/5A)")
    print("  2. I2C bus speed too slow (default 100kHz is OK)")
    print("  3. Wiring issue (check ground common to RPi+PCA9685+servos)")


if __name__ == "__main__":
    main()
