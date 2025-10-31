"""
Simple Servo Test (PCA9685, Raspberry Pi 5)

Tujuan:
- Deteksi apakah board PCA9685 tersedia
- Gerakkan satu servo (channel dari config) 90° ↔ 0° berulang kali

Cara pakai:
  python3 scripts/test_servo_simple.py [--simulate] [--cycles N] [--channel C] [--neutral DEG] [--verbose]

Catatan:
- Script ini hanya mendukung PCA9685 (I2C) di Raspberry Pi.
- Jika pustaka Adafruit tidak tersedia atau PCA9685 gagal inisialisasi, script akan memberikan diagnostik jelas dan saran menjalankan via interpreter venv.
"""

import sys
import os
import time
import argparse
import subprocess
from importlib import util as importlib_util

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import config
except Exception as e:
    print(f"[ERROR] Tidak bisa import config: {e}")
    sys.exit(1)

# Deteksi platform & venv sejak awal, dan relaunch ke venv jika di RPi tapi bukan venv
def is_raspberry_pi() -> bool:
    try:
        with open('/proc/cpuinfo', 'r') as f:
            data = f.read()
        return ('Raspberry Pi' in data) or ('BCM' in data)
    except Exception:
        return False


def in_virtualenv() -> bool:
    try:
        # venv detection: sys.prefix differs from base_prefix or VIRTUAL_ENV set
        return (getattr(sys, 'base_prefix', sys.prefix) != sys.prefix) or bool(os.environ.get('VIRTUAL_ENV'))
    except Exception:
        return False


