-- ============================================
-- Tabel untuk Bin Capacity Logging
-- ============================================
-- Tabel ini menyimpan history level kapasitas tong sampah
-- untuk monitoring dan alerting saat tong penuh

CREATE TABLE IF NOT EXISTS `bin_capacity_logs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `device_id` VARCHAR(100) NOT NULL,
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  -- Bin A (Organic)
  `bin_a_level` DECIMAL(5,2) NOT NULL COMMENT 'Level BIN A dalam persen (0-100)',
  `bin_a_distance` DECIMAL(6,2) NULL COMMENT 'Jarak sensor ke permukaan sampah (cm)',
  `bin_a_status` ENUM('OK', 'WARNING', 'FULL') NOT NULL DEFAULT 'OK',
  
  -- Bin B (Anorganic)
  `bin_b_level` DECIMAL(5,2) NOT NULL COMMENT 'Level BIN B dalam persen (0-100)',
  `bin_b_distance` DECIMAL(6,2) NULL COMMENT 'Jarak sensor ke permukaan sampah (cm)',
  `bin_b_status` ENUM('OK', 'WARNING', 'FULL') NOT NULL DEFAULT 'OK',
  
  -- Metadata
  `location_latitude` DECIMAL(10,8) NULL COMMENT 'GPS latitude (jika GPS enabled)',
  `location_longitude` DECIMAL(11,8) NULL COMMENT 'GPS longitude (jika GPS enabled)',
  `notes` VARCHAR(255) NULL COMMENT 'Catatan tambahan (optional)',
  
  PRIMARY KEY (`id`),
  KEY `idx_device_timestamp` (`device_id`, `timestamp`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_bin_a_status` (`bin_a_status`),
  KEY `idx_bin_b_status` (`bin_b_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='History log kapasitas tong sampah untuk monitoring dan alerting';

-- ============================================
-- View untuk Monitoring Status Terkini
-- ============================================
-- View ini menampilkan status terkini dari setiap device

CREATE OR REPLACE VIEW `bin_capacity_current` AS
SELECT 
  bcl.device_id,
  bcl.timestamp AS last_update,
  bcl.bin_a_level,
  bcl.bin_a_status,
  bcl.bin_b_level,
  bcl.bin_b_status,
  bcl.location_latitude,
  bcl.location_longitude,
  CASE 
    WHEN bcl.bin_a_status = 'FULL' OR bcl.bin_b_status = 'FULL' THEN 'URGENT'
    WHEN bcl.bin_a_status = 'WARNING' OR bcl.bin_b_status = 'WARNING' THEN 'WARNING'
    ELSE 'OK'
  END AS overall_status,
  TIMESTAMPDIFF(MINUTE, bcl.timestamp, NOW()) AS minutes_since_update
FROM bin_capacity_logs bcl
INNER JOIN (
  SELECT device_id, MAX(timestamp) AS max_timestamp
  FROM bin_capacity_logs
  GROUP BY device_id
) latest ON bcl.device_id = latest.device_id 
        AND bcl.timestamp = latest.max_timestamp;

-- ============================================
-- View untuk Alert Tong Penuh
-- ============================================
-- View ini menampilkan device yang tong-nya penuh atau warning

CREATE OR REPLACE VIEW `bin_capacity_alerts` AS
SELECT 
  bcc.device_id,
  bcc.last_update,
  bcc.bin_a_level,
  bcc.bin_a_status,
  bcc.bin_b_level,
  bcc.bin_b_status,
  bcc.overall_status,
  bcc.minutes_since_update,
  bcc.location_latitude,
  bcc.location_longitude,
  CASE 
    WHEN bcc.overall_status = 'URGENT' THEN 
      CONCAT('🔴 Device ', bcc.device_id, ' has FULL bins! ',
             IF(bcc.bin_a_status='FULL', CONCAT('BIN A: ', bcc.bin_a_level, '% '), ''),
             IF(bcc.bin_b_status='FULL', CONCAT('BIN B: ', bcc.bin_b_level, '% '), ''))
    WHEN bcc.overall_status = 'WARNING' THEN 
      CONCAT('⚠️  Device ', bcc.device_id, ' bins approaching full! ',
             IF(bcc.bin_a_status='WARNING', CONCAT('BIN A: ', bcc.bin_a_level, '% '), ''),
             IF(bcc.bin_b_status='WARNING', CONCAT('BIN B: ', bcc.bin_b_level, '% '), ''))
    ELSE NULL
  END AS alert_message
FROM bin_capacity_current bcc
WHERE bcc.overall_status IN ('WARNING', 'URGENT')
ORDER BY 
  FIELD(bcc.overall_status, 'URGENT', 'WARNING'),
  bcc.minutes_since_update ASC;

-- ============================================
-- Stored Procedure: Get Device Bin Status
-- ============================================
-- Procedure untuk mendapatkan status bin dari device tertentu

DELIMITER $$

CREATE PROCEDURE IF NOT EXISTS `sp_get_bin_status`(
  IN p_device_id VARCHAR(100)
)
BEGIN
  SELECT 
    device_id,
    last_update,
    bin_a_level,
    bin_a_status,
    bin_b_level,
    bin_b_status,
    overall_status,
    minutes_since_update,
    location_latitude,
    location_longitude
  FROM bin_capacity_current
  WHERE device_id = p_device_id;
END$$

DELIMITER ;

-- ============================================
-- Stored Procedure: Get All Alerts
-- ============================================
-- Procedure untuk mendapatkan semua alert tong penuh

DELIMITER $$

CREATE PROCEDURE IF NOT EXISTS `sp_get_bin_alerts`()
BEGIN
  SELECT 
    device_id,
    last_update,
    bin_a_level,
    bin_a_status,
    bin_b_level,
    bin_b_status,
    overall_status,
    alert_message,
    minutes_since_update,
    location_latitude,
    location_longitude
  FROM bin_capacity_alerts;
END$$

DELIMITER ;

-- ============================================
-- Index untuk Performance
-- ============================================
-- Index tambahan untuk query performance

-- Index untuk query berdasarkan status
CREATE INDEX IF NOT EXISTS idx_bin_status_composite 
ON bin_capacity_logs(device_id, bin_a_status, bin_b_status, timestamp);

-- Index untuk query historical data
CREATE INDEX IF NOT EXISTS idx_device_date 
ON bin_capacity_logs(device_id, DATE(timestamp));

-- ============================================
-- Sample Queries untuk Monitoring
-- ============================================

-- Query 1: Status terkini semua device
-- SELECT * FROM bin_capacity_current;

-- Query 2: Alert tong penuh
-- SELECT * FROM bin_capacity_alerts;

-- Query 3: History 24 jam terakhir untuk device tertentu
-- SELECT timestamp, bin_a_level, bin_b_level 
-- FROM bin_capacity_logs 
-- WHERE device_id = 'YOUR_DEVICE_ID' 
--   AND timestamp >= NOW() - INTERVAL 24 HOUR
-- ORDER BY timestamp DESC;

-- Query 4: Rata-rata level per jam (untuk grafik)
-- SELECT 
--   DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00') AS hour,
--   AVG(bin_a_level) AS avg_bin_a,
--   AVG(bin_b_level) AS avg_bin_b
-- FROM bin_capacity_logs
-- WHERE device_id = 'YOUR_DEVICE_ID'
--   AND timestamp >= NOW() - INTERVAL 7 DAY
-- GROUP BY hour
-- ORDER BY hour;

-- Query 5: Deteksi tong yang perlu dikosongkan (penuh >1 jam)
-- SELECT 
--   device_id,
--   last_update,
--   bin_a_level,
--   bin_b_level,
--   minutes_since_update
-- FROM bin_capacity_current
-- WHERE (bin_a_status = 'FULL' OR bin_b_status = 'FULL')
--   AND minutes_since_update > 60
-- ORDER BY minutes_since_update DESC;
