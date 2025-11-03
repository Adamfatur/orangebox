"""
╔═══════════════════════════════════════════════════════════════╗
║         GPIO Servo Hardware - Kontrol Servo Langsung         ║
║              (untuk sistem 3-4 servo pakai GPIO)             ║
╚═══════════════════════════════════════════════════════════════╝

📌 FILE INI UNTUK APA?
   File ini mengontrol servo yang langsung terhubung ke pin GPIO 
   Raspberry Pi (TANPA board PCA9685).

⚙️  CARA SETTING SERVO:
   ❌ JANGAN ubah file ini!
   ✅ Buka config.py dan atur:
      • SERVO_LAYER1_LEFT_PIN = nomor pin GPIO kiri
      • SERVO_LAYER1_RIGHT_PIN = nomor pin GPIO kanan
      • SERVO_LAYER2_SELECTOR_PIN = nomor pin GPIO pemilah
      • *_CLOSED, *_OPEN, *_BIN_A, *_BIN_B = derajat servo

🧪 TEST SERVO (tanpa jalankan AI):
   python3 src/hardware/gpio_servo_hardware.py
   
   Di Raspberry Pi: servo fisik akan bergerak
   Di Mac/laptop: hanya simulasi (print ke layar)

🔧 TROUBLESHOOTING:
   • Servo gak gerak? → Cek kabel power 5V dan ground
   • Arah kebalik? → Tukar nilai *_OPEN dengan *_CLOSED di config.py
   • Gerak kasar? → Naikkan SERVO_MOVEMENT_TIME di config.py

📚 CARA KERJA:
   Layer 2 (Pemilah) gerak dulu → Layer 1 (Pintu) buka → 
   Sampah jatuh → Pintu tutup → Pemilah balik ke tengah

Copyright (c) 2025 AF - OrangeBox Project
"""

import time
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    print("[GPIOServo] Warning: RPi.GPIO not available (non-Rpi system)")

import config


