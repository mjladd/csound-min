# csound-min
#
# This file exists only because CMake requires a CMakeLists.txt in the
# directory you configure. The build itself is src/CMakeLists.txt.
#
#   cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
#   ninja -C build

if (APPLE)
    cmake_minimum_required(VERSION 3.28)
else()
    cmake_minimum_required(VERSION 3.13.4)
endif()

cmake_policy(SET CMP0077 NEW)
cmake_policy(SET CMP0075 NEW)
cmake_policy(SET CMP0091 NEW)

project(Csound)

set(CMAKE_CXX_STANDARD 11)

enable_testing()

add_subdirectory(src)
