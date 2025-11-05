# Servo Guide — OrangeBox (consolidated)

This single guide replaces the separate servo markdown files and contains the installation steps, configuration, fixes, tests and troubleshooting for the 7-servo positional system (MG996R).

## Overview
- Required servos: 7x positional (0–180°), recommended MG996R (metal gear).
- Channels (PCA9685): CH 0 (Lock Left), CH 2 (Lock Right), CH 4 (Corner A), CH 6 (Corner B), CH 8 (Corner C), CH 9 (Corner D), CH 12 (Selector).
- Safe angle ranges used by the project: avoid 0° and 180°; default safe values are UP=10° and DOWN=100° for corners, locks and selector use mid-range values.

## Why this consolidation
Multiple markdown files caused confusion. This single document keeps everything servo-related in one place and points to the minimal quick references and scripts you will use.

## Quick safety checklist (read first)
1. Verify servo type: label must say "0-180°", "Standard Servo", or the model (MG996R). If it says "360°" or "Continuous Rotation" do NOT install.
2. Power: use a stable 5–6V power supply capable of the combined current (recommended: separate servo power supply, 5–10A depending on battery/power setup).
3. Ensure I2C and PCA9685 are connected and addressable (default 0x40). Run `sudo i2cdetect -y 1` on Raspberry Pi.

## Installation (summary)
1. Stop the system and neutralize servos:

```bash
python3 scripts/emergency_stop_servos.py
```

2. Backup current config (if you used the 3-servo temporary config):

```bash
cp config.py config.py.OLD_3SERVO_BACKUP
```

3. Mount the positional servos:
- Replace continuous-rotation servos on CH 0, CH 2, CH 4, CH 6 with MG996R (positional).
- Connect each servo: GND (brown) → GND, VCC (red) → 5–6V supply, Signal (orange) → PCA9685 channel.

4. Activate the 7-servo config when physical wiring is done:

```bash
cp config.py.READY_FOR_7_SERVO config.py
```

5. Test individual servos (mandatory):

```bash
python3 scripts/quick_servo_diagnostic.py
```
- For each new servo (CH 0,2,4,6) check 0°, 90°, 180° commands. Servo must stop at those positions.

6. Run full validation (recommended):

```bash
python3 scripts/validate_7servo_system.py
```

## Important code fixes (what changed and why)
- The project disabled a problematic "Enforce Max Swing" logic that previously forced extreme angles (0°/180°) causing positional servos to hunt or continuous-type behavior. This logic was intentionally removed; safe angles are now defined in `config.py.READY_FOR_7_SERVO`.
- Lock/unlock sequences were temporarily disabled to avoid spinning continuous servos; they have been re-enabled now that the system expects positional servos.
- Safety checks exist in `src/hardware/seven_servo_hardware.py` to clamp angles to 0–180° and snap to allowed target positions to reduce user error.

## Configuration pointers
- Use `config.py.READY_FOR_7_SERVO` as the canonical config for 7 positional servos. It sets safe default pulses and angles.
- If you need to fine tune physical alignment, set the per-servo offset variables (e.g., `SERVO_OFFSET_CORNER_A`) in `config.py`.

## Tests and validation
- `scripts/quick_servo_diagnostic.py` — test each channel individually.
- `scripts/servo_direct_test.py` — manual control for calibration and offsets.
- `scripts/validate_7servo_system.py` — full validation suite including stress test (10 cycles).

## Troubleshooting (common problems)
- Servo spins 360° continuously: wrong servo type (continuous). Solution: emergency stop and replace servo.
- Servo twitching / hunting at position: commanded angle too close to mechanical limit. Fix by using safe angles (e.g., 10° instead of 0°) and narrow pulse width in config.
- Corners not synchronized: ensure per-corner overrides are None so they use the global defaults, and check wiring/power.
- PCA9685 not found: enable I2C, check cables, run `sudo i2cdetect -y 1`.

## Minimal quick refs
- Quick Start (30–45 min): `QUICK_START_SERVO_BARU.txt` (use for rapid install).
- Full validation: `scripts/validate_7servo_system.py`.

## Where to find more details
Previously separate files (installation steps, checklist, bug analysis and hardware-mismatch notes) have been merged here. If you need a printed checklist, use the `QUICK_START_SERVO_BARU.txt` file for a short procedural summary.

---

If you'd like, I can now remove the older individual markdown files and update `README.md` to link to this single guide. Proceed? (I'll do it automatically if you confirm; I already prepared this consolidated doc.)
