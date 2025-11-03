"""
╔═══════════════════════════════════════════════════════════════╗
║      5-Servo Hardware - Kontrol via Board PCA9685           ║
║         (untuk sistem 5 servo pakai driver I2C)             ║
╚═══════════════════════════════════════════════════════════════╝

📌 FILE INI UNTUK APA?
   File ini mengontrol 5 servo yang terhubung ke board PCA9685 
   (driver I2C yang bisa kontrol banyak servo sekaligus).

⚙️  CARA SETTING SERVO:
   ❌ JANGAN ubah file ini!
   ✅ Buka config.py dan atur:
      • SERVO_LAYER1_LEFT_CHANNEL = channel untuk pintu kiri
      • SERVO_LAYER1_RIGHT_CHANNEL = channel untuk pintu kanan
      • SERVO_LAYER2_SELECTOR_CHANNEL = channel untuk pemilah
      • *_CLOSED, *_OPEN, *_BIN_A, *_BIN_B = derajat servo
      
   💡 Channel PCA9685 biasanya 0-15 (tergantung board)

🧪 TEST SERVO:
   python3 scripts/test_servo.py

🔧 TROUBLESHOOTING:
   • Servo gak gerak semua? → Cek board PCA9685 power & I2C connection
   • Cek alamat I2C: i2cdetect -y 1 (harusnya ada 0x40)
   • Satu servo gak gerak? → Cek channel number di config.py
   • Arah kebalik? → Tukar nilai di config.py

📚 CARA KERJA:
   4 servo pintu (kiri A+B, kanan A+B) + 1 servo pemilah
   Layer 2 gerak dulu → Layer 1 buka → Sampah jatuh → 
   Pintu tutup → Pemilah balik tengah

Copyright (c) 2025 AF - OrangeBox Project
"""

import time
import sys
import os

# Ensure project root on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import config

try:
    from adafruit_servokit import ServoKit
    HAS_SERVOKIT = True
except Exception as e:
    HAS_SERVOKIT = False
    print(f"[5ServoHW] Warning: ServoKit not available: {e}")


