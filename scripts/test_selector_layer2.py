"""
Test Layer-2 selector tilt and return to neutral (horizontal)
- No sensor feedback; uses overshoot technique to mitigate backlash
- Requires SERVO_LAYER2_SELECTOR_CHANNEL to be set in config.py

Usage:
  source .venv/bin/activate
  python3 scripts/test_selector_layer2.py
"""
import sys, os, time
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
from src.hardware.five_servo_hardware import FiveServoHardware


def main():
    print("=== Test: Layer-2 Selector Tilt & Return ===")
    print(f"SERVO_LAYER2_SELECTOR_CHANNEL={getattr(config, 'SERVO_LAYER2_SELECTOR_CHANNEL', None)}")
    print(f"NEUTRAL={getattr(config, 'SERVO_LAYER2_NEUTRAL', 90)}° | TILT={getattr(config, 'SERVO_LAYER2_TILT_ANGLE', 30)}°")
    print(f"OVERSHOOT={getattr(config, 'SERVO_LAYER2_NEUTRAL_OVERSHOOT_DEG', 3)}° | SETTLE={getattr(config, 'SERVO_LAYER2_SETTLE_TIME', 0.15)}s")

    hw = FiveServoHardware()
    if 'layer2_selector' not in hw.get_status()['servos']:
        print("⚠️  Layer 2 selector not configured. Set SERVO_LAYER2_SELECTOR_CHANNEL in config.py")
        return

    # Center first
    print("\nCentering to neutral...")
    hw.center_selector()
    time.sleep(0.5)

    tilt = int(getattr(config, 'SERVO_LAYER2_TILT_ANGLE', 30))

    print("\nTilt LEFT and return...")
    hw.tilt_and_return(-tilt)
    time.sleep(0.6)

    print("\nTilt RIGHT and return...")
    hw.tilt_and_return(+tilt)
    time.sleep(0.6)

    print("\nRepeat 3x for stability check...")
    for i in range(3):
        print(f" Round {i+1}/3: LEFT")
        hw.tilt_and_return(-tilt)
        time.sleep(0.5)
        print(f" Round {i+1}/3: RIGHT")
        hw.tilt_and_return(+tilt)
        time.sleep(0.5)

    print("\nCleanup...")
    hw.cleanup()
    print("✓ Done.")


if __name__ == "__main__":
    main()
