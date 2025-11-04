#!/usr/bin/env python3
"""
Test script untuk sistem 7-servo dengan locking mechanism

Menguji:
1. Inisialisasi semua servo
2. Sequence sorting ke BIN A (ORGANIC)
3. Sequence sorting ke BIN B (ANORGANIC)
4. Reset ke posisi ready

Copyright (c) 2025 AF - OrangeBox Project
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config
from src.hardware.seven_servo_hardware import SevenServoHardware


def print_banner():
    """Print banner"""
    print("\n" + "="*70)
    print("  🔧 7-SERVO LOCKING SYSTEM - TEST PROGRAM")
    print("="*70)
    print("\nThis test will:")
    print("  1. Initialize all 7 servos")
    print("  2. Test sorting sequence to BIN A (ORGANIC)")
    print("  3. Test sorting sequence to BIN B (ANORGANIC)")
    print("  4. Reset to ready position")
    print("\n" + "="*70 + "\n")


def test_initialization():
    """Test servo initialization"""
    print("\n┌─────────────────────────────────────────┐")
    print("│  TEST 1: Initialization                │")
    print("└─────────────────────────────────────────┘\n")
    
    try:
        hw = SevenServoHardware()
        print("\n✅ Initialization successful!")
        return hw
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_sorting_sequence(hw):
    """Test complete sorting sequences"""
    if hw is None:
        print("\n⚠️  Skipping sorting test (initialization failed)")
        return
    
    print("\n┌─────────────────────────────────────────┐")
    print("│  TEST 2: Sorting Sequences             │")
    print("└─────────────────────────────────────────┘\n")
    
    try:
        # Test BIN A
        print("\n" + "─"*60)
        print("Testing BIN A (ORGANIC)...")
        print("─"*60)
        input("Press ENTER to start BIN A test (or Ctrl+C to skip)...")
        
        success_a = hw.sort_to_bin_a()
        if success_a:
            print("\n✅ BIN A sorting successful!")
        else:
            print("\n⚠️  BIN A sorting completed with warnings")
        
        # Wait between tests
        print("\n⏱  Waiting 3 seconds before next test...")
        time.sleep(3)
        
        # Test BIN B
        print("\n" + "─"*60)
        print("Testing BIN B (ANORGANIC)...")
        print("─"*60)
        input("Press ENTER to start BIN B test (or Ctrl+C to skip)...")
        
        success_b = hw.sort_to_bin_b()
        if success_b:
            print("\n✅ BIN B sorting successful!")
        else:
            print("\n⚠️  BIN B sorting completed with warnings")
        
        print("\n✅ All sorting tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Sorting test failed: {e}")
        import traceback
        traceback.print_exc()


def test_reset(hw):
    """Test reset to ready position"""
    if hw is None:
        print("\n⚠️  Skipping reset test (initialization failed)")
        return
    
    print("\n┌─────────────────────────────────────────┐")
    print("│  TEST 3: Reset to Ready                │")
    print("└─────────────────────────────────────────┘\n")
    
    try:
        input("Press ENTER to reset to ready position (or Ctrl+C to skip)...")
        hw.reset_to_ready()
        print("\n✅ Reset successful!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Reset skipped by user")
    except Exception as e:
        print(f"\n❌ Reset failed: {e}")
        import traceback
        traceback.print_exc()


def test_individual_servos(hw):
    """Test individual servo movements"""
    if hw is None:
        print("\n⚠️  Skipping individual servo test (initialization failed)")
        return
    
    print("\n┌─────────────────────────────────────────┐")
    print("│  TEST 4: Individual Servo Movements    │")
    print("└─────────────────────────────────────────┘\n")
    
    try:
        # Test corner servos
        print("\n→ Testing Corner Servos...")
        for corner in ['corner_a', 'corner_b', 'corner_c', 'corner_d']:
            if corner in hw.servos:
                print(f"  Testing {corner.upper()}...")
                hw._move_servo(corner, hw.servos[corner]['down'])
                time.sleep(0.5)
                hw._move_servo(corner, hw.servos[corner]['up'])
                time.sleep(0.5)
        
        # Test lock servos
        print("\n→ Testing Lock Servos...")
        for lock in ['lock_left', 'lock_right']:
            if lock in hw.servos:
                print(f"  Testing {lock.upper()}...")
                hw._move_servo(lock, hw.servos[lock]['unlocked'])
                time.sleep(0.5)
                hw._move_servo(lock, hw.servos[lock]['locked'])
                time.sleep(0.5)
        
        # Test selector
        print("\n→ Testing Selector Servo...")
        if 'selector' in hw.servos:
            print("  Moving to BIN A...")
            hw._move_servo('selector', hw.servos['selector']['bin_a'])
            time.sleep(1)
            print("  Moving to NEUTRAL...")
            hw._move_servo('selector', hw.servos['selector']['neutral'])
            time.sleep(1)
            print("  Moving to BIN B...")
            hw._move_servo('selector', hw.servos['selector']['bin_b'])
            time.sleep(1)
            print("  Moving to NEUTRAL...")
            hw._move_servo('selector', hw.servos['selector']['neutral'])
        
        print("\n✅ Individual servo tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Individual test interrupted by user")
    except Exception as e:
        print(f"\n❌ Individual servo test failed: {e}")
        import traceback
        traceback.print_exc()


def print_configuration():
    """Print current configuration"""
    print("\n┌─────────────────────────────────────────┐")
    print("│  Current Configuration                 │")
    print("└─────────────────────────────────────────┘\n")
    
    print("Platform:", getattr(config, 'PLATFORM', 'unknown'))
    print("Servo Driver:", getattr(config, 'SERVO_DRIVER', 'unknown'))
    print("\nLayer 1 - Corner Servos:")
    print(f"  Corner A: CH {getattr(config, 'SERVO_L1_CORNER_A_CHANNEL', 'N/A')}")
    print(f"  Corner B: CH {getattr(config, 'SERVO_L1_CORNER_B_CHANNEL', 'N/A')}")
    print(f"  Corner C: CH {getattr(config, 'SERVO_L1_CORNER_C_CHANNEL', 'N/A')}")
    print(f"  Corner D: CH {getattr(config, 'SERVO_L1_CORNER_D_CHANNEL', 'N/A')}")
    print(f"  UP: {getattr(config, 'SERVO_L1_CORNER_UP', 'N/A')}°")
    print(f"  DOWN: {getattr(config, 'SERVO_L1_CORNER_DOWN', 'N/A')}°")
    
    print("\nLayer 1 - Lock Servos:")
    print(f"  Lock Left: CH {getattr(config, 'SERVO_L1_LOCK_LEFT_CHANNEL', 'N/A')}")
    print(f"  Lock Right: CH {getattr(config, 'SERVO_L1_LOCK_RIGHT_CHANNEL', 'N/A')}")
    print(f"  LOCKED: {getattr(config, 'SERVO_L1_LOCK_LOCKED', 'N/A')}°")
    print(f"  UNLOCKED: {getattr(config, 'SERVO_L1_LOCK_UNLOCKED', 'N/A')}°")
    
    print("\nLayer 2 - Selector:")
    print(f"  Selector: CH {getattr(config, 'SERVO_L2_SELECTOR_CHANNEL', 'N/A')}")
    print(f"  NEUTRAL: {getattr(config, 'SERVO_L2_SELECTOR_NEUTRAL', 'N/A')}°")
    print(f"  BIN A: {getattr(config, 'SERVO_L2_SELECTOR_BIN_A', 'N/A')}°")
    print(f"  BIN B: {getattr(config, 'SERVO_L2_SELECTOR_BIN_B', 'N/A')}°")
    
    print("\nTiming:")
    print(f"  Movement Time: {getattr(config, 'SERVO_MOVEMENT_TIME', 'N/A')}s")
    print(f"  Fall Time: {getattr(config, 'SERVO_FALL_TIME', 'N/A')}s")
    print(f"  Lift Time: {getattr(config, 'SERVO_LIFT_TIME', 'N/A')}s")
    print(f"  Lock Delay: {getattr(config, 'SERVO_LOCK_DELAY', 'N/A')}s")


def main():
    """Main test function"""
    print_banner()
    print_configuration()
    
    # Initialize hardware
    hw = test_initialization()
    
    if hw is None:
        print("\n❌ Cannot proceed with tests - initialization failed")
        print("\nℹ️  This is normal on macOS (simulation mode)")
        print("   All movements are simulated.")
        return 1
    
    # Interactive menu
    while True:
        print("\n" + "="*70)
        print("TEST MENU")
        print("="*70)
        print("1. Run full sorting sequence (BIN A + BIN B)")
        print("2. Test BIN A only")
        print("3. Test BIN B only")
        print("4. Test individual servos")
        print("5. Reset to ready position")
        print("6. Show configuration")
        print("q. Quit")
        print("="*70)
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == '1':
            test_sorting_sequence(hw)
        elif choice == '2':
            try:
                hw.sort_to_bin_a()
            except Exception as e:
                print(f"❌ Error: {e}")
        elif choice == '3':
            try:
                hw.sort_to_bin_b()
            except Exception as e:
                print(f"❌ Error: {e}")
        elif choice == '4':
            test_individual_servos(hw)
        elif choice == '5':
            test_reset(hw)
        elif choice == '6':
            print_configuration()
        elif choice == 'q':
            break
        else:
            print("❌ Invalid choice")
    
    # Cleanup
    print("\n🛑 Cleaning up...")
    try:
        hw.cleanup()
    except Exception:
        pass
    
    print("\n✅ Test program finished. Goodbye!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Program interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
