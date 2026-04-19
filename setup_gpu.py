"""
Advanced CUDA Fix for RTX 4080 - Handles Python version issues
"""

import subprocess
import sys
import platform
import urllib.request
import json

def get_system_info():
    """Get detailed system information."""
    print("=" * 70)
    print(" SYSTEM INFORMATION ")
    print("=" * 70)
    
    info = {
        'python_version': sys.version,
        'python_version_short': f"{sys.version_info.major}.{sys.version_info.minor}",
        'platform': platform.system(),
        'architecture': platform.machine(),
        'python_executable': sys.executable
    }
    
    print(f"Python Version: {info['python_version_short']} ({platform.python_implementation()})")
    print(f"Python Path: {sys.executable}")
    print(f"Platform: {info['platform']} {info['architecture']}")
    
    # Check if Python version is supported
    major, minor = sys.version_info.major, sys.version_info.minor
    
    if major == 3:
        if minor < 8:
            print(f"\n⚠ WARNING: Python {major}.{minor} is too old for latest PyTorch")
            print("  Recommended: Python 3.8-3.11")
            return info, 'old_python'
        elif minor > 11:
            print(f"\n⚠ WARNING: Python {major}.{minor} might be too new")
            print("  PyTorch might not have wheels for this version yet")
            return info, 'new_python'
        else:
            print(f"✓ Python {major}.{minor} is supported")
    
    return info, 'ok'

def get_correct_pytorch_command():
    """Determine the correct PyTorch installation command."""
    info, status = get_system_info()
    
    print("\n" + "=" * 70)
    print(" PYTORCH INSTALLATION COMMANDS ")
    print("=" * 70)
    
    commands = []
    
    # For Windows with supported Python versions
    if platform.system() == 'Windows':
        py_version = info['python_version_short']
        
        print("\nFor your system, try these commands in order:\n")
        
        # Option 1: Latest stable with CUDA 12.1
        print("Option 1 (Recommended - CUDA 12.1):")
        cmd1 = f"pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
        print(f"  {cmd1}")
        commands.append(cmd1)
        
        # Option 2: CUDA 11.8 (sometimes more compatible)
        print("\nOption 2 (Alternative - CUDA 11.8):")
        cmd2 = f"pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
        print(f"  {cmd2}")
        commands.append(cmd2)
        
        # Option 3: Direct wheel download
        print("\nOption 3 (Direct download for specific Python version):")
        if py_version == "3.11":
            cmd3 = "pip3 install https://download.pytorch.org/whl/cu121/torch-2.1.0%2Bcu121-cp311-cp311-win_amd64.whl"
        elif py_version == "3.10":
            cmd3 = "pip3 install https://download.pytorch.org/whl/cu121/torch-2.1.0%2Bcu121-cp310-cp310-win_amd64.whl"
        elif py_version == "3.9":
            cmd3 = "pip3 install https://download.pytorch.org/whl/cu121/torch-2.1.0%2Bcu121-cp39-cp39-win_amd64.whl"
        else:
            cmd3 = "Visit https://pytorch.org/get-started/locally/ for your Python version"
        print(f"  {cmd3}")
        commands.append(cmd3)
        
        # Option 4: Conda (if available)
        print("\nOption 4 (If you have Anaconda/Miniconda):")
        cmd4 = "conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia"
        print(f"  {cmd4}")
        commands.append(cmd4)
    
    return commands, info

