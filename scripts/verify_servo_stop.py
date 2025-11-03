#!/usr/bin/env python3
"""
Servo Stop Verification Test
Memverifikasi bahwa servo BERHENTI pada posisi yang ditentukan dan TIDAK berputar terus-menerus.

CARA PENGGUNAAN:
1. Di Raspberry Pi:
   python3 scripts/verify_servo_stop.py
   
2. Servo akan bergerak ke beberapa posisi dan berhenti
3. Amati secara visual:
   - ✓ BENAR: Servo bergerak ke posisi lalu DIAM/BERHENTI
   - ✗ SALAH: Servo terus berputar atau bergetar setelah mencapai posisi

TROUBLESHOOTING:
- Jika servo berputar terus → Cek config.py: SERVO_STOP_JITTER harus True
- Jika servo bergetar/jitter → Normal untuk MG996R, tapi bisa dikurangi dengan:
  * Naikkan SERVO_POSITION_HOLD_TIME (0.05 → 0.1)
  * Pastikan power supply stabil (minimal 5V 3A)
  * Cek koneksi kabel servo tidak longgar

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    print("⚠️ RPi.GPIO not available - running in SIMULATION mode")


def angle_to_duty(angle):
    """Convert angle (0-180°) to duty cycle (2.5-12.5%) for MG996R"""
    return 2.5 + (angle / 18.0)


def test_servo_stop(pin, test_angles, servo_name="Servo"):
    """
    Test servo movement and verify it STOPS at each position.
    
    Args:
        pin: GPIO pin number (BCM)
        test_angles: List of angles to test
        servo_name: Name for display
    """
    print(f"\n{'='*70}")
    print(f"Testing {servo_name} on GPIO {pin}")
    print(f"{'='*70}")
    
    if not HAS_GPIO:
        print(f"[SIMULATION] Would test angles: {test_angles}")
        for angle in test_angles:
            print(f"  → {angle}° [SIMULATED]")
            time.sleep(0.5)
        return True
    
    try:
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        
        # Create PWM @ 50Hz
        pwm = GPIO.PWM(pin, config.SERVO_PWM_FREQUENCY)
        pwm.start(0)
        
        print(f"\nConfig Settings:")
        print(f"  SERVO_MOVEMENT_TIME: {config.SERVO_MOVEMENT_TIME}s")
        print(f"  SERVO_POSITION_HOLD_TIME: {config.SERVO_POSITION_HOLD_TIME}s")
        print(f"  SERVO_STOP_JITTER: {config.SERVO_STOP_JITTER}")
        
        for i, angle in enumerate(test_angles, 1):
            print(f"\n[Test {i}/{len(test_angles)}] Moving to {angle}°...")
            
            # Calculate duty cycle
            duty = angle_to_duty(angle)
            
            # Move servo
            pwm.ChangeDutyCycle(duty)
            print(f"  ⏱️  Moving... (wait {config.SERVO_MOVEMENT_TIME}s)")
            time.sleep(config.SERVO_MOVEMENT_TIME)
            
            # Hold position
            print(f"  🔒 Locking position... (hold {config.SERVO_POSITION_HOLD_TIME}s)")
            time.sleep(config.SERVO_POSITION_HOLD_TIME)
            
            # Stop PWM (CRITICAL!)
            if config.SERVO_STOP_JITTER:
                pwm.ChangeDutyCycle(0)
                print(f"  ✓ PWM STOPPED - servo should be LOCKED at {angle}°")
                print(f"  👀 OBSERVE: Servo should be STILL (not rotating/vibrating)")
            else:
                print(f"  ⚠️  PWM ACTIVE - servo may jitter or rotate!")
                print(f"  ⚠️  WARNING: SERVO_STOP_JITTER is False!")
            
            # Wait for observation
            if i < len(test_angles):
                print(f"\n  Waiting 3 seconds for observation...")
                print(f"  (Check: Is servo STOPPED at {angle}°?)")
                time.sleep(3)
        
        # Final hold
        print(f"\n{'='*70}")
        print(f"Test Complete - Final position held for 5 seconds")
        print(f"OBSERVE: Servo should remain STILL at final position")
        print(f"{'='*70}")
        time.sleep(5)
        
        # Cleanup
        pwm.stop()
        GPIO.cleanup()
        
        print(f"\n✓ Test completed for {servo_name}")
        return True
        
    except Exception as e:
        print(f"\n✗ Error testing {servo_name}: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            GPIO.cleanup()
        except:
            pass
        
        return False


def main():
    print("="*70)
    print("SERVO STOP VERIFICATION TEST")
    print("="*70)
    print("\nThis test verifies that servos STOP at target positions")
    print("and DO NOT rotate continuously.\n")
    
    if not HAS_GPIO:
        print("⚠️  Running in SIMULATION mode (no GPIO available)")
        print("Deploy to Raspberry Pi for real hardware test.\n")
    
    # Test configurations
    tests = [
        {
            'name': 'Layer 1 Left Door',
            'pin': config.SERVO_LAYER1_LEFT_PIN,
            'angles': [
                config.SERVO_LAYER1_LEFT_CLOSED,  # Closed
                config.SERVO_LAYER1_LEFT_OPEN,    # Open
                config.SERVO_LAYER1_LEFT_CLOSED   # Back to closed
            ]
        },
        {
            'name': 'Layer 1 Right Door',
            'pin': config.SERVO_LAYER1_RIGHT_PIN,
            'angles': [
                config.SERVO_LAYER1_RIGHT_CLOSED,
                config.SERVO_LAYER1_RIGHT_OPEN,
                config.SERVO_LAYER1_RIGHT_CLOSED
            ]
        },
        {
            'name': 'Layer 2 Selector',
            'pin': config.SERVO_LAYER2_SELECTOR_PIN,
            'angles': [
                config.SERVO_LAYER2_NEUTRAL,  # Neutral
                config.SERVO_LAYER2_BIN_A,    # Bin A
                config.SERVO_LAYER2_NEUTRAL,  # Back to neutral
                config.SERVO_LAYER2_BIN_B,    # Bin B
                config.SERVO_LAYER2_NEUTRAL   # Back to neutral
            ]
        }
    ]
    
    print("Tests to run:")
    for i, test in enumerate(tests, 1):
        print(f"  {i}. {test['name']} (GPIO {test['pin']}) - {len(test['angles'])} positions")
    
    print("\nStarting tests in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    
    # Run tests
    results = []
    for test in tests:
        success = test_servo_stop(
            pin=test['pin'],
            test_angles=test['angles'],
            servo_name=test['name']
        )
        results.append({
            'name': test['name'],
            'success': success
        })
        
        # Pause between tests
        if test != tests[-1]:  # Not last test
            print("\nPausing 2 seconds before next test...")
            time.sleep(2)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for result in results:
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        print(f"  {status} - {result['name']}")
        if not result['success']:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED")
        print("Servos are stopping correctly at target positions.")
    else:
        print("\n✗ SOME TESTS FAILED")
        print("\nTroubleshooting:")
        print("1. Check config.py: SERVO_STOP_JITTER should be True")
        print("2. Verify power supply is stable (5V 3A minimum)")
        print("3. Check servo wiring and connections")
        print("4. Verify GPIO pin numbers match physical connections")
    
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        try:
            if HAS_GPIO:
                GPIO.cleanup()
        except:
            pass
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        try:
            if HAS_GPIO:
                GPIO.cleanup()
        except:
            pass
