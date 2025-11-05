"""
╔═══════════════════════════════════════════════════════════════╗
║                    ORANGEBOX - CONFIG FILE                    ║
║                   Pengaturan Utama Sistem                     ║
╚═══════════════════════════════════════════════════════════════╝

📋 FILE INI UNTUK APA?
   Semua pengaturan sistem ada di sini. Ubah nilai di file ini, 
   terus jalankan ulang program. Gampang!

🎯 YANG PENTING DIATUR:
   1. PLATFORM → 'mac' atau 'rpi' (baris ~22)
   2. SERVO → Derajat & pin/channel (mulai baris ~160)
   3. MODEL_PATH → Lokasi file model AI (baris ~40)

⚙️  PENGATURAN SERVO ADA DI:
   • Baris 160-230 → Setting pin, derajat, timing
   • Penjelasan lengkap ada di setiap bagian

🚀 CARA TEST:
   • Test servo: python3 scripts/test_servo.py
   • Lihat kamera: python3 main.py --test

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

# ============================================
# CAMERA CONFIGURATION
# ============================================

# PETUNJUK CEPAT (KAMERA)
# - Atur `PLATFORM` → 'mac' untuk laptop, 'rpi' untuk Raspberry Pi.
# - Di Raspberry Pi, kamera dipilih otomatis: PiCamera2 (jika ada) → USB webcam.
# - Mau manual? Jalankan `python3 main.py --camera 0` atau ubah `CAMERA_INDEX` di sini.
# - Cek perangkat kamera: `python3 -m src.core.camera_detector` (menampilkan daftar & pilihan otomatis).
# - Jika frame gelap/hitam di RPi, pastikan kamera aktif via `sudo raspi-config` (Interface → Camera) dan reboot.

# Platform yang digunakan
# Options: 'mac' atau 'rpi'
PLATFORM = 'mac'  # ← Ganti ke 'rpi' saat deploy ke Raspberry Pi

# Camera index (untuk webcam)
CAMERA_INDEX = 0  # 0 = internal, 1 = external webcam ← External webcam active

# ============================================
# UI SETTINGS
# ============================================

# Tampilan kamera bergaya (rounded cards, chips, logo) seperti di macOS mock
# Aktifkan di Raspberry Pi jika ingin UI selaras; nonaktifkan jika butuh performa maksimal
FANCY_UI = True  # Default: True; di RPi tetap bekerja, gunakan resolusi wajar

# ============================================
# MODEL CONFIGURATION
# ============================================

# Path ke model (relative dari project root)
MODEL_PATH = 'models/model.tflite'
LABELS_PATH = 'models/labels.txt'

# ============================================
# CLASSIFICATION SETTINGS
# ============================================

# Confidence threshold (0.0 - 1.0)
# For production we accept the binary boundary: 0.5
# This prevents the system from blocking on slightly-uncertain predictions
CONFIDENCE_THRESHOLD = 0.5  # Production: accept >=50%

# Motion detection threshold (pixels yang berubah untuk trigger)
# Semakin tinggi = hanya objek besar yang terdeteksi
# Semakin rendah = lebih sensitif (noise bisa trigger)
# Note: Untuk resolusi 160x120 = 19,200 pixels total
MOTION_THRESHOLD = 3000  # ~15% area berubah - hindari noise/shadow

# Stabilization frames (jumlah frame untuk konfirmasi objek stabil)
STABILIZATION_FRAMES = 5  # Lebih lama untuk hindari false positive

# Edge-trigger & hysteresis thresholds (small-res mask)
# Enter saat perubahan > ENTER, keluar saat < EXIT (EXIT < ENTER)
# Resolusi 160x120 = 19,200 pixels total
# BALANCE: Turunkan agar objek kecil/gerak minim tetap terpicu (MOG2+ROI membantu anti-bayangan)
MOTION_ENTER_THRESHOLD = 900   # ~4.7% area pada 160x120 - lebih sensitif
MOTION_EXIT_THRESHOLD = 450    # ~2.3% area - exit saat motion cukup mereda

# Berapa frame berturut-turut dibutuhkan untuk menganggap objek stabil/ada
MOTION_CONSECUTIVE_REQUIRED = 2  # 2 frame (60ms) agar responsif tanpa terlalu noisy

# Berapa frame 'still' untuk reset setelah cooldown
MOTION_STILL_FRAMES_RESET = 5  # Lebih cepat - 5 frame (150ms) untuk production

# =====================
# MORPHOLOGICAL FILTERING (Anti-Shadow)
# =====================
# Gunakan morphological operations untuk menghilangkan noise bayangan
ENABLE_MORPHOLOGICAL_FILTER = True
MORPH_KERNEL_SIZE = 5  # Kernel 5x5 untuk erosion/dilation lebih kuat anti-bayangan

# =====================
# BACKGROUND SUBTRACTOR (MOG2) - Anti-bayangan
# =====================
# Mengurangi sensitifitas terhadap perubahan cahaya/shadow
USE_MOG2 = True
MOG2_HISTORY = 300
MOG2_VAR_THRESHOLD = 16
MOG2_DETECT_SHADOWS = True  # Shadow akan ditandai 127 dan kita buang

# =====================
# STABILIZATION DELAY
# =====================
# Delay (detik) setelah objek terdeteksi SEBELUM mulai klasifikasi
# Beri waktu 4 detik untuk sampah jatuh dan tangan keluar dari area kamera
OBJECT_STABILIZATION_DELAY = 4.0  # 4 detik - hand-removal window
STABILIZATION_MAX_WAIT = 5.0      # Maks tunggu sebelum abort

# Cooldown (ms) setelah klasifikasi selesai - objek harus hilang dulu sebelum trigger lagi
# NOTE: Ini adalah MINIMUM cooldown. Actual cooldown akan lebih panjang jika servo sorting sedang berlangsung.
# Servo sorting duration ditambahkan secara otomatis di MainController berdasarkan SERVO_MOVEMENT_DURATION.
COOLDOWN_MS = 1500  # 1.5 detik - minimum cooldown sebelum motion bisa ditdeteksi lagi

# =====================
# SERVO MOVEMENT DURATION
# =====================
# Total durasi semua gerakan servo (Layer 1 + Layer 2) untuk urutan sorting lengkap.
# Ini mencakup: Layer 2 positioning + Layer 1 open + waste drop + Layer 1 close + Layer 2 reset
# Durasi ini DITAMBAHKAN ke COOLDOWN_MS agar pergerakan servo tidak terdeteksi sebagai objek baru
SERVO_MOVEMENT_DURATION = 3.5  # 3.5 detik - total durasi seluruh proses sorting

# =====================
# DISTANCE/NEARNESS GATING
# =====================
# Minimal luas ROI terhadap frame penuh agar dianggap "cukup dekat" untuk klasifikasi.
# Contoh: 0.10 = 10% dari area frame. Naikkan jika hanya ingin objek sangat dekat yang diproses.
MIN_ROI_AREA_RATIO = 0.03  # 3% area - deteksi objek kecil tetap lolos

# Threshold biner untuk frame difference (0-255). Lebih rendah = lebih sensitif
BINARY_DIFF_THRESHOLD = 18

# =====================
# DETECTION ROI (mask area deteksi)
# =====================
# Abaikan bagian atas frame tempat bayangan tangan sering muncul.
# 0.25 = abaikan 25% area teratas.
DETECTION_ROI_Y_START_RATIO = 0.25

# =====================
# COOLDOWN MODE
# =====================
# Jika True, cooldown selesai berdasarkan waktu saja (fixed time),
# tidak menunggu still frames.
FIXED_COOLDOWN_ONLY = True

# Setelah cooldown selesai, beri jeda singkat untuk menstabilkan background
# sehingga MOG2/absdiff tidak langsung memicu ghost detection.
REARM_MS = 600  # 0.6 detik re-arm background

# Opsional: estimasi jarak dengan asumsi pinhole camera (sederhana). Default off.
ENABLE_DISTANCE_ESTIMATION = False
# Jika ENABLE_DISTANCE_ESTIMATION=True, isi parameter berikut sesuai kalibrasi:
# - FOCAL_LENGTH_PX: panjang fokus dalam pixel (kalibrasi kamera)
# - KNOWN_OBJECT_HEIGHT_CM: tinggi referensi objek (cm) yang diharapkan di depan kamera
FOCAL_LENGTH_PX = 900.0
KNOWN_OBJECT_HEIGHT_CM = 10.0

# ============================================
# HARDWARE SETTINGS (Raspberry Pi)
# ============================================

# Proximity Sensor Configuration
# Set USE_PROXIMITY_SENSOR = False jika tidak menggunakan proximity sensor
# atau jika terjadi error "Cannot determine SOC peripheral base address" di RPi 5
USE_PROXIMITY_SENSOR = False  # Default: False (disable untuk RPi 5 compatibility)
PROXIMITY_SENSOR_PIN = 17      # GPIO Pin untuk proximity sensor (jika enabled)

# ============================================
# SERVO CONFIGURATION - 7-SERVO SYSTEM
# ============================================
# Total: 7 servo (6 Layer 1 + 1 Layer 2)
# 
# Layer 1 (6 Servo):
#   • 4 Servo Corner (A, B, C, D) - Mengangkat/menurunkan wadah
#   • 2 Servo Lock (Left, Right) - Mengunci wadah di posisi atas
#
# Layer 2 (1 Servo):
#   • Selector - Memilah ke Bin A atau B
#
# 🔧 CARA SETTING:
#   1. Pastikan SERVO_DRIVER = 'seven_servo'
#   2. Atur channel PCA9685 untuk setiap servo (0-15)
#   3. Atur angle untuk setiap posisi (UP/DOWN, LOCKED/UNLOCKED, dll)
#   4. Test dengan: python3 scripts/test_seven_servo.py

# Pilih driver servo
# 'seven_servo' = 7 servo dengan locking system (SISTEM TERBARU)
SERVO_DRIVER = 'seven_servo'

# Kalibrasi ServoKit (untuk MG996R/SG90 dsb.)
# Jika servo berputar liar/nyaris 360°, lebarkan rentang pulsa atau sesuaikan sesuai spesifikasi.
SERVOKIT_MIN_PULSE_MICROS = 500   # default aman 500µs
SERVOKIT_MAX_PULSE_MICROS = 2500  # default aman 2500µs
SERVOKIT_ACTUATION_RANGE = 180    # derajat total

# ──────────────────────────────────────────
# Layer 1 - Corner Servos (4 servo)
# ──────────────────────────────────────────
# Fungsi: Mengangkat dan menurunkan wadah di setiap sudut

# Mapping sesuai instruksi: 4,6,8,9 → A,B,C,D
SERVO_L1_CORNER_A_CHANNEL = 4    # Channel PCA9685 - Sudut A (Kiri Atas)
SERVO_L1_CORNER_B_CHANNEL = 6    # Channel PCA9685 - Sudut B (Kiri Bawah)
SERVO_L1_CORNER_C_CHANNEL = 8    # Channel PCA9685 - Sudut C (Kanan Atas)
SERVO_L1_CORNER_D_CHANNEL = 9    # Channel PCA9695 - Sudut D (Kanan Bawah)

# ⚠️ CRITICAL SAFETY: Angles MUST be 0-180° only (prevent 360° rotation)
SERVO_L1_CORNER_UP = 0           # Posisi UP (wadah terangkat, siap terima sampah)
SERVO_L1_CORNER_DOWN = 90        # Posisi DOWN (wadah turun setelah jatuh gravitasi)

# ──────────────────────────────────────────
# Layer 1 - Lock Servos (2 servo)
# ──────────────────────────────────────────
# Fungsi: Mengunci wadah di posisi atas (mencegah jatuh)
# 
# Konsep Locking (umum):
#   LOCKED (90°)   → Servo arm horizontal di bawah wadah (menahan)
#   UNLOCKED (0°)  → Servo arm vertikal (lepas, wadah bisa jatuh)

# Mapping: 0 dan 2 → Servo Kunci A dan B
SERVO_L1_LOCK_LEFT_CHANNEL = 0   # Servo Kunci A (atas tengah)
SERVO_L1_LOCK_RIGHT_CHANNEL = 2  # Servo Kunci B (bawah tengah)

# Global default (fallback) - tetap disediakan untuk kompatibilitas
# ⚠️ CRITICAL SAFETY: Angles MUST be 0-180° only (prevent 360° rotation)
SERVO_L1_LOCK_LOCKED = 90        # LOCKED: Horizontal, menahan wadah di atas
SERVO_L1_LOCK_UNLOCKED = 0       # UNLOCKED: Vertikal, lepas agar wadah jatuh

# Kustom per-servo sesuai arah fisik:
# ⚠️ TEMPORARY FIX: Balik arah jika servo berputar 360°
# Coba konfigurasi ini dulu untuk menghindari batas mekanis
SERVO_L1_LOCK_LEFT_LOCKED = 90
SERVO_L1_LOCK_LEFT_UNLOCKED = 0   # ← DIBALIK dari 180° ke 0°
SERVO_L1_LOCK_RIGHT_LOCKED = 90
SERVO_L1_LOCK_RIGHT_UNLOCKED = 180  # ← DIBALIK dari 0° ke 180°

# ──────────────────────────────────────────
# Layer 2 - Selector Servo (1 servo)
# ──────────────────────────────────────────
# Fungsi: Memilah sampah ke Bin A (Organik) atau Bin B (Anorganik)

# Mapping sesuai instruksi: 12 → Selector (Layer 2)
SERVO_L2_SELECTOR_CHANNEL = 12   # Channel PCA9685 - Pemilah

# ⚠️ CRITICAL SAFETY: Angles MUST be 0-180° only (prevent 360° rotation)
SERVO_L2_SELECTOR_NEUTRAL = 90   # NEUTRAL: Tengah (horizontal)
SERVO_L2_SELECTOR_BIN_A = 60     # BIN A (ORGANIC): 30° ke kiri dari neutral
SERVO_L2_SELECTOR_BIN_B = 120    # BIN B (ANORGANIC): 30° ke kanan dari neutral

# ──────────────────────────────────────────
# Timing Configuration
# ──────────────────────────────────────────
SERVO_LIFT_TIME = 0.3            # Waktu mengangkat wadah (Corner servos DOWN → UP)
SERVO_LOCK_DELAY = 0.1           # Delay setelah unlock/lock servo

# ============================================
# ============================================
# TIMING - Atur Kecepatan Gerakan
# ============================================
# Angka dalam DETIK - makin besar = makin lambat (tapi lebih aman)

SERVO_DROP_DELAY = 0.3          # Jeda setelah pemilah posisi (biar stabil dulu)
SERVO_FALL_TIME = 0.5           # Waktu sampah jatuh dari Layer 1 ke Layer 2
SERVO_SLIDE_TIME = 0.5          # Waktu sampah meluncur dari pemilah ke bin
SERVO_RESET_DELAY = 0.3         # Jeda setelah pemilah balik ke netral
SERVO_MOVEMENT_TIME = 0.15      # Waktu servo sampai ke posisi target

# Stagger delay (ms) antar servo saat gerak bersamaan untuk kurangi puncak arus
# 0 = semua start bersamaan secara PARALLEL (recommended untuk 7-servo)
# 5-10 = sedikit stagger untuk distribusi daya lebih baik
SERVO_STAGGER_DELAY_MS = 0

# ============================================
# PENGATURAN TEKNIS (Jangan diubah kalau tidak yakin)
# ============================================

SERVO_STOP_JITTER = True        # ⚠️ HARUS True! Biar servo gak berputar terus
SERVO_PWM_FREQUENCY = 50        # Frekuensi PWM (50Hz = standar servo MG996R)
SERVO_POSITION_HOLD_TIME = 0.05 # Waktu tahan posisi biar kunci mekanis

# PCA9685 Settings (untuk sistem 7-servo)
PCA9685_I2C_ADDRESS = 0x40      # Alamat I2C board PCA9685 (biasanya 0x40)
PCA9685_FREQUENCY = 50          # Sama dengan SERVO_PWM_FREQUENCY
PCA_CHANNELS_ONE_INDEXED = False # Set True jika papan Anda dilabeli 1-16 (bukan 0-15). Akan otomatis N→N-1.

# Debug timing untuk verifikasi gerakan paralel (print timestamp start/done per servo)
SERVO_DEBUG_TIMING = False

# Biarkan PWM tetap aktif khusus servo LOCK agar posisi tidak melorot saat menahan beban
# True direkomendasikan untuk sistem mekanis yang butuh gaya tahan pada posisi LOCKED
SERVO_KEEP_POWER_LOCKS = True

# ──────────────────────────────────────────
# Servo Angle Offsets (kalibrasi halus per-servo)
# ──────────────────────────────────────────
# Gunakan ini untuk menggeser sudut servo tertentu jika horn tidak bisa dipasang tepat 90°.
# Nilai positif memutar searah jarum jam; negatif berlawanan. Satuan: derajat.
SERVO_OFFSET_LOCK_LEFT = 0
SERVO_OFFSET_LOCK_RIGHT = 0
SERVO_OFFSET_CORNER_A = 0
SERVO_OFFSET_CORNER_B = 0
SERVO_OFFSET_CORNER_C = 0
SERVO_OFFSET_CORNER_D = 0
SERVO_OFFSET_SELECTOR = 0

# Batasi maksimum ayunan (derajat) dari posisi netral untuk safety
SERVO_MAX_SWING_LOCK_DEG = 90
SERVO_MAX_SWING_CORNER_DEG = 90

# Inisialisasi & shutdown behavior
# False = jangan gerakkan servo saat startup; biarkan diam sampai fase sorting
SERVO_INITIALIZE_AT_START = False
# False = jangan reset posisi saat shutdown; hanya matikan PWM (anti-gerak)
SERVO_RESET_ON_SHUTDOWN = False

# ============================================
# TIMING SETTINGS
# ============================================

# Delay untuk stabilisasi objek (detik)
STABILIZATION_DELAY = 0.5

# Duration untuk sorting (detik)
SORTING_DURATION = 2.0

# Cooldown antara trigger (detik)
TRIGGER_COOLDOWN = 1.0

# ============================================
# GPS/LOCATION SETTINGS
# ============================================

# Enable GPS location tracking
# Set False untuk menonaktifkan GPS (direkomendasikan untuk RPi 5 jika tidak ada modul GPS)
# GPS tidak wajib untuk operasi sistem - hanya untuk logging lokasi
ENABLE_GPS = False  # Default: False (disabled)

# GPS update interval (detik)
# Default: 300 (5 menit) untuk production, bisa lebih frequent untuk testing
GPS_UPDATE_INTERVAL = 300  # 5 menit

# Mock location untuk testing di Mac (latitude, longitude)
# Default: Jakarta (-6.2088, 106.8456)
# 
# CARA MENDAPATKAN KOORDINAT LOKASI ANDA:
# 1. Buka Google Maps (https://maps.google.com)
# 2. Klik kanan pada lokasi Anda
# 3. Klik koordinat yang muncul (contoh: -6.2088, 106.8456)
# 4. Copy dan paste ke bawah
# 
# Atau gunakan GPS_USE_IP_GEOLOCATION = True untuk auto-detect dari IP
GPS_MOCK_LOCATION = (-6.2088, 106.8456)  # Ganti dengan koordinat lokasi Anda

# Auto-detect location dari IP address (untuk Mac/testing)
# Jika True, akan override GPS_MOCK_LOCATION
# Akurasi: kota/wilayah (~5-50km), bukan GPS presisi
GPS_USE_IP_GEOLOCATION = False

# Enable saving location history ke file
# File akan di-append dengan JSONL format setiap update
GPS_SAVE_HISTORY = True
GPS_HISTORY_FILE = 'location_history.jsonl'

# Enable timezone detection (memerlukan timezonefinder library)
GPS_ENABLE_TIMEZONE = False  # Set True untuk enable jika library terinstall

# ============================================
# GPS HARDWARE SETTINGS (Raspberry Pi)
# ============================================
# GPS Module: U-blox NEO-6M
# Koneksi: VCC→5V, GND→GND, TX→GPIO15(RX), RX→GPIO14(TX)
# Setup: sudo raspi-config → Interface → Serial → No login, Yes hardware → Reboot

GPS_SERIAL_PORT = '/dev/serial0'       # Primary UART
GPS_BAUDRATE = 9600                    # NEO-6M default
GPS_READ_TIMEOUT = 5                   # Detik
GPS_MIN_SATELLITES = 4                 # Minimal 4 untuk 3D fix
GPS_USE_GPSD = True                    # Use GPSD daemon (install: sudo apt-get install gpsd gpsd-clients)

# ============================================
# DATABASE SETTINGS (MySQL RDS)
# ============================================

# Enable database logging
# Database menyimpan statistik klasifikasi TANPA data lokasi/GPS
# Location fields (latitude, longitude, location_id) akan selalu NULL
# Berguna untuk: analisis jumlah sampah, confidence scores, timestamp, device tracking
ENABLE_DATABASE = False  # Default: True (enabled untuk statistik)

# MySQL RDS Configuration
DB_HOST = 'orangebox.csxenzvznekp.ap-southeast-3.rds.amazonaws.com'
DB_USER = 'orangeboxmaster'
DB_PASSWORD = 'wpiGf0AtihhN2D3AjXUaSl'
DB_NAME = 'orangebox'
DB_PORT = 3306

# ============================================
# MULTI-DEVICE CONFIGURATION
# ============================================
# Device identifier (unique per Orange Box unit)
# 
# OPTIONS:
# 1. None - Auto-generate dari hostname + MAC address (recommended)
# 2. String manual - Set manual untuk custom naming
#
# CONTOH:
#   DEVICE_ID = None                    # Auto: "orangebox-rpi5-a1b2c3"
#   DEVICE_ID = "OB-CAMPUS-A-001"      # Manual: Unit pertama di kampus A
#   DEVICE_ID = "OB-MALL-B2-003"       # Manual: Unit ketiga di mall lantai B2
#
# BEST PRACTICE:
# - Production: Set manual dengan naming convention yang jelas
# - Development/Testing: Gunakan None (auto-generate)
#
DEVICE_ID = None  # Auto-generate (hostname-based)

# Device location/name (optional, untuk UI/reporting)
# Lebih mudah dibaca daripada DEVICE_ID
DEVICE_NAME = None  # e.g., "Mall Plaza Senayan - Lantai 2"
DEVICE_LOCATION = None  # e.g., "Jakarta Selatan"

