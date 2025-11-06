#!/usr/bin/env python3
"""
Quick Servo Diagnostic - Identifikasi Masalah 360° Rotation
==========================================================

Script ini untuk:
1. Test setiap servo satu per satu (isolasi masalah)
2. Cek apakah servo continuous-rotation atau positional
3. Verify channel mapping benar

CARA PAKAI:
    python3 scripts/quick_servo_diagnostic.py

HASIL:
- Jika servo berputar TERUS (tidak berhenti) = Continuous rotation servo atau angle ekstrem
- Jika servo bergerak sedikit lalu STOP = Normal positional servo
- Jika servo tidak bergerak = Channel salah atau wiring issue

Copyright (c) 2025 AF - OrangeBox Project
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config

try:
    from adafruit_servokit import ServoKit
    HAS_SERVOKIT = True
except Exception as e:
    HAS_SERVOKIT = False
    print(f"⚠️  ServoKit not available: {e}")
    print("Running in SIMULATION mode\n")


def print_banner():
    """Print banner"""
    print("\n" + "="*70)
    print("  🔧 QUICK SERVO DIAGNOSTIC - 360° ROTATION TROUBLESHOOTER")
    print("="*70)
    print("\n📋 Test ini akan:")
    print("  1. Test lock servos satu per satu (CH0, CH2)")
    print("  2. Test corner servos satu per satu (CH4, CH6, CH8, CH9)")
    print("  3. Test selector servo (CH12)")
    print("  4. Identifikasi servo yang berputar 360°")
    print("\n⚠️  PERHATIAN:")
    print("  - Pastikan wadah TIDAK berisi sampah")
    print("  - Siapkan tombol emergency stop (matikan power)")
    print("  - Amati setiap servo dengan seksama")
    print("\n" + "="*70 + "\n")


def test_single_servo(kit, channel, name, test_angles):
    """
    Test single servo dengan berbagai angle untuk detect continuous rotation
    
    Args:
        kit: ServoKit instance
        channel: PCA9685 channel (0-15)
        name: Nama servo untuk display
        test_angles: List of angles to test
    """
    print(f"\n{'─'*70}")
    print(f"🔍 Testing {name} (CH{channel})")
    print(f"{'─'*70}")
    
    if not HAS_SERVOKIT:
        print(f"   🎬 SIMULATION: {name} would move to {test_angles}")
        return
    
    try:
        # Apply calibration
        min_pulse = getattr(config, 'SERVOKIT_MIN_PULSE_MICROS', 750)
        max_pulse = getattr(config, 'SERVOKIT_MAX_PULSE_MICROS', 2250)
        kit.servo[channel].set_pulse_width_range(min_pulse, max_pulse)
        kit.servo[channel].actuation_range = 180
        
        for angle in test_angles:
            print(f"\n   → Moving to {angle}°...")
            kit.servo[channel].angle = angle
            
            print(f"   ⏱  Observasi 2 detik...")
            print(f"   👀 Apakah servo:")
            print(f"      - Bergerak sedikit lalu BERHENTI? ✅ (Normal)")
            print(f"      - Berputar TERUS tanpa henti? ❌ (Continuous/Extreme angle)")
            print(f"      - Tidak bergerak sama sekali? ⚠️  (Channel/wiring salah)")
            
            time.sleep(2)
        
        # Return to neutral
        print(f"\n   → Returning to 90° (neutral)...")
        kit.servo[channel].angle = 90
        time.sleep(1)
        
        # Stop PWM
        kit.servo[channel].angle = None
        
        print(f"\n   ✅ Test {name} selesai")
        
        # User feedback
        response = input(f"\n   Apakah {name} bergerak NORMAL (y) atau BERPUTAR 360° (n)? [y/n]: ").strip().lower()
        return response == 'y'
        
    except Exception as e:
        print(f"   ❌ Error testing {name}: {e}")
        return False


def main():
    """Main diagnostic function"""
    print_banner()
    
    if not HAS_SERVOKIT:
        print("❌ ServoKit not available. Cannot run hardware test.")
        print("   Install with: pip install adafruit-circuitpython-servokit")
        return 1
    
    try:
        # Initialize PCA9685
        address = getattr(config, 'PCA9685_I2C_ADDRESS', 0x40)
        kit = ServoKit(channels=16, address=address)
        kit._pca.frequency = getattr(config, 'PCA9685_FREQUENCY', 50)
        
        print(f"✅ PCA9685 initialized at 0x{address:02X}")
        
        # Confirm start
        input("\n⏸  Tekan ENTER untuk mulai test (atau Ctrl+C untuk batal)...")
        
        results = {}
        
        # Test Lock Servos
        print("\n" + "="*70)
        print("  SECTION 1: LOCK SERVOS (Pengunci)")
        print("="*70)
        
        # Lock Left (CH0)
        results['lock_left'] = test_single_servo(
            kit, 
            getattr(config, 'SERVO_L1_LOCK_LEFT_CHANNEL', 0),
            'Lock Left',
            [90, 0, 90]  # LOCKED → UNLOCKED → LOCKED
        )
        
        # Lock Right (CH2)
        results['lock_right'] = test_single_servo(
            kit,
            getattr(config, 'SERVO_L1_LOCK_RIGHT_CHANNEL', 2),
            'Lock Right',
            [90, 0, 90]  # LOCKED → UNLOCKED → LOCKED
        )
        
        # Test Corner Servos
        print("\n" + "="*70)
        print("  SECTION 2: CORNER SERVOS (Sudut Wadah)")
        print("="*70)
        
        corners = [
            ('corner_a', 'SERVO_L1_CORNER_A_CHANNEL', 4),
            ('corner_b', 'SERVO_L1_CORNER_B_CHANNEL', 6),
            ('corner_c', 'SERVO_L1_CORNER_C_CHANNEL', 8),
            ('corner_d', 'SERVO_L1_CORNER_D_CHANNEL', 9),
        ]
        
        for corner_id, config_key, default_ch in corners:
            ch = getattr(config, config_key, default_ch)
            results[corner_id] = test_single_servo(
                kit,
                ch,
                f'Corner {corner_id.upper()[-1]}',
                [0, 90, 0]  # UP → DOWN → UP
            )
        
        # Test Selector
        print("\n" + "="*70)
        print("  SECTION 3: SELECTOR SERVO (Pemilah)")
        print("="*70)
        
        results['selector'] = test_single_servo(
            kit,
            getattr(config, 'SERVO_L2_SELECTOR_CHANNEL', 12),
            'Selector',
            [90, 60, 120, 90]  # NEUTRAL → BIN_A → BIN_B → NEUTRAL
        )
        
        # Summary
        print("\n" + "="*70)
        print("  📊 DIAGNOSTIC SUMMARY")
        print("="*70)
        
        print("\n✅ NORMAL (Positional):")
        for name, is_ok in results.items():
            if is_ok:
                print(f"   - {name.upper()}")
        
        print("\n❌ BERMASALAH (360° Rotation):")
        problem_servos = [name for name, is_ok in results.items() if not is_ok]
        if problem_servos:
            for name in problem_servos:
                print(f"   - {name.upper()}")
            
            print("\n🔧 SOLUSI untuk servo bermasalah:")
            print("   1. Cek angle config di config.py (hindari 0°/180° ekstrem)")
            print("   2. Kurangi pulse width range (sudah di-adjust ke 750-2250µs)")
            print("   3. Ganti servo jika memang continuous-rotation type")
            print("   4. Cek power supply (5V/3A minimum untuk PCA9685)")
        else:
            print("   (Tidak ada)")
            print("\n   🎉 Semua servo normal!")
        
        print("\n" + "="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test dibatalkan oleh user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Program interrupted")
        sys.exit(1)