def auto_install_pytorch():
    """Automatically try different installation methods."""
    commands, info = get_correct_pytorch_command()
    
    print("\n" + "=" * 70)
    print(" AUTOMATED INSTALLATION ")
    print("=" * 70)
    
    response = input("\nTry automated installation? (y/n): ")
    if response.lower() != 'y':
        return False
    
    # First, uninstall existing PyTorch
    print("\nStep 1: Removing any existing PyTorch installation...")
    for pkg in ['torch', 'torchvision', 'torchaudio']:
        subprocess.run([sys.executable, '-m', 'pip', 'uninstall', pkg, '-y'], 
                      capture_output=True)
    print("  ✓ Cleaned up old installations")
    
    # Try each command until one works
    print("\nStep 2: Installing PyTorch with CUDA support...")
    
    for i, cmd in enumerate(commands[:3], 1):  # Try first 3 options
        if "Visit" in cmd:
            continue
            
        print(f"\nAttempt {i}: {cmd[:50]}...")
        
        try:
            # Parse command
            parts = cmd.split()
            if parts[0] == 'pip3':
                parts[0] = sys.executable
                parts.insert(1, '-m')
                parts.insert(2, 'pip')
                parts.remove('pip3')
            
            result = subprocess.run(parts, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("  ✓ Installation successful!")
                
                # Verify CUDA
                print("\nStep 3: Verifying CUDA support...")
                verification = subprocess.run(
                    [sys.executable, '-c', 'import torch; print(torch.cuda.is_available())'],
                    capture_output=True, text=True
                )
                
                if 'True' in verification.stdout:
                    print("  ✓ CUDA is working!")
                    
                    # Install CuPy
                    print("\nStep 4: Installing CuPy...")
                    subprocess.run([sys.executable, '-m', 'pip', 'install', 'cupy-cuda12x'],
                                 capture_output=True)
                    print("  ✓ CuPy installed")
                    
                    return True
                else:
                    print("  ✗ CUDA not detected, trying next method...")
            else:
                print(f"  ✗ Installation failed, trying next method...")
                
        except subprocess.TimeoutExpired:
            print("  ✗ Installation timed out, trying next method...")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    return False

def alternative_solution():
    """Provide alternative solutions."""
    print("\n" + "=" * 70)
    print(" ALTERNATIVE SOLUTIONS ")
    print("=" * 70)
    
    print("\nIf automatic installation failed, try these alternatives:\n")
    
    print("1. UPGRADE PIP FIRST:")
    print("   python -m pip install --upgrade pip")
    print("   Then retry the PyTorch installation")
    
    print("\n2. USE ANACONDA (Recommended for complex setups):")
    print("   a. Download Anaconda: https://www.anaconda.com/download")
    print("   b. Create new environment:")
    print("      conda create -n cuda_env python=3.10")
    print("      conda activate cuda_env")
    print("   c. Install PyTorch:")
    print("      conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia")
    
    print("\n3. USE PYTHON 3.10 (Most compatible):")
    print("   a. Download Python 3.10: https://www.python.org/downloads/release/python-31011/")
    print("   b. Install it")
    print("   c. Use: py -3.10 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    
    print("\n4. MANUAL WHEEL DOWNLOAD:")
    print("   a. Visit: https://download.pytorch.org/whl/torch_stable.html")
    print("   b. Find wheel for your Python version (cp310 = Python 3.10, etc.)")
    print("   c. Download and install: pip install [downloaded_file.whl]")

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║     ADVANCED CUDA FIX FOR RTX 4080                          ║
║     Handles Python version compatibility issues              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check current CUDA status
    try:
        import torch
        if torch.cuda.is_available():
            print("\n✓ CUDA is already working!")
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
            print("\nYou can run the GPU-accelerated code now!")
            return
    except ImportError:
        pass
    
    # Try automated installation
    if auto_install_pytorch():
        print("\n" + "=" * 70)
        print(" SUCCESS! ")
        print("=" * 70)
        print("\n✓ PyTorch with CUDA support is now installed!")
        print("✓ Your RTX 4080 is ready for GPU acceleration!")
        print("\nNow you can run:")
        print("  python gpu_benchmark.py")
        print("  python minefield_tangent_cuda.py")
        print("  python minefield_voronoi_cuda.py")
    else:
        # Provide alternatives if auto-install failed
        alternative_solution()
        
        print("\n" + "=" * 70)
        print(" MANUAL INTERVENTION REQUIRED ")
        print("=" * 70)
        print("\nThe automatic installation couldn't complete.")
        print("Please try the alternative solutions above.")
        print("\nMost common fix:")
        print("1. Update pip: python -m pip install --upgrade pip")
        print("2. Then run: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")

if __name__ == "__main__":
    main()