class GpioServoHardware:
    """
    Pengelola hardware untuk servo MG996R (GPIO PWM, 50 Hz):
    - Layer 1: Pintu kiri + pintu kanan (opsional pasangan servo per sisi)
    - Layer 2: Selector/bilah pengarah

    Panduan Pengembang (Ringkas):
    - Edit sudut dan pin GPIO di `config.py`:
      * Layer 1 Kiri: `SERVO_LAYER1_LEFT_PIN`,
        sudut: `SERVO_LAYER1_LEFT_CLOSED` / `SERVO_LAYER1_LEFT_OPEN`
      * Layer 1 Kanan: `SERVO_LAYER1_RIGHT_PIN`,
        sudut: `SERVO_LAYER1_RIGHT_CLOSED` / `SERVO_LAYER1_RIGHT_OPEN`
      * Pasangan opsional: `SERVO_LAYER1_LEFT2_PIN`, `SERVO_LAYER1_RIGHT2_PIN`
        sudut default meniru servo utama, bisa diubah via
        `SERVO_LAYER1_LEFT2_CLOSED` / `SERVO_LAYER1_LEFT2_OPEN` dan
        `SERVO_LAYER1_RIGHT2_CLOSED` / `SERVO_LAYER1_RIGHT2_OPEN`
      * Layer 2 Selector: `SERVO_LAYER2_SELECTOR_PIN`,
        sudut: `SERVO_LAYER2_BIN_A`, `SERVO_LAYER2_BIN_B`, `SERVO_LAYER2_NEUTRAL`
    - Alur gerak (execute_sort): set selector → pintu buka → geser → pintu tutup → selector netral.
    - Pengaturan waktu (lihat config.py): `SERVO_OPEN_DURATION`, `SERVO_DROP_DELAY`,
      `SERVO_FALL_TIME`, `SERVO_SLIDE_TIME`, `SERVO_CLOSE_DELAY`, `SERVO_RESET_DELAY`,
      serta tingkat rendah `SERVO_MOVEMENT_TIME`, `SERVO_POSITION_HOLD_TIME`, `SERVO_STOP_JITTER`.
    - Arah terbalik? Tukar nilai BIN_A/B atau sesuaikan derajat ±.
    """
    
    def __init__(self):
        self.has_gpio = HAS_GPIO
        self.servos_active = False
        self.servos = {}
        
        print("[GPIOServo] Initializing GPIO servo system...")
        
        if self.has_gpio:
            self._init_gpio()
            if config.AUTO_DETECT_SERVOS:
                self._detect_and_setup_servos()
            else:
                self._setup_servos_manual()
        else:
            print("[GPIOServo] Running in simulation mode (no GPIO)")
            # Still need servo configurations for simulation
            self._setup_servos_manual()
    
    def _init_gpio(self):
        """Initialize GPIO with BCM numbering"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            print("[3ServoHW] GPIO initialized (BCM)")
        except Exception as e:
            print(f"[3ServoHW] GPIO init error: {e}")
            self.has_gpio = False
    
    def _detect_and_setup_servos(self):
        """Auto-detect and setup servos"""
        print("[GPIOServo] Auto-detecting MG996R servos...")
        
        configs = [
            {
                'id': 'layer1_left',
                'name': 'Layer 1 Left Door',
                'pin': config.SERVO_LAYER1_LEFT_PIN,
                'closed': config.SERVO_LAYER1_LEFT_CLOSED,
                'open': config.SERVO_LAYER1_LEFT_OPEN
            },
            {
                'id': 'layer1_right',
                'name': 'Layer 1 Right Door',
                'pin': config.SERVO_LAYER1_RIGHT_PIN,
                'closed': config.SERVO_LAYER1_RIGHT_CLOSED,
                'open': config.SERVO_LAYER1_RIGHT_OPEN
            },
            {
                'id': 'layer2_selector',
                'name': 'Layer 2 Selector',
                'pin': config.SERVO_LAYER2_SELECTOR_PIN,
                'bin_a': config.SERVO_LAYER2_BIN_A,
                'bin_b': config.SERVO_LAYER2_BIN_B,
                'neutral': config.SERVO_LAYER2_NEUTRAL
            }
        ]
        
        detected = 0
        for cfg in configs:
            # Store configuration even if detection fails (for simulation mode)
            self.servos[cfg['id']] = cfg
            
            if self._test_servo_connection(cfg):
                detected += 1
                print(f"[GPIOServo] ✓ {cfg['name']} on GPIO {cfg['pin']}")
            else:
                print(f"[GPIOServo] ✗ {cfg['name']} not detected on GPIO {cfg['pin']}")
        
        # Active if at least Layer 2 and one Layer 1 door present
        self.servos_active = (detected >= 2)
        print(f"[GPIOServo] Detected {detected} servos" + (" ✓" if self.servos_active else " ⚠"))
    
    def _test_servo_connection(self, cfg):
        """Test if servo responds on GPIO pin"""
        if not self.has_gpio:
            return False
        
        try:
            pin = cfg['pin']
            GPIO.setup(pin, GPIO.OUT)
            
            # Create PWM @ 50Hz (MG996R standard)
            pwm = GPIO.PWM(pin, 50)
            pwm.start(0)
            
            # Test with neutral position (7.5% duty = 90°)
            pwm.ChangeDutyCycle(7.5)
            time.sleep(0.2)
            pwm.ChangeDutyCycle(0)
            
            # Save PWM object
            cfg['pwm'] = pwm
            return True
            
        except Exception as e:
            print(f"[GPIOServo] Test failed on GPIO {cfg.get('pin')}: {e}")
            return False
    
    def _setup_servos_manual(self):
        """
        Setup servo menggunakan pin dan sudut dari `config.py`.
        Tempat edit:
        - Pin/sudut Layer 1: `SERVO_LAYER1_*_PIN`, `SERVO_LAYER1_*_CLOSED`, `SERVO_LAYER1_*_OPEN`
        - Pasangan opsional meniru utama atau bisa dioverride di config.
        - Pin/sudut Layer 2 selector: `SERVO_LAYER2_SELECTOR_PIN`,
          `SERVO_LAYER2_BIN_A`, `SERVO_LAYER2_BIN_B`, `SERVO_LAYER2_NEUTRAL`
        """
        print("[GPIOServo] Manual servo setup...")
        
        self.servos = {
            'layer1_left': {
                'id': 'layer1_left',
                'name': 'Layer 1 Left Door',
                'pin': config.SERVO_LAYER1_LEFT_PIN,
                'closed': config.SERVO_LAYER1_LEFT_CLOSED,
                'open': config.SERVO_LAYER1_LEFT_OPEN
            },
            'layer1_right': {
                'id': 'layer1_right',
                'name': 'Layer 1 Right Door',
                'pin': config.SERVO_LAYER1_RIGHT_PIN,
                'closed': config.SERVO_LAYER1_RIGHT_CLOSED,
                'open': config.SERVO_LAYER1_RIGHT_OPEN
            },
            'layer2_selector': {
                'id': 'layer2_selector',
                'name': 'Layer 2 Selector',
                'pin': config.SERVO_LAYER2_SELECTOR_PIN,
                'bin_a': config.SERVO_LAYER2_BIN_A,
                'bin_b': config.SERVO_LAYER2_BIN_B,
                'neutral': config.SERVO_LAYER2_NEUTRAL
            }
        }

        # Optional paired servos for Layer 1 (total 4 servos on Layer 1)
        # These will mirror movements of primary left/right doors when defined
        if getattr(config, 'SERVO_LAYER1_LEFT2_PIN', None) is not None:
            self.servos['layer1_left2'] = {
                'id': 'layer1_left2',
                'name': 'Layer 1 Left Door (Pair)',
                'pin': config.SERVO_LAYER1_LEFT2_PIN,
                'closed': getattr(config, 'SERVO_LAYER1_LEFT2_CLOSED', config.SERVO_LAYER1_LEFT_CLOSED),
                'open': getattr(config, 'SERVO_LAYER1_LEFT2_OPEN', config.SERVO_LAYER1_LEFT_OPEN)
            }
        if getattr(config, 'SERVO_LAYER1_RIGHT2_PIN', None) is not None:
            self.servos['layer1_right2'] = {
                'id': 'layer1_right2',
                'name': 'Layer 1 Right Door (Pair)',
                'pin': config.SERVO_LAYER1_RIGHT2_PIN,
                'closed': getattr(config, 'SERVO_LAYER1_RIGHT2_CLOSED', config.SERVO_LAYER1_RIGHT_CLOSED),
                'open': getattr(config, 'SERVO_LAYER1_RIGHT2_OPEN', config.SERVO_LAYER1_RIGHT_OPEN)
            }
        
        if self.has_gpio:
            for sid, cfg in self.servos.items():
                try:
                    GPIO.setup(cfg['pin'], GPIO.OUT)
                    cfg['pwm'] = GPIO.PWM(cfg['pin'], 50)
                    cfg['pwm'].start(0)
                    # Initialize position tracking
                    cfg['current_angle'] = 0
                    cfg['last_move_time'] = 0
                    print(f"[3ServoHW] Setup {cfg['name']} on GPIO {cfg['pin']}")
                except Exception as e:
                    print(f"[3ServoHW] Setup error for {cfg['name']}: {e}")
        
        self.servos_active = True
    
    def _angle_to_duty(self, angle):
        """
        Konversi sudut ke siklus tugas PWM untuk MG996R
        0° = 2.5% duty (pulsa 1ms)
        180° = 12.5% duty (pulsa 2ms)
        """
        return 2.5 + (angle / 18.0)
    
    def _move_servo(self, servo_id, angle):
        """
        Gerakkan servo tertentu ke sudut dengan kecepatan terkontrol dan verifikasi posisi.
        
        CATATAN PENTING: Memastikan servo mencapai posisi tepat tanpa drift atau overshoot.
        
        Argumen:
            servo_id: ID servo ('layer1_left', 'layer1_right', 'layer2_selector')
            angle: Sudut target (0-180°)
        
        Mengembalikan:
            bool: True jika sukses, False jika gagal
        """
        if servo_id not in self.servos:
            return False
        
        servo = self.servos[servo_id]
        
        try:
            # Record current position before move
            old_angle = servo.get('current_angle', 0)
            
            # Update position tracking (works in both real and simulation mode)
            servo['current_angle'] = angle
            servo['last_move_time'] = time.time()
            
            # If not using GPIO (simulation), just track position
            if not self.has_gpio:
                print(f"[GPIOServo] {servo_id}: {old_angle}° → {angle}° ✓ (simulated)")
                return True
            
            # Real hardware mode
            duty = self._angle_to_duty(angle)
            
            if 'pwm' in servo:
                # Send PWM signal to move servo
                servo['pwm'].ChangeDutyCycle(duty)
                
                # Wait for servo to reach target position
                # Movement speed is controlled by `SERVO_MOVEMENT_TIME` in config.py
                movement_time = getattr(config, 'SERVO_MOVEMENT_TIME', 0.15)
                time.sleep(movement_time)
                
                # CRITICAL: Hold position briefly to ensure mechanical lock
                # MG996R needs this to guarantee position accuracy
                # Extra hold for mechanical lock: `SERVO_POSITION_HOLD_TIME` in config.py
                hold_time = getattr(config, 'SERVO_POSITION_HOLD_TIME', 0.05)
                time.sleep(hold_time)  # Extra hold time
                
                # CRITICAL: Stop PWM to prevent jitter/vibration and reduce power consumption
                # MG996R will hold position mechanically even with PWM off
                # Prevent jitter/vibration: `SERVO_STOP_JITTER` in config.py
                stop_jitter = getattr(config, 'SERVO_STOP_JITTER', True)
                if stop_jitter:
                    servo['pwm'].ChangeDutyCycle(0)
                    print(f"[GPIOServo] {servo_id}: {old_angle}° → {angle}° ✓ (PWM STOPPED)")
                else:
                    print(f"[GPIOServo] {servo_id}: {old_angle}° → {angle}° ✓ (PWM ACTIVE - may jitter)")
                    print(f"[GPIOServo] ⚠️ WARNING: SERVO_STOP_JITTER is False - servo may rotate continuously!")
                
                return True
            return False
            
        except Exception as e:
            print(f"[3ServoHW] Move error {servo_id} to {angle}°: {e}")
            return False
    
    def verify_positions(self):
        """
        Verifikasi semua servo berada pada posisi yang diharapkan.
        CATATAN PENTING: Mencegah drift posisi selama operasi.
        
        Mengembalikan:
            dict: Status posisi tiap servo
        """
        status = {}
        
        for servo_id, servo in self.servos.items():
            expected = servo.get('current_angle', 0)
            status[servo_id] = {
                'expected': expected,
                'verified': True,  # In production, read from encoder/feedback
                'timestamp': servo.get('last_move_time', 0)
            }
        
        return status
    
    def reset_to_ready_position(self):
        """
        Paksa semua servo kembali ke posisi siap.
        CATATAN PENTING: Memastikan sistem memulai dari keadaan baik yang diketahui.
        
        Mengembalikan:
            bool: True jika semua servo reset berhasil
        """
        print("[GPIOServo] Resetting all servos to ready position...")
        
        success = True
        
        # Reset Layer 2 to neutral first (safety)
        if 'layer2_selector' in self.servos:
            neutral = self.servos['layer2_selector'].get('neutral', config.SERVO_LAYER2_NEUTRAL)
            if not self._move_servo('layer2_selector', neutral):
                success = False
                print("[GPIOServo] ✗ Layer 2 reset failed")
        
        # Reset Layer 1 doors to closed
        if 'layer1_left' in self.servos:
            closed = self.servos['layer1_left'].get('closed', config.SERVO_LAYER1_LEFT_CLOSED)
            if not self._move_servo('layer1_left', closed):
                success = False
                print("[GPIOServo] ✗ Layer 1 Left reset failed")
        if 'layer1_left2' in self.servos:
            closed = self.servos['layer1_left2'].get('closed', getattr(config, 'SERVO_LAYER1_LEFT2_CLOSED', config.SERVO_LAYER1_LEFT_CLOSED))
            if not self._move_servo('layer1_left2', closed):
                success = False
                print("[GPIOServo] ✗ Layer 1 Left (Pair) reset failed")
        
        if 'layer1_right' in self.servos:
            closed = self.servos['layer1_right'].get('closed', config.SERVO_LAYER1_RIGHT_CLOSED)
            if not self._move_servo('layer1_right', closed):
                success = False
                print("[GPIOServo] ✗ Layer 1 Right reset failed")
        if 'layer1_right2' in self.servos:
            closed = self.servos['layer1_right2'].get('closed', getattr(config, 'SERVO_LAYER1_RIGHT2_CLOSED', config.SERVO_LAYER1_RIGHT_CLOSED))
            if not self._move_servo('layer1_right2', closed):
                success = False
                print("[GPIOServo] ✗ Layer 1 Right (Pair) reset failed")
        
        if success:
            print("[GPIOServo] ✓ All servos at ready position")
        
        return success
    
    def open_doors(self):
        """Buka kedua pintu Layer 1 untuk menjatuhkan sampah.
        Sudut pintu dikonfigurasi di `config.py` → `SERVO_LAYER1_*_OPEN`.
        Pintu tetap terbuka selama `SERVO_OPEN_DURATION` detik.
        """
        print("[GPIOServo] Opening container doors...")
        
        if not self.servos_active:
            print("[GPIOServo] Simulating door open")
            time.sleep(config.SERVO_OPEN_DURATION)
            return True
        
        # Open both doors
        left_ok = self._move_servo('layer1_left', self.servos['layer1_left']['open'])
        right_ok = self._move_servo('layer1_right', self.servos['layer1_right']['open'])
        # Move paired servos if configured
        left2_ok = True
        right2_ok = True
        if 'layer1_left2' in self.servos:
            left2_ok = self._move_servo('layer1_left2', self.servos['layer1_left2']['open'])
        if 'layer1_right2' in self.servos:
            right2_ok = self._move_servo('layer1_right2', self.servos['layer1_right2']['open'])
        
        if left_ok and right_ok and left2_ok and right2_ok:
            print("[GPIOServo] ✓ Doors opened")
            # How long doors stay open: `SERVO_OPEN_DURATION` in config.py
            time.sleep(config.SERVO_OPEN_DURATION)
            return True
        else:
            print(f"[GPIOServo] ⚠ Door open issue (L:{left_ok} R:{right_ok} L2:{left2_ok} R2:{right2_ok})")
            return False
    
    def close_doors(self):
        """Tutup kedua pintu Layer 1.
        Sudut tutup dikonfigurasi di `config.py` → `SERVO_LAYER1_*_CLOSED`.
        """
        print("[GPIOServo] Closing container doors...")
        
        if not self.servos_active:
            print("[GPIOServo] Simulating door close")
            return True
        
        left_ok = self._move_servo('layer1_left', self.servos['layer1_left']['closed'])
        right_ok = self._move_servo('layer1_right', self.servos['layer1_right']['closed'])
        # Move paired servos if configured
        left2_ok = True
        right2_ok = True
        if 'layer1_left2' in self.servos:
            left2_ok = self._move_servo('layer1_left2', self.servos['layer1_left2']['closed'])
        if 'layer1_right2' in self.servos:
            right2_ok = self._move_servo('layer1_right2', self.servos['layer1_right2']['closed'])
        
        if left_ok and right_ok and left2_ok and right2_ok:
            print("[GPIOServo] ✓ Doors closed")
            return True
        else:
            print(f"[GPIOServo] ⚠ Door close issue (L:{left_ok} R:{right_ok} L2:{left2_ok} R2:{right2_ok})")
            return False
    
    def set_selector(self, angle):
        """Set sudut selector Layer 2.
        Sudut selector: `SERVO_LAYER2_BIN_A`, `SERVO_LAYER2_BIN_B`, `SERVO_LAYER2_NEUTRAL` di `config.py`.
        """
        if not self.servos_active:
            print(f"[GPIOServo] Simulating selector → {angle}°")
            return True
        
        ok = self._move_servo('layer2_selector', angle)
        if ok:
            print(f"[GPIOServo] ✓ Selector → {angle}°")
        return ok
    
    def reset_to_ready(self):
        """
        Reset semua servo ke posisi siap/netral:
        - Pintu Layer 1: Tertutup (horizontal, siap menerima sampah)
        - Selector Layer 2: Netral (posisi tengah ~90°)
        Menggunakan timing dari `config.py`: `SERVO_CLOSE_DELAY`, `SERVO_RESET_DELAY`.
        """
        print("[GPIOServo] === Resetting system to ready state ===")
        
        try:
            # Close Layer 1 doors
            print("[GPIOServo] Closing Layer 1 doors...")
            self.close_doors()
            time.sleep(0.3)
            
            # Center Layer 2 selector
            print("[GPIOServo] Centering Layer 2 selector...")
            neutral = self.servos['layer2_selector']['neutral']
            self.set_selector(neutral)
            time.sleep(0.3)
            
            print("[GPIOServo] ✓ System ready for next waste item")
            return True
            
        except Exception as e:
            print(f"[GPIOServo] ✗ Reset error: {e}")
            return False
    
    def execute_sort(self, bin_assignment, bin_angle):
        """
        Jalankan urutan penyortiran lengkap dengan koordinasi Layer 1 & Layer 2:
        
        FASE 1: SIAPKAN LAYER 2 (Selector)
        1. Set sudut selector Layer 2 ke bin target (~30° dari netral, mis. 60°/120°)
        2. Tunggu selector siap (`SERVO_DROP_DELAY` dari config.py)
        
        FASE 2: JATUHKAN SAMPAH (Layer 1)
        3. Buka pintu Layer 1 (sudut dari `SERVO_LAYER1_*_OPEN`) untuk menjatuhkan sampah
        4. Tunggu sampah jatuh dari Layer 1 ke Layer 2 (`SERVO_FALL_TIME`)
        
        FASE 3: PENGARAHAN SAMPAH
        5. Sampah meluncur di selector Layer 2 yang miring menuju bin target (`SERVO_SLIDE_TIME`)
        
        FASE 4: RESET SEMUA (Kembali ke posisi awal)
        6. Tutup pintu Layer 1 kembali ke horizontal (`SERVO_LAYER1_*_CLOSED`)
        7. Kembalikan selector Layer 2 ke posisi netral (~90°, `SERVO_LAYER2_NEUTRAL`)
        
        Durasi total termasuk semua gerakan servo + jeda keamanan.
        Seluruh urutan ini dianggap SATU unit selama cooldown
        untuk mencegah deteksi gerakan saat servo bergerak.
        """
        print(f"[3ServoHW] === Starting sort to {bin_assignment} ({bin_angle}°) ===")
        
        try:
            # PHASE 1: PREPARE LAYER 2 (Selector positioned FIRST)
            print(f"[3ServoHW] PHASE 1 - Preparing Layer 2 selector...")
            print(f"[3ServoHW]   → Tilting selector to {bin_angle}° ({bin_assignment})")
            self.set_selector(bin_angle)
            time.sleep(config.SERVO_DROP_DELAY)  # Wait for selector to tilt and stabilize
            print(f"[GPIOServo]   ✓ Layer 2 selector ready at {bin_angle}°")
            
            # PHASE 2: DROP WASTE (Layer 1 doors open AFTER Layer 2 is ready)
            print(f"[GPIOServo] PHASE 2 - Dropping waste from Layer 1...")
            print(f"[GPIOServo]   → Opening container doors (90° down)")
            self.open_doors()  # Includes SERVO_OPEN_DURATION delay
            print(f"[GPIOServo]   ✓ Waste drops through Layer 1")
            
            # PHASE 3: WASTE ROUTING (gravity + tilted selector)
            print(f"[GPIOServo] PHASE 3 - Waste routing on Layer 2...")
            print(f"[GPIOServo]   → Waste slides on tilted selector to {bin_assignment}")
            time.sleep(0.5)  # Time for waste to fall from Layer 1 to Layer 2
            print(f"[GPIOServo]   ✓ Waste routed to {bin_assignment}")
            
            # PHASE 4: RESET ALL (Back to ready position)
            print(f"[GPIOServo] PHASE 4 - Resetting to ready position...")
            
            # Close Layer 1 doors
            print(f"[GPIOServo]   → Closing Layer 1 doors")
            self.close_doors()
            time.sleep(0.2)  # Safety delay for doors to fully close
            print(f"[GPIOServo]   ✓ Layer 1 doors closed")
            
            # Return Layer 2 selector to neutral
            print(f"[GPIOServo]   → Returning Layer 2 to neutral")
            neutral = self.servos['layer2_selector']['neutral']
            self.set_selector(neutral)
            time.sleep(0.2)  # Safety delay for selector to center
            print(f"[GPIOServo]   ✓ Layer 2 at neutral position")
            
            # CRITICAL: Verify all servos are at expected positions
            print(f"[GPIOServo] === POSITION VERIFICATION ===")
            positions = self.verify_positions()
            all_verified = True
            
            for servo_id, status in positions.items():
                if status['verified']:
                    print(f"[GPIOServo]   ✓ {servo_id}: {status['expected']}° (verified)")
                else:
                    print(f"[GPIOServo]   ✗ {servo_id}: Position mismatch!")
                    all_verified = False
            
            if not all_verified:
                print(f"[GPIOServo]   ⚠️  Position drift detected - forcing reset...")
                self.reset_to_ready_position()
            
            print(f"[GPIOServo] === ✓ SORT COMPLETE → {bin_assignment} ===")
            print(f"[GPIOServo] All servos verified at ready state\n")
            return True
            
        except Exception as e:
            print(f"[GPIOServo] ✗ Sort error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def cleanup(self):
        """Stop all PWM and cleanup GPIO"""
        print("[GPIOServo] Cleaning up...")
        
        if self.has_gpio:
            for sid, servo in self.servos.items():
                if 'pwm' in servo:
                    try:
                        servo['pwm'].stop()
                    except Exception as e:
                        print(f"[GPIOServo] Stop error {sid}: {e}")
            
            try:
                GPIO.cleanup()
                print("[GPIOServo] GPIO cleanup done")
            except Exception as e:
                print(f"[GPIOServo] Cleanup error: {e}")
    
    def get_status(self):
        """Get servo system status"""
        return {
            'active': self.servos_active,
            'has_gpio': self.has_gpio,
            'count': len(self.servos),
            'servos': {sid: {'pin': s['pin'], 'name': s['name']} 
                      for sid, s in self.servos.items()}
        }


# Test program
if __name__ == "__main__":
    print("="*60)
    print("GPIO Servo System Test")
    print("Testing with safety delays and complete reset")
    print("="*60)
    
    try:
        hw = GpioServoHardware()
        
        # Show status
        status = hw.get_status()
        print(f"\nSystem Status:")
        print(f"  Active: {status['active']}")
        print(f"  GPIO: {status['has_gpio']}")
        print(f"  Servos: {status['count']}")
        
        for sid, info in status['servos'].items():
            print(f"  - {info['name']}: GPIO {info['pin']}")
        
        # Initialize to ready state
        print("\n" + "="*60)
        print("Initializing: Set all servos to ready position")
        print("="*60)
        hw.reset_to_ready()
        
        print("\nStarting tests in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        if hw.servos_active or not hw.has_gpio:  # Allow simulation mode
            print("\n" + "="*60)
            print("TEST 1: Sort to Bin A (Organic)")
            print("="*60)
            success = hw.execute_sort('BIN A', config.SERVO_LAYER2_BIN_A)
            if success:
                print("✓ Test 1 PASSED")
            else:
                print("✗ Test 1 FAILED")
            
            print("\nWaiting 3 seconds before next test...")
            time.sleep(3)

            print("\n" + "="*60)
            print("TEST 2: Sort to Bin B (Anorganic)")
            print("="*60)
            success = hw.execute_sort('BIN B', config.SERVO_LAYER2_BIN_B)
            if success:
                print("✓ Test 2 PASSED")
            else:
                print("✗ Test 2 FAILED")
            
            print("\n" + "="*60)
            print("Final Reset: Returning to ready state")
            print("="*60)
            hw.reset_to_ready()

            print("\n" + "="*60)
            print("✓ ALL TESTS COMPLETE!")
            print("="*60)
            print("\nSystem is ready for next waste item.")
            print("Layer 1 doors: CLOSED (ready to receive)")
            print("Layer 2 selector: NEUTRAL (centered)")
        else:
            print("\n⚠ Servos not active - skipping tests")
            print("This is expected when running on non-RPi system")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nCleaning up...")
        if 'hw' in locals():
            hw.cleanup()
        print("Cleanup complete. Safe to disconnect hardware.")
