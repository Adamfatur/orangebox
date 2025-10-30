"""
Simple Servo Test (PCA9685, Raspberry Pi 5)

Tujuan:
- Deteksi apakah board PCA9685 tersedia
- Gerakkan satu servo (channel dari config) 90° ↔ 0° berulang kali

Cara pakai:
  python3 scripts/test_servo_simple.py

Catatan:
- Script ini hanya mendukung PCA9685 (I2C) di Raspberry Pi.
- Jika pustaka Adafruit tidak tersedia, script akan keluar dengan pesan kesalahan.
"""

import sys
import os
import time

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import config
except Exception as e:
    print(f"[ERROR] Tidak bisa import config: {e}")
    sys.exit(1)

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
    print("[SIMULASI] Selesai. Untuk gerak nyata, pasang paket: adafruit-blinka, adafruit-circuitpython-pca9685, adafruit-circuitpython-motor")


def main():
    print("=" * 60)
    print("OrangeBox Simple Servo Test (PCA9685)")
    print("=" * 60)

    # Ambil channel & sudut (dipakai untuk real maupun simulasi)
    channel = clamp_channel(getattr(config, 'SERVO_CHANNEL', 0))
    angle_neutral = clamp_angle(getattr(config, 'SERVO_LAYER2_NEUTRAL', getattr(config, 'SERVO_ANGLE_NEUTRAL', 90)))
    angle_low = 0
    angle_high = 90
    cycles = 8

    if not ADAFRUIT_AVAILABLE:
        print(f"[PERINGATAN] Adafruit PCA9685 library tidak tersedia: {ADAFRUIT_IMPORT_ERROR}")
        print("Pastikan paket terpasang: adafruit-blinka, adafruit-circuitpython-pca9685, adafruit-circuitpython-motor")
        simulate_servo_test(channel, angle_neutral, angle_high, angle_low, cycles)
        return

    # Init I2C & PCA9685
    try:
        i2c = busio.I2C(SCL, SDA)
        pca = PCA9685(i2c)
        pwm_freq = getattr(config, 'SERVO_PWM_FREQUENCY', 50)
        pca.frequency = pwm_freq
        print(f"✓ PCA9685 terdeteksi, frequency = {pwm_freq} Hz")
    except Exception as e:
        print(f"[PERINGATAN] Inisialisasi PCA9685 gagal: {e}")
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
        s = adafruit_servo.Servo(
            pca.channels[channel],
            min_pulse=500,
            max_pulse=2500
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
        # Set ke netral dulu
        s.angle = angle_neutral
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