def create_and_setup_venv(venv_py: str):
    print("[INFO] Membuat virtualenv proyek...")
    subprocess.run([sys.executable, "-m", "venv", os.path.join(ROOT, "venv")], check=True)
    print("[INFO] Meng-upgrade pip/setuptools/wheel di venv...")
    subprocess.run([venv_py, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
    print("[INFO] Menginstal paket Adafruit...")
    subprocess.run([venv_py, "-m", "pip", "install",
                    "adafruit-blinka",
                    "adafruit-circuitpython-pca9685",
                    "adafruit-circuitpython-motor"], check=True)


if is_raspberry_pi() and not in_virtualenv():
    venv_py = os.path.join(ROOT, 'venv', 'bin', 'python')
    script_path = os.path.join(ROOT, 'scripts', os.path.basename(__file__))
    if not os.path.exists(venv_py):
        try:
            create_and_setup_venv(venv_py)
        except Exception as e:
            print(f"[ERROR] Gagal membuat/menyiapkan venv: {e}")
            print("Silakan jalankan 'bash install.sh' atau siapkan venv secara manual.")
            sys.exit(1)
    print(f"[INFO] Menjalankan ulang via venv interpreter: {venv_py}")
    os.execv(venv_py, [venv_py, script_path] + sys.argv[1:])

# Cek ketersediaan pustaka Adafruit PCA9685 (fallback ke simulasi bila tidak ada)
ADAFRUIT_AVAILABLE = True
try:
    from board import SCL, SDA
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo as adafruit_servo
except Exception as e:
    ADAFRUIT_AVAILABLE = False
    ADAFRUIT_IMPORT_ERROR = e

# Jika di RPi dan sudah dalam venv namun paket Adafruit belum terinstal, coba install otomatis
if is_raspberry_pi() and in_virtualenv() and not ADAFRUIT_AVAILABLE:
    missing = []
    if importlib_util.find_spec('board') is None:
        missing.append('adafruit-blinka')
    if importlib_util.find_spec('adafruit_pca9685') is None:
        missing.append('adafruit-circuitpython-pca9685')
    if importlib_util.find_spec('adafruit_motor') is None:
        missing.append('adafruit-circuitpython-motor')
    if missing:
        try:
            print(f"[INFO] Menginstal paket Adafruit yang hilang: {' '.join(missing)}")
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
            # Coba import ulang
            from board import SCL, SDA
            import busio
            from adafruit_pca9685 import PCA9685
            from adafruit_motor import servo as adafruit_servo
            ADAFRUIT_AVAILABLE = True
            ADAFRUIT_IMPORT_ERROR = None
        except Exception as e:
            ADAFRUIT_AVAILABLE = False
            ADAFRUIT_IMPORT_ERROR = e


def print_env_diagnostics():
    print("\n[DIAGNOSTIK] Lingkungan eksekusi")
    print(f"  Python: {sys.executable}")
    print(f"  Versi:  {sys.version.split()[0]}")
    print(f"  Platform: {'RPi' if is_raspberry_pi() else sys.platform}")
    print(f"  Virtualenv: {'YA' if in_virtualenv() else 'TIDAK'}")
    mods = ['board', 'busio', 'adafruit_pca9685', 'adafruit_motor']
    availability = {m: (importlib_util.find_spec(m) is not None) for m in mods}
    print(f"  Modul:   {availability}")
    # Sarankan interpreter venv bila ada di proyek
    proj_root = ROOT
    venv_py = os.path.join(proj_root, 'venv', 'bin', 'python')
    if os.path.exists(venv_py):
        print(f"  Saran:   Jalankan via venv → {venv_py} scripts/test_servo_simple.py")
    # Petunjuk I2C di RPi
    if is_raspberry_pi():
        print("  I2C:     Pastikan aktif (raspi-config) dan PCA9685 terdeteksi di 'i2cdetect -y 1' (0x40)")


def clamp_angle(v: int) -> int:
    try:
        return max(0, min(180, int(v)))
    except Exception:
        return 90

def clamp_channel(v: int) -> int:
    try:
        return max(0, min(15, int(v)))
    except Exception:
        return 0

def simulate_servo_test(channel: int, angle_neutral: int, angle_high: int, angle_low: int, cycles: int):
    print("\n[SIMULASI] Pustaka Adafruit belum tersedia atau PCA9685 gagal inisialisasi.")
    print("[SIMULASI] Menjalankan uji gerak virtual agar alur bisa dipantau.")
    print(f"Channel (virtual): {channel}")
    print(f"Netral: {angle_neutral}°, Gerak: {angle_high}° ↔ {angle_low}°, Siklus: {cycles}")
    print("Mulai simulasi...")
    time.sleep(0.5)
    for i in range(1, cycles + 1):
        print(f"  [SIM] Siklus {i}: ke {angle_high}°")
        time.sleep(0.35)
        print(f"  [SIM] Siklus {i}: ke {angle_low}°")
        time.sleep(0.35)
    print(f"  [SIM] Kembali ke netral {angle_neutral}°")
    time.sleep(0.4)
    print("[SIMULASI] Selesai.")
    # Tambah guidance yang lebih jelas
    print_env_diagnostics()
    print("\n[PETUNJUK] Untuk gerak nyata:")
    print("  1) Jalankan di Raspberry Pi dengan interpreter venv proyek")
    print("  2) Pastikan paket di venv: adafruit-blinka, adafruit-circuitpython-pca9685, adafruit-circuitpython-motor")
    print("  3) Aktifkan I2C dan cek PCA9685 via 'i2cdetect -y 1' (alamat 0x40)")


def main():
    parser = argparse.ArgumentParser(description="OrangeBox Simple Servo Test (PCA9685)")
    parser.add_argument("--simulate", action="store_true", help="Paksa mode simulasi (tanpa gerak fisik)")
    parser.add_argument("--cycles", type=int, default=8, help="Jumlah siklus gerak 90° ↔ 0°")
    parser.add_argument("--channel", type=int, help="Override channel servo (0-15)")
    parser.add_argument("--neutral", type=int, help="Override sudut netral (0-180)")
    parser.add_argument("--address", type=str, help="Alamat I2C PCA9685 (mis. 0x40 atau 64)")
    parser.add_argument("--pwm-min", type=int, help="Pulse minimum (µs), default 500")
    parser.add_argument("--pwm-max", type=int, help="Pulse maksimum (µs), default 2500")
    parser.add_argument("--verbose", action="store_true", help="Tampilkan diagnostik lingkungan dan modul")
    args = parser.parse_args()

    print("=" * 60)
    print("OrangeBox Simple Servo Test (PCA9685)")
    print("=" * 60)

    # Ambil channel & sudut (dipakai untuk real maupun simulasi)
    channel_cfg = getattr(config, 'SERVO_CHANNEL', 0)
    neutral_cfg = getattr(config, 'SERVO_LAYER2_NEUTRAL', getattr(config, 'SERVO_ANGLE_NEUTRAL', 90))
    channel = clamp_channel(args.channel if args.channel is not None else channel_cfg)
    angle_neutral = clamp_angle(args.neutral if args.neutral is not None else neutral_cfg)
    angle_low = 0
    angle_high = 90
    cycles = max(1, int(args.cycles))

    if args.verbose:
        print_env_diagnostics()

    if args.simulate:
        simulate_servo_test(channel, angle_neutral, angle_high, angle_low, cycles)
        return

    if not ADAFRUIT_AVAILABLE:
        print(f"[PERINGATAN] Adafruit PCA9685 library tidak tersedia: {ADAFRUIT_IMPORT_ERROR}")
        print("Paket wajib di interpreter aktif: adafruit-blinka, adafruit-circuitpython-pca9685, adafruit-circuitpython-motor")
        print_env_diagnostics()
        simulate_servo_test(channel, angle_neutral, angle_high, angle_low, cycles)
        return

    # Init I2C & PCA9685
    try:
        i2c = busio.I2C(SCL, SDA)
        # Alamat I2C: dari argumen atau default (0x40)
        def parse_addr(s):
            try:
                return int(s, 0)  # mendukung '0x40' atau '64'
            except Exception:
                return None

        addr_arg = parse_addr(args.address) if args.address else None
        i2c_address = addr_arg if addr_arg is not None else 0x40
        pca = PCA9685(i2c, address=i2c_address)
        pwm_freq = getattr(config, 'SERVO_PWM_FREQUENCY', 50)
        pca.frequency = pwm_freq
        print(f"✓ PCA9685 terdeteksi @ 0x{pca.address:02X}, frequency = {pwm_freq} Hz")
    except Exception as e:
        print(f"[PERINGATAN] Inisialisasi PCA9685 gagal: {e}")
        print_env_diagnostics()
        simulate_servo_test(channel, angle_neutral, angle_high, angle_low, cycles)
        return

    print(f"Channel: {channel} (pakai config.SERVO_CHANNEL)")
    print(f"Uji gerak: {angle_high}° ↔ {angle_low}° sebanyak {cycles} kali")

    # Scan semua channel untuk memastikan servo tunggal yang terhubung ikut bergerak
    print("\nScanning channels (0–15) dengan pola gerak kecil...")
    for ch in range(16):
        try:
            sscan = adafruit_servo.Servo(pca.channels[ch], min_pulse=500, max_pulse=2500)
            print(f"[SCAN] CH {ch}: neutral → {max(0, angle_neutral-20)}° → {min(180, angle_neutral+20)}° → neutral")
            sscan.angle = angle_neutral
            time.sleep(0.35)
            sscan.angle = max(0, angle_neutral-20)
            time.sleep(0.45)
            sscan.angle = min(180, angle_neutral+20)
            time.sleep(0.45)
            sscan.angle = angle_neutral
            time.sleep(0.30)
        except Exception as se:
            print(f"[SCAN] CH {ch} error: {se}")

    # Buat instance servo pada channel
    try:
        min_pulse = args.pwm_min if args.pwm_min is not None else 500
        max_pulse = args.pwm_max if args.pwm_max is not None else 2500
        print(f"Konfigurasi PWM: min={min_pulse} µs, max={max_pulse} µs")
        s = adafruit_servo.Servo(
            pca.channels[channel],
            min_pulse=min_pulse,
            max_pulse=max_pulse
        )
    except Exception as e:
        print(f"[PERINGATAN] Gagal membuat instance servo pada channel {channel}: {e}")
        try:
            pca.deinit()
        except Exception:
            pass
        simulate_servo_test(channel, angle_neutral, angle_high, angle_low, cycles)
        return

    try:
        # Sweep kuat untuk diagnosa (0 → 30 → 60 → 90 → 120 → 150 → 180)
        print("Sweep 0–180° untuk diagnosa...")
        for a in [0, 30, 60, 90, 120, 150, 180]:
            s.angle = a
            print(f"  angle = {a}°")
            time.sleep(0.9)

        # Set ke netral dulu
        s.angle = angle_neutral
        print(f"Set netral ke {angle_neutral}°")
        time.sleep(1.0)

        # Gerak 90 ↔ 0 berulang
        for i in range(cycles):
            print(f"[TEST] Cycle {i+1}/{cycles}: {angle_high}° → {angle_low}°")
            s.angle = angle_high
            time.sleep(1.0)
            s.angle = angle_low
            time.sleep(1.0)

        # Kembali ke netral
        print("Mengembalikan ke posisi netral...")
        s.angle = angle_neutral
        time.sleep(0.8)
        print("✓ Selesai")
    except KeyboardInterrupt:
        print("\nDibatalkan oleh pengguna")
    except Exception as e:
        print(f"[ERROR] Gerakan servo gagal: {e}")
    finally:
        try:
            if hasattr(pca, 'deinit'):
                pca.deinit()
        except Exception:
            pass


if __name__ == '__main__':
    main()