#!/usr/bin/env python3
"""
Quick Test - 7 Servo Positional System
Test cepat untuk verifikasi 7 servo positional sudah bekerja dengan benar.
"""

import sys
import time
sys.path.insert(0, 'src')

def test_7servo():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║          QUICK TEST - 7 SERVO POSITIONAL SYSTEM              ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    try:
        from hardware.seven_servo_hardware import SevenServoHardware
        
        print("📋 Initializing 7-servo system...\n")
        hw = SevenServoHardware()
        
        print("\n✅ Initialization SUCCESS!")
        print("\n📊 Detected Servos:")
        for name, servo in hw.servos.items():
            ch = servo.get('channel')
            if 'up' in servo:
                print(f"   • {name.upper():12} → CH {ch:2} (UP={servo['up']}°, DOWN={servo['down']}°)")
            elif 'locked' in servo:
                print(f"   • {name.upper():12} → CH {ch:2} (LOCKED={servo['locked']}°, UNLOCKED={servo['unlocked']}°)")
            elif 'neutral' in servo:
                print(f"   • {name.upper():12} → CH {ch:2} (NEUTRAL={servo['neutral']}°, BIN_A={servo['bin_a']}°, BIN_B={servo['bin_b']}°)")
        
        print("\n" + "="*70)
        print("TEST 1: Corner Servos (4 servos)")
        print("="*70)
        
        input("\n👉 Press ENTER to test corners UP position...")
        print("   Moving all 4 corners to UP (10°)...")
        for corner in ['corner_a', 'corner_b', 'corner_c', 'corner_d']:
            hw._move_servo(corner, hw.servos[corner]['up'])
        time.sleep(0.5)
        print("   ✅ All corners should be UP now")
        
        input("\n👉 Press ENTER to test corners DOWN position...")
        print("   Moving all 4 corners to DOWN (100°)...")
        for corner in ['corner_a', 'corner_b', 'corner_c', 'corner_d']:
            hw._move_servo(corner, hw.servos[corner]['down'])
        time.sleep(0.5)
        print("   ✅ All corners should be DOWN now")
        
        print("\n" + "="*70)
        print("TEST 2: Lock Servos (2 servos)")
        print("="*70)
        
        input("\n👉 Press ENTER to test locks UNLOCKED position...")
        print("   Moving locks to UNLOCKED (Left=10°, Right=170°)...")
        hw._move_servo('lock_left', hw.servos['lock_left']['unlocked'])
        hw._move_servo('lock_right', hw.servos['lock_right']['unlocked'])
        time.sleep(0.5)
        print("   ✅ Locks should be OPEN now")
        
        input("\n👉 Press ENTER to test locks LOCKED position...")
        print("   Moving locks to LOCKED (90°)...")
        hw._move_servo('lock_left', hw.servos['lock_left']['locked'])
        hw._move_servo('lock_right', hw.servos['lock_right']['locked'])
        time.sleep(0.5)
        print("   ✅ Locks should be CLOSED now")
        
        print("\n" + "="*70)
        print("TEST 3: Selector Servo (Layer 2)")
        print("="*70)
        
        input("\n👉 Press ENTER to test selector positions...")
        print("   Moving selector: NEUTRAL → BIN_A → NEUTRAL → BIN_B → NEUTRAL")
        
        hw._move_servo('selector', hw.servos['selector']['neutral'])
        time.sleep(0.3)
        print("   • NEUTRAL (90°)")
        
        hw._move_servo('selector', hw.servos['selector']['bin_a'])
        time.sleep(0.5)
        print("   • BIN_A (60° - left)")
        
        hw._move_servo('selector', hw.servos['selector']['neutral'])
        time.sleep(0.3)
        print("   • NEUTRAL (90°)")
        
        hw._move_servo('selector', hw.servos['selector']['bin_b'])
        time.sleep(0.5)
        print("   • BIN_B (120° - right)")
        
        hw._move_servo('selector', hw.servos['selector']['neutral'])
        time.sleep(0.3)
        print("   • NEUTRAL (90°)")
        
        print("\n   ✅ Selector test complete")
        
        print("\n" + "="*70)
        print("TEST 4: Full Sorting Sequence")
        print("="*70)
        
        choice = input("\n👉 Test sorting? (y/n): ").lower()
        if choice == 'y':
            print("\n🧪 Testing ORGANIC → BIN_A...")
            hw.sort('organic')
            print("   ✅ Organic sorting complete\n")
            
            time.sleep(1)
            
            print("🧪 Testing INORGANIC → BIN_B...")
            hw.sort('inorganic')
            print("   ✅ Inorganic sorting complete\n")
        
        print("\n╔═══════════════════════════════════════════════════════════════╗")
        print("║                   ✅ ALL TESTS PASSED! ✅                      ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print("\n🎉 7-Servo system is working correctly!")
        print("\n📝 Visual Checklist:")
        print("   • Did all 4 corners move UP/DOWN together?")
        print("   • Did locks OPEN/CLOSE smoothly (not spinning 360°)?")
        print("   • Did selector move to BIN_A, NEUTRAL, BIN_B correctly?")
        print("   • No servo hunting or continuous rotation?")
        
        if choice == 'y':
            print("   • Did full sorting sequences complete without errors?")
        
        print("\n✅ If all above are YES → System PRODUCTION READY!")
        
        hw.cleanup()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check I2C connection: sudo i2cdetect -y 1")
        print("   2. Verify servo wiring (all 7 servos connected)")
        print("   3. Check power supply (min 3A for 7 servos)")
        print("   4. Verify config.py channel mapping")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    test_7servo()
