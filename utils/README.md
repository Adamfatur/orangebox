# 🛠️ Utilities

Folder ini berisi script utilities dan helper untuk development dan troubleshooting.

## 📄 Files

### run_mac.py
Python runner untuk macOS yang bypass venv check.
```bash
python3 utils/run_mac.py --test
```

**Kegunaan:** 
- Development di macOS tanpa virtual environment
- Testing cepat tanpa setup venv

### fix_venv.sh
Script untuk memperbaiki masalah virtual environment.
```bash
bash utils/fix_venv.sh
```

**Kegunaan:**
- Fix missing OpenCV di venv
- Repair broken venv setup
- Reinstall dependencies

### setup.sh
Setup wizard dengan GUI interaktif (alternative installer).
```bash
bash utils/setup.sh
```

**Kegunaan:**
- Alternative untuk `install.sh` dengan GUI
- Membutuhkan `dialog` atau `whiptail`
- Lebih user-friendly untuk pemula

## 💡 Catatan

**Untuk penggunaan normal, gunakan:**
```bash
bash install.sh      # Install otomatis
python3 main.py      # Run aplikasi
```

Script di folder ini hanya untuk kasus khusus atau troubleshooting.

---

**Version:** 1.2  
**Last Updated:** November 4, 2025
