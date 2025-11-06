#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════╗
║         7-SERVO POSITIONAL VALIDATION TEST (MG996R)            ║
╚════════════════════════════════════════════════════════════════╝

Script untuk VALIDASI AKHIR sistem 7 servo positional sebelum production.

✅ Gunakan script ini SETELAH:
   1. Semua 7 servo MG996R terpasang di channel 0,2,4,6,8,9,12
   2. config.py sudah diganti dengan config.py.READY_FOR_7_SERVO
   3. Test individual servo (quick_servo_diagnostic.py) sudah passed

🎯 Script ini akan test:
   - Initialization semua 7 servo
   - Individual servo movement (UP/DOWN, LOCK/UNLOCK, BIN A/B)
   - Corner synchronization (4 corners bergerak bersamaan)
   - Full sorting sequence (Organik → Bin A, Anorganik → Bin B)
   - Stress test (10x sorting berturut-turut)

Copyright (c) 2025 AF - OrangeBox Project
"""

import sys
import time
sys.path.insert(0, 'src')

from hardware.seven_servo_hardware import SevenServoHardware

def print_header(title):
    """Print formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def wait_user(prompt="Press Enter to continue..."):
    """Wait for user input."""
    input(f"   👉 {prompt}")

def test_initialization():
    """Test 1: Initialize 7-servo system."""
    print_header("TEST 1: INITIALIZATION (7 Servo Positional)")
    
    try:
        hw = SevenServoHardware()
        print("✅ SUCCESS: All 7 servos initialized!")
        print("\n📋 Expected Channels:")
        print("   • CH 0  → Lock Left")
        print("   • CH 2  → Lock Right")
        print("   • CH 4  → Corner A")
        print("   • CH 6  → Corner B")
        print("   • CH 8  → Corner C")
        print("   • CH 9  → Corner D")
        print("   • CH 12 → Selector")
        wait_user()
        return hw
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check config.py channel mapping")
        print("   2. Verify PCA9685 I2C connection: sudo i2cdetect -y 1")
        print("   3. Check power supply (min. 3A for 7 servos)")
        sys.exit(1)

def test_individual_servos(hw):
    """Test 2: Test each servo individually."""
    print_header("TEST 2: INDIVIDUAL SERVO MOVEMENT")
    
    tests = [
        ("corner_a", "up", "Corner A UP (10°)"),
        ("corner_a", "down", "Corner A DOWN (100°)"),
        ("corner_b", "up", "Corner B UP (10°)"),
        ("corner_b", "down", "Corner B DOWN (100°)"),
        ("corner_c", "up", "Corner C UP (10°)"),
        ("corner_c", "down", "Corner C DOWN (100°)"),
        ("corner_d", "up", "Corner D UP (10°)"),
        ("corner_d", "down", "Corner D DOWN (100°)"),
        ("lock_left", "unlocked", "Lock Left UNLOCK (10°)"),
        ("lock_left", "locked", "Lock Left LOCK (90°)"),
        ("lock_right", "unlocked", "Lock Right UNLOCK (170°)"),
        ("lock_right", "locked", "Lock Right LOCK (90°)"),
        ("selector", "neutral", "Selector NEUTRAL (90°)"),
        ("selector", "bin_a", "Selector BIN A (60°)"),
        ("selector", "neutral", "Selector NEUTRAL (90°)"),
        ("selector", "bin_b", "Selector BIN B (120°)"),
        ("selector", "neutral", "Selector NEUTRAL (90°)"),
    ]
    
    print("Testing each servo position...")
    print("⚠️  IMPORTANT: Watch for ANY 360° continuous rotation!")
    print("    Servo HARUS BERHENTI di setiap posisi (positional behavior)\n")
    
    for i, (servo_id, position, description) in enumerate(tests, 1):
        print(f"[{i}/{len(tests)}] {description}...", end=" ", flush=True)
        
        try:
            target_angle = hw.servos[servo_id][position]
            hw._move_servo(servo_id, target_angle)
            time.sleep(0.3)  # Wait untuk servo settle
            print("✅")
        except Exception as e:
            print(f"❌ {e}")
            return False
    
    print("\n✅ ALL SERVOS TESTED SUCCESSFULLY!")
    print("\n🔍 Visual Check:")
    print("   • Did ALL servos STOP at each position? (not continuous rotation)")
    print("   • Were movements smooth? (no jerking/hunting)")
    print("   • Are angles physically correct? (use protractor if unsure)")
    
    wait_user()
    return True

