#!/bin/bash
# Orange Box - Verification Test Suite
# Tests all components before deployment

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║     🧡 ORANGE BOX - VERIFICATION TEST SUITE 🧡               ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0

test_result() {
    if [ $? -eq 0 ]; then
        echo "  ✓ $1"
        ((PASS++))
    else
        echo "  ✗ $1"
        ((FAIL++))
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Testing Directory Structure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test -d deployment && test_result "deployment/ exists"
test -d tools && test_result "tools/ exists"
test -d docs && test_result "docs/ exists"
test -d assets && test_result "assets/ exists"
test -d src && test_result "src/ exists"
test -d models && test_result "models/ exists"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 Testing Essential Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test -f main.py && test_result "main.py exists"
test -f config.py && test_result "config.py exists"
test -f requirements.txt && test_result "requirements.txt exists"
test -f setup.sh && test_result "setup.sh exists"
test -f models/model_quant_infer.tflite && test_result "model file exists"
test -f assets/logo-orangebox.png && test_result "logo exists"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 Testing Symlinks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test -L service && test_result "service symlink exists"
test -L logo.png && test_result "logo.png symlink exists"
readlink service | grep -q "deployment/service.sh" && test_result "service points correctly"
readlink logo.png | grep -q "assets/logo-orangebox.png" && test_result "logo.png points correctly"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Testing Script Permissions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test -x setup.sh && test_result "setup.sh executable"
test -x deployment/deploy.sh && test_result "deploy.sh executable"
test -x deployment/service.sh && test_result "service.sh executable"
test -x deployment/update.sh && test_result "update.sh executable"
test -x deployment/health-check.sh && test_result "health-check.sh executable"
test -x tools/gui-installer.py && test_result "gui-installer.py executable"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Testing Script Syntax"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

bash -n setup.sh 2>/dev/null && test_result "setup.sh syntax valid"
bash -n deployment/deploy.sh 2>/dev/null && test_result "deploy.sh syntax valid"
bash -n deployment/service.sh 2>/dev/null && test_result "service.sh syntax valid"
bash -n deployment/update.sh 2>/dev/null && test_result "update.sh syntax valid"
bash -n deployment/health-check.sh 2>/dev/null && test_result "health-check.sh syntax valid"
python3 -m py_compile tools/gui-installer.py 2>/dev/null && test_result "gui-installer.py syntax valid"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 Testing Python Modules"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -c "import sys; sys.path.insert(0, '.'); from src.core.waste_classifier import WasteClassifier" 2>/dev/null && test_result "WasteClassifier imports"
python3 -c "import sys; sys.path.insert(0, '.'); from src.core.main_controller import MainController" 2>/dev/null && test_result "MainController imports"
python3 -c "import sys; sys.path.insert(0, '.'); from src.hardware.hardware_interface_mock import HardwareInterface" 2>/dev/null && test_result "HardwareInterface (mock) imports"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Testing Python Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -c "import cv2" 2>/dev/null && test_result "OpenCV available"
python3 -c "import numpy" 2>/dev/null && test_result "NumPy available"
python3 -c "import subprocess, time, os, sys" 2>/dev/null && test_result "Standard libs available"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Testing Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test -f README.md && test_result "README.md exists"
test -f INSTALL.txt && test_result "INSTALL.txt exists"
test -f docs/DEPLOYMENT.md && test_result "DEPLOYMENT.md exists"
test -f docs/QUICKSTART.md && test_result "QUICKSTART.md exists"
test -f docs/CHEATSHEET.txt && test_result "CHEATSHEET.txt exists"
test -f docs/PROJECT_STRUCTURE.md && test_result "PROJECT_STRUCTURE.md exists"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Testing Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "PLATFORM.*=" config.py && test_result "PLATFORM defined in config.py"
grep -q "CAMERA_INDEX.*=" config.py && test_result "CAMERA_INDEX defined in config.py"
grep -q "CONFIDENCE_THRESHOLD.*=" config.py && test_result "CONFIDENCE_THRESHOLD defined in config.py"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo "  Total:  $((PASS + FAIL))"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ ALL TESTS PASSED! Project is ready for deployment."
    echo ""
    exit 0
else
    echo "⚠️  SOME TESTS FAILED. Please review errors above."
    echo ""
    exit 1
fi
