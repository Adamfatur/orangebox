#!/bin/bash
# Orange Box - Simple Setup Launcher
# Detects environment and runs appropriate installer

cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║          🧡 ORANGE BOX - SETUP WIZARD 🧡                     ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check available installers
has_dialog=false
has_python=false
has_flask=false

if command -v dialog &> /dev/null || command -v whiptail &> /dev/null; then
    has_dialog=true
fi

if command -v python3 &> /dev/null; then
    has_python=true
    # Check if Flask is available
    if python3 -c "import flask" &> /dev/null; then
        has_flask=true
    fi
fi

echo "Available installation methods:"
echo ""

# Show available options
option_count=0
declare -a options
declare -a commands

if [ "$has_flask" = true ]; then
    option_count=$((option_count + 1))
    options[$option_count]="GUI Installer (Dialog/Whiptail)"
    commands[$option_count]="gui"
    echo "  $option_count. 🌐 GUI Installer (Dialog/Whiptail) - Recommended"
fi

if [ "$has_dialog" = true ]; then
    option_count=$((option_count + 1))
    options[$option_count]="TUI Installer (Terminal UI)"
    commands[$option_count]="tui"
    echo "  $option_count. 🎨 TUI Installer (Terminal UI)"
fi

option_count=$((option_count + 1))
options[$option_count]="Command-line Installer"
commands[$option_count]="cli"
echo "  $option_count. 📦 Command-line Installer"

echo ""

# Get user choice
if [ $option_count -eq 1 ]; then
    echo "Only one installer available, starting automatically..."
    choice=1
else
    read -p "Select [1-$option_count]: " choice
fi

# Validate choice
if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt $option_count ]; then
    echo "❌ Invalid choice. Using command-line installer..."
    choice=$option_count
fi

# Run selected installer
selected_command="${commands[$choice]}"

case "$selected_command" in
    "gui")
        echo ""
        echo "🌐 Starting GUI Installer (Dialog/Whiptail)..."
        echo ""
        python3 tools/gui-installer.py
        ;;
    "cli")
        echo ""
        echo "📦 Starting Command-line Installer..."
        echo ""
        bash deployment/deploy.sh
        ;;
    *)
        echo "❌ Unknown installer type. Using command-line installer..."
        bash deployment/deploy.sh
        ;;
esac
