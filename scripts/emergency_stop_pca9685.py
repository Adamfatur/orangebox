#!/usr/bin/env python3
"""
Emergency Servo Stop for PCA9685
Stops all servo movement immediately by disabling PCA9685 outputs.

Usage:
    python3 scripts/emergency_stop_pca9685.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from board import SCL, SDA
    import busio
    from adafruit_pca9685 import PCA9685
    HAS_PCA = True
except ImportError:
    HAS_PCA = False
    print("ERROR: PCA9685 library not available!")
    print("Install: sudo apt install python3-circuitpython-pca9685")
    sys.exit(1)

def emergency_stop():
    """Stop all PCA9685 servo outputs immediately."""
    print("🛑 EMERGENCY SERVO STOP - PCA9685")
    print("=" * 50)
    
    try:
        # Initialize I2C
        i2c = busio.I2C(SCL, SDA)
        
        # Initialize PCA9685
        pca = PCA9685(i2c)
        
        # Disable all outputs
        print("Disabling all PCA9685 outputs...")
        for channel in range(16):
            try:
                pca.channels[channel].duty_cycle = 0
                print(f"  Channel {channel}: OFF")
            except Exception as e:
                print(f"  Channel {channel}: Error - {e}")
        
        # Deinitialize
        pca.deinit()
        
        print("\n✓ All servo outputs stopped")
        print("✓ PCA9685 deinitialized")
        print("\nServos should now be stopped.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    emergency_stop()
