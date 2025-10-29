"""
Database Service Module
Modul untuk menyimpan data waste classification ke MySQL RDS (AWS).

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

import pymysql
import time
from typing import Dict, Optional, List
from datetime import datetime
from contextlib import contextmanager


class DatabaseService:
    """
    Service untuk menyimpan waste classification data ke MySQL database.
    Menyimpan: total sampah, lokasi geografis, jumlah organic/anorganic.
    """
    
    def __init__(self, host: str, user: str, password: str, database: str, port: int = 3306):
        """
        Inisialisasi DatabaseService.
        
        Args:
            host: MySQL RDS host
            user: Database username
            password: Database password
            database: Database name
            port: MySQL port (default: 3306)
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None
        
        print(f"[DatabaseService] Initialized for {host}")
        
        # Try to connect and create tables
        self._initialize_database()
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager untuk database connection.
        Automatically handle connection open/close.
        """
        conn = None
        try:
            conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            yield conn
        except Exception as e:
            print(f"[DatabaseService] Connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _initialize_database(self):
        """
        Create database and tables jika belum ada.
        """
        try:
            # First, connect without database to create it
            conn_no_db = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port,
                connect_timeout=30
            )
            try:
                with conn_no_db.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                conn_no_db.commit()
                print(f"[DatabaseService] Database '{self.database}' ready")
            finally:
                conn_no_db.close()
            
            # Now connect to the database and create tables
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Table: locations
                    # Menyimpan setiap update lokasi GPS
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS locations (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            timestamp DATETIME NOT NULL,
                            latitude DOUBLE NOT NULL,
                            longitude DOUBLE NOT NULL,
                            accuracy FLOAT,
                            device_id VARCHAR(100),
                            source VARCHAR(20),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_timestamp (timestamp),
                            INDEX idx_device (device_id),
                            INDEX idx_coords (latitude, longitude)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)
                    
                    # Table: analysis_results
                    # Menyimpan hasil analisa (klasifikasi) lengkap
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS analysis_results (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            timestamp DATETIME NOT NULL,
                            device_id VARCHAR(100),
                            label VARCHAR(20) NOT NULL,
                            confidence FLOAT NOT NULL,
                            organic_score FLOAT,
                            anorganic_score FLOAT,
                            bin_assignment VARCHAR(20),
                            bin_angle INT,
                            location_id INT,
                            latitude DOUBLE,
                            longitude DOUBLE,
                            location_accuracy FLOAT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL,
                            INDEX idx_timestamp (timestamp),
                            INDEX idx_device (device_id),
                            INDEX idx_label (label),
                            INDEX idx_bin (bin_assignment)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)
                    
                    # Table: waste_summary
                    # Menyimpan summary per session/device
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS waste_summary (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            session_start DATETIME NOT NULL,
                            session_end DATETIME,
                            device_id VARCHAR(100),
                            total_sorted INT DEFAULT 0,
                            organic_count INT DEFAULT 0,
                            anorganic_count INT DEFAULT 0,
                            latitude DOUBLE,
                            longitude DOUBLE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            INDEX idx_session (session_start),
                            INDEX idx_device (device_id)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)
                    
                conn.commit()
                print("[DatabaseService] Database tables initialized successfully")
                
        except Exception as e:
            print(f"[DatabaseService] Error initializing database: {e}")
            raise
    
    def insert_waste_record(self, label: str, confidence: float, 
                           latitude: Optional[float] = None,
                           longitude: Optional[float] = None,
                           location_accuracy: Optional[float] = None,
                           device_id: Optional[str] = None) -> bool:
        """
        Insert single waste classification record.
        DEPRECATED: Use insert_analysis_result instead.
        This method kept for backward compatibility.
        
        Args:
            label: 'ORGANIC' atau 'ANORGANIC'
            confidence: Confidence score (0.0 - 1.0)
            latitude: GPS latitude (optional)
            longitude: GPS longitude (optional)
            location_accuracy: GPS accuracy dalam meter (optional)
            device_id: Unique device identifier (optional)
            
        Returns:
            True jika berhasil, False jika gagal
        """
        # Redirect to new method
        bin_assignment = "BIN A" if label == "ORGANIC" else "BIN B"
        bin_angle = 0 if label == "ORGANIC" else 90
        
        return self.insert_analysis_result(
            label=label,
            confidence=confidence,
            bin_assignment=bin_assignment,
            bin_angle=bin_angle,
            latitude=latitude,
            longitude=longitude,
            location_accuracy=location_accuracy,
            device_id=device_id
        )
    
    def insert_location(self, latitude: float, longitude: float,
                       accuracy: Optional[float] = None,
                       device_id: Optional[str] = None,
                       source: str = 'gps') -> Optional[int]:
        """
        Insert location record.
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            accuracy: GPS accuracy dalam meter
            device_id: Unique device identifier
            source: 'gps' atau 'mock'
            
        Returns:
            Location ID jika berhasil, None jika gagal
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO locations
                        (timestamp, latitude, longitude, accuracy, device_id, source)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        datetime.now(),
                        latitude,
                        longitude,
                        accuracy,
                        device_id,
                        source
                    ))
                    conn.commit()
                    
                    # Get inserted location ID
                    location_id = cursor.lastrowid
                    print(f"[DatabaseService] Location recorded: ({latitude:.4f}, {longitude:.4f}) - ID: {location_id}")
                    return location_id
                    
        except Exception as e:
            print(f"[DatabaseService] Error inserting location: {e}")
            return None
    
    def insert_analysis_result(self, label: str, confidence: float,
                              bin_assignment: str, bin_angle: int,
                              latitude: Optional[float] = None,
                              longitude: Optional[float] = None,
                              location_accuracy: Optional[float] = None,
                              device_id: Optional[str] = None,
                              location_id: Optional[int] = None) -> bool:
        """
        Insert analysis result (klasifikasi) lengkap.
        
        Args:
            label: 'ORGANIC' atau 'ANORGANIC'
            confidence: Confidence score (0.0 - 1.0)
            bin_assignment: 'BIN A' atau 'BIN B'
            bin_angle: Servo angle (0 untuk BIN A, 90 untuk BIN B)
            latitude: GPS latitude (optional)
            longitude: GPS longitude (optional)
            location_accuracy: GPS accuracy dalam meter (optional)
            device_id: Unique device identifier (optional)
            location_id: Foreign key ke locations table (optional)
            
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Parse all_scores dari confidence
                    if label == 'ORGANIC':
                        organic_score = confidence
                        anorganic_score = 1.0 - confidence
                    else:
                        organic_score = 1.0 - confidence
                        anorganic_score = confidence
                    
                    sql = """
                        INSERT INTO analysis_results
                        (timestamp, device_id, label, confidence, organic_score, anorganic_score,
                         bin_assignment, bin_angle, location_id, latitude, longitude, location_accuracy)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        datetime.now(),
                        device_id,
                        label,
                        confidence,
                        organic_score,
                        anorganic_score,
                        bin_assignment,
                        bin_angle,
                        location_id,
                        latitude,
                        longitude,
                        location_accuracy
                    ))
                    conn.commit()
                    
            print(f"[DatabaseService] Analysis recorded: {label} ({confidence:.2%}) -> {bin_assignment} ({bin_angle}°)")
            return True
            
        except Exception as e:
            print(f"[DatabaseService] Error inserting analysis result: {e}")
            return False
    
    def update_session_summary(self, device_id: str,
                               total_sorted: int,
                               organic_count: int,
                               anorganic_count: int,
                               latitude: Optional[float] = None,
                               longitude: Optional[float] = None) -> bool:
        """
        Update atau insert summary untuk session saat ini.
        
        Args:
            device_id: Unique device identifier
            total_sorted: Total sampah yang disortir
            organic_count: Jumlah organik
            anorganic_count: Jumlah anorganik
            latitude: Current GPS latitude (optional)
            longitude: Current GPS longitude (optional)
            
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if session already exists for today
                    cursor.execute("""
                        SELECT id, session_start FROM waste_summary
                        WHERE device_id = %s 
                        AND DATE(session_start) = CURDATE()
                        ORDER BY session_start DESC
                        LIMIT 1
                    """, (device_id,))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing session
                        sql = """
                            UPDATE waste_summary 
                            SET session_end = %s,
                                total_sorted = %s,
                                organic_count = %s,
                                anorganic_count = %s,
                                latitude = %s,
                                longitude = %s
                            WHERE id = %s
                        """
                        cursor.execute(sql, (
                            datetime.now(),
                            total_sorted,
                            organic_count,
                            anorganic_count,
                            latitude,
                            longitude,
                            existing['id']
                        ))
                    else:
                        # Insert new session
                        sql = """
                            INSERT INTO waste_summary
                            (session_start, session_end, device_id, 
                             total_sorted, organic_count, anorganic_count,
                             latitude, longitude)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql, (
                            datetime.now(),
                            datetime.now(),
                            device_id,
                            total_sorted,
                            organic_count,
                            anorganic_count,
                            latitude,
                            longitude
                        ))
                    
                    conn.commit()
                    
            return True
            
        except Exception as e:
            print(f"[DatabaseService] Error updating summary: {e}")
            return False
    
    def get_today_summary(self, device_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get summary untuk hari ini.
        
        Args:
            device_id: Filter by device (optional)
            
        Returns:
            Dictionary dengan summary data atau None
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    if device_id:
                        sql = """
                            SELECT * FROM waste_summary
                            WHERE device_id = %s 
                            AND DATE(session_start) = CURDATE()
                            ORDER BY session_start DESC
                            LIMIT 1
                        """
                        cursor.execute(sql, (device_id,))
                    else:
                        sql = """
                            SELECT * FROM waste_summary
                            WHERE DATE(session_start) = CURDATE()
                            ORDER BY session_start DESC
                            LIMIT 1
                        """
                        cursor.execute(sql)
                    
                    return cursor.fetchone()
                    
        except Exception as e:
            print(f"[DatabaseService] Error fetching summary: {e}")
            return None
    
    def get_total_stats(self, device_id: Optional[str] = None) -> Dict:
        """
        Get total statistics (all time).
        
        Args:
            device_id: Filter by device (optional)
            
        Returns:
            Dictionary dengan total stats
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    if device_id:
                        sql = """
                            SELECT 
                                COUNT(*) as total_records,
                                SUM(CASE WHEN label = 'ORGANIC' THEN 1 ELSE 0 END) as organic_count,
                                SUM(CASE WHEN label = 'ANORGANIC' THEN 1 ELSE 0 END) as anorganic_count,
                                AVG(confidence) as avg_confidence
                            FROM analysis_results
                            WHERE device_id = %s
                        """
                        cursor.execute(sql, (device_id,))
                    else:
                        sql = """
                            SELECT 
                                COUNT(*) as total_records,
                                SUM(CASE WHEN label = 'ORGANIC' THEN 1 ELSE 0 END) as organic_count,
                                SUM(CASE WHEN label = 'ANORGANIC' THEN 1 ELSE 0 END) as anorganic_count,
                                AVG(confidence) as avg_confidence
                            FROM analysis_results
                        """
                        cursor.execute(sql)
                    
                    result = cursor.fetchone()
                    return result if result else {}
                    
        except Exception as e:
            print(f"[DatabaseService] Error fetching stats: {e}")
            return {}
    
    def get_recent_analysis(self, limit: int = 10, device_id: Optional[str] = None) -> List[Dict]:
        """
        Get recent analysis results.
        
        Args:
            limit: Number of records to fetch
            device_id: Filter by device (optional)
            
        Returns:
            List of analysis result dictionaries
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    if device_id:
                        sql = """
                            SELECT 
                                ar.*,
                                l.latitude as loc_latitude,
                                l.longitude as loc_longitude,
                                l.accuracy as loc_accuracy
                            FROM analysis_results ar
                            LEFT JOIN locations l ON ar.location_id = l.id
                            WHERE ar.device_id = %s
                            ORDER BY ar.timestamp DESC
                            LIMIT %s
                        """
                        cursor.execute(sql, (device_id, limit))
                    else:
                        sql = """
                            SELECT 
                                ar.*,
                                l.latitude as loc_latitude,
                                l.longitude as loc_longitude,
                                l.accuracy as loc_accuracy
                            FROM analysis_results ar
                            LEFT JOIN locations l ON ar.location_id = l.id
                            ORDER BY ar.timestamp DESC
                            LIMIT %s
                        """
                        cursor.execute(sql, (limit,))
                    
                    return cursor.fetchall()
                    
        except Exception as e:
            print(f"[DatabaseService] Error fetching analysis records: {e}")
            return []
    
    def get_recent_locations(self, limit: int = 10, device_id: Optional[str] = None) -> List[Dict]:
        """
        Get recent location records.
        
        Args:
            limit: Number of records to fetch
            device_id: Filter by device (optional)
            
        Returns:
            List of location dictionaries
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    if device_id:
                        sql = """
                            SELECT * FROM locations
                            WHERE device_id = %s
                            ORDER BY timestamp DESC
                            LIMIT %s
                        """
                        cursor.execute(sql, (device_id, limit))
                    else:
                        sql = """
                            SELECT * FROM locations
                            ORDER BY timestamp DESC
                            LIMIT %s
                        """
                        cursor.execute(sql, (limit,))
                    
                    return cursor.fetchall()
                    
        except Exception as e:
            print(f"[DatabaseService] Error fetching locations: {e}")
            return []
        """
        Get total statistics (all time).
        
        Args:
            device_id: Filter by device (optional)
            
        Returns:
            Dictionary dengan total stats
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    if device_id:
                        sql = """
                            SELECT 
                                COUNT(*) as total_records,
                                SUM(CASE WHEN label = 'ORGANIC' THEN 1 ELSE 0 END) as organic_count,
                                SUM(CASE WHEN label = 'ANORGANIC' THEN 1 ELSE 0 END) as anorganic_count,
                                AVG(confidence) as avg_confidence
                            FROM waste_records
                            WHERE device_id = %s
                        """
                        cursor.execute(sql, (device_id,))
                    else:
                        sql = """
                            SELECT 
                                COUNT(*) as total_records,
                                SUM(CASE WHEN label = 'ORGANIC' THEN 1 ELSE 0 END) as organic_count,
                                SUM(CASE WHEN label = 'ANORGANIC' THEN 1 ELSE 0 END) as anorganic_count,
                                AVG(confidence) as avg_confidence
                            FROM waste_records
                        """
                        cursor.execute(sql)
                    
                    result = cursor.fetchone()
                    return result if result else {}
                    
        except Exception as e:
            print(f"[DatabaseService] Error fetching stats: {e}")
            return {}
    
    def get_recent_records(self, limit: int = 10, device_id: Optional[str] = None) -> List[Dict]:
        """
        Get recent waste records.
        
        Args:
            limit: Number of records to fetch
            device_id: Filter by device (optional)
            
        Returns:
            List of record dictionaries
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    if device_id:
                        sql = """
                            SELECT * FROM waste_records
                            WHERE device_id = %s
                            ORDER BY timestamp DESC
                            LIMIT %s
                        """
                        cursor.execute(sql, (device_id, limit))
                    else:
                        sql = """
                            SELECT * FROM waste_records
                            ORDER BY timestamp DESC
                            LIMIT %s
                        """
                        cursor.execute(sql, (limit,))
                    
                    return cursor.fetchall()
                    
        except Exception as e:
            print(f"[DatabaseService] Error fetching records: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True jika connection berhasil, False jika gagal
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result:
                        print("[DatabaseService] Connection test: SUCCESS")
                        return True
            return False
        except Exception as e:
            print(f"[DatabaseService] Connection test: FAILED - {e}")
            return False
    
    # ============================================
    # MULTI-DEVICE QUERY METHODS
    # ============================================
    
    def get_all_devices(self) -> List[Dict]:
        """
        Get list of all devices yang pernah connect ke database.
        
        Returns:
            List of device info dictionaries
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT 
                            device_id,
                            COUNT(*) as record_count,
                            MIN(timestamp) as first_seen,
                            MAX(timestamp) as last_seen
                        FROM analysis_results
                        WHERE device_id IS NOT NULL
                        GROUP BY device_id
                        ORDER BY last_seen DESC
                    """
                    cursor.execute(sql)
                    return cursor.fetchall()
        except Exception as e:
            print(f"[DatabaseService] Error fetching devices: {e}")
            return []
    
    def get_today_summary_by_device(self, device_id: str) -> Optional[Dict]:
        """
        Get today's summary untuk device tertentu.
        
        Args:
            device_id: Device ID to filter
            
        Returns:
            Summary dictionary atau None
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT * FROM waste_summary
                        WHERE device_id = %s
                        AND DATE(session_start) = CURDATE()
                        ORDER BY session_start DESC
                        LIMIT 1
                    """
                    cursor.execute(sql, (device_id,))
                    return cursor.fetchone()
        except Exception as e:
            print(f"[DatabaseService] Error fetching today's summary: {e}")
            return None
    
    def get_stats_by_device(self, device_id: str) -> Optional[Dict]:
        """
        Get statistics untuk device tertentu.
        
        Args:
            device_id: Device ID to filter
            
        Returns:
            Stats dictionary atau None
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT 
                            COUNT(*) as total_records,
                            SUM(CASE WHEN label = 'ORGANIC' THEN 1 ELSE 0 END) as organic_count,
                            SUM(CASE WHEN label = 'ANORGANIC' THEN 1 ELSE 0 END) as anorganic_count,
                            AVG(confidence) as avg_confidence
                        FROM analysis_results
                        WHERE device_id = %s
                    """
                    cursor.execute(sql, (device_id,))
                    return cursor.fetchone()
        except Exception as e:
            print(f"[DatabaseService] Error fetching stats: {e}")
            return None
    
    def get_device_history(self, device_id: str, days: int = 7) -> List[Dict]:
        """
        Get history untuk device tertentu dalam X hari terakhir.
        
        Args:
            device_id: Device ID to filter
            days: Number of days to look back
            
        Returns:
            List of analysis results
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT *
                        FROM analysis_results
                        WHERE device_id = %s
                        AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                        ORDER BY timestamp DESC
                    """
                    cursor.execute(sql, (device_id, days))
                    return cursor.fetchall()
        except Exception as e:
            print(f"[DatabaseService] Error fetching device history: {e}")
            return []
    
    def get_device_daily_stats(self, device_id: str, days: int = 30) -> List[Dict]:
        """
        Get daily statistics untuk device tertentu.
        Useful untuk dashboard/charts.
        
        Args:
            device_id: Device ID to filter
            days: Number of days to look back
            
        Returns:
            List of daily stats
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT 
                            DATE(timestamp) as date,
                            COUNT(*) as total_count,
                            SUM(CASE WHEN label = 'ORGANIC' THEN 1 ELSE 0 END) as organic_count,
                            SUM(CASE WHEN label = 'ANORGANIC' THEN 1 ELSE 0 END) as anorganic_count,
                            AVG(confidence) as avg_confidence
                        FROM analysis_results
                        WHERE device_id = %s
                        AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                        GROUP BY DATE(timestamp)
                        ORDER BY date DESC
                    """
                    cursor.execute(sql, (device_id, days))
                    return cursor.fetchall()
        except Exception as e:
            print(f"[DatabaseService] Error fetching daily stats: {e}")
            return []


# Test function
def main():
    """Test DatabaseService with RDS."""
    print("Testing DatabaseService with MySQL RDS...")
    print("="*60)
    
    # RDS credentials (from user)
    db_config = {
        'host': 'orangebox.csxenzvznekp.ap-southeast-3.rds.amazonaws.com',
        'user': 'orangeboxmaster',
        'password': 'wpiGf0AtihhN2D3AjXUaSl',
        'database': 'orangebox',
        'port': 3306
    }
    
    try:
        # Initialize service
        print("\n1. Initializing DatabaseService...")
        db = DatabaseService(**db_config)
        
        # Test connection
        print("\n2. Testing connection...")
        if not db.test_connection():
            print("Connection failed! Check credentials and network.")
            return
        
        # Insert test record
        print("\n3. Inserting test location...")
        location_id = db.insert_location(
            latitude=-6.2088,
            longitude=106.8456,
            accuracy=10.5,
            device_id='test-device-001',
            source='gps'
        )
        print(f"   Location ID: {location_id}")
        
        print("\n4. Inserting test analysis result (ORGANIC)...")
        success = db.insert_analysis_result(
            label='ORGANIC',
            confidence=0.95,
            bin_assignment='BIN A',
            bin_angle=0,
            latitude=-6.2088,
            longitude=106.8456,
            location_accuracy=10.5,
            device_id='test-device-001',
            location_id=location_id
        )
        print(f"   Insert result: {'SUCCESS' if success else 'FAILED'}")
        
        # Insert another location
        print("\n5. Inserting second test location...")
        location_id2 = db.insert_location(
            latitude=-6.2089,
            longitude=106.8457,
            accuracy=12.3,
            device_id='test-device-001',
            source='gps'
        )
        print(f"   Location ID: {location_id2}")
        
        # Insert another analysis result
        print("\n6. Inserting test analysis result (ANORGANIC)...")
        success = db.insert_analysis_result(
            label='ANORGANIC',
            confidence=0.88,
            bin_assignment='BIN B',
            bin_angle=90,
            latitude=-6.2089,
            longitude=106.8457,
            location_accuracy=12.3,
            device_id='test-device-001',
            location_id=location_id2
        )
        print(f"   Insert result: {'SUCCESS' if success else 'FAILED'}")
        
        # Update session summary
        print("\n7. Updating session summary...")
        success = db.update_session_summary(
            device_id='test-device-001',
            total_sorted=2,
            organic_count=1,
            anorganic_count=1,
            latitude=-6.2088,
            longitude=106.8456
        )
        print(f"   Update result: {'SUCCESS' if success else 'FAILED'}")
        
        # Get today summary
        print("\n8. Fetching today's summary...")
        summary = db.get_today_summary('test-device-001')
        if summary:
            print(f"   Total Sorted: {summary['total_sorted']}")
            print(f"   Organic: {summary['organic_count']}")
            print(f"   Anorganic: {summary['anorganic_count']}")
            print(f"   Location: ({summary['latitude']}, {summary['longitude']})")
        
        # Get total stats
        print("\n7. Fetching total statistics...")
        stats = db.get_total_stats('test-device-001')
        if stats:
            print(f"   Total Records: {stats.get('total_records', 0)}")
            print(f"   Organic: {stats.get('organic_count', 0)}")
            print(f"   Anorganic: {stats.get('anorganic_count', 0)}")
            print(f"   Avg Confidence: {stats.get('avg_confidence', 0):.2%}")
        
        # Get recent analysis results
        print("\n8. Fetching recent analysis results...")
        records = db.get_recent_analysis(limit=5, device_id='test-device-001')
        print(f"   Found {len(records)} records:")
        for i, rec in enumerate(records, 1):
            print(f"   {i}. {rec['label']} ({rec['confidence']:.2%}) -> {rec['bin_assignment']} at {rec['timestamp']}")
        
        # Get recent locations
        print("\n9. Fetching recent locations...")
        locations = db.get_recent_locations(limit=5, device_id='test-device-001')
        print(f"   Found {len(locations)} locations:")
        for i, loc in enumerate(locations, 1):
            print(f"   {i}. ({loc['latitude']:.6f}, {loc['longitude']:.6f}) - {loc['source']} at {loc['timestamp']}")
        
        print("\n" + "="*60)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
