#!/usr/bin/env bash

CC=gcc
CXX=g++
NRF_BLE_DRIVER_VERSION=4.1.100

echo "Installing cmake+ninja"
python -m pip install cmake ninja

echo "Setting up vcpkg"
if [ ! -d vcpkg ]; then
    git clone https://github.com/microsoft/vcpkg.git
fi
./vcpkg/bootstrap-vcpkg.sh
export VCPKG_ROOT=$(pwd)/vcpkg
export PATH=$VCPKG_ROOT:$PATH

echo "Building vcpkg dependencies"
vcpkg install spdlog asio

if [ ! -d pc-ble-driver ]; then
    echo "Cloning pc-ble-driver"
    git clone https://github.com/NordicSemiconductor/pc-ble-driver.git
    cd pc-ble-driver && git checkout c0ffd41
fi

echo "Building pc-ble-driver"
cd pc-ble-driver
git clean -fdx
cmake . -B build --log-level=TRACE \
    -DCMAKE_BUILD_TYPE=Release -DDISABLE_TESTS=1 -DDISABLE_EXAMPLES=1 -DSD_API_VER_NUMS="2;5" \
    -DNRF_BLE_DRIVER_VERSION=$NRF_BLE_DRIVER_VERSION $PC_BLE_DRIVER_ARCH \
    -DCMAKE_C_COMPILER=$CC -DCMAKE_CXX_COMPILER=$CXX
cmake --build build
cmake --install build --prefix install