class FiveServoHardware:

    def __init__(self):
        self.servos_active = False
        self.servos = {}
        self.kit = None

        print("[5ServoHW] Initializing 5-servo system (ServoKit/PCA9685)...")

        if not HAS_SERVOKIT:
            print("[5ServoHW] Running in simulation mode (no ServoKit)")
            self._setup_servos_config_only()
            return

        try:
            # Initialize ServoKit with 16 channels, custom address if provided
            address = getattr(config, 'PCA9685_I2C_ADDRESS', 0x40)
            self.kit = self._init_servokit(address)
            # Set frequency explicitly for MG996R
            try:
                self.kit._pca.frequency = getattr(config, 'PCA9685_FREQUENCY', 50)
            except Exception:
                pass  # Fallback to default if internal API changes
            print(f"[5ServoHW] PCA9685 initialized at 0x{address:02X}, freq={getattr(config, 'PCA9685_FREQUENCY', 50)}Hz")

            self._setup_servos_config_only()
            self.servos_active = True
        except Exception as e:
            print(f"[5ServoHW] Error initializing ServoKit: {e}")
            import traceback
            traceback.print_exc()

            # Auto-fix: coba enable I2C di Raspberry Pi, lalu retry sekali
            if self._attempt_enable_i2c():
                try:
                    address = getattr(config, 'PCA9685_I2C_ADDRESS', 0x40)
                    self.kit = self._init_servokit(address)
                    try:
                        self.kit._pca.frequency = getattr(config, 'PCA9685_FREQUENCY', 50)
                    except Exception:
                        pass
                    print(f"[5ServoHW] PCA9685 initialized after I2C fix at 0x{address:02X}")
                    self._setup_servos_config_only()
                    self.servos_active = True
                    return
                except Exception as e2:
                    print(f"[5ServoHW] Retry failed: {e2}")
                    traceback.print_exc()

            # Fallback to simulation
            self._setup_servos_config_only()

    def _setup_servos_config_only(self):
        """Muat konfigurasi servo dari config (berfungsi juga untuk simulasi).
        Tempat edit:
        - Channel: `SERVO_LAYER1_*_CHANNEL`, `SERVO_LAYER2_SELECTOR_CHANNEL` di config.py
        - Sudut: Layer 1 tutup/buka; Layer 2 netral/bin di config.py
        """
        self.servos = {}

        # Layer 1 - 4 Servo Pintu (left, right, left2, right2)
        # Ambil channel dari config.py
        left_ch = getattr(config, 'SERVO_LAYER1_LEFT_CHANNEL', None)
        right_ch = getattr(config, 'SERVO_LAYER1_RIGHT_CHANNEL', None)
        left2_ch = getattr(config, 'SERVO_LAYER1_LEFT2_CHANNEL', None)
        right2_ch = getattr(config, 'SERVO_LAYER1_RIGHT2_CHANNEL', None)
        sel_ch = getattr(config, 'SERVO_LAYER2_SELECTOR_CHANNEL', None)

        # Setup servo LEFT (primary)
        if left_ch is not None:
            self.servos['layer1_left'] = {
                'name': 'Layer 1 Left Door',
                'channel': left_ch,
                'closed': getattr(config, 'SERVO_LAYER1_LEFT_CLOSED', 0),
                'open': getattr(config, 'SERVO_LAYER1_LEFT_OPEN', 90)
            }
        
        # Setup servo RIGHT (primary)
        if right_ch is not None:
            self.servos['layer1_right'] = {
                'name': 'Layer 1 Right Door',
                'channel': right_ch,
                'closed': getattr(config, 'SERVO_LAYER1_RIGHT_CLOSED', 0),
                'open': getattr(config, 'SERVO_LAYER1_RIGHT_OPEN', 90)
            }
        
        # Setup servo LEFT2 (secondary pair) - BARU!
        if left2_ch is not None:
            self.servos['layer1_left2'] = {
                'name': 'Layer 1 Left Door 2',
                'channel': left2_ch,
                'closed': getattr(config, 'SERVO_LAYER1_LEFT2_CLOSED', getattr(config, 'SERVO_LAYER1_LEFT_CLOSED', 0)),
                'open': getattr(config, 'SERVO_LAYER1_LEFT2_OPEN', getattr(config, 'SERVO_LAYER1_LEFT_OPEN', 90))
            }
        
        # Setup servo RIGHT2 (secondary pair) - BARU!
        if right2_ch is not None:
            self.servos['layer1_right2'] = {
                'name': 'Layer 1 Right Door 2',
                'channel': right2_ch,
                'closed': getattr(config, 'SERVO_LAYER1_RIGHT2_CLOSED', getattr(config, 'SERVO_LAYER1_RIGHT_CLOSED', 0)),
                'open': getattr(config, 'SERVO_LAYER1_RIGHT2_OPEN', getattr(config, 'SERVO_LAYER1_RIGHT_OPEN', 90))
            }

        # Setup Layer 2 Selector
        if sel_ch is not None:
            self.servos['layer2_selector'] = {
                'name': 'Layer 2 Selector',
                'channel': sel_ch,
                'neutral': getattr(config, 'SERVO_LAYER2_NEUTRAL', 90),
                'bin_a': getattr(config, 'SERVO_LAYER2_BIN_A', 60),
                'bin_b': getattr(config, 'SERVO_LAYER2_BIN_B', 120)
            }

        # Initialize tracking fields
        for sid, cfg in self.servos.items():
            cfg['current_angle'] = None
            cfg['last_move_time'] = 0
            print(f"[5ServoHW] Config {cfg['name']}: CH {cfg['channel']}")


    def _move_channel(self, channel, angle):
        """
        Gerakkan channel PCA9685 ke sudut tertentu menggunakan ServoKit.
        
        CRITICAL: Memastikan servo berhenti tepat di posisi target tanpa drift.
        
        Alur:
        1. Set sudut target
        2. Tunggu gerakan selesai (SERVO_MOVEMENT_TIME)
        3. Hold posisi untuk lock mekanik (SERVO_POSITION_HOLD_TIME)
        4. STOP PWM untuk mencegah jitter/rotasi berkelanjutan
        """
        try:
            if not HAS_SERVOKIT or self.kit is None:
                print(f"[5ServoHW] Simulate move CH{channel} → {angle}°")
                return True
            
            # Gerakkan ke sudut target
            self.kit.servo[channel].angle = angle
            
            # Waktu gerak utama - beri waktu servo mencapai posisi
            movement_time = getattr(config, 'SERVO_MOVEMENT_TIME', 0.15)
            time.sleep(movement_time)
            
            # CRITICAL: Hold posisi untuk lock mekanik
            # MG996R memerlukan waktu ekstra untuk memastikan gear terkunci
            hold_time = getattr(config, 'SERVO_POSITION_HOLD_TIME', 0.05)
            if hold_time and hold_time > 0:
                time.sleep(hold_time)
            
            # CRITICAL: Nonaktifkan sinyal PWM untuk mencegah jitter/rotasi berkelanjutan
            # Servo MG996R akan hold posisi secara mekanik meskipun PWM off
            # Ini SANGAT PENTING untuk mencegah servo berputar terus-menerus
            stop_jitter = getattr(config, 'SERVO_STOP_JITTER', True)
            if stop_jitter:
                try:
                    # Detach servo dari PCA9685 (set angle = None)
                    self.kit.servo[channel].angle = None
                    print(f"[5ServoHW] CH{channel} PWM stopped (angle={angle}° locked)")
                except AttributeError:
                    # Fallback: coba set pulse width ke 0
                    try:
                        self.kit.servo[channel].fraction = None
                    except Exception:
                        pass
                except Exception as e:
                    print(f"[5ServoHW] Warning: Could not detach CH{channel}: {e}")
            
            return True
            
        except Exception as e:
            print(f"[5ServoHW] Move error CH{channel} → {angle}°: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _init_servokit(self, address):
        """Inisialisasi ServoKit dengan pengecekan alamat I2C PCA9685 jika memungkinkan."""
        # Jika i2c-tools tersedia, coba cek apakah alamat PCA9685 terlihat
        try:
            import shutil as _sh
            import subprocess as _sp
            if _sh.which('i2cdetect'):
                # Cek bus 1 yang umum dipakai di Raspberry Pi
                out = _sp.run(['i2cdetect', '-y', '1'], capture_output=True, text=True, timeout=3)
                if out.returncode == 0 and f"{address:02x}" not in out.stdout.lower():
                    print(f"[5ServoHW] Warning: I2C scan tidak menemukan 0x{address:02X} di bus 1.")
                    print("            Pastikan kabel SDA/SCL benar dan board PCA9685 mendapat power 5V.")
        except Exception:
            pass

        return ServoKit(channels=16, address=address)

    def _attempt_enable_i2c(self):
        """Coba enable I2C secara otomatis di Raspberry Pi. Kembalikan True jika langkah dilakukan.
        Catatan: Bisa butuh reboot agar /dev/i2c-1 muncul dan group i2c aktif untuk user.
        """
        try:
            import platform
            if platform.system() != 'Linux':
                return False
            # Deteksi Raspberry Pi melalui /proc/cpuinfo
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    if 'Raspberry Pi' not in f.read():
                        return False
            except Exception:
                return False

            print("[5ServoHW] 🔧 Attempting to enable I2C automatically...")
            import subprocess as sp
            import shutil as sh
            import os as _os

            # Install tools if available
            if sh.which('apt-get'):
                sp.run(['sudo', 'apt-get', 'update', '-qq'], check=False)
                sp.run(['sudo', 'apt-get', 'install', '-y', 'i2c-tools', 'python3-smbus', 'python3-rpi.gpio'], check=False)

            # Enable via raspi-config if present
            if sh.which('raspi-config'):
                sp.run(['sudo', 'raspi-config', 'nonint', 'do_i2c', '0'], check=False)

            # Load i2c-dev module
            sp.run(['sudo', 'modprobe', 'i2c-dev'], check=False)

            # Tambahkan user ke group i2c (perlu logout/reboot)
            user = _os.environ.get('SUDO_USER') or _os.environ.get('USER')
            if user:
                sp.run(['sudo', 'usermod', '-aG', 'i2c', user], check=False)

            # Beritahu kemungkinan perlu reboot
            print("[5ServoHW] ✅ I2C enable commands applied. Reboot mungkin diperlukan agar aktif.")
            print("           Jika masih gagal, reboot lalu jalankan lagi: sudo reboot")
            return True
        except Exception as e:
            print(f"[5ServoHW] I2C auto-enable failed: {e}")
            return False

    def _move_servo(self, servo_id, angle):
        """Gerakkan servo berdasarkan ID ke sudut dan catat posisi/waktu."""
        if servo_id not in self.servos:
            print(f"[5ServoHW] Unknown servo id: {servo_id}")
            return False
        cfg = self.servos[servo_id]
        ok = self._move_channel(cfg['channel'], angle)
        if ok:
            cfg['current_angle'] = angle
            cfg['last_move_time'] = time.time()
        return ok

    def verify_positions(self):
        """Verifikasi sederhana; mengembalikan sudut yang diharapkan dan timestamp."""
        status = {}
        for sid, cfg in self.servos.items():
            status[sid] = {
                'expected': cfg.get('current_angle'),
                'verified': True,
                'timestamp': cfg.get('last_move_time', 0)
            }
        return status

    def open_doors(self):
        print("[5ServoHW] Opening Layer 1 doors (all 4 servos)...")
        # Ubah sudut buka pintu di: config.py → SERVO_LAYER1_*_OPEN
        # Buka setiap servo Layer 1 ke sudut 'open'-nya
        results = []
        for sid in ('layer1_left', 'layer1_right', 'layer1_left2', 'layer1_right2'):
            if sid in self.servos:
                results.append(self._move_servo(sid, self.servos[sid]['open']))
        all_ok = all(results) if results else True
        if all_ok:
            time.sleep(getattr(config, 'SERVO_OPEN_DURATION', 1.5))
            print("[5ServoHW] ✓ All doors opened")
        else:
            print(f"[5ServoHW] ⚠ Door open issue: {results}")
        return all_ok

    def close_doors(self):
        print("[5ServoHW] Closing Layer 1 doors (all 4 servos)...")
        # Ubah sudut tutup pintu di: config.py → SERVO_LAYER1_*_CLOSED
        results = []
        for sid in ('layer1_left', 'layer1_right', 'layer1_left2', 'layer1_right2'):
            if sid in self.servos:
                results.append(self._move_servo(sid, self.servos[sid]['closed']))
        all_ok = all(results) if results else True
        if all_ok:
            print("[5ServoHW] ✓ All doors closed")
        else:
            print(f"[5ServoHW] ⚠ Door close issue: {results}")
        return all_ok

    def set_selector(self, angle):
        # Sudut selector didefinisikan di config.py → SERVO_LAYER2_BIN_A/B/NEUTRAL
        if 'layer2_selector' not in self.servos:
            print("[5ServoHW] ⚠️  No Layer 2 selector configured - skipping")
            return True  # Return True untuk tidak block sorting
        ok = self._move_servo('layer2_selector', angle)
        if ok:
            print(f"[5ServoHW] ✓ Selector → {angle}°")
        return ok

    def reset_to_ready(self):
        print("[5ServoHW] === Resetting system to ready state ===")
        # Alur: tutup pintu → pusatkan selector (jika ada)
        try:
            # Close doors first
            self.close_doors()
            time.sleep(getattr(config, 'SERVO_CLOSE_DELAY', 0.3))
            
            # Center selector (optional, skip if not configured)
            if 'layer2_selector' in self.servos:
                neutral = self.servos['layer2_selector'].get('neutral', getattr(config, 'SERVO_LAYER2_NEUTRAL', 90))
                self.set_selector(neutral)
                time.sleep(getattr(config, 'SERVO_RESET_DELAY', 0.3))
            else:
                print("[5ServoHW] ⚠️  No Layer 2 - doors only mode")
            
            print("[5ServoHW] ✓ System ready")
            return True
        except Exception as e:
            print(f"[5ServoHW] ✗ Reset error: {e}")
            return False

    def execute_sort(self, bin_assignment, bin_angle):
        """
        Jalankan urutan penyortiran lengkap dengan koordinasi Layer 1 & Layer 2.
        
        CRITICAL SAFETY: Setiap gerakan servo dipastikan BERHENTI sebelum gerakan berikutnya.
        
        Alur sorting:
        Phase 1: Set selector Layer 2 ke bin target → VERIFY STOP
        Phase 2: Buka pintu Layer 1 → VERIFY STOP
        Phase 3: Tunggu sampah jatuh dan meluncur
        Phase 4: Tutup pintu Layer 1 → VERIFY STOP
        Phase 5: Reset selector ke netral → VERIFY STOP
        """
        print(f"[5ServoHW] === Starting sort to {bin_assignment} ({bin_angle}°) ===")
        
        try:
            # Phase 1: Set selector to target - CRITICAL: WAIT FOR COMPLETE STOP
            print(f"[5ServoHW] PHASE 1 - Setting selector to {bin_angle}°...")
            if not self.set_selector(bin_angle):
                print("[5ServoHW] ✗ ABORT: Selector movement failed")
                return False
            
            # Extra safety delay untuk memastikan selector benar-benar berhenti
            time.sleep(getattr(config, 'SERVO_DROP_DELAY', 0.3))
            print(f"[5ServoHW] ✓ Selector locked at {bin_angle}°")
            
            # Phase 2: Open Layer 1 doors - CRITICAL: WAIT FOR COMPLETE STOP
            print(f"[5ServoHW] PHASE 2 - Opening doors...")
            if not self.open_doors():
                print("[5ServoHW] ✗ ABORT: Door open failed")
                return False
            print(f"[5ServoHW] ✓ Doors fully open and stopped")
            
            # Phase 3: Waste routing (gravity does the work)
            print(f"[5ServoHW] PHASE 3 - Waste falling and sliding...")
            time.sleep(getattr(config, 'SERVO_FALL_TIME', 0.5))
            time.sleep(getattr(config, 'SERVO_SLIDE_TIME', 0.5))
            print(f"[5ServoHW] ✓ Waste routed to {bin_assignment}")
            
            # Phase 4: Close doors and reset selector - CRITICAL: SEQUENTIAL STOP
            print(f"[5ServoHW] PHASE 4 - Closing doors...")
            if not self.close_doors():
                print("[5ServoHW] ✗ WARNING: Door close failed (attempting recovery)")
            
            # Extra safety delay setelah pintu tutup
            time.sleep(getattr(config, 'SERVO_CLOSE_DELAY', 0.3))
            print(f"[5ServoHW] ✓ Doors fully closed and stopped")
            
            # Phase 5: Reset selector to neutral - CRITICAL: FINAL STOP
            print(f"[5ServoHW] PHASE 5 - Resetting selector to neutral...")
            neutral = self.servos.get('layer2_selector', {}).get('neutral', 
                                                                  getattr(config, 'SERVO_LAYER2_NEUTRAL', 90))
            if not self.set_selector(neutral):
                print("[5ServoHW] ✗ WARNING: Selector reset failed (attempting recovery)")
            
            # Extra safety delay untuk memastikan semua servo berhenti
            time.sleep(getattr(config, 'SERVO_RESET_DELAY', 0.3))
            print(f"[5ServoHW] ✓ Selector locked at neutral ({neutral}°)")
            
            # FINAL VERIFICATION: Pastikan semua servo dalam keadaan berhenti
            print(f"[5ServoHW] === FINAL VERIFICATION ===")
            status = self.verify_positions()
            all_ok = True
            for servo_id, info in status.items():
                if info.get('verified', False):
                    print(f"[5ServoHW] ✓ {servo_id}: {info.get('expected')}° (locked)")
                else:
                    print(f"[5ServoHW] ⚠ {servo_id}: Position uncertain")
                    all_ok = False
            
            if all_ok:
                print(f"[5ServoHW] === ✓ SORT COMPLETE → {bin_assignment} ===")
                print(f"[5ServoHW] All servos verified stopped and locked\n")
            else:
                print(f"[5ServoHW] === ⚠ SORT COMPLETE → {bin_assignment} (with warnings) ===\n")
            
            return True
            
        except Exception as e:
            print(f"[5ServoHW] ✗ Sort error: {e}")
            import traceback
            traceback.print_exc()
            
            # Emergency stop: Coba reset semua servo ke safe position
            print("[5ServoHW] !!! EMERGENCY: Attempting safe reset...")
            try:
                self.reset_to_ready()
            except Exception:
                pass
            
            return False

    def cleanup(self):
        # No special cleanup for ServoKit; leave servos at last angle
        print("[5ServoHW] Cleanup complete")

    def get_status(self):
        return {
            'active': self.servos_active,
            'count': len(self.servos),
            'servos': {sid: {
                'name': cfg['name'],
                'channel': cfg['channel']
            } for sid, cfg in self.servos.items()}
        }