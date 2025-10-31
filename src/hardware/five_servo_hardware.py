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
    """
    Pengelola hardware untuk 5 servo via PCA9685 menggunakan Adafruit ServoKit:
    - Layer 1: Pintu kiri (A+B), pintu kanan (A+B) → total 4 servo
    - Layer 2: Selector/bilah pengarah → 1 servo
    Selaras dengan perilaku di all-code-main (gerak berbasis derajat, 50 Hz).

    Panduan Pengembang (Ringkas):
    - Edit sudut dan pemetaan channel di `config.py`:
      * Layer 1 Kiri A/B: `SERVO_L1_LEFT_A_CH`, `SERVO_L1_LEFT_B_CH`
        Sudut: `SERVO_LAYER1_LEFT_CLOSED` / `SERVO_LAYER1_LEFT_OPEN`,
                `SERVO_LAYER1_LEFT2_CLOSED` / `SERVO_LAYER1_LEFT2_OPEN`
      * Layer 1 Kanan A/B: `SERVO_L1_RIGHT_A_CH`, `SERVO_L1_RIGHT_B_CH`
        Sudut: `SERVO_LAYER1_RIGHT_CLOSED` / `SERVO_LAYER1_RIGHT_OPEN`,
                `SERVO_LAYER1_RIGHT2_CLOSED` / `SERVO_LAYER1_RIGHT2_OPEN`
      * Layer 2 Selector: `SERVO_L2_SELECTOR_CH`,
        Sudut: `SERVO_LAYER2_BIN_A`, `SERVO_LAYER2_BIN_B`, `SERVO_LAYER2_NEUTRAL`
    - Alur gerak (execute_sort): set selector → pintu buka → geser → pintu tutup → selector netral.
    - Arah terbalik? Tukar nilai BIN_A/B di `config.py` atau sesuaikan derajat ±.
    - Pengaturan waktu di `config.py`: `SERVO_OPEN_DURATION`, `SERVO_DROP_DELAY`, `SERVO_FALL_TIME`,
      `SERVO_SLIDE_TIME`, `SERVO_CLOSE_DELAY`, `SERVO_RESET_DELAY`, `SERVO_MOVEMENT_TIME`.
    """

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
            self.kit = ServoKit(channels=16, address=address)
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
            self._setup_servos_config_only()

    def _setup_servos_config_only(self):
        """Muat konfigurasi servo dari config (berfungsi juga untuk simulasi).
        Tempat edit:
        - Channel: `SERVO_L1_*_CH`, `SERVO_L2_SELECTOR_CH` di config.py
        - Sudut: Layer 1 tutup/buka; Layer 2 netral/bin di config.py
        """
        self.servos = {}

        # Layer 1 - Left door (A + optional B)
        left_a_ch = getattr(config, 'SERVO_L1_LEFT_A_CH', None)
        left_b_ch = getattr(config, 'SERVO_L1_LEFT_B_CH', None)
        right_a_ch = getattr(config, 'SERVO_L1_RIGHT_A_CH', None)
        right_b_ch = getattr(config, 'SERVO_L1_RIGHT_B_CH', None)
        sel_ch = getattr(config, 'SERVO_L2_SELECTOR_CH', None)

        if left_a_ch is not None:
            self.servos['layer1_left_a'] = {
                'name': 'Layer 1 Left A',
                'channel': left_a_ch,
                'closed': getattr(config, 'SERVO_LAYER1_LEFT_CLOSED', 0),
                'open': getattr(config, 'SERVO_LAYER1_LEFT_OPEN', 90)
            }
        if left_b_ch is not None:
            self.servos['layer1_left_b'] = {
                'name': 'Layer 1 Left B',
                'channel': left_b_ch,
                'closed': getattr(config, 'SERVO_LAYER1_LEFT2_CLOSED', getattr(config, 'SERVO_LAYER1_LEFT_CLOSED', 0)),
                'open': getattr(config, 'SERVO_LAYER1_LEFT2_OPEN', getattr(config, 'SERVO_LAYER1_LEFT_OPEN', 90))
            }
        if right_a_ch is not None:
            self.servos['layer1_right_a'] = {
                'name': 'Layer 1 Right A',
                'channel': right_a_ch,
                'closed': getattr(config, 'SERVO_LAYER1_RIGHT_CLOSED', 0),
                'open': getattr(config, 'SERVO_LAYER1_RIGHT_OPEN', 90)
            }
        if right_b_ch is not None:
            self.servos['layer1_right_b'] = {
                'name': 'Layer 1 Right B',
                'channel': right_b_ch,
                'closed': getattr(config, 'SERVO_LAYER1_RIGHT2_CLOSED', getattr(config, 'SERVO_LAYER1_RIGHT_CLOSED', 0)),
                'open': getattr(config, 'SERVO_LAYER1_RIGHT2_OPEN', getattr(config, 'SERVO_LAYER1_RIGHT_OPEN', 90))
            }

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
        """Gerakkan channel PCA9685 ke sudut tertentu menggunakan ServoKit."""
        try:
            if not HAS_SERVOKIT or self.kit is None:
                print(f"[5ServoHW] Simulate move CH{channel} → {angle}°")
                return True
            self.kit.servo[channel].angle = angle
            time.sleep(getattr(config, 'SERVO_MOVEMENT_TIME', 0.15))
            return True
        except Exception as e:
            print(f"[5ServoHW] Move error CH{channel} → {angle}°: {e}")
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
        print("[5ServoHW] Opening Layer 1 doors (all pairs)...")
        # Ubah sudut buka pintu di: config.py → SERVO_LAYER1_*_OPEN
        # Buka setiap servo Layer 1 ke sudut 'open'-nya
        results = []
        for sid in ('layer1_left_a', 'layer1_left_b', 'layer1_right_a', 'layer1_right_b'):
            if sid in self.servos:
                results.append(self._move_servo(sid, self.servos[sid]['open']))
        all_ok = all(results) if results else True
        if all_ok:
            time.sleep(getattr(config, 'SERVO_OPEN_DURATION', 1.5))
            print("[5ServoHW] ✓ Doors opened")
        else:
            print(f"[5ServoHW] ⚠ Door open issue: {results}")
        return all_ok

    def close_doors(self):
        print("[5ServoHW] Closing Layer 1 doors (all pairs)...")
        # Ubah sudut tutup pintu di: config.py → SERVO_LAYER1_*_CLOSED
        results = []
        for sid in ('layer1_left_a', 'layer1_left_b', 'layer1_right_a', 'layer1_right_b'):
            if sid in self.servos:
                results.append(self._move_servo(sid, self.servos[sid]['closed']))
        all_ok = all(results) if results else True
        if all_ok:
            print("[5ServoHW] ✓ Doors closed")
        else:
            print(f"[5ServoHW] ⚠ Door close issue: {results}")
        return all_ok

    def set_selector(self, angle):
        # Sudut selector didefinisikan di config.py → SERVO_LAYER2_BIN_A/B/NEUTRAL
        if 'layer2_selector' not in self.servos:
            print("[5ServoHW] No selector configured")
            return False
        ok = self._move_servo('layer2_selector', angle)
        if ok:
            print(f"[5ServoHW] ✓ Selector → {angle}°")
        return ok

    def reset_to_ready(self):
        print("[5ServoHW] === Resetting system to ready state ===")
        # Alur: tutup pintu → pusatkan selector
        try:
            # Close doors first
            self.close_doors()
            time.sleep(getattr(config, 'SERVO_CLOSE_DELAY', 0.3))
            # Center selector
            neutral = self.servos['layer2_selector'].get('neutral', getattr(config, 'SERVO_LAYER2_NEUTRAL', 90)) if 'layer2_selector' in self.servos else getattr(config, 'SERVO_LAYER2_NEUTRAL', 90)
            self.set_selector(neutral)
            time.sleep(getattr(config, 'SERVO_RESET_DELAY', 0.3))
            print("[5ServoHW] ✓ System ready")
            return True
        except Exception as e:
            print(f"[5ServoHW] ✗ Reset error: {e}")
            return False

    def execute_sort(self, bin_assignment, bin_angle):
        print(f"[5ServoHW] === Starting sort to {bin_assignment} ({bin_angle}°) ===")
        # Alur: set selector → buka pintu → tunggu geser → tutup pintu → pusatkan selector
        try:
            # Phase 1: set selector to target
            self.set_selector(bin_angle)
            time.sleep(getattr(config, 'SERVO_DROP_DELAY', 0.3))
            # Phase 2: open Layer 1 doors
            self.open_doors()
            time.sleep(getattr(config, 'SERVO_FALL_TIME', 0.5))
            # Phase 3: slide time on selector
            time.sleep(getattr(config, 'SERVO_SLIDE_TIME', 0.5))
            # Phase 4: close doors and reset selector
            self.close_doors()
            time.sleep(getattr(config, 'SERVO_CLOSE_DELAY', 0.3))
            neutral = self.servos['layer2_selector'].get('neutral', getattr(config, 'SERVO_LAYER2_NEUTRAL', 90)) if 'layer2_selector' in self.servos else getattr(config, 'SERVO_LAYER2_NEUTRAL', 90)
            self.set_selector(neutral)
            time.sleep(getattr(config, 'SERVO_RESET_DELAY', 0.3))

            print(f"[5ServoHW] === ✓ SORT COMPLETE → {bin_assignment} ===")
            return True
        except Exception as e:
            print(f"[5ServoHW] ✗ Sort error: {e}")
            import traceback
            traceback.print_exc()
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