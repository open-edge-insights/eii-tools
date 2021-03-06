# Copyright (c) 2020 Intel Corporation.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM,OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

cmake_minimum_required(VERSION 3.11)
project(sw_trigger_utility VERSION 1.0.0 LANGUAGES C CXX)

# Globals
set(EII_COMMON_CMAKE "${CMAKE_CURRENT_SOURCE_DIR}/../common/cmake")

# Set C++ version
set(CMAKE_CXX_STANDARD 14)

# Set CFLAGS for C/C++
set(CMAKE_C_FLAGS "-fPIE -fPIC -O2 -Wall -pedantic -fstack-protector-strong -fno-strict-overflow -fno-delete-null-pointer-checks -fwrapv -D_FORTIFY_SOURCE=2")
set(CMAKE_CXX_FLAGS "${CMAKE_C_FLAGS}")

# Set LDFLAGS
set(CMAKE_SHARED_LINKER_FLAGS "-z noexecstack -z relro -z now")

# Add cmake module path
set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake" "${EII_COMMON_CMAKE}")

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
if(EXISTS "${CMAKE_CURRENT_BINARY_DIR}/compile_commands.json")
    EXECUTE_PROCESS(COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${CMAKE_CURRENT_BINARY_DIR}/compile_commands.json
        ${CMAKE_CURRENT_SOURCE_DIR}/compile_commands.json
    )
endif()

# Finding packages
find_package(EIIMsgEnv REQUIRED)
find_package(EIIUtils REQUIRED)
find_package(EIIConfigMgr REQUIRED)
find_package(EIIMessageBus REQUIRED)
find_package(PkgConfig REQUIRED)
find_package(IntelSafeString REQUIRED)

# Include header directories
include_directories(
    include/
    ${EIIMsgEnv_INCLUDE}
    ${EIIUtils_INCLUDE}
    ${EIIConfigMgr_INCLUDE}
    ${EIIMessageBus_INCLUDE}
    ${IntelSafeString_INCLUDE})

set(SOURCES src/sw_trigger_vi.cpp)
link_directories(${CMAKE_INSTALL_PREFIX}/lib)
add_executable(sw_trigger_utility ${SOURCES})

target_link_libraries(sw_trigger_utility
    PRIVATE
        ${EIIUtils_LIBRARIES}
        ${EIIMsgEnv_LIBRARIES}
        ${EIIConfigMgr_LIBRARIES}
        ${EIIMessageBus_LIBRARIES}
        ${ZMQ_LIBRARIES}
        ${CJSON_LIBRARIEES}
        ${IntelSafeString_LIBRARIES})
