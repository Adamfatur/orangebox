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
# PENGATURAN SERVO - BACA INI DULU! 🔧
# ============================================

# 📌 CARA SETTING SERVO (Simpel & Mudah):
# 
# 1️⃣ TENTUKAN JENIS SERVO KAMU:
#    • Pakai GPIO langsung (3 servo) → Set SERVO_DRIVER = 'gpio'
#    • Pakai board PCA9685 (5 servo) → Set SERVO_DRIVER = 'servokit'
#
# 2️⃣ ATUR PIN (untuk GPIO) atau CHANNEL (untuk PCA9685):
#    Lihat bagian Layer 1 dan Layer 2 di bawah
#
# 3️⃣ ATUR DERAJAT SERVO:
#    • Servo biasanya bergerak 0° sampai 180°
#    • Mulai dari 90° (tengah), terus coba naik/turun 10-20°
#    • Kalau arah terbalik, tukar angkanya
#
# 4️⃣ TEST GERAKAN:
#    python3 scripts/test_servo.py
#
# ❓ MASALAH UMUM:
#    • Servo berputar terus? → SERVO_STOP_JITTER harus True
#    • Arah salah? → Tukar nilai OPEN/CLOSED atau BIN_A/BIN_B
#    • Servo gak gerak? → Cek kabel power 5V dan ground
#    • Gerakan patah-patah? → Kurangi SERVO_MOVEMENT_TIME

# Pilih driver servo (pilih salah satu):
SERVO_DRIVER = 'servokit'   # 'servokit' = pakai PCA9685 (5 servo) | 'gpio' = langsung ke GPIO (3 servo)

# Kalibrasi ServoKit (untuk MG996R/SG90 dsb.)
# Jika servo berputar liar/nyaris 360°, lebarkan rentang pulsa atau sesuaikan sesuai spesifikasi.
SERVOKIT_MIN_PULSE_MICROS = 500   # default aman 500µs
SERVOKIT_MAX_PULSE_MICROS = 2500  # default aman 2500µs
SERVOKIT_ACTUATION_RANGE = 180    # derajat total

# ============================================
# LAYER 1 - PINTU WADAH (2-4 Servo)
# ============================================
# Fungsi: Pintu kiri/kanan buat jatuhkan sampah ke bawah

# 🚪 Pintu Kiri (2 servo)
SERVO_LAYER1_LEFT_PIN = 12          # Pin GPIO (kalau pakai GPIO)
SERVO_LAYER1_LEFT_CHANNEL = 0       # Channel PCA9685 (kalau pakai ServoKit)
SERVO_LAYER1_LEFT_CLOSED = 0        # Derajat saat TUTUP (misal: 0° = horizontal)
SERVO_LAYER1_LEFT_OPEN = 90         # Derajat saat BUKA (misal: 90° = vertikal ke bawah)

# 🚪 Pintu Kanan (2 servo)
SERVO_LAYER1_RIGHT_PIN = 13         # Pin GPIO (kalau pakai GPIO)
SERVO_LAYER1_RIGHT_CHANNEL = 2      # Channel PCA9685 (kalau pakai ServoKit)
SERVO_LAYER1_RIGHT_CLOSED = 0       # Derajat saat TUTUP
SERVO_LAYER1_RIGHT_OPEN = 90        # Derajat saat BUKA

# 🚪 Pintu Kiri 2 (pasangan kiri)
SERVO_LAYER1_LEFT2_PIN = 19         # Pin GPIO (kalau pakai GPIO) - Set ke None untuk disable
SERVO_LAYER1_LEFT2_CHANNEL = 1      # Channel PCA9685 (kalau pakai ServoKit) - Set ke None untuk disable
SERVO_LAYER1_LEFT2_CLOSED = SERVO_LAYER1_LEFT_CLOSED
SERVO_LAYER1_LEFT2_OPEN = SERVO_LAYER1_LEFT_OPEN

# 🚪 Pintu Kanan 2 (pasangan kanan)
SERVO_LAYER1_RIGHT2_PIN = 26        # Pin GPIO (kalau pakai GPIO) - Set ke None untuk disable
SERVO_LAYER1_RIGHT2_CHANNEL = 3     # Channel PCA9685 (kalau pakai ServoKit) - Set ke None untuk disable
SERVO_LAYER1_RIGHT2_CLOSED = SERVO_LAYER1_RIGHT_CLOSED
SERVO_LAYER1_RIGHT2_OPEN = SERVO_LAYER1_RIGHT_OPEN

# Sinkronisasi Layer 1: buka keempat pintu sekaligus (A+B+C+D) atau hanya sisi sesuai BIN
# False = buka sesuai sisi (BIN A=LEFT → A+B; BIN B=RIGHT → C+D)
# True  = buka semua (A+B+C+D) serentak
SERVO_LAYER1_OPEN_BOTH_SIDES = True

