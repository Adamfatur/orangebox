#!/usr/bin/env python3
"""
Test script untuk bin capacity monitoring system
Run: python3 scripts/test_bin_monitor.py
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.bin_monitor import BinMonitor


def print_header():
    """Print test header"""
    print("\n" + "="*70)
    print("🗑️  BIN CAPACITY MONITORING - TEST SCRIPT")
    print("="*70)
    print("\nThis script tests the ultrasonic sensors for bin monitoring.")
    print("Place objects in/out of bins to see real-time level changes.\n")
    print("Press Ctrl+C to stop\n")


def print_status_line(status, iteration):
    """Print formatted status line"""
    bin_a = status['bin_a_level']
    bin_b = status['bin_b_level']
    a_full = status['bin_a_full']
    b_full = status['bin_b_full']
    active = status['monitoring_active']
    
    # Status icons
    a_icon = "🔴 FULL" if a_full else "🟢 OK  "
    b_icon = "🔴 FULL" if b_full else "🟢 OK  "
    active_icon = "✅" if active else "❌"
    
    print(f"\r[{iteration:3d}s] {active_icon} | "
          f"BIN A: {bin_a:5.1f}% {a_icon} | "
          f"BIN B: {bin_b:5.1f}% {b_icon}", end='', flush=True)


def test_sensors_only():
    """Test sensors without Blynk (quick hardware test)"""
    print_header()
    print("Mode: SENSOR TEST ONLY (no Blynk)\n")
    
    try:
        from gpiozero import DistanceSensor
    except ImportError:
        print("❌ gpiozero not installed!")
        print("   Install with: pip install gpiozero")
        return
    
    import config
    
    print("Initializing sensors...")
    print(f"  BIN A: TRIG={config.BIN_A_SENSOR_TRIG}, ECHO={config.BIN_A_SENSOR_ECHO}")
    print(f"  BIN B: TRIG={config.BIN_B_SENSOR_TRIG}, ECHO={config.BIN_B_SENSOR_ECHO}")
    print()
    
    try:
        sensor_a = DistanceSensor(
            echo=config.BIN_A_SENSOR_ECHO,
            trigger=config.BIN_A_SENSOR_TRIG,
            max_distance=2
        )
        print("✅ BIN A sensor initialized")
        
        sensor_b = DistanceSensor(
            echo=config.BIN_B_SENSOR_ECHO,
            trigger=config.BIN_B_SENSOR_TRIG,
            max_distance=2
        )
        print("✅ BIN B sensor initialized")
        print()
        
        print("Reading sensors for 30 seconds...\n")
        
        for i in range(30):
            dist_a = sensor_a.distance * 100  # meters to cm
            dist_b = sensor_b.distance * 100
            
            # Calculate percentages
            empty = config.BIN_EMPTY_DISTANCE_CM
            full = config.BIN_FULL_DISTANCE_CM
            range_total = empty - full
            
            level_a = ((empty - dist_a) / range_total) * 100
            level_b = ((empty - dist_b) / range_total) * 100
            
            level_a = max(0, min(100, level_a))
            level_b = max(0, min(100, level_b))
            
            print(f"\r[{i+1:2d}s] "
                  f"BIN A: {dist_a:5.1f}cm → {level_a:5.1f}% | "
                  f"BIN B: {dist_b:5.1f}cm → {level_b:5.1f}%", end='', flush=True)
            
            time.sleep(1)
        
        print("\n\n✅ Sensor test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            sensor_a.close()
            sensor_b.close()
        except:
            pass
        print("🛑 Sensors closed")


def test_full_system():
    """Test full system with Blynk integration"""
    print_header()
    print("Mode: FULL SYSTEM TEST (with Blynk)\n")
    
    monitor = BinMonitor(enable_blynk=True)
    
    try:
        print("Starting monitoring...\n")
        monitor.start_monitoring()
        
        # Wait for first reading
        time.sleep(2)
        
        print("Monitoring for 60 seconds...\n")
        
        for i in range(60):
            status = monitor.get_status_dict()
            print_status_line(status, i+1)
            time.sleep(1)
        
        print("\n\n✅ Test completed successfully!")
        
        # Print final summary
        final_status = monitor.get_status_dict()
        print("\n" + "-"*70)
        print("FINAL STATUS:")
        print("-"*70)
        print(f"BIN A: {final_status['bin_a_level']:.1f}% ({'FULL' if final_status['bin_a_full'] else 'OK'})")
        print(f"BIN B: {final_status['bin_b_level']:.1f}% ({'FULL' if final_status['bin_b_full'] else 'OK'})")
        print(f"Monitoring: {'Active' if final_status['monitoring_active'] else 'Inactive'}")
        print("-"*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🛑 Shutting down...")
        monitor.cleanup()


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test bin capacity monitoring system')
    parser.add_argument('--sensors-only', action='store_true',
                        help='Test sensors only (no Blynk)')
    parser.add_argument('--duration', type=int, default=30,
                        help='Test duration in seconds (default: 30)')
    
    args = parser.parse_args()
    
    if args.sensors_only:
        test_sensors_only()
    else:
        test_full_system()


if __name__ == "__main__":
    main()
