@echo off

set NRF_BLE_DRIVER_VERSION=4.1.100

echo Installing cmake+ninja
python -m pip install cmake ninja

echo Setting up vcpkg
if not exist vcpkg (
    git clone https://github.com/microsoft/vcpkg.git
)
call vcpkg\bootstrap-vcpkg.bat
set VCPKG_ROOT=%CD%\vcpkg
set PATH=%CD%\vcpkg;%PATH%

echo Building vcpkg dependencies
vcpkg install spdlog asio

if not exist pc-ble-driver (
    echo Cloning pc-ble-driver
    git clone https://github.com/NordicSemiconductor/pc-ble-driver.git
    pushd pc-ble-driver
    git checkout c0ffd419053e2405fffdb02ce7f1f9acceff4a66
) else (
    pushd pc-ble-driver
)

echo Building pc-ble-driver
git clean -fdx
cmake . -B build -DDISABLE_TESTS=1 -DDISABLE_EXAMPLES=1 -DSD_API_VER_NUMS="2;5" -DNRF_BLE_DRIVER_VERSION=%NRF_BLE_DRIVER_VERSION%
cmake --build build --config Release
cmake --install build --config Release --prefix install

popd
echo Done
