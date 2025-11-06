"""
======================================================================
          ** ORANGEBOX - SCRIPT DIAGNOSA SERVO MENDASAR **
======================================================================

⚠️  PERHATIAN:
    - Script ini ditujukan untuk berjalan di Raspberry Pi yang terhubung
      ke PCA9685 I2C Servo Driver.
    - Pastikan library `adafruit-circuitpython-servokit` sudah terinstall.
      (Jalankan `pip3 install adafruit-circuitpython-servokit`)

TUJUAN SCRIPT INI:
1.  **Mengisolasi Masalah**: Memastikan board PCA9685 terdeteksi dan berfungsi.
2.  **Memetakan Koneksi Fisik**: Mengetahui servo mana yang terhubung ke
    channel PCA9685 nomor berapa (0-15).
3.  **Menguji Rentang Gerak**: Mencari tahu sudut minimum dan maksimum yang aman
    untuk setiap servo (misal: 0-180 derajat).

CARA PENGGUNAAN:
1.  Jalankan script: `python3 scripts/diagnose_servos.py`
2.  Anda akan diminta memasukkan nomor channel (0-15).
3.  Kemudian, masukkan sudut (angle) yang ingin diuji (0-180).
4.  Amati servo mana yang bergerak dan catat hasilnya di kertas.
    Contoh catatan:
      - Channel 0 -> Servo Kunci Kiri
      - Channel 4 -> Servo Sudut Kanan Atas
      - ...dan seterusnya.
5.  Ulangi untuk semua channel yang terhubung servo.
6.  Ketik 'q' atau 'quit' untuk keluar.

Setelah pemetaan selesai, kita bisa memperbaiki `config.py` dengan 100% yakin.
"""

import sys
import time

try:
    # Import library khusus Raspberry Pi
    import board
    import busio
    from adafruit_servokit import ServoKit
    IS_RPI = True
except (NotImplementedError, ImportError):
    # Jika gagal, kita berada di lingkungan non-Raspberry Pi (misal: Mac/Windows)
    IS_RPI = False

def main():
    """Fungsi utama untuk menjalankan diagnosa servo."""
    print(__doc__)

    if not IS_RPI:
        print("\n[ERROR] Script ini hanya bisa dijalankan di Raspberry Pi.")
        print("Pastikan library 'adafruit-blinka' dan 'adafruit-circuitpython-servokit' terinstall.")
        sys.exit(1)

    # Inisialisasi I2C bus dan ServoKit
    try:
        print("\n[INFO] Mencoba inisialisasi I2C bus dan board PCA9685...")
        i2c = busio.I2C(board.SCL, board.SDA)
        # Alamat default PCA9685 adalah 0x40. Ganti jika Anda mengubahnya.
        kit = ServoKit(channels=16, i2c=i2c, address=0x40)
        print("[OK] Board PCA9685 berhasil terdeteksi dan diinisialisasi.")
        print("=" * 70)
    except ValueError as e:
        print(f"\n[FATAL ERROR] Gagal menemukan board PCA9685 di alamat I2C yang diharapkan.")
        print(f"Detail: {e}")
        print("\nSOLUSI:")
        print("1. Pastikan board PCA9685 sudah terhubung dengan benar ke pin SCL, SDA, VCC, dan GND di Raspberry Pi.")
        print("2. Pastikan I2C sudah diaktifkan melalui `sudo raspi-config` (Interface Options -> I2C).")
        print("3. Cek alamat I2C dengan menjalankan `i2cdetect -y 1` di terminal. Jika bukan 0x40, ubah di script ini.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] Terjadi error yang tidak terduga saat inisialisasi: {e}")
        sys.exit(1)

    # Loop interaktif untuk menguji servo
    while True:
        try:
            # --- Input Channel ---
            channel_input = input("\nMasukkan nomor channel (0-15) atau 'q' untuk keluar: ").strip().lower()
            if channel_input in ['q', 'quit', 'exit']:
                print("\n[INFO] Keluar dari script diagnosa.")
                break
            
            channel = int(channel_input)
            if not 0 <= channel <= 15:
                print("[ERROR] Channel harus antara 0 dan 15.")
                continue

            # --- Input Angle ---
            angle_input = input(f"Masukkan sudut untuk channel {channel} (0-180): ").strip().lower()
            if angle_input in ['q', 'quit', 'exit']:
                print("\n[INFO] Keluar dari script diagnosa.")
                break

            angle = int(angle_input)
            if not 0 <= angle <= 180:
                print("[ERROR] Sudut harus antara 0 dan 180 untuk mencegah kerusakan servo.")
                continue

            # --- Gerakkan Servo ---
            print(f"[AKSI] Menggerakkan servo di channel {channel} ke sudut {angle} derajat...")
            kit.servo[channel].angle = angle
            # Beri sedikit waktu agar servo sampai ke posisi dan matikan PWM untuk mengurangi jitter/panas
            time.sleep(0.5)
            # kit.servo[channel].fraction = None # Opsional: matikan PWM jika servo tidak perlu menahan beban

            print("[OK] Perintah terkirim. Amati servo mana yang bergerak.")

        except ValueError:
            print("[ERROR] Input tidak valid. Masukkan angka untuk channel dan sudut.")
        except KeyboardInterrupt:
            print("\n\n[INFO] Script dihentikan oleh pengguna. Keluar.")
            break
        except Exception as e:
            print(f"\n[ERROR] Terjadi kesalahan saat menjalankan perintah: {e}")
            continue

if __name__ == "__main__":
    main()