# Stagger delay (ms) antar servo saat gerak bersamaan untuk kurangi puncak arus
# 0 = semua start bersamaan (butuh PSU kuat, mungkin inkonsisten)
# 8-12 = staggered start, lebih stabil di PSU terbatas, masih terlihat hampir bersamaan
# >20 = mulai terlihat berurutan
SERVO_STAGGER_DELAY_MS = 10

# ============================================
# LAYER 2 - PEMILAH (1 Servo)
# ============================================
# Fungsi: Arahkan sampah ke Bin A (Organik) atau Bin B (Anorganik)

# 🎯 Servo Pemilah
SERVO_LAYER2_SELECTOR_PIN = 18      # Pin GPIO (kalau pakai GPIO)
SERVO_LAYER2_SELECTOR_CHANNEL = None   # Set ke None untuk disable (nanti bisa pakai CH 4 atau 5)
# ⚠️  Layer 2 belum ada servo fisik, tapi tetap di-simulasi di kode
# ⚠️  Nanti kalau mau tambah, set SERVO_LAYER2_SELECTOR_CHANNEL = 4 (atau channel lain yang kosong)
SERVO_LAYER2_BIN_A = 60             # Derajat untuk Bin A / Organik (misal: miring kiri 30°)
SERVO_LAYER2_BIN_B = 120            # Derajat untuk Bin B / Anorganik (misal: miring kanan 30°)
SERVO_LAYER2_NEUTRAL = 90           # Posisi netral/tengah (horizontal)

# Layer 2 Behavior Settings
# Seberapa jauh miring dari netral (derajat). Digunakan untuk uji tilt tanpa klasifikasi
SERVO_LAYER2_TILT_ANGLE = 30
# Toleransi posisi netral (derajat) untuk verifikasi lunak (tanpa sensor)
SERVO_LAYER2_NEUTRAL_TOLERANCE = 2
# Overshoot untuk menghilangkan backlash saat kembali ke netral
SERVO_LAYER2_NEUTRAL_OVERSHOOT_DEG = 3
# Waktu tunggu agar posisi stabil setelah sampai target
SERVO_LAYER2_SETTLE_TIME = 0.15
# Setelah tilt, selalu kembali ke netral?
SERVO_LAYER2_RETURN_AFTER_TILT = True

# ============================================
# TIMING - Atur Kecepatan Gerakan
# ============================================
# Angka dalam DETIK - makin besar = makin lambat (tapi lebih aman)

SERVO_OPEN_DURATION = 1.5       # Berapa lama pintu Layer 1 tetap terbuka
SERVO_DROP_DELAY = 0.3          # Jeda setelah pemilah posisi (biar stabil dulu)
SERVO_FALL_TIME = 0.5           # Waktu sampah jatuh dari Layer 1 ke Layer 2
SERVO_SLIDE_TIME = 0.5          # Waktu sampah meluncur dari pemilah ke bin
SERVO_CLOSE_DELAY = 0.3         # Jeda setelah pintu tutup (safety)
SERVO_RESET_DELAY = 0.3         # Jeda setelah pemilah balik ke netral
SERVO_MOVEMENT_TIME = 0.15      # Waktu servo sampai ke posisi target

# ============================================
# PENGATURAN TEKNIS (Jangan diubah kalau tidak yakin)
# ============================================

SERVO_STOP_JITTER = True        # ⚠️ HARUS True! Biar servo gak berputar terus
SERVO_PWM_FREQUENCY = 50        # Frekuensi PWM (50Hz = standar servo MG996R)
SERVO_POSITION_HOLD_TIME = 0.05 # Waktu tahan posisi biar kunci mekanis
SERVO_POSITION_TOLERANCE = 2    # Toleransi error posisi (derajat)

# PCA9685 Settings (kalau pakai ServoKit)
PCA9685_I2C_ADDRESS = 0x40      # Alamat I2C board PCA9685 (biasanya 0x40)
PCA9685_FREQUENCY = 50          # Sama dengan SERVO_PWM_FREQUENCY

# Legacy (backward compatibility - abaikan aja)
SERVO_CHANNEL = 0
SERVO_ANGLE_BIN_A = 0
SERVO_ANGLE_BIN_B = 90
SERVO_ANGLE_NEUTRAL = 45
AUTO_DETECT_SERVOS = False

# PCA9685 channel mapping for 5-servo system
# Layer 1 doors (two servos per side: A and B)
SERVO_L1_LEFT_A_CH = 2       # Example: 2 (adjust to your wiring)
SERVO_L1_LEFT_B_CH = None    # Optional second servo on left side
SERVO_L1_RIGHT_A_CH = 3      # Example: 3 (adjust to your wiring)
SERVO_L1_RIGHT_B_CH = None   # Optional second servo on right side

# Layer 2 selector
SERVO_L2_SELECTOR_CH = 0     # Example: 0 (adjust to your wiring)

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
ENABLE_DATABASE = True  # Default: True (enabled untuk statistik)

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

