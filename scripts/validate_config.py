#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║         CONFIG VALIDATOR - 7-Servo System                   ║
║     Validate semua konfigurasi sebelum deploy                ║
╚═══════════════════════════════════════════════════════════════╝

Script ini akan memvalidasi:
✅ Servo driver setting
✅ Channel assignment (0-15 untuk PCA9685)
✅ Angle values (0-180° saja, prevent 360° rotation)
✅ Timing values (reasonable)
✅ PCA9685 I2C address
✅ Duplicate channels

Copyright (c) 2025 AF - OrangeBox Project
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(title):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def validate_servo_driver():
    """Validate SERVO_DRIVER setting"""
    print_header("SERVO DRIVER VALIDATION")
    
    driver = getattr(config, 'SERVO_DRIVER', None)
    
    if driver is None:
        print_error("SERVO_DRIVER not found in config.py")
        return False
    
    if driver != 'seven_servo':
        print_error(f"SERVO_DRIVER = '{driver}' (expected 'seven_servo')")
        print(f"   Please set: SERVO_DRIVER = 'seven_servo'")
        return False
    
    print_success(f"SERVO_DRIVER = '{driver}' ✓")
    return True

def validate_channels():
    """Validate all channel assignments"""
    print_header("CHANNEL ASSIGNMENT VALIDATION")
    
    channels = {
        'SERVO_L1_CORNER_A_CHANNEL': getattr(config, 'SERVO_L1_CORNER_A_CHANNEL', None),
        'SERVO_L1_CORNER_B_CHANNEL': getattr(config, 'SERVO_L1_CORNER_B_CHANNEL', None),
        'SERVO_L1_CORNER_C_CHANNEL': getattr(config, 'SERVO_L1_CORNER_C_CHANNEL', None),
        'SERVO_L1_CORNER_D_CHANNEL': getattr(config, 'SERVO_L1_CORNER_D_CHANNEL', None),
        'SERVO_L1_LOCK_LEFT_CHANNEL': getattr(config, 'SERVO_L1_LOCK_LEFT_CHANNEL', None),
        'SERVO_L1_LOCK_RIGHT_CHANNEL': getattr(config, 'SERVO_L1_LOCK_RIGHT_CHANNEL', None),
        'SERVO_L2_SELECTOR_CHANNEL': getattr(config, 'SERVO_L2_SELECTOR_CHANNEL', None),
    }
    
    errors = []
    used_channels = []
    
    for name, channel in channels.items():
        if channel is None:
            print_error(f"{name} not set")
            errors.append(name)
            continue
        
        # Validate channel range (0-15 for PCA9685)
        if not isinstance(channel, int) or channel < 0 or channel > 15:
            print_error(f"{name} = {channel} (must be 0-15)")
            errors.append(name)
            continue
        
        # Check for duplicates
        if channel in used_channels:
            print_error(f"{name} = {channel} (DUPLICATE! Already used)")
            errors.append(name)
        else:
            used_channels.append(channel)
            print_success(f"{name} = {channel}")
    
    return len(errors) == 0

def validate_angles():
    """Validate all angle values (must be 0-180)"""
    print_header("ANGLE VALUE VALIDATION")
    
    angles = {
        'SERVO_L1_CORNER_UP': getattr(config, 'SERVO_L1_CORNER_UP', None),
        'SERVO_L1_CORNER_DOWN': getattr(config, 'SERVO_L1_CORNER_DOWN', None),
        'SERVO_L1_LOCK_LOCKED': getattr(config, 'SERVO_L1_LOCK_LOCKED', None),
        'SERVO_L1_LOCK_UNLOCKED': getattr(config, 'SERVO_L1_LOCK_UNLOCKED', None),
        'SERVO_L2_SELECTOR_NEUTRAL': getattr(config, 'SERVO_L2_SELECTOR_NEUTRAL', None),
        'SERVO_L2_SELECTOR_BIN_A': getattr(config, 'SERVO_L2_SELECTOR_BIN_A', None),
        'SERVO_L2_SELECTOR_BIN_B': getattr(config, 'SERVO_L2_SELECTOR_BIN_B', None),
    }
    
    errors = []
    
    for name, angle in angles.items():
        if angle is None:
            print_error(f"{name} not set")
            errors.append(name)
            continue
        
        # CRITICAL: Angle must be 0-180
        if not isinstance(angle, (int, float)) or angle < 0 or angle > 180:
            print_error(f"{name} = {angle}° (INVALID! Must be 0-180°)")
            print(f"   ⚠️  This will cause servo to rotate 360° continuously!")
            errors.append(name)
        else:
            print_success(f"{name} = {angle}°")
    
    return len(errors) == 0

