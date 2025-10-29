"""
Location Service for OrangeBox
Handles GPS data collection from serial GNSS module

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

import time
import threading
import subprocess
from datetime import datetime
from typing import Optional, Tuple, Dict


class LocationService:
    """
    Service untuk mendapatkan lokasi (latitude, longitude) dari device.
    Support untuk Raspberry Pi (via GPS hardware) dan Mac (via simulasi/mock).
    """
    
    def __init__(self, platform: str = 'mac', mock_location: Optional[Tuple[float, float]] = None):
        """
        Inisialisasi LocationService.
        
        Args:
            platform: 'rpi' untuk Raspberry Pi, 'mac' untuk macOS (default)
            mock_location: Tuple (latitude, longitude) untuk simulasi di Mac
                          Default: Jakarta (-6.2088, 106.8456)
        """
        self.platform = platform
        self.current_location = None
        self.last_update_time = 0
        self.is_running = False
        self.update_thread = None
        self.lock = threading.Lock()
        
        # Default mock location (Jakarta)
        if mock_location is None:
            self.mock_location = (-6.2088, 106.8456)
        else:
            self.mock_location = mock_location
        
        # GPS device path untuk RPi
        self.gps_device = "/dev/ttyAMA0"  # Serial port untuk GPS module
        self.gps_baudrate = 9600
        
        print(f"[LocationService] Initialized for platform: {platform}")
        print(f"[LocationService] Mock location: {self.mock_location}")
    
    def get_location(self) -> Optional[Dict]:
        """
        Dapatkan lokasi saat ini.
        
        Returns:
            Dictionary dengan format:
            {
                'latitude': -6.2088,
                'longitude': 106.8456,
                'accuracy': 10.0,  # meters (hanya untuk real GPS)
                'timestamp': '2025-10-23T14:30:45',
                'source': 'gps' atau 'mock'
            }
            atau None jika gagal
        """
        with self.lock:
            if self.current_location is None:
                # Coba fetch lokasi sekali
                location = self._fetch_location()
                if location:
                    self.current_location = location
                    self.last_update_time = time.time()
            
            return self.current_location
    
    def _fetch_location(self) -> Optional[Dict]:
        """
        Internal method untuk fetch lokasi dari device.
        """
        if self.platform == 'rpi':
            return self._fetch_location_rpi()
        else:  # mac atau platform lainnya
            return self._fetch_location_mock()
    
    def _fetch_location_rpi(self) -> Optional[Dict]:
        """
        Fetch lokasi dari Raspberry Pi dengan GPS module.
        Mendukung:
        1. GPSD daemon (recommended) - via gpspipe
        2. Direct serial read (fallback) - via pynmea2
        
        Modul GPS yang didukung:
        - NEO-6M, NEO-7M, NEO-8M, NEO-9M (U-blox)
        - GT-U7, GT-U10 (GlobalTop) 
        - PA1010D (Adafruit)
        """
        import config
        
        use_gpsd = getattr(config, 'GPS_USE_GPSD', True)
        
        if use_gpsd:
            return self._fetch_via_gpsd()
        else:
            return self._fetch_via_serial()
    
    def _fetch_via_gpsd(self) -> Optional[Dict]:
        """
        Fetch GPS data via GPSD daemon (recommended method).
        GPSD harus sudah running: sudo systemctl start gpsd
        """
        try:
            # Cek apakah GPSD service berjalan
            result = subprocess.run(
                ['systemctl', 'is-active', 'gpsd'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode != 0:
                print("[LocationService] GPSD service not running. Start with: sudo systemctl start gpsd")
                return None
            
            # Get GPS data via gpspipe (read 5 lines untuk dapat TPV message)
            result = subprocess.run(
                ['gpspipe', '-w', '-n', '5'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"[LocationService] gpspipe error: {result.stderr}")
                return None
            
            # Parse setiap line untuk cari TPV message
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                    
                try:
                    gps_data = json.loads(line)
                    
                    # TPV = Time-Position-Velocity (contains lat/lon)
                    if gps_data.get('class') == 'TPV':
                        lat = gps_data.get('lat')
                        lon = gps_data.get('lon')
                        mode = gps_data.get('mode', 0)  # 0=no fix, 2=2D, 3=3D
                        
                        # Validate fix
                        if lat is None or lon is None or mode < 2:
                            continue
                        
                        accuracy = gps_data.get('eph', None)  # Estimated Position Error (horizontal)
                        
                        if lat is not None and lon is not None:
                            return {
                                'latitude': lat,
                                'longitude': lon,
                                'accuracy': accuracy,
                                'timestamp': datetime.now().isoformat(),
                                'source': 'gps'
                            }
                except json.JSONDecodeError:
                    pass
            
            print("[LocationService] No valid GPS fix from GPSD")
            return None
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"[LocationService] GPSD error: {e}")
            return None
    
    def _fetch_via_serial(self) -> Optional[Dict]:
        """
        Fetch GPS data via direct serial port read (fallback method).
        Membaca NMEA sentences dari GPS module.
        Requires: pynmea2 library (pip install pynmea2)
        """
        import config
        
        try:
            import serial
            import pynmea2
        except ImportError:
            print("[LocationService] Missing libraries: pip install pyserial pynmea2")
            return None
        
        serial_port = getattr(config, 'GPS_SERIAL_PORT', '/dev/serial0')
        baudrate = getattr(config, 'GPS_BAUDRATE', 9600)
        timeout = getattr(config, 'GPS_READ_TIMEOUT', 5)
        min_sats = getattr(config, 'GPS_MIN_SATELLITES', 4)
        
        try:
            # Open serial connection
            ser = serial.Serial(serial_port, baudrate, timeout=timeout)
            
            # Read lines hingga dapat valid fix (max 20 lines)
            for _ in range(20):
                line = ser.readline().decode('ascii', errors='ignore').strip()
                
                if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                    # GGA = Global Positioning System Fix Data
                    try:
                        msg = pynmea2.parse(line)
                        
                        # Validate fix quality and satellite count
                        if msg.gps_qual > 0 and msg.num_sats >= min_sats:
                            lat = msg.latitude
                            lon = msg.longitude
                            
                            if lat and lon:
                                # Calculate accuracy dari HDOP (Horizontal Dilution of Precision)
                                hdop = msg.horizontal_dil if hasattr(msg, 'horizontal_dil') else None
                                accuracy = hdop * 5 if hdop else None  # Rough estimate: HDOP * 5 meters
                                
                                ser.close()
                                return {
                                    'latitude': lat,
                                    'longitude': lon,
                                    'accuracy': accuracy,
                                    'timestamp': datetime.now().isoformat(),
                                    'source': 'gps',
                                    'satellites': msg.num_sats
                                }
                    except pynmea2.ParseError:
                        continue
            
            ser.close()
            print(f"[LocationService] No valid GPS fix from serial port (need {min_sats}+ satellites)")
            return None
            
        except serial.SerialException as e:
            print(f"[LocationService] Serial port error: {e}")
            print(f"[LocationService] Check: 1) GPS module connected, 2) UART enabled, 3) Port: {serial_port}")
            return None
        except Exception as e:
            print(f"[LocationService] Unexpected error reading serial GPS: {e}")
            return None
    
    def _fetch_location_mock(self) -> Dict:
        """
        Simulasi lokasi untuk testing di Mac.
        Bisa add random variation untuk lebih realistis.
        """
        import random
        
        # Add small random variation (±0.001 degrees ≈ ±100 meters)
        variation = 0.001
        lat = self.mock_location[0] + random.uniform(-variation, variation)
        lon = self.mock_location[1] + random.uniform(-variation, variation)
        
        return {
            'latitude': round(lat, 6),
            'longitude': round(lon, 6),
            'accuracy': random.uniform(5.0, 15.0),  # 5-15 meters (simulasi)
            'timestamp': datetime.now().isoformat(),
            'source': 'mock'
        }
    
    def start_background_update(self, update_interval: int = 300):
        """
        Mulai background thread untuk update lokasi secara berkala.
        
        Args:
            update_interval: Interval update dalam detik (default: 300 = 5 menit)
        """
        if self.is_running:
            print("[LocationService] Already running")
            return
        
        self.is_running = True
        self.update_interval = update_interval
        
        self.update_thread = threading.Thread(
            target=self._background_update_loop,
            daemon=True
        )
        self.update_thread.start()
        
        print(f"[LocationService] Background update started (interval: {update_interval}s)")
    
    def stop_background_update(self):
        """
        Stop background thread untuk update lokasi.
        """
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=2)
        
        print("[LocationService] Background update stopped")
    
    def _background_update_loop(self):
        """
        Loop untuk background update lokasi.
        """
        while self.is_running:
            try:
                new_location = self._fetch_location()
                
                if new_location:
                    with self.lock:
                        self.current_location = new_location
                        self.last_update_time = time.time()
                    
                    print(f"[LocationService] Location updated: "
                          f"{new_location['latitude']:.4f}, "
                          f"{new_location['longitude']:.4f} "
                          f"(source: {new_location['source']})")
                else:
                    print("[LocationService] Failed to fetch location")
                
                # Wait untuk next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"[LocationService] Error in background update: {e}")
                time.sleep(self.update_interval)
    
    def get_location_info_string(self) -> str:
        """
        Dapatkan string informasi lokasi untuk display.
        
        Returns:
            String format: "📍 -6.2088°, 106.8456° (Accuracy: 10m)"
        """
        location = self.get_location()
        
        if location is None:
            return "📍 Location: Unavailable"
        
        lat = location['latitude']
        lon = location['longitude']
        source_icon = "🛰️" if location['source'] == 'gps' else "📱"
        
        info = f"{source_icon} {lat:.4f}°, {lon:.4f}°"
        
        if location.get('accuracy'):
            info += f" (±{location['accuracy']:.1f}m)"
        
        return info
    
    def save_location_to_file(self, filepath: str = "location_log.jsonl"):
        """
        Save lokasi saat ini ke file (append mode - JSONL format).
        
        Args:
            filepath: Path file untuk save (relative atau absolute)
        """
        location = self.get_location()
        
        if location is None:
            return False
        
        try:
            # Append location ke file (JSONL - JSON Lines format)
            with open(filepath, 'a') as f:
                f.write(json.dumps(location) + '\n')
            
            print(f"[LocationService] Location saved to {filepath}")
            return True
            
        except Exception as e:
            print(f"[LocationService] Error saving location: {e}")
            return False
    
    def get_last_update_age(self) -> float:
        """
        Dapatkan age dari last location update dalam detik.
        
        Returns:
            Detik sejak last update (0 jika belum pernah update)
        """
        if self.last_update_time == 0:
            return float('inf')
        
        return time.time() - self.last_update_time
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Hitung jarak Haversine antara dua koordinat (dalam kilometer).
        
        Args:
            lat1, lon1: Koordinat pertama
            lat2, lon2: Koordinat kedua
        
        Returns:
            Jarak dalam kilometer
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r
    
    def get_timezone_from_location(self) -> Optional[str]:
        """
        Get timezone dari lokasi saat ini (memerlukan timezonefinder).
        Ini optional - hanya jika library tersedia.
        
        Returns:
            String timezone (e.g., 'Asia/Jakarta') atau None
        """
        try:
            from timezonefinder import TimezoneFinder
            
            location = self.get_location()
            if location is None:
                return None
            
            tf = TimezoneFinder()
            tz = tf.timezone_at(
                lat=location['latitude'],
                lng=location['longitude']
            )
            
            return tz
            
        except ImportError:
            # timezonefinder not installed
            return None
        except Exception as e:
            print(f"[LocationService] Error getting timezone: {e}")
            return None


# Test function
def main():
    """Test function untuk LocationService."""
    import platform as sys_platform
    
    print("Testing LocationService...")
    print(f"System Platform: {sys_platform.system()}")
    
    # Determine platform
    if sys_platform.system() == 'Darwin':  # macOS
        plat = 'mac'
    elif sys_platform.system() == 'Linux':
        plat = 'rpi'
    else:
        plat = 'mac'
    
    # Create service
    service = LocationService(platform=plat)
    
    # Get single location
    print("\n1. Single location fetch:")
    loc = service.get_location()
    if loc:
        print(f"   Location: {service.get_location_info_string()}")
        print(f"   Full data: {loc}")
    
    # Test background update
    print("\n2. Starting background update (10 second interval for testing)...")
    service.start_background_update(update_interval=10)
    
    # Wait dan collect beberapa updates
    for i in range(3):
        time.sleep(11)
        loc = service.get_location()
        if loc:
            print(f"   Update {i+1}: {service.get_location_info_string()}")
    
    # Stop background update
    service.stop_background_update()
    
    # Test distance calculation
    print("\n3. Distance calculation test:")
    jakarta = (-6.2088, 106.8456)
    bandung = (-6.9175, 107.6019)
    distance = LocationService.calculate_distance(
        jakarta[0], jakarta[1],
        bandung[0], bandung[1]
    )
    print(f"   Distance Jakarta-Bandung: {distance:.2f} km")
    
    print("\n✅ LocationService test complete!")


if __name__ == "__main__":
    main()