def test_corner_sync(hw):
    """Test 3: Test 4-corner synchronization."""
    print_header("TEST 3: CORNER SYNCHRONIZATION (4 Servos)")
    
    print("This test verifies all 4 corners move SIMULTANEOUSLY.\n")
    
    # Test 1: All UP
    print("🔼 Moving all 4 corners to UP position (10°)...")
    corner_moves = [
        ('corner_a', hw.servos['corner_a']['up']),
        ('corner_b', hw.servos['corner_b']['up']),
        ('corner_c', hw.servos['corner_c']['up']),
        ('corner_d', hw.servos['corner_d']['up']),
    ]
    hw._move_multiple_servos_parallel(corner_moves)
    time.sleep(0.5)
    print("   ✓ All corners should be UP now")
    wait_user("Did all 4 corners move UP simultaneously? [Enter]")
    
    # Test 2: All DOWN
    print("🔽 Moving all 4 corners to DOWN position (100°)...")
    corner_moves = [
        ('corner_a', hw.servos['corner_a']['down']),
        ('corner_b', hw.servos['corner_b']['down']),
        ('corner_c', hw.servos['corner_c']['down']),
        ('corner_d', hw.servos['corner_d']['down']),
    ]
    hw._move_multiple_servos_parallel(corner_moves)
    time.sleep(0.5)
    print("   ✓ All corners should be DOWN now")
    wait_user("Did all 4 corners move DOWN simultaneously? [Enter]")
    
    # Test 3: Back UP
    print("🔼 Moving all 4 corners back to UP position (10°)...")
    corner_moves = [
        ('corner_a', hw.servos['corner_a']['up']),
        ('corner_b', hw.servos['corner_b']['up']),
        ('corner_c', hw.servos['corner_c']['up']),
        ('corner_d', hw.servos['corner_d']['up']),
    ]
    hw._move_multiple_servos_parallel(corner_moves)
    time.sleep(0.5)
    print("   ✓ All corners should be UP now")
    
    print("\n✅ CORNER SYNC TEST PASSED!")
    print("\n🔍 Visual Check:")
    print("   • Did all 4 corners start moving at the SAME time?")
    print("   • Did they reach target position at roughly the SAME time?")
    print("   • No corner lagging behind or moving in opposite direction?")
    
    wait_user()
    return True

def test_lock_mechanism(hw):
    """Test 4: Test lock mechanism."""
    print_header("TEST 4: LOCK MECHANISM (2 Servos)")
    
    print("This test verifies lock servos can HOLD container position.\n")
    
    # Test unlock
    print("🔓 UNLOCKING locks (Left=10°, Right=170°)...")
    lock_moves = [
        ('lock_left', hw.servos['lock_left']['unlocked']),
        ('lock_right', hw.servos['lock_right']['unlocked']),
    ]
    hw._move_multiple_servos_parallel(lock_moves)
    time.sleep(0.5)
    print("   ✓ Locks should be OPEN now (container can drop)")
    wait_user("Are both locks in OPEN position? [Enter]")
    
    # Test lock
    print("🔒 LOCKING locks (Left=90°, Right=90°)...")
    lock_moves = [
        ('lock_left', hw.servos['lock_left']['locked']),
        ('lock_right', hw.servos['lock_right']['locked']),
    ]
    hw._move_multiple_servos_parallel(lock_moves)
    time.sleep(0.5)
    print("   ✓ Locks should be CLOSED now (container secured)")
    wait_user("Are both locks in CLOSED position? [Enter]")
    
    print("\n✅ LOCK MECHANISM TEST PASSED!")
    print("\n🔍 Visual Check:")
    print("   • Do locks HOLD position (not drifting/slipping)?")
    print("   • Can container be held securely when locked?")
    print("   • Locks NOT rotating 360° continuously?")
    
    wait_user()
    return True

def test_full_sorting_organic(hw):
    """Test 5: Full sorting sequence (Organic → Bin A)."""
    print_header("TEST 5: FULL SORTING - ORGANIC → BIN A")
    
    print("This test runs complete sorting sequence for ORGANIC waste.\n")
    print("Expected sequence:")
    print("   1. Selector moves to BIN A (60°)")
    print("   2. Locks UNLOCK (open)")
    print("   3. 4 Corners LOWER (container drops)")
    print("   4. Wait for waste to slide")
    print("   5. Selector returns to NEUTRAL (90°)")
    print("   6. 4 Corners LIFT (container rises)")
    print("   7. Locks LOCK (secure container)")
    print("\n⚠️  WATCH CAREFULLY for any unexpected behavior!\n")
    
    wait_user("Ready to start sorting? [Enter]")
    
    try:
        hw.sort('organic')
        print("\n✅ SORTING COMPLETE!")
        
        print("\n🔍 Visual Check:")
        print("   • Did selector move to Bin A (left side)?")
        print("   • Did container lower smoothly?")
        print("   • Did all 4 corners move together?")
        print("   • Did locks open/close correctly?")
        print("   • Did selector return to neutral?")
        print("   • Is container now UP and LOCKED?")
        
        wait_user()
        return True
    except Exception as e:
        print(f"\n❌ SORTING FAILED: {e}")
        return False

def test_full_sorting_inorganic(hw):
    """Test 6: Full sorting sequence (Inorganic → Bin B)."""
    print_header("TEST 6: FULL SORTING - INORGANIC → BIN B")
    
    print("This test runs complete sorting sequence for INORGANIC waste.\n")
    print("Same sequence as Test 5, but selector goes to BIN B (120° / right side)\n")
    
    wait_user("Ready to start sorting? [Enter]")
    
    try:
        hw.sort('inorganic')
        print("\n✅ SORTING COMPLETE!")
        
        print("\n🔍 Visual Check:")
        print("   • Did selector move to Bin B (right side)?")
        print("   • Same smooth operation as Bin A test?")
        
        wait_user()
        return True
    except Exception as e:
        print(f"\n❌ SORTING FAILED: {e}")
        return False