def validate_timing():
    """Validate timing values"""
    print_header("TIMING VALIDATION")
    
    timings = {
        'SERVO_DROP_DELAY': getattr(config, 'SERVO_DROP_DELAY', None),
        'SERVO_FALL_TIME': getattr(config, 'SERVO_FALL_TIME', None),
        'SERVO_SLIDE_TIME': getattr(config, 'SERVO_SLIDE_TIME', None),
        'SERVO_LIFT_TIME': getattr(config, 'SERVO_LIFT_TIME', None),
        'SERVO_LOCK_DELAY': getattr(config, 'SERVO_LOCK_DELAY', None),
        'SERVO_RESET_DELAY': getattr(config, 'SERVO_RESET_DELAY', None),
        'SERVO_MOVEMENT_TIME': getattr(config, 'SERVO_MOVEMENT_TIME', None),
        'SERVO_STAGGER_DELAY_MS': getattr(config, 'SERVO_STAGGER_DELAY_MS', None),
    }
    
    warnings = []
    
    for name, value in timings.items():
        if value is None:
            print_warning(f"{name} not set (will use default)")
            warnings.append(name)
            continue
        
        # Check reasonable range
        if 'MS' in name:  # Milliseconds
            if value < 0 or value > 1000:
                print_warning(f"{name} = {value}ms (unusual, check if correct)")
                warnings.append(name)
            else:
                print_success(f"{name} = {value}ms")
        else:  # Seconds
            if value < 0 or value > 10:
                print_warning(f"{name} = {value}s (unusual, check if correct)")
                warnings.append(name)
            else:
                print_success(f"{name} = {value}s")
    
    # Check SERVO_STAGGER_DELAY_MS specifically
    stagger = getattr(config, 'SERVO_STAGGER_DELAY_MS', None)
    if stagger is not None and stagger == 0:
        print_success(f"SERVO_STAGGER_DELAY_MS = 0 (PARALLEL movement - RECOMMENDED)")
    elif stagger is not None and stagger > 0:
        print(f"   ℹ️  SERVO_STAGGER_DELAY_MS = {stagger}ms (sequential movement)")
        print(f"   ℹ️  Set to 0 for REALTIME parallel movement")
    
    return len(warnings) == 0

def validate_pca9685():
    """Validate PCA9685 settings"""
    print_header("PCA9685 SETTINGS VALIDATION")
    
    address = getattr(config, 'PCA9685_I2C_ADDRESS', None)
    frequency = getattr(config, 'PCA9685_FREQUENCY', None)
    
    all_ok = True
    
    if address is None:
        print_error("PCA9685_I2C_ADDRESS not set")
        all_ok = False
    elif address != 0x40:
        print_warning(f"PCA9685_I2C_ADDRESS = 0x{address:02X} (non-standard, default is 0x40)")
    else:
        print_success(f"PCA9685_I2C_ADDRESS = 0x{address:02X}")
    
    if frequency is None:
        print_error("PCA9685_FREQUENCY not set")
        all_ok = False
    elif frequency != 50:
        print_warning(f"PCA9685_FREQUENCY = {frequency}Hz (standard servo is 50Hz)")
    else:
        print_success(f"PCA9685_FREQUENCY = {frequency}Hz")
    
    # Check pulse calibration
    min_pulse = getattr(config, 'SERVOKIT_MIN_PULSE_MICROS', None)
    max_pulse = getattr(config, 'SERVOKIT_MAX_PULSE_MICROS', None)
    actuation = getattr(config, 'SERVOKIT_ACTUATION_RANGE', None)
    
    if min_pulse:
        print_success(f"SERVOKIT_MIN_PULSE_MICROS = {min_pulse}μs")
    if max_pulse:
        print_success(f"SERVOKIT_MAX_PULSE_MICROS = {max_pulse}μs")
    if actuation:
        print_success(f"SERVOKIT_ACTUATION_RANGE = {actuation}°")
    
    return all_ok

def main():
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║     OrangeBox v1.2 - Configuration Validator             ║{RESET}")
    print(f"{BLUE}║              7-Servo System Checker                      ║{RESET}")
    print(f"{BLUE}╚════════════════════════════════════════════════════════════╝{RESET}")
    
    results = []
    
    # Run all validations
    results.append(("Servo Driver", validate_servo_driver()))
    results.append(("Channel Assignment", validate_channels()))
    results.append(("Angle Values", validate_angles()))
    results.append(("Timing Settings", validate_timing()))
    results.append(("PCA9685 Settings", validate_pca9685()))
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    all_passed = True
    for name, passed in results:
        if passed:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
            all_passed = False
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    
    if all_passed:
        print(f"\n{GREEN}✅ ALL VALIDATIONS PASSED!{RESET}")
        print(f"{GREEN}   Configuration is SAFE for deployment{RESET}\n")
        return 0
    else:
        print(f"\n{RED}❌ VALIDATION FAILED!{RESET}")
        print(f"{RED}   Please fix errors above before deploying{RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
