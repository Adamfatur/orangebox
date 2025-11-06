#!/usr/bin/env python3
"""
Find Physical Channel Mapping
Cari tau servo mana yang terhubung ke channel berapa

CARA PAKAI:
    python3 scripts/find_channel_mapping.py

Script ini akan test channel 0-15 satu per satu.
Catat servo fisik mana yang bergerak untuk setiap channel.

Copyright (c) 2025 AF - OrangeBox Project
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config

try:
    from adafruit_servokit import ServoKit
    HAS_SERVOKIT = True
except Exception as e:
    HAS_SERVOKIT = False
    print(f"❌ ServoKit not available: {e}")
    sys.exit(1)

def test_channel(kit, channel):
    """Test single channel dengan gerakan kecil"""
    print(f"\n{'='*60}")
    print(f"  Testing Channel {channel}")
    print(f"{'='*60}")
    
    try:
        # Calibration
        kit.servo[channel].set_pulse_width_range(750, 2250)
        kit.servo[channel].actuation_range = 180
        
        print(f"\n   → Gerakan test: 90° → 100° → 80° → 90°")
        print(f"   👀 AMATI: Servo fisik MANA yang bergerak?")
        
        # Test sequence: small movements around 90° (safe)
        for angle in [90, 100, 80, 90]:
            kit.servo[channel].angle = angle
            time.sleep(0.8)
        
        # Stop PWM
        kit.servo[channel].angle = None
        
        print(f"\n   ✓ Channel {channel} test selesai")
        
        # User input
        servo_name = input(f"\n   Servo fisik apa yang bergerak? (atau tekan ENTER jika tidak ada): ").strip()
        
        return servo_name if servo_name else "TIDAK ADA"
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return "ERROR"

def main():
    """Main function"""
    print("\n" + "="*60)
    print("  🔍 CHANNEL MAPPING FINDER")
    print("="*60)
    print("\n⚠️  Script ini akan test channel 0-15 satu per satu.")
    print("   Catat servo FISIK mana yang bergerak!\n")
    
    if not HAS_SERVOKIT:
        print("❌ Cannot run - ServoKit not available")
        return 1
    
    try:
        # Initialize
        address = getattr(config, 'PCA9685_I2C_ADDRESS', 0x40)
        kit = ServoKit(channels=16, address=address)
        kit._pca.frequency = 50
        
        print(f"✅ PCA9685 initialized at 0x{address:02X}\n")
        
        # Channels to test (focus on used channels)
        channels_to_test = [0, 2, 4, 6, 8, 9, 12]
        
        mapping = {}
        
        for ch in channels_to_test:
            input(f"\n⏸  Tekan ENTER untuk test Channel {ch}...")
            result = test_channel(kit, ch)
            mapping[ch] = result
        
        # Summary
        print("\n" + "="*60)
        print("  📋 CHANNEL MAPPING SUMMARY")
        print("="*60 + "\n")
        
        for ch, servo in mapping.items():
            status = "✅" if servo not in ["TIDAK ADA", "ERROR"] else "❌"
            print(f"   {status} Channel {ch:2d} → {servo}")
        
        print("\n" + "="*60)
        print("\n💡 UPDATE config.py dengan mapping ini:")
        print("\n   # Lock Servos")
        for ch, servo in mapping.items():
            if "lock" in servo.lower() or "pengunci" in servo.lower():
                side = "LEFT" if "kiri" in servo.lower() or "left" in servo.lower() else "RIGHT"
                print(f"   SERVO_L1_LOCK_{side}_CHANNEL = {ch}")
        
        print("\n   # Corner Servos")
        for ch, servo in mapping.items():
            if "corner" in servo.lower() or "sudut" in servo.lower():
                print(f"   # {servo} → Channel {ch}")
        
        print("\n   # Selector")
        for ch, servo in mapping.items():
            if "selector" in servo.lower() or "pemilah" in servo.lower():
                print(f"   SERVO_L2_SELECTOR_CHANNEL = {ch}")
        
        print("\n" + "="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test dibatalkan")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