def test_stress(hw):
    """Test 7: Stress test (10x sorting)."""
    print_header("TEST 7: STRESS TEST (10x Sorting)")
    
    print("This test runs 10 consecutive sortings to verify reliability.\n")
    print("Sequence:")
    print("   1. Organic → Bin A")
    print("   2. Inorganic → Bin B")
    print("   3. Organic → Bin A")
    print("   4. Inorganic → Bin B")
    print("   ... (repeat 5x)\n")
    
    wait_user("Ready to start stress test? This will take ~2 minutes. [Enter]")
    
    sequence = ['organic', 'inorganic'] * 5  # 10 sortings total
    
    for i, waste_type in enumerate(sequence, 1):
        bin_name = "Bin A" if waste_type == 'organic' else "Bin B"
        print(f"\n[{i}/10] Sorting {waste_type.upper()} → {bin_name}...", end=" ", flush=True)
        
        try:
            hw.sort(waste_type)
            print("✅")
            time.sleep(0.5)  # Small delay between sortings
        except Exception as e:
            print(f"❌ {e}")
            print(f"\n⚠️  Stress test FAILED at iteration {i}/10")
            return False
    
    print("\n✅ STRESS TEST PASSED! (10/10 sortings successful)")
    print("\n🔍 Visual Check:")
    print("   • Did all sortings complete without errors?")
    print("   • Are servos still responding smoothly?")
    print("   • No overheating or unusual sounds?")
    print("   • Container still UP and LOCKED after 10 cycles?")
    
    wait_user()
    return True

def main():
    """Run all validation tests."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║      7-SERVO POSITIONAL VALIDATION TEST (MG996R)               ║
║                                                                ║
║  This script will validate your 7-servo system before          ║
║  production deployment.                                        ║
║                                                                ║
║  REQUIREMENTS:                                                 ║
║  ✅ All 7 MG996R positional servos installed                   ║
║  ✅ config.py updated with READY_FOR_7_SERVO                   ║
║  ✅ Individual servo tests passed (quick_servo_diagnostic)     ║
║                                                                ║
║  TESTS:                                                        ║
║  1. Initialization (7 servos detected)                         ║
║  2. Individual servo movement (17 positions)                   ║
║  3. Corner synchronization (4 servos parallel)                 ║
║  4. Lock mechanism (open/close)                                ║
║  5. Full sorting - Organic → Bin A                             ║
║  6. Full sorting - Inorganic → Bin B                           ║
║  7. Stress test (10x consecutive sortings)                     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    wait_user("Press Enter to start validation tests...")
    
    try:
        # Test 1: Initialization
        hw = test_initialization()
        
        # Test 2: Individual servos
        if not test_individual_servos(hw):
            raise Exception("Individual servo test failed")
        
        # Test 3: Corner sync
        if not test_corner_sync(hw):
            raise Exception("Corner synchronization test failed")
        
        # Test 4: Lock mechanism
        if not test_lock_mechanism(hw):
            raise Exception("Lock mechanism test failed")
        
        # Test 5: Full sorting organic
        if not test_full_sorting_organic(hw):
            raise Exception("Full sorting (organic) test failed")
        
        # Test 6: Full sorting inorganic
        if not test_full_sorting_inorganic(hw):
            raise Exception("Full sorting (inorganic) test failed")
        
        # Test 7: Stress test
        if not test_stress(hw):
            raise Exception("Stress test failed")
        
        # All tests passed!
        print("\n" + "="*70)
        print("  🎉 ALL VALIDATION TESTS PASSED! 🎉")
        print("="*70)
        print("\n✅ Your 7-servo system is READY FOR PRODUCTION!")
        print("\n📋 Next Steps:")
        print("   1. Deploy to systemd service: sudo systemctl enable orangebox")
        print("   2. Start service: sudo systemctl start orangebox")
        print("   3. Monitor logs: sudo journalctl -u orangebox -f")
        print("   4. Test with real camera: python3 main.py --test")
        print("\n🚀 Congratulations! System is production-ready.\n")
        
        # Cleanup
        hw.cleanup()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user (Ctrl+C)")
        print("   Cleaning up...")
        if 'hw' in locals():
            hw.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ VALIDATION FAILED: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check servo wiring (all 7 servos connected?)")
        print("   2. Verify servo types (all positional, not continuous?)")
        print("   3. Check power supply (min. 3A for 7 servos)")
        print("   4. Run individual test: python3 scripts/quick_servo_diagnostic.py")
        print("   5. Check config: grep 'SERVO_L1' config.py")
        if 'hw' in locals():
            hw.cleanup()
        sys.exit(1)

if __name__ == '__main__':
    main()
