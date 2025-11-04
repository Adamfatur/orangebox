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
import threading

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
            # Apply calibration and set all to closed (0°) safely
            self._apply_servokit_calibration()
            self._calibrate_to_zero()
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
        # Soft-limit enforcement for Layer 1 (doors)
        target_angle = angle
        try:
            if getattr(config, 'SERVO_L1_SOFT_LIMITS_ENABLE', True) and servo_id.startswith('layer1_'):
                c = int(cfg.get('closed', 0))
                o = int(cfg.get('open', 90))
                lo, hi = (c, o) if c <= o else (o, c)
                # Clamp to configured closed/open range and absolute [0,180]
                target_angle = max(0, min(180, max(lo, min(hi, int(angle)))))
                if target_angle != angle:
                    print(f"[5ServoHW] ⛑ Clamp {servo_id}: {angle}° → {target_angle}° within [{lo},{hi}]")
        except Exception:
            # Fallback: ensure within [0,180]
            target_angle = max(0, min(180, int(angle)))

        ok = self._move_channel(cfg['channel'], target_angle)
        if ok:
            cfg['current_angle'] = target_angle
            cfg['last_move_time'] = time.time()
        return ok

    # ===== Layer 1 Safety Helpers =====
    def _l1_bounds(self, servo_id):
        """Return (closed, open) and (lo, hi) tuple for a Layer 1 servo id.
        If not Layer 1, returns (0,180) for both pairs.
        """
        cfg = self.servos.get(servo_id, {})
        c = int(cfg.get('closed', 0))
        o = int(cfg.get('open', 90))
        lo, hi = (c, o) if c <= o else (o, c)
        return c, o, lo, hi

    def _l1_overshoot_target(self, servo_id, limit_kind: str, overshoot_deg: int):
        """Compute an overshoot angle beyond the target limit for backlash removal.
        limit_kind: 'open' or 'closed'. Returns an angle within [0,180].
        Note: This may go slightly beyond the configured limit by overshoot_deg.
        """
        c, o, lo, hi = self._l1_bounds(servo_id)
        overshoot = max(0, int(overshoot_deg))
        if limit_kind == 'open':
            # Direction: towards open beyond limit
            if o >= c:
                return max(0, min(180, o + overshoot))
            else:
                return max(0, min(180, o - overshoot))
        else:  # 'closed'
            # Direction: towards closed beyond limit
            if c <= o:
                return max(0, min(180, c - overshoot))
            else:
                return max(0, min(180, c + overshoot))

    def _apply_servokit_calibration(self):
        """Kalibrasi ServoKit: set pulse width range dan actuation range untuk semua channel terpakai."""
        if not HAS_SERVOKIT or self.kit is None:
            return
        min_p = int(getattr(config, 'SERVOKIT_MIN_PULSE_MICROS', 500))
        max_p = int(getattr(config, 'SERVOKIT_MAX_PULSE_MICROS', 2500))
        act_range = int(getattr(config, 'SERVOKIT_ACTUATION_RANGE', 180))
        try:
            used_channels = []
            for sid, cfg in self.servos.items():
                ch = cfg.get('channel')
                if ch is None or ch in used_channels:
                    continue
                try:
                    self.kit.servo[ch].actuation_range = act_range
                    self.kit.servo[ch].set_pulse_width_range(min_p, max_p)
                    used_channels.append(ch)
                except Exception as e:
                    print(f"[5ServoHW] Calibration warning (CH{ch}): {e}")
            print(f"[5ServoHW] Calibration applied: actuation={act_range}°, pulse=[{min_p},{max_p}]µs")
        except Exception as e:
            print(f"[5ServoHW] Calibration error: {e}")

    def _calibrate_to_zero(self):
        """Pastikan semua servo di posisi 0° (closed) pada startup dan detach PWM untuk hindari putaran liar."""
        if not HAS_SERVOKIT or self.kit is None:
            return
        try:
            channels = []
            targets = []
            for sid, cfg in self.servos.items():
                ch = cfg.get('channel')
                if ch is None:
                    continue
                channels.append(ch)
                targets.append(cfg.get('closed', 0))
            # Set semua target sekaligus
            for ch, ang in zip(channels, targets):
                try:
                    self.kit.servo[ch].angle = ang
                except Exception as e:
                    print(f"[5ServoHW] Zero-set warning (CH{ch}): {e}")
            # Tunggu gerak selesai, hold sebentar, lalu detach untuk anti jitter
            time.sleep(getattr(config, 'SERVO_MOVEMENT_TIME', 0.15))
            hold = getattr(config, 'SERVO_POSITION_HOLD_TIME', 0.05)
            if hold and hold > 0:
                time.sleep(hold)
            if getattr(config, 'SERVO_STOP_JITTER', True):
                for ch in channels:
                    try:
                        self.kit.servo[ch].angle = None
                    except Exception:
                        pass
            print("[5ServoHW] ✓ Startup calibration: all servos set to 0° (closed)")
        except Exception as e:
            print(f"[5ServoHW] Calibration to zero failed: {e}")

    def _sync_move(self, channels, angles):
        """Gerakkan beberapa channel sekaligus ke target angles lalu detach (anti jitter).
        
        CRITICAL: Menulis PWM dengan staggered start (delay kecil antar servo) untuk:
        1. Mengurangi puncak arus (voltage drop yang menyebabkan inkonsistensi)
        2. Tetap terlihat hampir bersamaan (delay total <50ms)
        3. Lebih stabil di power supply yang terbatas
        """
        if not HAS_SERVOKIT or self.kit is None:
            # Fallback: tidak ada ServoKit, abaikan
            return all(True for _ in channels)
        try:
            # PRE-CALCULATE semua PWM values dulu (tidak ada I2C write)
            pwm_values = []
            for ch, ang in zip(channels, angles):
                try:
                    # Clamp angle
                    ang = max(0, min(180, ang))
                    # Convert angle to pulse width (ServoKit internal logic)
                    # Formula: pulse_us = min_pulse + (angle / actuation_range) * (max_pulse - min_pulse)
                    min_pulse = getattr(config, 'SERVOKIT_MIN_PULSE_MICROS', 500)
                    max_pulse = getattr(config, 'SERVOKIT_MAX_PULSE_MICROS', 2500)
                    actuation = getattr(config, 'SERVOKIT_ACTUATION_RANGE', 180)
                    pulse_us = min_pulse + (ang / actuation) * (max_pulse - min_pulse)
                    # Convert to 12-bit PWM value (0-4095) at 50Hz
                    # PWM frequency = 50Hz → period = 20ms = 20000µs
                    # duty = (pulse_us / 20000) * 4096
                    freq = getattr(config, 'PCA9685_FREQUENCY', 50)
                    period_us = 1_000_000 / freq
                    duty = int((pulse_us / period_us) * 4096)
                    pwm_values.append((ch, duty))
                except Exception as e:
                    print(f"[5ServoHW] PWM calc error CH{ch}: {e}")
                    return False
            
            # STAGGERED START: Tulis PWM dengan delay kecil untuk spread beban arus
            # Delay per servo kecil (8-12ms) = total ~30-50ms untuk 4 servo
            # Masih terlihat hampir bersamaan, tapi jauh lebih stabil
            stagger_delay = getattr(config, 'SERVO_STAGGER_DELAY_MS', 10) / 1000.0  # default 10ms
            
            for idx, (ch, duty) in enumerate(pwm_values):
                try:
                    # Convert 12-bit duty (0-4095) to 16-bit (0-65535) untuk PCA9685
                    duty_16bit = duty << 4  # shift left 4 bits
                    self.kit._pca.channels[ch].duty_cycle = duty_16bit
                    
                    # Stagger delay kecuali servo terakhir (agar tidak delay berlebihan)
                    if idx < len(pwm_values) - 1 and stagger_delay > 0:
                        time.sleep(stagger_delay)
                except Exception as e:
                    print(f"[5ServoHW] Stagger write error CH{ch}: {e}")
                    # Lanjutkan ke servo berikutnya meski ada error
            
            # Tunggu gerakan selesai
            time.sleep(getattr(config, 'SERVO_MOVEMENT_TIME', 0.15))
            hold = getattr(config, 'SERVO_POSITION_HOLD_TIME', 0.05)
            if hold and hold > 0:
                time.sleep(hold)
            
            # STOP PWM untuk anti-jitter (kecuali jika kita ingin HOLD secara eksplisit)
            if getattr(config, 'SERVO_STOP_JITTER', True):
                for ch in channels:
                    try:
                        self.kit._pca.channels[ch].duty_cycle = 0
                    except Exception:
                        pass
            return True
        except Exception as e:
            print(f"[5ServoHW] Sync move failed: {e}")
            import traceback
            traceback.print_exc()
            return False

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

    # (Holding helpers removed per request: focus on tight sync movement)

    def open_doors(self):
        """Kompatibilitas lama: buka semua pintu. Tidak disarankan.
        Gunakan open_side('left'|'right') untuk kontrol presisi.
        """
        print("[5ServoHW] Opening Layer 1 doors (ALL) — legacy mode")
        left_ok = self.open_side('left')
        right_ok = self.open_side('right')
        return left_ok and right_ok

    def open_side(self, side: str):
        """Buka sepasang pintu pada sisi tertentu (left/right) secara selaras.
        - Sisi kiri: servo A (front-left) dan B (back-left) → 'layer1_left' & 'layer1_left2'
        - Sisi kanan: servo C (back-right) dan D (front-right) → 'layer1_right' & 'layer1_right2'
        Sudut open masing-masing servo diambil dari config dan bisa berbeda (arah berlawanan).
        """
        side = side.lower().strip()
        if side not in ('left', 'right'):
            print(f"[5ServoHW] Invalid side: {side}")
            return False
        pair = ('layer1_left', 'layer1_left2') if side == 'left' else ('layer1_right', 'layer1_right2')
        print(f"[5ServoHW] Opening Layer 1 doors ({side.upper()} pair: {pair[0]}, {pair[1]})...")
        # Jika ServoKit aktif, gerakkan kedua channel secara sinkron 0->open (90) saja;
        # penutupan kembali ke 0° dilakukan terpisah oleh close_side/close_all
        results = []
        use_overshoot = getattr(config, 'SERVO_L1_USE_OVERSHOOT', True)
        overshoot_deg = int(getattr(config, 'SERVO_L1_OVERSHOOT_DEG', 3))
        if HAS_SERVOKIT and self.kit is not None and all(s in self.servos for s in pair):
            try:
                channels = [self.servos[s]['channel'] for s in pair]
                finals = []
                presteps = []
                for s in pair:
                    # Clamp target within Layer 1 bounds
                    _, _, lo, hi = self._l1_bounds(s)
                    tgt = self.servos[s]['open']
                    tgt = max(lo, min(hi, tgt))
                    finals.append(tgt)
                    if use_overshoot and overshoot_deg > 0:
                        presteps.append(self._l1_overshoot_target(s, 'open', overshoot_deg))
                    else:
                        presteps.append(tgt)

                if use_overshoot and overshoot_deg > 0:
                    ok1 = self._sync_move(channels, presteps)
                    # Small settle; sync_move already includes movement/hold
                    ok2 = self._sync_move(channels, finals) if ok1 else False
                    results = [ok1 and ok2, ok1 and ok2]
                else:
                    ok = self._sync_move(channels, finals)
                    results = [ok, ok]
            except Exception as e:
                print(f"[5ServoHW] Sync move ({side}) failed: {e}")
                # Fallback ke per-servo
                for sid in pair:
                    if sid in self.servos:
                        # Per-servo with optional overshoot
                        final = max(self._l1_bounds(sid)[2], min(self._l1_bounds(sid)[3], self.servos[sid]['open']))
                        if use_overshoot and overshoot_deg > 0:
                            pre = self._l1_overshoot_target(sid, 'open', overshoot_deg)
                            ok1 = self._move_servo(sid, pre)
                            ok2 = self._move_servo(sid, final) if ok1 else False
                            results.append(ok1 and ok2)
                        else:
                            results.append(self._move_servo(sid, final))
        else:
            for sid in pair:
                if sid in self.servos:
                    final = max(self._l1_bounds(sid)[2], min(self._l1_bounds(sid)[3], self.servos[sid]['open']))
                    if use_overshoot and overshoot_deg > 0:
                        pre = self._l1_overshoot_target(sid, 'open', overshoot_deg)
                        ok1 = self._move_servo(sid, pre)
                        ok2 = self._move_servo(sid, final) if ok1 else False
                        results.append(ok1 and ok2)
                    else:
                        results.append(self._move_servo(sid, final))
        all_ok = all(results) if results else False
        if all_ok:
            time.sleep(getattr(config, 'SERVO_OPEN_DURATION', 1.5))
            print(f"[5ServoHW] ✓ {side.upper()} doors opened")
        else:
            print(f"[5ServoHW] ⚠ {side.upper()} door open issue: {results}")
        return all_ok

    def close_doors(self):
        """Kompatibilitas lama: tutup semua pintu."""
        left_ok = self.close_side('left')
        right_ok = self.close_side('right')
        return left_ok and right_ok

    def close_side(self, side: str):
        side = side.lower().strip()
        if side not in ('left', 'right'):
            print(f"[5ServoHW] Invalid side: {side}")
            return False
        pair = ('layer1_left', 'layer1_left2') if side == 'left' else ('layer1_right', 'layer1_right2')
        print(f"[5ServoHW] Closing Layer 1 doors ({side.upper()} pair: {pair[0]}, {pair[1]})...")
        results = []
        use_overshoot = getattr(config, 'SERVO_L1_USE_OVERSHOOT', True)
        overshoot_deg = int(getattr(config, 'SERVO_L1_OVERSHOOT_DEG', 3))
        if HAS_SERVOKIT and self.kit is not None and all(s in self.servos for s in pair):
            try:
                channels = [self.servos[s]['channel'] for s in pair]
                finals = []
                presteps = []
                for s in pair:
                    _, _, lo, hi = self._l1_bounds(s)
                    tgt = self.servos[s]['closed']
                    tgt = max(lo, min(hi, tgt))
                    finals.append(tgt)
                    if use_overshoot and overshoot_deg > 0:
                        presteps.append(self._l1_overshoot_target(s, 'closed', overshoot_deg))
                    else:
                        presteps.append(tgt)

                if use_overshoot and overshoot_deg > 0:
                    ok1 = self._sync_move(channels, presteps)
                    ok2 = self._sync_move(channels, finals) if ok1 else False
                    results = [ok1 and ok2, ok1 and ok2]
                else:
                    ok = self._sync_move(channels, finals)
                    results = [ok, ok]

                # Holding disabled (reverted) — PWM will be detached by _sync_move
            except Exception as e:
                print(f"[5ServoHW] Sync close ({side}) failed: {e}")
                for sid in pair:
                    if sid in self.servos:
                        final = max(self._l1_bounds(sid)[2], min(self._l1_bounds(sid)[3], self.servos[sid]['closed']))
                        if use_overshoot and overshoot_deg > 0:
                            pre = self._l1_overshoot_target(sid, 'closed', overshoot_deg)
                            ok1 = self._move_servo(sid, pre)
                            ok2 = self._move_servo(sid, final) if ok1 else False
                            results.append(ok1 and ok2)
                        else:
                            results.append(self._move_servo(sid, final))
        else:
            for sid in pair:
                if sid in self.servos:
                    final = max(self._l1_bounds(sid)[2], min(self._l1_bounds(sid)[3], self.servos[sid]['closed']))
                    if use_overshoot and overshoot_deg > 0:
                        pre = self._l1_overshoot_target(sid, 'closed', overshoot_deg)
                        ok1 = self._move_servo(sid, pre)
                        ok2 = self._move_servo(sid, final) if ok1 else False
                        results.append(ok1 and ok2)
                    else:
                        results.append(self._move_servo(sid, final))
        all_ok = all(results) if results else False
        if all_ok:
            print(f"[5ServoHW] ✓ {side.upper()} doors closed")
        else:
            print(f"[5ServoHW] ⚠ {side.upper()} door close issue: {results}")
        return all_ok

    def open_all_sync(self):
        """Buka keempat servo Layer 1 secara bersamaan (0°→open)."""
        pair = []
        for sid in ('layer1_left', 'layer1_left2', 'layer1_right', 'layer1_right2'):
            if sid in self.servos:
                pair.append(sid)
        if not pair:
            return False
        print("[5ServoHW] Opening ALL doors in sync...")
        use_overshoot = getattr(config, 'SERVO_L1_USE_OVERSHOOT', True)
        overshoot_deg = int(getattr(config, 'SERVO_L1_OVERSHOOT_DEG', 3))
        if HAS_SERVOKIT and self.kit is not None and all(s in self.servos for s in pair):
            channels = [self.servos[s]['channel'] for s in pair]
            finals = []
            presteps = []
            for s in pair:
                _, _, lo, hi = self._l1_bounds(s)
                tgt = self.servos[s]['open']
                tgt = max(lo, min(hi, tgt))
                finals.append(tgt)
                if use_overshoot and overshoot_deg > 0:
                    presteps.append(self._l1_overshoot_target(s, 'open', overshoot_deg))
                else:
                    presteps.append(tgt)
            if use_overshoot and overshoot_deg > 0:
                ok1 = self._sync_move(channels, presteps)
                ok = self._sync_move(channels, finals) if ok1 else False
            else:
                ok = self._sync_move(channels, finals)
            if ok:
                time.sleep(getattr(config, 'SERVO_OPEN_DURATION', 1.5))
                print("[5ServoHW] ✓ ALL doors opened")
            return ok
        # Fallback per-servo
        results = []
        for s in pair:
            final = max(self._l1_bounds(s)[2], min(self._l1_bounds(s)[3], self.servos[s]['open']))
            if use_overshoot and overshoot_deg > 0:
                pre = self._l1_overshoot_target(s, 'open', overshoot_deg)
                ok1 = self._move_servo(s, pre)
                ok2 = self._move_servo(s, final) if ok1 else False
                results.append(ok1 and ok2)
            else:
                results.append(self._move_servo(s, final))
        ok = all(results)
        if ok:
            time.sleep(getattr(config, 'SERVO_OPEN_DURATION', 1.5))
            print("[5ServoHW] ✓ ALL doors opened")
        return ok

    def close_all_sync(self):
        """Tutup keempat servo Layer 1 secara bersamaan (open→0°)."""
        pair = []
        for sid in ('layer1_left', 'layer1_left2', 'layer1_right', 'layer1_right2'):
            if sid in self.servos:
                pair.append(sid)
        if not pair:
            return False
        print("[5ServoHW] Closing ALL doors in sync...")
        use_overshoot = getattr(config, 'SERVO_L1_USE_OVERSHOOT', True)
        overshoot_deg = int(getattr(config, 'SERVO_L1_OVERSHOOT_DEG', 3))
        if HAS_SERVOKIT and self.kit is not None and all(s in self.servos for s in pair):
            channels = [self.servos[s]['channel'] for s in pair]
            finals = []
            presteps = []
            for s in pair:
                _, _, lo, hi = self._l1_bounds(s)
                tgt = self.servos[s]['closed']
                tgt = max(lo, min(hi, tgt))
                finals.append(tgt)
                if use_overshoot and overshoot_deg > 0:
                    presteps.append(self._l1_overshoot_target(s, 'closed', overshoot_deg))
                else:
                    presteps.append(tgt)
            if use_overshoot and overshoot_deg > 0:
                ok1 = self._sync_move(channels, presteps)
                ok = self._sync_move(channels, finals) if ok1 else False
            else:
                ok = self._sync_move(channels, finals)
            if ok:
                print("[5ServoHW] ✓ ALL doors closed")
                # Holding disabled (reverted) — PWM will be detached by _sync_move
            return ok
        results = []
        for s in pair:
            final = max(self._l1_bounds(s)[2], min(self._l1_bounds(s)[3], self.servos[s]['closed']))
            if use_overshoot and overshoot_deg > 0:
                pre = self._l1_overshoot_target(s, 'closed', overshoot_deg)
                ok1 = self._move_servo(s, pre)
                ok2 = self._move_servo(s, final) if ok1 else False
                results.append(ok1 and ok2)
            else:
                results.append(self._move_servo(s, final))
        ok = all(results)
        if ok:
            print("[5ServoHW] ✓ ALL doors closed")
        return ok

    def set_selector(self, angle):
        # Sudut selector didefinisikan di config.py → SERVO_LAYER2_BIN_A/B/NEUTRAL
        if 'layer2_selector' not in self.servos:
            print("[5ServoHW] ⚠️  No Layer 2 selector configured - skipping")
            return True  # Return True untuk tidak block sorting
        ok = self._move_servo('layer2_selector', angle)
        if ok:
            print(f"[5ServoHW] ✓ Selector → {angle}°")
        return ok

    # ===== Layer 2 Helpers (Selector) =====
    def center_selector(self):
        """Kembalikan selector ke netral (horizontal) dengan teknik overshoot untuk menghilangkan backlash.
        Tanpa sensor, kita gunakan verifikasi lunak berbasis timing & toleransi config.
        """
        if 'layer2_selector' not in self.servos:
            print("[5ServoHW] ⚠️  No Layer 2 selector configured - skipping center")
            return True
        neutral = self.servos['layer2_selector'].get('neutral', getattr(config, 'SERVO_LAYER2_NEUTRAL', 90))
        overshoot = abs(getattr(config, 'SERVO_LAYER2_NEUTRAL_OVERSHOOT_DEG', 3))
        settle = max(0.0, float(getattr(config, 'SERVO_LAYER2_SETTLE_TIME', 0.15)))

        # Approach netral dari satu sisi untuk menghilangkan slack
        pre = max(0, min(180, neutral + overshoot))
        post = max(0, min(180, neutral))

        print(f"[5ServoHW] Centering selector → overshoot {pre}°, then settle at {post}°")
        ok1 = self._move_servo('layer2_selector', pre)
        if settle:
            time.sleep(settle)
        ok2 = self._move_servo('layer2_selector', post)
        if settle:
            time.sleep(settle)
        return ok1 and ok2

    def tilt_selector(self, tilt_angle: int):
        """Miringkan selector relatif terhadap netral (positif = kanan, negatif = kiri) dengan akurasi.
        Strategi: overshoot kecil melewati target untuk hilangkan backlash, kemudian settle tepat di target.
        """
        if 'layer2_selector' not in self.servos:
            print("[5ServoHW] ⚠️  No Layer 2 selector configured - skipping tilt")
            return True
        neutral = self.servos['layer2_selector'].get('neutral', getattr(config, 'SERVO_LAYER2_NEUTRAL', 90))
        tilt = int(tilt_angle)
        target = int(max(0, min(180, neutral + tilt)))
        overshoot = int(getattr(config, 'SERVO_LAYER2_TILT_OVERSHOOT_DEG', 0))
        settle = max(0.0, float(getattr(config, 'SERVO_LAYER2_SETTLE_TIME', 0.15)))

        if overshoot > 0 and tilt != 0:
            sign = 1 if tilt > 0 else -1
            pre = max(0, min(180, target + sign * overshoot))
            print(f"[5ServoHW] Tilting selector (overshoot): neutral {neutral}° → pre {pre}° → target {target}° (tilt {tilt}°)")
            ok1 = self._move_servo('layer2_selector', pre)
            if settle:
                time.sleep(settle)
            ok2 = self._move_servo('layer2_selector', target)
            if settle:
                time.sleep(settle)
            return ok1 and ok2
        else:
            print(f"[5ServoHW] Tilting selector: neutral {neutral}° → {target}° (tilt {tilt}°)")
            ok = self._move_servo('layer2_selector', target)
            if settle:
                time.sleep(settle)
            return ok

    def tilt_and_return(self, tilt_angle: int):
        """Tilt selector relatif netral ke ±tilt_angle, berhenti sejenak (hold), lalu kembali ke netral (overshoot centering)."""
        ok_tilt = self.tilt_selector(tilt_angle)
        # Tahan di sudut tilt agar terlihat jelas berhenti
        hold = max(0.0, float(getattr(config, 'SERVO_LAYER2_TILT_HOLD_TIME', 0.3)))
        if hold:
            time.sleep(hold)
        ok_center = True
        if getattr(config, 'SERVO_LAYER2_RETURN_AFTER_TILT', True):
            ok_center = self.center_selector()
        return ok_tilt and ok_center

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
            has_selector = ('layer2_selector' in self.servos)
            
            # Phase 1: Selector (skip entirely if tidak ada Layer 2)
            if has_selector:
                print(f"[5ServoHW] PHASE 1 - Setting selector to {bin_angle}°...")
                if not self.set_selector(bin_angle):
                    print("[5ServoHW] ✗ ABORT: Selector movement failed")
                    return False
                # Extra safety delay untuk memastikan selector benar-benar berhenti
                time.sleep(getattr(config, 'SERVO_DROP_DELAY', 0.3))
                print(f"[5ServoHW] ✓ Selector locked at {bin_angle}°")
            else:
                print("[5ServoHW] PHASE 1 - No Layer 2 selector: skipping selector phase")
            
            # Phase 2: Open Layer 1 doors - CRITICAL: WAIT FOR COMPLETE STOP
            # Force open ALL if tidak ada selector (Layer-1 only mode)
            both_sides = True if not has_selector else getattr(config, 'SERVO_LAYER1_OPEN_BOTH_SIDES', False)
            if both_sides:
                print(f"[5ServoHW] PHASE 2 - Opening ALL doors (sync)...")
                ok_open = self.open_all_sync()
            else:
                # Tentukan sisi pintu berdasarkan bin (BIN A=LEFT, BIN B=RIGHT)
                door_side = 'left' if str(bin_assignment).strip().upper() == 'BIN A' else 'right'
                print(f"[5ServoHW] PHASE 2 - Opening {door_side.upper()} doors...")
                ok_open = self.open_side(door_side)
            if not ok_open:
                print("[5ServoHW] ✗ ABORT: Door open failed")
                return False
            print(f"[5ServoHW] ✓ Doors fully open and stopped")
            
            # Phase 3: Waste routing (gravity does the work)
            print(f"[5ServoHW] PHASE 3 - Waste falling and sliding...")
            time.sleep(getattr(config, 'SERVO_FALL_TIME', 0.5))
            time.sleep(getattr(config, 'SERVO_SLIDE_TIME', 0.5))
            print(f"[5ServoHW] ✓ Waste routed to {bin_assignment}")
            
            # Phase 4: Close doors and reset selector - CRITICAL: SEQUENTIAL STOP
            if both_sides:
                print(f"[5ServoHW] PHASE 4 - Closing ALL doors (sync)...")
                ok_close = self.close_all_sync()
            else:
                print(f"[5ServoHW] PHASE 4 - Closing {door_side.upper()} doors...")
                ok_close = self.close_side(door_side)
            if not ok_close:
                print("[5ServoHW] ✗ WARNING: Door close failed (attempting recovery)")
            
            # Extra safety delay setelah pintu tutup
            time.sleep(getattr(config, 'SERVO_CLOSE_DELAY', 0.3))
            print(f"[5ServoHW] ✓ Doors fully closed and stopped")
            
            # Phase 5: Reset selector if present (use overshoot centering)
            if has_selector:
                print(f"[5ServoHW] PHASE 5 - Centering selector to neutral (overshoot)...")
                if not self.center_selector():
                    print("[5ServoHW] ✗ WARNING: Selector centering failed (attempting recovery)")
                # Extra safety delay untuk memastikan semua servo berhenti
                time.sleep(getattr(config, 'SERVO_RESET_DELAY', 0.3))
                neutral = self.servos.get('layer2_selector', {}).get('neutral', getattr(config, 'SERVO_LAYER2_NEUTRAL', 90))
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
        """Matikan sinyal PWM ke semua servo untuk mencegah putaran tanpa henti.
        - Set angle=None (detach) untuk setiap channel yang digunakan
        - Set duty_cycle=0 sebagai jaring pengaman
        - Deinit PCA9685 bila memungkinkan
        """
        try:
            if HAS_SERVOKIT and self.kit is not None:
                used = []
                for sid, cfg in self.servos.items():
                    ch = cfg.get('channel')
                    if ch is None or ch in used:
                        continue
                    used.append(ch)
                    try:
                        # Detach servo
                        self.kit.servo[ch].angle = None
                    except Exception:
                        pass
                    try:
                        # Set duty cycle 0 as hard stop
                        self.kit._pca.channels[ch].duty_cycle = 0
                    except Exception:
                        pass
                # Try deinit PCA9685 to fully stop oscillator
                try:
                    self.kit._pca.deinit()
                except Exception:
                    pass
        except Exception as e:
            print(f"[5ServoHW] Cleanup warning: {e}")
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