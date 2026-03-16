#!/bin/bash

# Build script for IARC Mission 10 Pathfinding Comparison
# Usage: ./build.sh [debug|release]

BUILD_TYPE=${1:-release}

echo "======================================"
echo " IARC Pathfinding Build Script"
echo "======================================"
echo ""

# Convert to proper case
if [ "$BUILD_TYPE" = "debug" ]; then
    CMAKE_BUILD_TYPE="Debug"
elif [ "$BUILD_TYPE" = "release" ]; then
    CMAKE_BUILD_TYPE="Release"
else
    echo "Invalid build type. Use 'debug' or 'release'"
    exit 1
fi

echo "Build type: $CMAKE_BUILD_TYPE"
echo ""

# Check for required dependencies
echo "Checking dependencies..."

# Function to check if package is installed
check_package() {
    if dpkg -l | grep -q "ii  $1"; then
        echo "  ✓ $1 installed"
    else
        echo "  ✗ $1 NOT installed"
        echo "    Run: sudo apt-get install $1"
        MISSING_DEPS=true
    fi
}

MISSING_DEPS=false

check_package "build-essential"
check_package "cmake"
check_package "libcgal-dev"
check_package "libboost-all-dev"
check_package "libgmp-dev"
check_package "libmpfr-dev"

if [ "$MISSING_DEPS" = true ]; then
    echo ""
    echo "ERROR: Missing dependencies. Install them first:"
    echo "sudo apt-get update"
    echo "sudo apt-get install build-essential cmake libcgal-dev libboost-all-dev libgmp-dev libmpfr-dev"
    exit 1
fi

echo ""
echo "All dependencies satisfied!"
echo ""

# Create build directory
echo "Creating build directory..."
mkdir -p build
cd build

# Run CMake
echo "Running CMake..."
cmake .. -DCMAKE_BUILD_TYPE=$CMAKE_BUILD_TYPE

if [ $? -ne 0 ]; then
    echo "ERROR: CMake configuration failed"
    exit 1
fi

echo ""
echo "Building project..."
make -j$(nproc)

if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

echo ""
echo "======================================"
echo " Build Successful!"
echo "======================================"
echo ""
echo "Executable: build/minefield_comparison"
echo ""
echo "To run the program:"
echo "  cd build"
echo "  ./minefield_comparison"
echo ""
echo "To visualize results (requires Python3 + matplotlib):"
echo "  python3 ../visualize_cpp_results.py"
echo ""
