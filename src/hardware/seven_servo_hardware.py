"""
╔═══════════════════════════════════════════════════════════════╗
║      7-Servo Hardware - Advanced Locking System             ║
║     (Layer 1: 6 servos + Layer 2: 1 servo selector)         ║
╚═══════════════════════════════════════════════════════════════╝

📌 SISTEM 7 SERVO - MAJOR UPGRADE

🏗️ ARSITEKTUR:
   Layer 1 (6 Servo):
   • 4 Servo Corner (A, B, C, D) - Mengangkat/menurunkan wadah
     - Corner A: Sudut kiri atas
     - Corner B: Sudut kiri bawah  
     - Corner C: Sudut kanan atas
     - Corner D: Sudut kanan bawah
   
   • 2 Servo Lock (Pengunci) - Mengunci wadah di posisi atas
     - Lock Left: Pengunci sisi kiri (tengah)
     - Lock Right: Pengunci sisi kanan (tengah)
   
   Layer 2 (1 Servo):
   • Selector - Memilah ke Bin A atau B

🔄 ALUR KERJA (FASE):
   
   FASE 1 - SELECTOR POSITIONING:
   → Servo selector (Layer 2) bergerak 30° ke arah Bin A atau B
   → Posisi stabil, siap menerima sampah
   
   FASE 2 - UNLOCK & DROP:
   → 2 Servo Lock (Left & Right) UNLOCK (buka pengunci)
   → 4 Servo Corner tetap di posisi 0° (atas)
   → Wadah jatuh OTOMATIS karena gravitasi (turun 90°)
   → Sampah meluncur ke selector lalu ke bin
   
   FASE 3 - WAITING:
   → Tunggu sampah jatuh sempurna (SERVO_FALL_TIME)
   
   FASE 4 - LIFT & LOCK:
   → 4 Servo Corner bergerak NAIK dari 90° ke 0° (angkat wadah)
   → 2 Servo Lock LOCK (kunci kembali untuk menahan wadah)
   → Wadah terkunci di posisi atas
   
   FASE 5 - RESET SELECTOR:
   → Servo selector kembali ke posisi NEUTRAL (90°)
   → Sistem siap untuk sorting berikutnya

🔐 KONSEP LOCKING MECHANISM:

   Servo Lock bekerja seperti PIN/GRENDEL:
   
   LOCKED (wadah di atas):
   • Angle: 90° (horizontal/menyangga)
   • Posisi: Servo arm horizontal di BAWAH wadah
   • Fungsi: Menahan wadah agar tidak jatuh
   • Timing: Aktif setelah wadah dinaikkan
   
   UNLOCKED (wadah jatuh):
   • Angle: 0° (vertikal/lepas)
   • Posisi: Servo arm vertikal, tidak menghalangi
   • Fungsi: Membiarkan wadah jatuh bebas
   • Timing: Sebelum wadah jatuh

   Sequence Lock/Unlock:
   1. Unlock: Lock servo 90° → 0° (lepas pengunci)
   2. Wait: 0.1s untuk servo stabil
   3. Drop: Wadah jatuh karena gravitasi
   4. Lift: Corner servo 90° → 0° (angkat wadah)
   5. Lock: Lock servo 0° → 90° (pasang pengunci kembali)

⚙️  KONFIGURASI (config.py):

   # Layer 1 - Corner Servos (4 servo)
   SERVO_L1_CORNER_A_CHANNEL = 0    # Kiri atas
   SERVO_L1_CORNER_B_CHANNEL = 1    # Kiri bawah
   SERVO_L1_CORNER_C_CHANNEL = 2    # Kanan atas
   SERVO_L1_CORNER_D_CHANNEL = 3    # Kanan bawah
   
   SERVO_L1_CORNER_UP = 0           # Posisi atas (wadah terangkat)
   SERVO_L1_CORNER_DOWN = 90        # Posisi bawah (wadah jatuh)
   
   # Layer 1 - Lock Servos (2 servo)
   SERVO_L1_LOCK_LEFT_CHANNEL = 4   # Pengunci kiri
   SERVO_L1_LOCK_RIGHT_CHANNEL = 5  # Pengunci kanan
   
   SERVO_L1_LOCK_LOCKED = 90        # Terkunci (horizontal, menahan)
   SERVO_L1_LOCK_UNLOCKED = 0       # Terbuka (vertikal, lepas)
   
   # Layer 2 - Selector Servo (1 servo)
   SERVO_L2_SELECTOR_CHANNEL = 6    # Pemilah
   SERVO_L2_SELECTOR_NEUTRAL = 90   # Tengah
   SERVO_L2_SELECTOR_BIN_A = 60     # Ke Bin A (30° dari neutral)
   SERVO_L2_SELECTOR_BIN_B = 120    # Ke Bin B (30° dari neutral)

📚 TIMING SETTINGS:
   SERVO_MOVEMENT_TIME = 0.15       # Waktu gerakan servo
   SERVO_FALL_TIME = 0.5            # Waktu wadah jatuh
   SERVO_LIFT_TIME = 0.3            # Waktu mengangkat wadah
   SERVO_LOCK_DELAY = 0.1           # Delay setelah unlock/lock
   SERVO_DROP_DELAY = 0.3           # Delay setelah selector posisi

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
    print(f"[7ServoHW] Warning: ServoKit not available: {e}")


class SevenServoHardware:
    """
    Hardware controller untuk sistem 7 servo dengan locking mechanism.
    
    Attributes:
        servos: Dict konfigurasi semua servo
        kit: Instance ServoKit untuk PCA9685
        servos_active: Status aktif hardware
    """

    def __init__(self):
        """Initialize 7-servo system dengan PCA9685."""
        self.servos_active = False
        self.servos = {}
        self.kit = None

        print("[7ServoHW] ╔════════════════════════════════════════════════╗")
        print("[7ServoHW] ║   Initializing 7-Servo Locking System        ║")
        print("[7ServoHW] ║   Layer 1: 6 servos (4 corners + 2 locks)    ║")
        print("[7ServoHW] ║   Layer 2: 1 servo (selector)                ║")
        print("[7ServoHW] ╚════════════════════════════════════════════════╝")

        if not HAS_SERVOKIT:
            print("[7ServoHW] Running in SIMULATION mode (no hardware)")
            self._setup_servos_config()
            return

        try:
            # Initialize PCA9685 board
            address = getattr(config, 'PCA9685_I2C_ADDRESS', 0x40)
            self.kit = ServoKit(channels=16, address=address)
            
            # Set PWM frequency for servos
            try:
                self.kit._pca.frequency = getattr(config, 'PCA9685_FREQUENCY', 50)
            except Exception:
                pass
            
            print(f"[7ServoHW] ✓ PCA9685 initialized at 0x{address:02X}, freq={getattr(config, 'PCA9685_FREQUENCY', 50)}Hz")

            # Setup servo configuration
            self._setup_servos_config()
            
            # Apply calibration for MG996R/SG90
            self._apply_servokit_calibration()
            
            # Initialize all servos to safe starting position
            self._initialize_positions()
            
            self.servos_active = True
            print("[7ServoHW] ✓ All servos initialized and ready")
            
        except Exception as e:
            print(f"[7ServoHW] ❌ Error initializing ServoKit: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to simulation
            print("[7ServoHW] → Falling back to SIMULATION mode")
            self._setup_servos_config()

    def _setup_servos_config(self):
        """Load servo configuration from config.py"""
        
        # Layer 1 - Corner Servos (4 servo untuk sudut wadah)
        corner_channels = {
            'corner_a': getattr(config, 'SERVO_L1_CORNER_A_CHANNEL', 0),  # Kiri atas
            'corner_b': getattr(config, 'SERVO_L1_CORNER_B_CHANNEL', 1),  # Kiri bawah
            'corner_c': getattr(config, 'SERVO_L1_CORNER_C_CHANNEL', 2),  # Kanan atas
            'corner_d': getattr(config, 'SERVO_L1_CORNER_D_CHANNEL', 3),  # Kanan bawah
        }
        
        corner_up = getattr(config, 'SERVO_L1_CORNER_UP', 0)
        corner_down = getattr(config, 'SERVO_L1_CORNER_DOWN', 90)
        
        for name, channel in corner_channels.items():
            if channel is not None:
                self.servos[name] = {
                    'name': f'Layer 1 {name.upper()}',
                    'channel': channel,
                    'up': corner_up,
                    'down': corner_down,
                    'current_angle': None,
                    'last_move_time': 0
                }
                print(f"[7ServoHW] • {self.servos[name]['name']}: CH {channel} (UP={corner_up}°, DOWN={corner_down}°)")
        
        # Layer 1 - Lock Servos (2 servo pengunci)
        lock_channels = {
            'lock_left': getattr(config, 'SERVO_L1_LOCK_LEFT_CHANNEL', 4),
            'lock_right': getattr(config, 'SERVO_L1_LOCK_RIGHT_CHANNEL', 5),
        }
        
        lock_locked = getattr(config, 'SERVO_L1_LOCK_LOCKED', 90)
        lock_unlocked = getattr(config, 'SERVO_L1_LOCK_UNLOCKED', 0)
        
        for name, channel in lock_channels.items():
            if channel is not None:
                self.servos[name] = {
                    'name': f'Layer 1 {name.upper()}',
                    'channel': channel,
                    'locked': lock_locked,
                    'unlocked': lock_unlocked,
                    'current_angle': None,
                    'last_move_time': 0
                }
                print(f"[7ServoHW] • {self.servos[name]['name']}: CH {channel} (LOCKED={lock_locked}°, UNLOCKED={lock_unlocked}°)")
        
        # Layer 2 - Selector Servo (1 servo pemilah)
        selector_channel = getattr(config, 'SERVO_L2_SELECTOR_CHANNEL', 6)
        
        if selector_channel is not None:
            self.servos['selector'] = {
                'name': 'Layer 2 SELECTOR',
                'channel': selector_channel,
                'neutral': getattr(config, 'SERVO_L2_SELECTOR_NEUTRAL', 90),
                'bin_a': getattr(config, 'SERVO_L2_SELECTOR_BIN_A', 60),
                'bin_b': getattr(config, 'SERVO_L2_SELECTOR_BIN_B', 120),
                'current_angle': None,
                'last_move_time': 0
            }
            print(f"[7ServoHW] • {self.servos['selector']['name']}: CH {selector_channel} (NEUTRAL={self.servos['selector']['neutral']}°, BIN_A={self.servos['selector']['bin_a']}°, BIN_B={self.servos['selector']['bin_b']}°)")

    def _apply_servokit_calibration(self):
        """Apply calibration for MG996R/SG90 servos"""
        if not HAS_SERVOKIT or self.kit is None:
            return
        
        try:
            min_pulse = getattr(config, 'SERVOKIT_MIN_PULSE_MICROS', 500)
            max_pulse = getattr(config, 'SERVOKIT_MAX_PULSE_MICROS', 2500)
            actuation_range = getattr(config, 'SERVOKIT_ACTUATION_RANGE', 180)
            
            for servo_id, cfg in self.servos.items():
                channel = cfg['channel']
                self.kit.servo[channel].set_pulse_width_range(min_pulse, max_pulse)
                self.kit.servo[channel].actuation_range = actuation_range
            
            print(f"[7ServoHW] ✓ Calibration applied: pulse {min_pulse}-{max_pulse}μs, range {actuation_range}°")
        except Exception as e:
            print(f"[7ServoHW] ⚠ Calibration warning: {e}")

    def _initialize_positions(self):
        """Initialize all servos to safe starting positions"""
        print("[7ServoHW] → Setting initial positions...")
        
        # Layer 1 Corner servos to UP position (wadah terangkat)
        for name in ['corner_a', 'corner_b', 'corner_c', 'corner_d']:
            if name in self.servos:
                self._move_servo(name, self.servos[name]['up'])
        
        # Layer 1 Lock servos to LOCKED position (pengunci aktif)
        for name in ['lock_left', 'lock_right']:
            if name in self.servos:
                self._move_servo(name, self.servos[name]['locked'])
        
        # Layer 2 Selector to NEUTRAL position
        if 'selector' in self.servos:
            self._move_servo('selector', self.servos['selector']['neutral'])
        
        print("[7ServoHW] ✓ Initial positions set: Wadah UP & LOCKED, Selector NEUTRAL")

    def _move_servo(self, servo_id, angle):
        """
        Move servo to specific angle with safety checks.
        
        Args:
            servo_id: Servo identifier (e.g., 'corner_a', 'lock_left', 'selector')
            angle: Target angle in degrees (MUST be 0-180)
        
        Returns:
            bool: Success status
        """
        if servo_id not in self.servos:
            print(f"[7ServoHW] ⚠ Servo '{servo_id}' not found")
            return False
        
        # ═══════════════════════════════════════════════════════════
        # CRITICAL SAFETY: Validate angle to prevent 360° rotation
        # ═══════════════════════════════════════════════════════════
        if not isinstance(angle, (int, float)):
            print(f"[7ServoHW] ❌ SAFETY: Invalid angle type {type(angle)} for '{servo_id}'")
            return False
            
        if angle < 0 or angle > 180:
            print(f"[7ServoHW] ❌ SAFETY VIOLATION: Angle {angle}° out of range (0-180°)")
            print(f"[7ServoHW]    Servo '{servo_id}' will NOT move - preventing damage!")
            return False
        
        cfg = self.servos[servo_id]
        channel = cfg['channel']
        
        # Update tracking
        cfg['current_angle'] = angle
        cfg['last_move_time'] = time.time()
        
        # Execute movement
        return self._move_channel(channel, angle)

    def _move_channel(self, channel, angle):
        """
        Low-level channel movement with PWM control.
        
        Args:
            channel: PCA9685 channel (0-15)
            angle: Target angle in degrees
        """
        try:
            if not HAS_SERVOKIT or self.kit is None:
                print(f"[7ServoHW] 🎬 SIMULATE: CH{channel} → {angle}°")
                time.sleep(0.05)  # Simulate movement time
                return True
            
            # Move to target angle
            self.kit.servo[channel].angle = angle
            
            # Wait for movement to complete
            movement_time = getattr(config, 'SERVO_MOVEMENT_TIME', 0.15)
            time.sleep(movement_time)
            
            # Hold position for mechanical lock
            hold_time = getattr(config, 'SERVO_POSITION_HOLD_TIME', 0.05)
            if hold_time > 0:
                time.sleep(hold_time)
            
            # Stop PWM to prevent jitter (optional)
            stop_jitter = getattr(config, 'SERVO_STOP_JITTER', True)
            if stop_jitter:
                try:
                    self.kit.servo[channel].angle = None
                    # print(f"[7ServoHW] ✓ CH{channel} locked at {angle}°")
                except Exception:
                    pass
            
            return True
            
        except Exception as e:
            print(f"[7ServoHW] ❌ Move error CH{channel} → {angle}°: {e}")
            return False

    def _move_multiple_servos_parallel(self, servo_moves):
        """
        Move multiple servos in PARALLEL (simultaneously) using threads.
        This ensures all servos move at the SAME TIME for synchronized motion.
        
        Args:
            servo_moves: List of tuples (servo_id, angle)
                        e.g., [('corner_a', 0), ('corner_b', 0), ...]
        
        Returns:
            bool: True if all movements successful
        """
        threads = []
        results = {}
        
        def move_worker(servo_id, angle, result_dict):
            """Worker thread for moving one servo"""
            success = self._move_servo(servo_id, angle)
            result_dict[servo_id] = success
        
        # Start all servo movements simultaneously
        for servo_id, angle in servo_moves:
            thread = threading.Thread(
                target=move_worker,
                args=(servo_id, angle, results)
            )
            thread.start()
            threads.append(thread)
            
            # Optional stagger to reduce power spike
            stagger = getattr(config, 'SERVO_STAGGER_DELAY_MS', 0) / 1000.0
            if stagger > 0:
                time.sleep(stagger)
        
        # Wait for all movements to complete
        for thread in threads:
            thread.join()
        
        # Check if all successful
        return all(results.values())

    # ═══════════════════════════════════════════════════════════════
    # HIGH-LEVEL SORTING OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    def sort_to_bin_a(self):
        """Execute complete sorting sequence to BIN A (ORGANIC)"""
        print("\n[7ServoHW] ╔══════════════════════════════════════════╗")
        print("[7ServoHW] ║  SORTING TO BIN A (ORGANIC)            ║")
        print("[7ServoHW] ╚══════════════════════════════════════════╝")
        return self._execute_sort_sequence('bin_a')

    def sort_to_bin_b(self):
        """Execute complete sorting sequence to BIN B (ANORGANIC)"""
        print("\n[7ServoHW] ╔══════════════════════════════════════════╗")
        print("[7ServoHW] ║  SORTING TO BIN B (ANORGANIC)          ║")
        print("[7ServoHW] ╚══════════════════════════════════════════╝")
        return self._execute_sort_sequence('bin_b')

    def execute_sort(self, bin_name, selector_angle):
        """
        Execute sorting sequence (compatibility method for MainController).
        
        Args:
            bin_name: 'BIN A' or 'BIN B' (string label)
            selector_angle: Target angle for selector (not used in new system,
                           we determine bin from bin_name)
        
        Returns:
            bool: Success status
        """
        # Map bin_name to internal method
        if 'A' in bin_name.upper():
            return self.sort_to_bin_a()
        else:
            return self.sort_to_bin_b()

    def _execute_sort_sequence(self, target_bin):
        """
        Execute the complete 5-phase sorting sequence.
        
        Args:
            target_bin: 'bin_a' or 'bin_b'
        
        Returns:
            bool: Success status
        """
        try:
            # Get target angle for selector
            if target_bin == 'bin_a':
                selector_angle = self.servos['selector']['bin_a']
            else:
                selector_angle = self.servos['selector']['bin_b']
            
            # ═══════════════════════════════════════════════════════════
            # FASE 1: SELECTOR POSITIONING
            # ═══════════════════════════════════════════════════════════
            print(f"\n[7ServoHW] 🎯 FASE 1: Positioning selector to {target_bin.upper()} ({selector_angle}°)...")
            self._move_servo('selector', selector_angle)
            
            # Delay untuk selector stabil
            drop_delay = getattr(config, 'SERVO_DROP_DELAY', 0.3)
            print(f"[7ServoHW]    ⏱ Waiting {drop_delay}s for selector to stabilize...")
            time.sleep(drop_delay)
            
            # ═══════════════════════════════════════════════════════════
            # FASE 2: UNLOCK & DROP
            # ═══════════════════════════════════════════════════════════
            print(f"\n[7ServoHW] 🔓 FASE 2: Unlocking and dropping waste...")
            
            # Unlock BOTH lock servos SIMULTANEOUSLY
            print(f"[7ServoHW]    → Unlocking BOTH locks simultaneously...")
            lock_moves = []
            if 'lock_left' in self.servos:
                lock_moves.append(('lock_left', self.servos['lock_left']['unlocked']))
            if 'lock_right' in self.servos:
                lock_moves.append(('lock_right', self.servos['lock_right']['unlocked']))
            
            # Execute unlock in parallel for synchronized motion
            if lock_moves:
                self._move_multiple_servos_parallel(lock_moves)
            
            # Short delay for unlock to complete
            lock_delay = getattr(config, 'SERVO_LOCK_DELAY', 0.1)
            print(f"[7ServoHW]    ⏱ Lock delay {lock_delay}s...")
            time.sleep(lock_delay)
            
            # Wadah akan jatuh OTOMATIS karena gravitasi
            # Corner servos tetap di posisi UP (0°), tidak perlu gerak
            print(f"[7ServoHW]    ↓ Waste container dropping by GRAVITY...")
            
            # ═══════════════════════════════════════════════════════════
            # FASE 3: WAITING FOR WASTE TO FALL
            # ═══════════════════════════════════════════════════════════
            print(f"\n[7ServoHW] ⏳ FASE 3: Waiting for waste to fall...")
            fall_time = getattr(config, 'SERVO_FALL_TIME', 0.5)
            print(f"[7ServoHW]    ⏱ Fall time: {fall_time}s")
            time.sleep(fall_time)
            
            # Additional slide time on selector
            slide_time = getattr(config, 'SERVO_SLIDE_TIME', 0.5)
            print(f"[7ServoHW]    ⏱ Slide time: {slide_time}s")
            time.sleep(slide_time)
            
            # ═══════════════════════════════════════════════════════════
            # FASE 4: LIFT & LOCK
            # ═══════════════════════════════════════════════════════════
            print(f"\n[7ServoHW] ⬆️ FASE 4: Lifting container and locking...")
            
            # Lift ALL corner servos SIMULTANEOUSLY (DOWN → UP)
            print(f"[7ServoHW]    ↑ Lifting ALL 4 corners simultaneously (REALTIME)...")
            corner_moves = []
            for corner in ['corner_a', 'corner_b', 'corner_c', 'corner_d']:
                if corner in self.servos:
                    corner_moves.append((corner, self.servos[corner]['up']))
            
            # Execute lift in parallel for synchronized motion
            if corner_moves:
                self._move_multiple_servos_parallel(corner_moves)
            
            # Wait for lift to complete
            lift_time = getattr(config, 'SERVO_LIFT_TIME', 0.3)
            print(f"[7ServoHW]    ⏱ Lift time: {lift_time}s")
            time.sleep(lift_time)
            
            # Lock BOTH lock servos SIMULTANEOUSLY (menahan wadah di posisi atas)
            print(f"[7ServoHW]    🔒 Locking BOTH locks simultaneously (REALTIME)...")
            lock_moves = []
            if 'lock_left' in self.servos:
                lock_moves.append(('lock_left', self.servos['lock_left']['locked']))
            if 'lock_right' in self.servos:
                lock_moves.append(('lock_right', self.servos['lock_right']['locked']))
            
            # Execute lock in parallel for synchronized motion
            if lock_moves:
                self._move_multiple_servos_parallel(lock_moves)
            
            # Delay after lock
            print(f"[7ServoHW]    ⏱ Lock delay {lock_delay}s...")
            time.sleep(lock_delay)
            
            # ═══════════════════════════════════════════════════════════
            # FASE 5: RESET SELECTOR
            # ═══════════════════════════════════════════════════════════
            print(f"\n[7ServoHW] 🔄 FASE 5: Resetting selector to NEUTRAL...")
            neutral_angle = self.servos['selector']['neutral']
            self._move_servo('selector', neutral_angle)
            
            # Delay after reset
            reset_delay = getattr(config, 'SERVO_RESET_DELAY', 0.3)
            print(f"[7ServoHW]    ⏱ Reset delay {reset_delay}s...")
            time.sleep(reset_delay)
            
            print(f"\n[7ServoHW] ✅ SORTING COMPLETE! Waste sorted to {target_bin.upper()}")
            print("[7ServoHW]    → Container: UP & LOCKED")
            print("[7ServoHW]    → Selector: NEUTRAL")
            print("[7ServoHW]    → System ready for next sorting\n")
            
            return True
            
        except Exception as e:
            print(f"\n[7ServoHW] ❌ ERROR during sorting: {e}")
            import traceback
            traceback.print_exc()
            
            # Emergency reset
            print("[7ServoHW] 🚨 Attempting emergency reset...")
            self.reset_to_ready()
            return False

    def reset_to_ready(self):
        """Reset all servos to ready/standby state"""
        print("\n[7ServoHW] 🔄 Resetting to READY state...")
        
        try:
            # Lift all corners to UP
            for corner in ['corner_a', 'corner_b', 'corner_c', 'corner_d']:
                if corner in self.servos:
                    self._move_servo(corner, self.servos[corner]['up'])
            
            # Lock all locks
            for lock in ['lock_left', 'lock_right']:
                if lock in self.servos:
                    self._move_servo(lock, self.servos[lock]['locked'])
            
            # Selector to neutral
            if 'selector' in self.servos:
                self._move_servo('selector', self.servos['selector']['neutral'])
            
            print("[7ServoHW] ✓ Reset complete - System READY")
            
        except Exception as e:
            print(f"[7ServoHW] ⚠ Reset warning: {e}")

    def cleanup(self):
        """Cleanup and safe shutdown"""
        print("\n[7ServoHW] 🛑 Shutting down...")
        
        try:
            # Reset to safe position
            self.reset_to_ready()
            
            # Disable all PWM signals
            if HAS_SERVOKIT and self.kit is not None:
                for servo_id, cfg in self.servos.items():
                    try:
                        self.kit.servo[cfg['channel']].angle = None
                    except Exception:
                        pass
            
            print("[7ServoHW] ✓ Shutdown complete")
            
        except Exception as e:
            print(f"[7ServoHW] ⚠ Cleanup warning: {e}")


# ═══════════════════════════════════════════════════════════════
# TESTING & DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════

def test_sequence():
    """Test the complete sorting sequence"""
    print("\n" + "="*60)
    print("7-SERVO HARDWARE TEST")
    print("="*60)
    
    hw = SevenServoHardware()
    
    try:
        print("\n→ Testing BIN A sorting...")
        hw.sort_to_bin_a()
        time.sleep(2)
        
        print("\n→ Testing BIN B sorting...")
        hw.sort_to_bin_b()
        time.sleep(2)
        
        print("\n→ Final reset...")
        hw.reset_to_ready()
        
        print("\n✅ Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
    finally:
        hw.cleanup()


if __name__ == "__main__":
    test_sequence()
