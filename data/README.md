# 📊 Data

Folder ini berisi file data runtime dan konfigurasi device.

## 📄 Files

### location_history.jsonl
Log history lokasi GPS dalam format JSONL (JSON Lines).

**Format:**
```json
{"timestamp": "2025-11-04T10:30:00", "latitude": -6.2088, "longitude": 106.8456, "accuracy": 10}
```

**Kegunaan:**
- Tracking lokasi OrangeBox
- Analisis pergerakan device
- Audit trail

**Config:**
```python
# config.py
GPS_SAVE_HISTORY = True
GPS_HISTORY_FILE = 'data/location_history.jsonl'
```

### device_config.txt
Konfigurasi device-specific.

**Kegunaan:**
- Serial number device
- Hardware configuration
- Deployment info

## 🔒 Privacy Note

File `location_history.jsonl` berisi data lokasi GPS. 

**Untuk production:**
- Pastikan `ENABLE_GPS = False` di `config.py` jika tidak diperlukan
- File ini **TIDAK** dikirim ke database (privacy-first design)
- Data hanya tersimpan lokal di device

**Untuk disable GPS:**
```python
# config.py
ENABLE_GPS = False
```

---

**Version:** 1.2  
**Last Updated:** November 4, 2025
