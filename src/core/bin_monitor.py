"""
Bin Capacity Monitor - Ultrasonic Sensor Integration with Blynk
Monitors waste bin fill levels for BIN A (Organic) and BIN B (Anorganic)

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

import time
import threading
import sys
import os

# Ensure project root on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import config

# Import hardware libraries (with graceful fallback for non-RPi platforms)
HAS_GPIOZERO = False
HAS_BLYNK = False

try:
    from gpiozero import DistanceSensor
    HAS_GPIOZERO = True
except Exception as e:
    print(f"[BinMonitor] Warning: gpiozero not available: {e}")

try:
    import BlynkLib
    HAS_BLYNK = True
except Exception as e:
    print(f"[BinMonitor] Warning: BlynkLib not available: {e}")


class BinMonitor:
    """
    Monitor kapasitas tong sampah menggunakan sensor ultrasonic HC-SR04.
    Mendukung 2 tong (BIN A dan BIN B) dengan sensor terpisah.
    Kirim data real-time ke Blynk IoT dashboard dan database.
    """
    
    def __init__(self, enable_blynk=True, database_service=None, device_id=None, location_service=None):
        """
        Initialize Bin Monitor
        
        Args:
            enable_blynk: Enable Blynk cloud reporting (default: True)
            database_service: DatabaseService instance untuk logging ke DB (optional)
            device_id: Unique device identifier (optional)
            location_service: LocationService instance untuk GPS data (optional)
        """
        self.platform = getattr(config, 'PLATFORM', 'rpi')
        self.enable_blynk = enable_blynk and getattr(config, 'ENABLE_BIN_MONITORING', False)
        self.database_service = database_service
        self.device_id = device_id
        self.location_service = location_service
        self.is_active = False
        self.monitoring_thread = None
        self.stop_flag = threading.Event()
        
        # Bin capacity data
        self.bin_a_level = 0.0  # Percentage (0-100)
        self.bin_b_level = 0.0  # Percentage (0-100)
        self.bin_a_distance = None  # Distance in cm
        self.bin_b_distance = None  # Distance in cm
        self.last_update_time = 0
        self.last_db_log_time = 0  # Track last database log time
        
        # Lock for thread-safe access
        self.data_lock = threading.Lock()
        
        # Hardware objects
        self.sensor_bin_a = None
        self.sensor_bin_b = None
        self.blynk = None
        
        # Configuration from config.py
        self.bin_a_trig = getattr(config, 'BIN_A_SENSOR_TRIG', 23)
        self.bin_a_echo = getattr(config, 'BIN_A_SENSOR_ECHO', 24)
        self.bin_b_trig = getattr(config, 'BIN_B_SENSOR_TRIG', 5)
        self.bin_b_echo = getattr(config, 'BIN_B_SENSOR_ECHO', 6)
        
        # Calibration (distance in cm)
        self.empty_distance = getattr(config, 'BIN_EMPTY_DISTANCE_CM', 80.0)
        self.full_distance = getattr(config, 'BIN_FULL_DISTANCE_CM', 5.0)
        self.full_threshold = getattr(config, 'BIN_FULL_THRESHOLD_PERCENT', 85.0)
        
        # Blynk configuration
        self.blynk_token = getattr(config, 'BLYNK_AUTH_TOKEN', '')
        self.blynk_vpin_bin_a = getattr(config, 'BLYNK_VPIN_BIN_A', 3)
        self.blynk_vpin_bin_b = getattr(config, 'BLYNK_VPIN_BIN_B', 4)
        self.update_interval = getattr(config, 'BIN_MONITOR_UPDATE_INTERVAL', 5.0)
        
        # Database logging configuration
        self.db_log_interval = getattr(config, 'BIN_DB_LOG_INTERVAL', 60.0)  # Log to DB every 60 seconds
        self.warning_threshold = getattr(config, 'BIN_WARNING_THRESHOLD_PERCENT', 70.0)
        
        # Initialize hardware (only on Raspberry Pi)
        if self.platform == 'rpi' and self.enable_blynk:
            self._initialize_hardware()
        else:
            print("[BinMonitor] Running in SIMULATION mode (disabled or not on RPi)")
    
    def _initialize_hardware(self):
        """Initialize ultrasonic sensors and Blynk connection"""
        print("\n[BinMonitor] ╔════════════════════════════════════════════════╗")
        print("[BinMonitor] ║   Initializing Bin Capacity Monitor          ║")
        print("[BinMonitor] ╚════════════════════════════════════════════════╝")
        
        if not HAS_GPIOZERO:
            print("[BinMonitor] ❌ gpiozero not installed - sensor disabled")
            return
        
        try:
            # Initialize BIN A sensor
            print(f"[BinMonitor] → Setting up BIN A sensor (TRIG={self.bin_a_trig}, ECHO={self.bin_a_echo})...")
            self.sensor_bin_a = DistanceSensor(
                echo=self.bin_a_echo,
                trigger=self.bin_a_trig,
                max_distance=2,  # 2 meters max
                threshold_distance=0.1
            )
            print("[BinMonitor] ✓ BIN A sensor initialized")
            
            # Initialize BIN B sensor
            print(f"[BinMonitor] → Setting up BIN B sensor (TRIG={self.bin_b_trig}, ECHO={self.bin_b_echo})...")
            self.sensor_bin_b = DistanceSensor(
                echo=self.bin_b_echo,
                trigger=self.bin_b_trig,
                max_distance=2,
                threshold_distance=0.1
            )
            print("[BinMonitor] ✓ BIN B sensor initialized")
            
        except Exception as e:
            print(f"[BinMonitor] ⚠️  Sensor initialization failed: {e}")
            print("[BinMonitor] → Continuing without sensors...")
            self.sensor_bin_a = None
            self.sensor_bin_b = None
        
        # Initialize Blynk if enabled and token provided
        if HAS_BLYNK and self.blynk_token:
            try:
                print(f"[BinMonitor] → Connecting to Blynk Cloud...")
                self.blynk = BlynkLib.Blynk(
                    self.blynk_token,
                    server='blynk.cloud',
                    port=8080
                )
                print("[BinMonitor] ✓ Blynk connected")
                print(f"[BinMonitor]   • BIN A → Virtual Pin V{self.blynk_vpin_bin_a}")
                print(f"[BinMonitor]   • BIN B → Virtual Pin V{self.blynk_vpin_bin_b}")
            except Exception as e:
                print(f"[BinMonitor] ⚠️  Blynk initialization failed: {e}")
                self.blynk = None
        else:
            if not HAS_BLYNK:
                print("[BinMonitor] ⚠️  BlynkLib not installed")
            if not self.blynk_token:
                print("[BinMonitor] ⚠️  Blynk token not configured")
            print("[BinMonitor] → Continuing without Blynk cloud reporting...")
        
        print("[BinMonitor] → Calibration:")
        print(f"[BinMonitor]   • Empty: {self.empty_distance} cm (0% full)")
        print(f"[BinMonitor]   • Full: {self.full_distance} cm (100% full)")
        print(f"[BinMonitor]   • Threshold: {self.full_threshold}% (bin considered full)")
        print("[BinMonitor] ✓ Initialization complete\n")
    
    def _get_distance_cm(self, sensor):
        """
        Get distance from ultrasonic sensor in centimeters
        
        Args:
            sensor: DistanceSensor object
            
        Returns:
            float: Distance in cm, or None if error
        """
        if sensor is None:
            return None
        
        try:
            # gpiozero returns distance in meters
            return sensor.distance * 100
        except Exception as e:
            print(f"[BinMonitor] ⚠️  Sensor read error: {e}")
            return None
    
    def _map_to_percentage(self, distance_cm):
        """
        Convert distance (cm) to fill percentage
        
        Args:
            distance_cm: Measured distance in cm
            
        Returns:
            float: Fill percentage (0-100), clamped
        """
        if distance_cm is None:
            return 0.0
        
        # Validate reading
        if distance_cm > self.empty_distance + 5 or distance_cm < self.full_distance - 5:
            # Out of range - likely invalid reading
            return 0.0
        
        # Calculate percentage
        total_range = self.empty_distance - self.full_distance
        distance_from_bottom = self.empty_distance - distance_cm
        percentage = (distance_from_bottom / total_range) * 100
        
        # Clamp to 0-100
        return max(0, min(100, percentage))
    
    def _monitoring_loop(self):
        """Background thread for continuous monitoring"""
        print("[BinMonitor] 🔄 Monitoring thread started")
        
        while not self.stop_flag.is_set():
            try:
                # Run Blynk event loop (non-blocking)
                if self.blynk:
                    self.blynk.run()
                
                # Read sensors
                distance_a = self._get_distance_cm(self.sensor_bin_a)
                distance_b = self._get_distance_cm(self.sensor_bin_b)
                
                # Convert to percentage
                level_a = self._map_to_percentage(distance_a)
                level_b = self._map_to_percentage(distance_b)
                
                # Update with thread safety
                with self.data_lock:
                    self.bin_a_level = level_a
                    self.bin_b_level = level_b
                    self.bin_a_distance = distance_a
                    self.bin_b_distance = distance_b
                    self.last_update_time = time.time()
                
                # Log readings (verbose mode)
                if getattr(config, 'BIN_MONITOR_VERBOSE', False):
                    print(f"[BinMonitor] BIN A: {distance_a:.1f}cm → {level_a:.1f}% | BIN B: {distance_b:.1f}cm → {level_b:.1f}%")
                
                # Send to Blynk
                if self.blynk:
                    try:
                        self.blynk.virtual_write(self.blynk_vpin_bin_a, level_a)
                        self.blynk.virtual_write(self.blynk_vpin_bin_b, level_b)
                    except Exception as e:
                        print(f"[BinMonitor] ⚠️  Blynk write error: {e}")
                
                # Log to Database (less frequent than Blynk)
                current_time = time.time()
                if self.database_service and self.device_id:
                    if (current_time - self.last_db_log_time) >= self.db_log_interval:
                        try:
                            # Get GPS location if available
                            latitude = None
                            longitude = None
                            if self.location_service:
                                location = self.location_service.get_location()
                                if location:
                                    latitude = location.get('latitude')
                                    longitude = location.get('longitude')
                            
                            # Insert to database
                            success = self.database_service.insert_bin_capacity_log(
                                device_id=self.device_id,
                                bin_a_level=level_a,
                                bin_a_distance=distance_a,
                                bin_b_level=level_b,
                                bin_b_distance=distance_b,
                                latitude=latitude,
                                longitude=longitude,
                                warning_threshold=self.warning_threshold,
                                full_threshold=self.full_threshold
                            )
                            
                            if success:
                                self.last_db_log_time = current_time
                                if getattr(config, 'BIN_MONITOR_VERBOSE', False):
                                    print(f"[BinMonitor] ✓ Logged to database")
                        except Exception as e:
                            print(f"[BinMonitor] ⚠️  Database log error: {e}")
                
                # Wait before next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"[BinMonitor] ❌ Error in monitoring loop: {e}")
                time.sleep(1)  # Prevent tight loop on error
        
        print("[BinMonitor] 🛑 Monitoring thread stopped")
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        if self.is_active:
            print("[BinMonitor] ⚠️  Already monitoring")
            return
        
        if self.platform != 'rpi' or not self.enable_blynk:
            print("[BinMonitor] ℹ️  Monitoring disabled (simulation mode or config)")
            return
        
        if self.sensor_bin_a is None and self.sensor_bin_b is None:
            print("[BinMonitor] ⚠️  No sensors available - monitoring disabled")
            return
        
        print("[BinMonitor] ▶️  Starting bin capacity monitoring...")
        self.stop_flag.clear()
        self.is_active = True
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="BinMonitor"
        )
        self.monitoring_thread.start()
        
        print("[BinMonitor] ✓ Monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring thread"""
        if not self.is_active:
            return
        
        print("[BinMonitor] ⏹️  Stopping bin capacity monitoring...")
        self.stop_flag.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=3.0)
        
        self.is_active = False
        print("[BinMonitor] ✓ Monitoring stopped")
    
    def get_bin_level(self, bin_name):
        """
        Get current fill level for a specific bin
        
        Args:
            bin_name: 'A' or 'B' (case-insensitive)
            
        Returns:
            float: Fill percentage (0-100)
        """
        with self.data_lock:
            if bin_name.upper() == 'A':
                return self.bin_a_level
            elif bin_name.upper() == 'B':
                return self.bin_b_level
            else:
                return 0.0
    
    def is_bin_full(self, bin_name):
        """
        Check if a bin is considered full
        
        Args:
            bin_name: 'A' or 'B' (case-insensitive)
            
        Returns:
            bool: True if bin is full (>= threshold)
        """
        level = self.get_bin_level(bin_name)
        return level >= self.full_threshold
    
    def get_status_dict(self):
        """
        Get complete status as dictionary
        
        Returns:
            dict: Status information
        """
        with self.data_lock:
            return {
                'bin_a_level': self.bin_a_level,
                'bin_b_level': self.bin_b_level,
                'bin_a_full': self.bin_a_level >= self.full_threshold,
                'bin_b_full': self.bin_b_level >= self.full_threshold,
                'last_update': self.last_update_time,
                'monitoring_active': self.is_active
            }
    
    def cleanup(self):
        """Cleanup resources"""
        print("\n[BinMonitor] 🛑 Shutting down...")
        
        # Stop monitoring thread
        self.stop_monitoring()
        
        # Close sensors
        if self.sensor_bin_a:
            try:
                self.sensor_bin_a.close()
            except Exception:
                pass
        
        if self.sensor_bin_b:
            try:
                self.sensor_bin_b.close()
            except Exception:
                pass
        
        print("[BinMonitor] ✓ Cleanup complete")


# Testing function
def test_bin_monitor():
    """Test bin monitoring system"""
    print("\n" + "="*60)
    print("BIN CAPACITY MONITOR TEST")
    print("="*60)
    
    monitor = BinMonitor(enable_blynk=True)
    
    try:
        monitor.start_monitoring()
        
        print("\nMonitoring for 30 seconds... (Press Ctrl+C to stop)")
        print("Place objects in/out of bins to see level changes\n")
        
        for i in range(30):
            time.sleep(1)
            status = monitor.get_status_dict()
            
            print(f"\r[{i+1:2d}s] BIN A: {status['bin_a_level']:5.1f}% {'🔴 FULL' if status['bin_a_full'] else '🟢 OK'} | "
                  f"BIN B: {status['bin_b_level']:5.1f}% {'🔴 FULL' if status['bin_b_full'] else '🟢 OK'}", end='')
        
        print("\n\n✅ Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    finally:
        monitor.cleanup()


if __name__ == "__main__":
    test_bin_monitor()
