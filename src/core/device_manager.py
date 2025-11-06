"""
Device ID Management
Generate dan manage unique device identifier untuk multi-device support

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

import os
import socket
import hashlib
import uuid
import platform
from typing import Optional


class DeviceManager:
    """
    Manage device identification untuk multi-device deployment.
    Setiap Orange Box harus punya ID unik untuk tracking di database.
    """
    
    def __init__(self):
        self.device_id = None
        self.device_name = None
        self.device_location = None
        self._device_info = {}
    
    def get_device_id(self, custom_id: Optional[str] = None) -> str:
        """
        Get atau generate device ID yang unik.
        
        Args:
            custom_id: Custom device ID (None = auto-generate)
            
        Returns:
            Unique device ID string
        """
        if custom_id:
            self.device_id = custom_id
            return custom_id
        
        # Generate dari hostname + MAC address
        hostname = self._get_hostname()
        mac = self._get_mac_address()
        
        # Format: orangebox-{hostname}-{mac_short}
        # Contoh: orangebox-raspberrypi-a1b2c3
        mac_short = mac[:6]  # 6 karakter pertama dari MAC
        device_id = f"orangebox-{hostname}-{mac_short}".lower()
        
        # Clean up (remove invalid characters)
        device_id = ''.join(c if c.isalnum() or c == '-' else '_' for c in device_id)
        
        self.device_id = device_id
        return device_id
    
    def _get_hostname(self) -> str:
        """Get hostname of the device"""
        try:
            hostname = socket.gethostname()
            # Clean hostname (remove domain if present)
            hostname = hostname.split('.')[0]
            # Limit length
            if len(hostname) > 20:
                hostname = hostname[:20]
            return hostname
        except:
            return "unknown"
    
    def _get_mac_address(self) -> str:
        """Get MAC address of the device"""
        try:
            mac = uuid.getnode()
            mac_hex = format(mac, '012x')
            return mac_hex
        except:
            # Fallback: generate from hostname hash
            hostname = self._get_hostname()
            hash_obj = hashlib.md5(hostname.encode())
            return hash_obj.hexdigest()[:12]
    
    def get_device_info(self) -> dict:
        """
        Get comprehensive device information.
        
        Returns:
            Dict with device info (ID, hostname, MAC, platform, etc.)
        """
        if self._device_info:
            return self._device_info
        
        info = {
            'device_id': self.device_id or self.get_device_id(),
            'hostname': self._get_hostname(),
            'mac_address': self._get_mac_address(),
            'platform': platform.system(),
            'platform_release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'device_name': self.device_name,
            'device_location': self.device_location
        }
        
        # Add Raspberry Pi specific info
        if self._is_raspberry_pi():
            info['is_raspberry_pi'] = True
            info['rpi_model'] = self._get_rpi_model()
            info['rpi_serial'] = self._get_rpi_serial()
        else:
            info['is_raspberry_pi'] = False
        
        self._device_info = info
        return info
    
    def _is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                return 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo
        except:
            return False
    
    def _get_rpi_model(self) -> Optional[str]:
        """Get Raspberry Pi model"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().strip('\x00')
                return model
        except:
            return None
    
    def _get_rpi_serial(self) -> Optional[str]:
        """Get Raspberry Pi serial number"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        serial = line.split(':')[1].strip()
                        return serial
        except:
            return None
    
    def generate_short_id(self, length: int = 8) -> str:
        """
        Generate short device ID (untuk display/UI).
        
        Args:
            length: Length of short ID
            
        Returns:
            Short device ID (e.g., "A1B2C3D4")
        """
        full_id = self.device_id or self.get_device_id()
        hash_obj = hashlib.sha256(full_id.encode())
        short_id = hash_obj.hexdigest()[:length].upper()
        return short_id
    
    def save_device_config(self, filepath: str = 'device_config.txt'):
        """
        Save device configuration to file.
        Berguna untuk tracking device saat deploy ke production.
        
        Args:
            filepath: Path to config file
        """
        info = self.get_device_info()
        
        with open(filepath, 'w') as f:
            f.write("="*60 + "\n")
            f.write("ORANGE BOX - DEVICE CONFIGURATION\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Device ID:       {info['device_id']}\n")
            f.write(f"Short ID:        {self.generate_short_id()}\n")
            f.write(f"Hostname:        {info['hostname']}\n")
            f.write(f"MAC Address:     {info['mac_address']}\n")
            f.write(f"Platform:        {info['platform']} {info['platform_release']}\n")
            f.write(f"Machine:         {info['machine']}\n")
            
            if info['is_raspberry_pi']:
                f.write(f"\nRaspberry Pi:    Yes\n")
                f.write(f"Model:           {info.get('rpi_model', 'Unknown')}\n")
                f.write(f"Serial:          {info.get('rpi_serial', 'Unknown')}\n")
            
            if self.device_name:
                f.write(f"\nDevice Name:     {self.device_name}\n")
            if self.device_location:
                f.write(f"Location:        {self.device_location}\n")
            
            f.write("\n" + "="*60 + "\n")
        
        print(f"[DeviceManager] Device config saved to: {filepath}")
    
    def print_device_info(self):
        """Print device information to console"""
        info = self.get_device_info()
        
        print("\n" + "="*60)
        print("ORANGE BOX - DEVICE INFORMATION")
        print("="*60)
        print(f"Device ID:       {info['device_id']}")
        print(f"Short ID:        {self.generate_short_id()}")
        print(f"Hostname:        {info['hostname']}")
        print(f"MAC Address:     {info['mac_address']}")
        print(f"Platform:        {info['platform']} {info['platform_release']}")
        
        if info['is_raspberry_pi']:
            print(f"Raspberry Pi:    {info.get('rpi_model', 'Yes')}")
            if info.get('rpi_serial'):
                print(f"Serial Number:   {info['rpi_serial']}")
        
        if self.device_name:
            print(f"Device Name:     {self.device_name}")
        if self.device_location:
            print(f"Location:        {self.device_location}")
        
        print("="*60 + "\n")


def get_device_id(custom_id: Optional[str] = None) -> str:
    """
    Convenience function to quickly get device ID.
    
    Args:
        custom_id: Custom device ID (None = auto-generate)
        
    Returns:
        Device ID string
    """
    manager = DeviceManager()
    return manager.get_device_id(custom_id)


# Test program
if __name__ == "__main__":
    print("Testing Device ID Management...\n")
    
    # Create device manager
    manager = DeviceManager()
    
    # Set custom name/location (optional)
    manager.device_name = "Development Unit - MacBook"
    manager.device_location = "Jakarta Office"
    
    # Get device ID
    device_id = manager.get_device_id()
    print(f"Generated Device ID: {device_id}")
    print(f"Short ID: {manager.generate_short_id()}\n")
    
    # Print full info
    manager.print_device_info()
    
    # Save to file
    manager.save_device_config()
    
    # Test with custom ID
    print("\nTesting with custom ID:")
    custom_manager = DeviceManager()
    custom_id = custom_manager.get_device_id("OB-CAMPUS-A-001")
    print(f"Custom Device ID: {custom_id}")
    print(f"Short ID: {custom_manager.generate_short_id()}")
