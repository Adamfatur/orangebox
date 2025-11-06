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
   SERVO_L1_CORNER_A_CHANNEL = 0    # Default: 4 (Kiri atas)
   SERVO_L1_CORNER_B_CHANNEL = 2    # Default: 6 (Kiri bawah)
   SERVO_L1_CORNER_C_CHANNEL = 4    # Default: 8 (Kanan atas)
   SERVO_L1_CORNER_D_CHANNEL = 6    # Default: 9 (Kanan bawah)
   
   SERVO_L1_CORNER_UP = 90          # Posisi atas (wadah terangkat)
   SERVO_L1_CORNER_DOWN = 180       # Posisi bawah (wadah jatuh)
   
   # Layer 1 - Lock Servos (2 servo)
   SERVO_L1_LOCK_LEFT_CHANNEL = 0   # Default: 0 (Pengunci kiri)
   SERVO_L1_LOCK_RIGHT_CHANNEL = 2  # Default: 2 (Pengunci kanan)
   
   SERVO_L1_LOCK_LOCKED = 90        # Terkunci (horizontal, menahan)
   SERVO_L1_LOCK_UNLOCKED = 10      # Terbuka (vertikal, lepas)
   
   # Layer 2 - Selector Servo (1 servo)
   SERVO_L2_SELECTOR_CHANNEL = 14   # Default: 12 (Pemilah)
   SERVO_L2_SELECTOR_NEUTRAL = 90   # Tengah
   SERVO_L2_SELECTOR_BIN_A = 45     # Ke Bin A (45° dari neutral)
   SERVO_L2_SELECTOR_BIN_B = 135    # Ke Bin B (135° dari neutral)

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
            
            # Initialize all servos to safe starting position (optional)
            if getattr(config, 'SERVO_INITIALIZE_AT_START', False):
                self._initialize_positions()
            else:
                # Ensure PWM off at start (no movement)
                try:
                    for servo_id, cfg in self.servos.items():
                        self.kit.servo[cfg['channel']].angle = None
                except Exception:
                    pass
            
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
        def _normalize_channel(ch):
            """Normalize channel index based on config, validate range.
            - Supports 1-based indices if PCA_CHANNELS_ONE_INDEXED=True (maps N -> N-1)
            - Returns None for invalid values.
            """
            if ch is None:
                return None
            try:
                ch_int = int(ch)
            except Exception:
                print(f"[7ServoHW] ⚠ Invalid channel value: {ch} (must be int 0-15)")
                return None
            original = ch_int
            if getattr(config, 'PCA_CHANNELS_ONE_INDEXED', False):
                ch_int = ch_int - 1
            if ch_int < 0 or ch_int > 15:
                print(f"[7ServoHW] ⚠ Channel out of range after normalize: {original} → {ch_int} (valid 0-15)")
                return None
            if getattr(config, 'PCA_CHANNELS_ONE_INDEXED', False) and original != ch_int:
                print(f"[7ServoHW] • Channel mapping (1-based→0-based): {original} → {ch_int}")
            return ch_int
        
        # Layer 1 - Corner Servos (4 servo untuk sudut wadah)
        corner_channels = {
            'corner_a': _normalize_channel(getattr(config, 'SERVO_L1_CORNER_A_CHANNEL', 4)),  # Kiri atas
            'corner_b': _normalize_channel(getattr(config, 'SERVO_L1_CORNER_B_CHANNEL', 6)),  # Kiri bawah
            'corner_c': _normalize_channel(getattr(config, 'SERVO_L1_CORNER_C_CHANNEL', 8)),  # Kanan atas
            'corner_d': _normalize_channel(getattr(config, 'SERVO_L1_CORNER_D_CHANNEL', 9)),  # Kanan bawah
        }
        
        # Global defaults (fallback jika per-servo angles tidak di-set)
        corner_up_default = getattr(config, 'SERVO_L1_CORNER_UP', 0)
        corner_down_default = getattr(config, 'SERVO_L1_CORNER_DOWN', 90)
        max_corner_swing = getattr(config, 'SERVO_MAX_SWING_CORNER_DEG', 90)
        
        # Per-servo angle configuration (untuk servo dengan arah berbeda)
        per_servo_angles = {
            'corner_a': {
                'up': getattr(config, 'SERVO_L1_CORNER_A_UP', corner_up_default),
                'down': getattr(config, 'SERVO_L1_CORNER_A_DOWN', corner_down_default)
            },
            'corner_b': {
                'up': getattr(config, 'SERVO_L1_CORNER_B_UP', corner_up_default),
                'down': getattr(config, 'SERVO_L1_CORNER_B_DOWN', corner_down_default)
            },
            'corner_c': {
                'up': getattr(config, 'SERVO_L1_CORNER_C_UP', corner_up_default),
                'down': getattr(config, 'SERVO_L1_CORNER_C_DOWN', corner_down_default)
            },
            'corner_d': {
                'up': getattr(config, 'SERVO_L1_CORNER_D_UP', corner_up_default),
                'down': getattr(config, 'SERVO_L1_CORNER_D_DOWN', corner_down_default)
            },
        }
        
        for name, channel in corner_channels.items():
            if channel is not None:
                # Get per-servo angles (bisa berbeda untuk CW vs CCW servos)
                servo_up = per_servo_angles[name]['up']
                servo_down = per_servo_angles[name]['down']
                
                # Enforce max swing for this specific servo
                delta_corner = servo_down - servo_up
                if abs(delta_corner) != max_corner_swing:
                    sign = 1 if delta_corner >= 0 else -1
                    adjusted = servo_up + sign * max_corner_swing
                    print(f"[7ServoHW] • Adjust {name} swing: {servo_up}→{servo_down} (Δ{delta_corner}°) → {servo_up}→{adjusted} (Δ{sign*max_corner_swing}°)")
                    servo_down = adjusted
                
                self.servos[name] = {
                    'name': f'Layer 1 {name.upper()}',
                    'channel': channel,
                    'up': servo_up,
                    'down': servo_down,
                    'current_angle': None,
                    'last_move_time': 0
                }
                print(f"[7ServoHW] • {self.servos[name]['name']}: CH {channel} (UP={servo_up}°, DOWN={servo_down}°)")

        
        # Layer 1 - Lock Servos (2 servo pengunci)
        lock_channels = {
            'lock_left': _normalize_channel(getattr(config, 'SERVO_L1_LOCK_LEFT_CHANNEL', 0)),
            'lock_right': _normalize_channel(getattr(config, 'SERVO_L1_LOCK_RIGHT_CHANNEL', 2)),
        }
        
        lock_locked = getattr(config, 'SERVO_L1_LOCK_LOCKED', 90)
        lock_unlocked = getattr(config, 'SERVO_L1_LOCK_UNLOCKED', 0)
        
        max_lock_swing = getattr(config, 'SERVO_MAX_SWING_LOCK_DEG', 90)

        for name, channel in lock_channels.items():
            if channel is not None:
                # Per-servo overrides for lock angles (support opposite directions)
                if name == 'lock_left':
                    locked_angle = getattr(config, 'SERVO_L1_LOCK_LEFT_LOCKED', lock_locked)
                    unlocked_angle = getattr(config, 'SERVO_L1_LOCK_LEFT_UNLOCKED', lock_unlocked)
                elif name == 'lock_right':
                    locked_angle = getattr(config, 'SERVO_L1_LOCK_RIGHT_LOCKED', lock_locked)
                    unlocked_angle = getattr(config, 'SERVO_L1_LOCK_RIGHT_UNLOCKED', lock_unlocked)
                else:
                    locked_angle = lock_locked
                    unlocked_angle = lock_unlocked

                # Enforce max swing (e.g., exactly 90° movement from locked)
                delta = unlocked_angle - locked_angle
                if abs(delta) != max_lock_swing:
                    sign = 1 if delta >= 0 else -1
                    adjusted = locked_angle + sign * max_lock_swing
                    print(f"[7ServoHW] • Adjust {name} swing: {locked_angle}→{unlocked_angle} (Δ{delta}°) → {locked_angle}→{adjusted} (Δ{sign*max_lock_swing}°)")
                    unlocked_angle = adjusted

                self.servos[name] = {
                    'name': f'Layer 1 {name.upper()}',
                    'channel': channel,
                    'locked': locked_angle,
                    'unlocked': unlocked_angle,
                    'current_angle': None,
                    'last_move_time': 0
                }
                print(f"[7ServoHW] • {self.servos[name]['name']}: CH {channel} (LOCKED={locked_angle}°, UNLOCKED={unlocked_angle}°)")
        
        # Layer 2 - Selector Servo (1 servo pemilah)
        selector_channel = _normalize_channel(getattr(config, 'SERVO_L2_SELECTOR_CHANNEL', 12))
        
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
        
        # Enforce allowed targets per servo type to avoid out-of-spec moves
        allowed = None
        if servo_id in ('corner_a','corner_b','corner_c','corner_d'):
            # Corners hanya boleh ke UP atau DOWN
            allowed = [self.servos[servo_id]['up'], self.servos[servo_id]['down']]
        elif servo_id in ('lock_left','lock_right'):
            # Locks hanya boleh ke LOCKED atau UNLOCKED
            allowed = [self.servos[servo_id]['locked'], self.servos[servo_id]['unlocked']]
        elif servo_id == 'selector':
            allowed = [self.servos['selector']['neutral'], self.servos['selector']['bin_a'], self.servos['selector']['bin_b']]

        if allowed is not None and angle not in allowed:
            # Snap ke target terdekat untuk safety
            nearest = min(allowed, key=lambda x: abs(x - float(angle)))
            print(f"[7ServoHW] ⚠ Safety snap '{servo_id}' {angle}° → {nearest}° (allowed={allowed})")
            angle = nearest

        # Apply optional per-servo offset and clamp
        offset = self._get_offset(servo_id)
        target = angle + offset
        if target < 0 or target > 180:
            clamped = max(0, min(180, target))
            print(f"[7ServoHW] ⚠ Angle {angle}° + offset {offset:+}° → {target}° clamped to {clamped}° for '{servo_id}'")
            target = clamped
        
        cfg = self.servos[servo_id]
        channel = cfg['channel']
        
        # Update tracking
        cfg['current_angle'] = target
        cfg['last_move_time'] = time.time()
        
        # Execute movement
        return self._move_channel(channel, target, servo_id=servo_id)

    def _get_offset(self, servo_id):
        """Return per-servo angle offset from config (degrees)."""
        try:
            if servo_id == 'lock_left':
                return getattr(config, 'SERVO_OFFSET_LOCK_LEFT', 0)
            if servo_id == 'lock_right':
                return getattr(config, 'SERVO_OFFSET_LOCK_RIGHT', 0)
            if servo_id == 'corner_a':
                return getattr(config, 'SERVO_OFFSET_CORNER_A', 0)
            if servo_id == 'corner_b':
                return getattr(config, 'SERVO_OFFSET_CORNER_B', 0)
            if servo_id == 'corner_c':
                return getattr(config, 'SERVO_OFFSET_CORNER_C', 0)
            if servo_id == 'corner_d':
                return getattr(config, 'SERVO_OFFSET_CORNER_D', 0)
            if servo_id == 'selector':
                return getattr(config, 'SERVO_OFFSET_SELECTOR', 0)
        except Exception:
            pass
        return 0

    def _move_channel(self, channel, angle, servo_id=None):
        """
        Low-level channel movement with PWM control.
        
        Args:
            channel: PCA9685 channel (0-15)
            angle: Target angle in degrees
        """
        try:
            if not HAS_SERVOKIT or self.kit is None:
                print(f"[7ServoHW] 🎬 SIMULATE: {servo_id or 'CH'+str(channel)} @ CH{channel} → {angle}°")
                time.sleep(0.05)  # Simulate movement time
                return True
            
            # Move to target angle
            if getattr(config, 'SERVO_DEBUG_TIMING', False):
                print(f"[7ServoHW] → MOVE {servo_id or 'CH'+str(channel)} @ CH{channel} = {angle}°")
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
            keep_power_locks = getattr(config, 'SERVO_KEEP_POWER_LOCKS', True)
            # Untuk lock servo, biarkan PWM tetap aktif agar posisi stabil menahan beban
            if stop_jitter and not (keep_power_locks and (servo_id in ('lock_left','lock_right'))):
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
            if getattr(config, 'SERVO_DEBUG_TIMING', False):
                t0 = time.time()
                print(f"[7ServoHW][T+] start {servo_id} → {angle}° at {t0:.3f}")
            success = self._move_servo(servo_id, angle)
            if getattr(config, 'SERVO_DEBUG_TIMING', False):
                t1 = time.time()
                print(f"[7ServoHW][T+] done  {servo_id} → {angle}° at {t1:.3f} (Δ{t1 - t0:.3f}s)")
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
            
            # ⚠️ FIX: Corner servos HARUS AKTIF DITURUNKAN (tidak ada gravitasi otomatis!)
            # Turunkan ALL corner servos SIMULTANEOUSLY (UP → DOWN)
            print(f"[7ServoHW]    ↓ Lowering ALL 4 corners simultaneously (UP→DOWN)...")
            corner_moves = []
            for corner in ['corner_a', 'corner_b', 'corner_c', 'corner_d']:
                if corner in self.servos:
                    corner_moves.append((corner, self.servos[corner]['down']))
            
            # Execute lowering in parallel for synchronized motion
            if corner_moves:
                self._move_multiple_servos_parallel(corner_moves)
            
            print(f"[7ServoHW]    ✓ Waste container lowered!")
            
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
            # Optional reset to safe position
            if getattr(config, 'SERVO_RESET_ON_SHUTDOWN', False):
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

    def center_all_servos(self, angle: float = 90.0):
        """Move all servos to a common center angle (default 90°) for calibration.
        Note: This is for horn alignment; ensure mechanical clearance.
        """
        print(f"\n[7ServoHW] 🎯 Centering all servos to {angle}° for calibration...")
        try:
            moves = []
            for sid in ['corner_a','corner_b','corner_c','corner_d','lock_left','lock_right','selector']:
                if sid in self.servos:
                    moves.append((sid, angle))
            if moves:
                self._move_multiple_servos_parallel(moves)
            print("[7ServoHW] ✓ All servos centered")
        except Exception as e:
            print(f"[7ServoHW] ⚠ Centering warning: {e}")


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
