"""
Test 4 Servo Layer-1 (Pintu Kiri & Kanan, masing-masing 2 servo)

Tujuan:
- Gerakkan 4 servo layer-1 secara sinkron dengan pasangan berlawanan arah jika diperlukan
- Pastikan berhenti aman (PWM off) setelah gerak, untuk mencegah putar terus
- Mudah dikalibrasi per sisi: titik berhenti, sudut buka/tutup, durasi

Cara pakai (Raspberry Pi + PCA9685):
  source .venv/bin/activate  # bila pakai venv
  python3 scripts/test_servo_layer1_quad.py

Catatan:
- Gunakan channel PCA9685 nyata Anda (ganti di bawah)
- Jika mekanik membuat salah satu servo harus arah kebalikan, set OPEN/TUTUP yang terbalik
- Sudut 0..180, gunakan kecil dulu untuk uji aman (±10° dari titik berhenti)
"""

import time
from typing import Optional

try:
    from adafruit_servokit import ServoKit
    HAS_SERVOKIT = True
except Exception as e:
    HAS_SERVOKIT = False
    print(f"[Layer1QuadTest] Warning: ServoKit not available: {e}")

# ============== KONFIGURASI ==============
# CHANNEL PCA9685 (0..15) - GANTI SESUAI KABEL ANDA
LEFT_A_CH = 2     # contoh: 2
LEFT_B_CH = 4     # contoh: 4 (servo kedua sisi kiri)
RIGHT_A_CH = 3    # contoh: 3
RIGHT_B_CH = 5    # contoh: 5 (servo kedua sisi kanan)

# Titik berhenti (netral) masing-masing servo (hasil kalibrasi)
STOP_LEFT_A  = 90.0
STOP_LEFT_B  = 90.0
STOP_RIGHT_A = 90.0
STOP_RIGHT_B = 90.0

# Sudut saat BUKA dan TUTUP untuk tiap servo
# Catatan penting: jika sisi B adalah kebalikan arah, tukar nilai buka/tutup
# Contoh kiri: A buka 70, B buka 120 untuk pergerakan berlawanan arah
OPEN_LEFT_A  = 70
CLOSE_LEFT_A = 120
OPEN_LEFT_B  = 120  # kebalikan A
CLOSE_LEFT_B = 70   # kebalikan A

OPEN_RIGHT_A  = 70
CLOSE_RIGHT_A = 120
OPEN_RIGHT_B  = 120  # kebalikan A
CLOSE_RIGHT_B = 70   # kebalikan A

# Durasi tahan saat buka/tutup
DUR_OPEN_S  = 0.20  # berapa lama memberi waktu bergerak ke posisi buka
DUR_CLOSE_S = 0.20  # berapa lama memberi waktu bergerak ke posisi tutup
HOLD_LOCK_S = 0.05  # tahan sebentar untuk lock mekanik

# Setel frekuensi PCA9685 (MG996R: 50 Hz)
PCA_FREQUENCY = 50

# ============ AKHIR KONFIGURASI ==========


def clamp_angle(a: float) -> float:
    return max(0.0, min(180.0, float(a)))


def set_angle(kit: ServoKit, ch: int, ang: Optional[float]):
    try:
        kit.servo[ch].angle = None if ang is None else clamp_angle(ang)
    except Exception as e:
        print(f"[Layer1QuadTest] CH{ch} set_angle error: {e}")


def stop_pwm_pair(kit: ServoKit, ch1: int, ch2: int):
    # Matikan sinyal agar tidak jitter/rotasi
    set_angle(kit, ch1, None)
    set_angle(kit, ch2, None)


def move_pair(kit: ServoKit, ch1: int, ch2: int, a1: float, a2: float, dur: float):
    set_angle(kit, ch1, a1)
    set_angle(kit, ch2, a2)
    time.sleep(dur)
    # hold sebentar lalu stop PWM
    time.sleep(HOLD_LOCK_S)
    stop_pwm_pair(kit, ch1, ch2)


def to_stop_pair(kit: ServoKit, ch1: int, ch2: int, s1: float, s2: float):
    set_angle(kit, ch1, s1)
    set_angle(kit, ch2, s2)
    time.sleep(HOLD_LOCK_S)
    stop_pwm_pair(kit, ch1, ch2)


def main():
    if not HAS_SERVOKIT:
        print("[Layer1QuadTest] ServoKit tidak tersedia. Jalankan di Raspberry Pi dengan PCA9685.")
        return

    kit = ServoKit(channels=16)
    try:
        try:
            kit._pca.frequency = PCA_FREQUENCY
        except Exception:
            pass
        print(f"[Layer1QuadTest] PCA9685 freq={PCA_FREQUENCY}Hz")

        print("[Layer1QuadTest] Set awal: STOP semua servo")
        to_stop_pair(kit, LEFT_A_CH, LEFT_B_CH, STOP_LEFT_A, STOP_LEFT_B)
        to_stop_pair(kit, RIGHT_A_CH, RIGHT_B_CH, STOP_RIGHT_A, STOP_RIGHT_B)
        time.sleep(0.3)

        print("\n=== UJI: BUKA KEDUA SISI (kiri & kanan) ===")
        move_pair(kit, LEFT_A_CH, LEFT_B_CH, OPEN_LEFT_A, OPEN_LEFT_B, DUR_OPEN_S)
        move_pair(kit, RIGHT_A_CH, RIGHT_B_CH, OPEN_RIGHT_A, OPEN_RIGHT_B, DUR_OPEN_S)
        print("✓ TERBUKA (matikan PWM)")
        time.sleep(0.5)

        print("\n=== UJI: TUTUP KEDUA SISI (kiri & kanan) ===")
        move_pair(kit, LEFT_A_CH, LEFT_B_CH, CLOSE_LEFT_A, CLOSE_LEFT_B, DUR_CLOSE_S)
        move_pair(kit, RIGHT_A_CH, RIGHT_B_CH, CLOSE_RIGHT_A, CLOSE_RIGHT_B, DUR_CLOSE_S)
        print("✓ TERTUTUP (matikan PWM)")
        time.sleep(0.5)

        print("\n=== RESET KE TITIK BERHENTI ===")
        to_stop_pair(kit, LEFT_A_CH, LEFT_B_CH, STOP_LEFT_A, STOP_LEFT_B)
        to_stop_pair(kit, RIGHT_A_CH, RIGHT_B_CH, STOP_RIGHT_A, STOP_RIGHT_B)
        print("✓ Reset done")

        print("\nSelesai. Sesuaikan sudut bila perlu, ulangi jalankan skrip.")

    except KeyboardInterrupt:
        print("\n[Layer1QuadTest] Dihentikan oleh user")
    finally:
        # Matikan semua channel yang digunakan
        stop_pwm_pair(kit, LEFT_A_CH, LEFT_B_CH)
        stop_pwm_pair(kit, RIGHT_A_CH, RIGHT_B_CH)
        print("[Layer1QuadTest] PWM dimatikan untuk semua servo layer-1")


if __name__ == "__main__":
    main()
