from gpiozero import DistanceSensor
import BlynkLib
import time

# --- KONFIGURASI BLYNK ---
BLYNK_AUTH = "RxBhkOBj0NkeyKRLCNWoaqb8hWy9mnFZ"  # Ganti dengan token milikmu
V_PIN_LEVEL = 4  # Virtual Pin untuk Gauge (0-100%)

# --- KONFIGURASI HARDWARE ---
PIN_TRIG = 23
PIN_ECHO = 24

# --- KALIBRASI (GANTI SESUAI TONG SAMPAH KAMU) ---
JARAK_SAAT_KOSONG_CM = 80.0  # 0% Penuh
JARAK_SAAT_PENUH_CM = 5.0    # 100% Penuh

# --- INISIALISASI BLYNK ---
blynk = BlynkLib.Blynk(BLYNK_AUTH, server='blynk.cloud', port=8080)

# --- INISIALISASI SENSOR ---
sensor = DistanceSensor(echo=PIN_ECHO, trigger=PIN_TRIG, max_distance=2, threshold_distance=0.1)
# max_distance 2 meter (bisa disesuaikan)

print("Inisialisasi selesai. Menyambungkan ke Blynk...")
print("Gunakan CTRL+C untuk berhenti.\n")

def get_distance_cm():
    """Mengembalikan jarak dalam satuan CM."""
    return sensor.distance * 100  # gpiozero mengembalikan nilai dalam meter

def map_to_percentage(jarak):
    """Konversi jarak (cm) menjadi persentase penuh."""
    rentang_total = JARAK_SAAT_KOSONG_CM - JARAK_SAAT_PENUH_CM
    jarak_terukur_dari_dasar = JARAK_SAAT_KOSONG_CM - jarak
    persentase = (jarak_terukur_dari_dasar / rentang_total) * 100
    return max(0, min(100, persentase))

try:
    while True:
        blynk.run()
        jarak_dibaca = get_distance_cm()

        # Validasi jarak agar tidak salah baca
        if jarak_dibaca > JARAK_SAAT_KOSONG_CM + 5 or jarak_dibaca < JARAK_SAAT_PENUH_CM - 5:
            print(f"[!] Bacaan tidak valid: {jarak_dibaca:.1f} cm -> kirim 0%")
            persentase_penuh = 0
        else:
            persentase_penuh = map_to_percentage(jarak_dibaca)
            print(f"Jarak: {jarak_dibaca:.1f} cm  |  Penuh: {persentase_penuh:.1f}%")

        # Kirim ke Blynk
        blynk.virtual_write(V_PIN_LEVEL, persentase_penuh)

        # Update tiap 5 detik
        time.sleep(1)

except KeyboardInterrupt:
    print("\nProgram dihentikan oleh user.")

finally:
    sensor.close()
    print("Sensor dimatikan. GPIO dibersihkan.")
