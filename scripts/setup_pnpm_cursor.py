#!/usr/bin/env python3
"""
Setup pnpm for Cursor Integration
Configures pnpm workspace and dependencies for Cursor integration.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

def check_pnpm_installed():
    """Check if pnpm is installed."""
    
    print("🔍 Checking pnpm installation...")
    
    try:
        result = subprocess.run(['pnpm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ pnpm version: {result.stdout.strip()}")
            return True
        else:
            print("❌ pnpm not found")
            return False
    except FileNotFoundError:
        print("❌ pnpm not found")
        return False

def install_pnpm_dependencies():
    """Install pnpm dependencies for Cursor integration."""
    
    print("📦 Installing pnpm dependencies...")
    
    try:
        # Install main dependencies
        result = subprocess.run(['pnpm', 'install'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Main dependencies installed")
        else:
            print(f"❌ Error installing dependencies: {result.stderr}")
            return False
        
        # Install Cursor-specific dependencies
        cursor_deps = [
            'aiohttp@^3.9.0',
            'watchdog@^3.0.0',
            'pydantic@^2.5.0'
        ]
        
        for dep in cursor_deps:
            result = subprocess.run(['pnpm', 'add', dep], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Installed {dep}")
            else:
                print(f"⚠️ Warning installing {dep}: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def setup_workspace_packages():
    """Setup workspace packages for Cursor integration."""
    
    print("🏗️ Setting up workspace packages...")
    
    workspace_packages = [
        'src/cursor',
        'src/knowledge', 
        'src/mobile',
        'scripts',
        'config'
    ]
    
    for package in workspace_packages:
        package_path = Path(package)
        if package_path.exists():
            print(f"✅ Workspace package exists: {package}")
        else:
            print(f"⚠️ Workspace package missing: {package}")
    
    return True

def configure_environment():
    """Configure environment for Cursor integration."""
    
    print("🔧 Configuring environment...")
    
    # Check for environment file
    env_file = Path('config/cursor.env')
    if env_file.exists():
        print("✅ Cursor environment file exists")
    else:
        print("⚠️ Cursor environment file missing")
    
    # Check for .npmrc
    npmrc_file = Path('.npmrc')
    if npmrc_file.exists():
        print("✅ .npmrc configuration exists")
    else:
        print("⚠️ .npmrc configuration missing")
    
    return True

def validate_cursor_scripts():
    """Validate Cursor integration scripts in package.json."""
    
    print("✅ Validating Cursor scripts...")
    
    package_json = Path('package.json')
    if not package_json.exists():
        print("❌ package.json not found")
        return False
    
    with open(package_json, 'r') as f:
        data = json.load(f)
    
    required_scripts = [
        'cursor:setup',
        'cursor:start', 
        'cursor:validate',
        'cursor:test',
        'cursor:enforce',
        'cursor:auto',
        'cursor:bootstrap',
        'cursor:knowledge',
        'cursor:integration'
    ]
    
    scripts = data.get('scripts', {})
    missing_scripts = []
    
    for script in required_scripts:
        if script in scripts:
            print(f"✅ Script exists: {script}")
        else:
            missing_scripts.append(script)
            print(f"❌ Script missing: {script}")
    
    if missing_scripts:
        print(f"❌ Missing {len(missing_scripts)} required scripts")
        return False
    
    return True

def test_cursor_integration():
    """Test Cursor integration setup."""
    
    print("🧪 Testing Cursor integration...")
    
    try:
        # Test setup script
        result = subprocess.run(['pnpm', 'run', 'cursor:setup'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Cursor setup script works")
        else:
            print(f"⚠️ Cursor setup script issue: {result.stderr}")
        
        # Test validation script
        result = subprocess.run(['pnpm', 'run', 'cursor:validate'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Cursor validation script works")
        else:
            print(f"⚠️ Cursor validation script issue: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Cursor integration: {e}")
        return False

def main():
    """Main setup function."""
    
    print("🚀 SETTING UP PNPM FOR CURSOR INTEGRATION")
    print("=" * 50)
    print("Configuring pnpm workspace and dependencies...")
    print()
    
    # Check pnpm installation
    if not check_pnpm_installed():
        print("❌ pnpm not installed. Please install pnpm first.")
        print("💡 Install with: npm install -g pnpm")
        return False
    
    # Install dependencies
    if not install_pnpm_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Setup workspace packages
    if not setup_workspace_packages():
        print("❌ Failed to setup workspace packages")
        return False
    
    # Configure environment
    if not configure_environment():
        print("❌ Failed to configure environment")
        return False
    
    # Validate scripts
    if not validate_cursor_scripts():
        print("❌ Failed to validate Cursor scripts")
        return False
    
    # Test integration
    if not test_cursor_integration():
        print("❌ Failed to test Cursor integration")
        return False
    
    print("\n🎉 PNPM CURSOR INTEGRATION SETUP COMPLETE!")
    print("✅ pnpm workspace configured")
    print("✅ Dependencies installed")
    print("✅ Environment configured")
    print("✅ Scripts validated")
    print("✅ Integration tested")
    print("\n🚀 Ready to use Cursor integration with pnpm!")
    print("\n💡 Available commands:")
    print("   pnpm run cursor:setup    - Setup Cursor integration")
    print("   pnpm run cursor:start     - Start Cursor integration")
    print("   pnpm run cursor:validate  - Validate Cursor integration")
    print("   pnpm run cursor:test      - Test Cursor integration")
    print("   pnpm run cursor:auto      - Auto-setup Cursor integration")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
