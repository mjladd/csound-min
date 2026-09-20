if (APPLE)
    cmake_minimum_required(VERSION 3.28)
else()
    cmake_minimum_required(VERSION 3.13.4)
endif()

set (CMAKE_CXX_STANDARD 11)

cmake_policy(SET CMP0077 NEW)
cmake_policy(SET CMP0075 NEW)
cmake_policy(SET CMP0091 NEW)

include(src/cmake/cmake-utilities.cmake)

# silence RPATH cmake warning
set(CMAKE_MACOSX_RPATH 1)
set(CMAKE_EXPORT_COMPILE_COMMANDS 1)
set(CMAKE_OSX_DEPLOYMENT_TARGET 11)



message(STATUS "VCPKG_TARGET_TRIPLET: ${VCPKG_TARGET_TRIPLET}")
message(STATUS "CMAKE_TOOLCHAIN_FILE: ${CMAKE_TOOLCHAIN_FILE}")

project(Csound)

enable_testing()

string(TOUPPER "${CMAKE_SYSTEM_NAME}" CMAKE_SYSTEM_NAME_UPPER)

# Collect private libraries for static linking (for pkg-config --static)
set(CSOUND_PRIVATE_LIBS "")

set(libcsound_private_include_dirs "")
set(libcsound_public_include_dirs "")

SET(BUILD_SHARED_LIBS ON)

if (${CMAKE_CXX_COMPILER_ID} MATCHES "Clang")
  set(CMAKE_COMPILER_IS_CLANG 1)
endif()

message(STATUS "Csound directory: ${CMAKE_HOME_DIRECTORY}")


# Project definitions
set(CS_VERSION "7")
set(CS_SUBVER "0")
set(CS_PATCHLEVEL "0")
set(APIVERSION "${CS_VERSION}.${CS_SUBVER}")

message(STATUS "Csound version: ${CS_VERSION}.${CS_SUBVER}.${CS_PATCHLEVEL}")


set(MACOSX_FRAMEWORK_BUNDLE_VERSION "${CS_VERSION}.${CS_SUBVER}.${CS_PATCHLEVEL}")
set(MACOSX_FRAMEWORK_SHORT_VERSION_STRING "${CS_VERSION}.${CS_SUBVER}.${CS_PATCHLEVEL}")
set(MACOSX_FRAMEWORK_IDENTIFIER "CSND")

# Relative install paths
set(EXECUTABLE_INSTALL_DIR "bin")
set(LOCALE_INSTALL_DIR "share/locale")
set(HEADER_INSTALL_DIR "include/csound")
set(SAMPLES_INSTALL_DIR "/samples")

    set(CS_FRAMEWORK_DEST "$ENV{HOME}/Library/Frameworks" CACHE PATH "Csound framework path")

set(CS_OPCODE_DIR "" CACHE PATH "opcodedir path")


if(APPLE)
    set(CMAKE_INSTALL_RPATH ${CS_FRAMEWORK_DEST})
endif()

include(TestBigEndian)
include(CheckFunctionExists)
include(CheckIncludeFile)
include(CheckIncludeFileCXX)
include(CheckLibraryExists)
include(CMakeParseArguments)
include(CheckCCompilerFlag)
include(CheckCXXCompilerFlag)
include(CheckCSourceCompiles)
include(CheckCXXSourceCompiles)
include(CMakePushCheckState)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/src/cmake/Modules/)
list(APPEND CMAKE_PREFIX_PATH /usr /usr/local /opt/local /sw)
message(STATUS "CMake module path: ${CMAKE_MODULE_PATH}")

if (CMAKE_HOST_SYSTEM_NAME MATCHES "Darwin")
    execute_process(
        COMMAND brew --prefix bison
        RESULT_VARIABLE BREW_BISON
        OUTPUT_VARIABLE BREW_BISON_PREFIX
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    if (BREW_BISON EQUAL 0 AND EXISTS "${BREW_BISON_PREFIX}")
        message(STATUS "Found Bison keg installed by Homebrew at ${BREW_BISON_PREFIX}")
        set(BISON_EXECUTABLE "${BREW_BISON_PREFIX}/bin/bison")
    elseif(EXISTS "/usr/local/bin/bison")
        message(STATUS "Bison in /usr/local/bin")
        set(BISON_EXECUTABLE "/usr/local/bin/bison")
    endif()

    execute_process(
        COMMAND brew --prefix flex
        RESULT_VARIABLE BREW_FLEX
        OUTPUT_VARIABLE BREW_FLEX_PREFIX
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    if (BREW_FLEX EQUAL 0 AND EXISTS "${BREW_FLEX_PREFIX}")
        message(STATUS "Found Flex keg installed by Homebrew at ${BREW_FLEX_PREFIX}")
        set(FLEX_EXECUTABLE "${BREW_FLEX_PREFIX}/bin/flex")
   elseif(EXISTS "/usr/local/bin/flex")
        message(STATUS "Flex in /usr/local/bin")
        set(FLEX_EXECUTABLE "/usr/local/bin/flex")
    endif()

endif()

### COMPILER OPTIMIZATION FLAGS
option(USE_COMPILER_OPTIMIZATIONS "Use the default Csound compiler optimization flags" ON)
option(USE_AVX2 "Enable AVX2 SIMD instructions on x86-64 (ignored on other architectures)" ON)
option(USE_APPLE_M1_BASELINE "On macOS arm64, tune for Apple M1 as the baseline CPU (-mcpu=apple-m1)" ON)
## USER OPTIONS ##
# Optional targets, they should all default to ON (check_deps will disable them if not possible to build)
option(USE_DOUBLE "Set to use double-precision floating point for audio samples." ON)
option(USE_LIBSNDFILE "Use libsndfile for sndfile IO, if available" ON)
option(BUILD_PERFTHREAD_CLASS "Include the Csound performance thread support (C++) " ON)
option(BUILD_UTILITIES "Build stand-alone executables for utilities that can also be used with -U" ON)
option(NEW_PARSER_DEBUG "Enable tracing of new parser" OFF)
option(BUILD_MULTI_CORE "Enable building for multicore system" ON)
option(FAIL_MISSING "Fail when a required external dependency is not present (useful for packagers)" OFF)
option(BUILD_STATIC_LIBRARY "Also build a static version of the csound library" OFF)
option(USE_LRINT "Use lrint/lrintf for converting floating point values to integers." ON)
option(USE_CURL "Use CURL library" ON)
option(USE_DEFAULT_OPCODEDIR "Use default opcodedir for the system" ON)
option(BUILD_TESTS "Build tests" OFF)
option(LEXER_DEBUG "Build lexer with debug option" OFF)
option(USE_GIT_COMMIT "Show the git commit in version information" ON)
option(REQUIRE_PTHREADS "For non-Windows systems, set whether Csound will use threads or not" ON)
option(DEBUG_ERROR_ON_WARNING "For a debug build, error on a compiler# warning" OFF)
option(BUILD_PLUGINS "Build external opcodes as plugins" OFF)
    # Keep this WASI-only mode out of native platform configurations, including
    # caches left behind by a previous cross-compilation.
    unset(BUILD_WASI_BROWSER CACHE)
    set(BUILD_WASI_BROWSER OFF)
option(BUILD_WITH_LTO "Build with link-time optimisations" OFF)
option(USE_SHORT_TABLE_LENGTH  "Build with original max table length 2^24" OFF)
option(USE_ASA  "Use address sanitizer in Debug build" ON)
option(USE_LIBSAMPLERATE "Use libsamplerate for sample rate conversion" ON)
option(USE_LOCK_BARRIER "Use lock-based barrier in PARCS " OFF)
option(ALIGN_MEMORY "Align memory allocation to MYFLT size" OFF)
option(PRESERVE_NAN "Force preserving NaNs against optimisation removal" ON)
# Build metadata overrides for reproducible/sandboxed builds (e.g. Nix).
set(CSOUND_GIT_HASH "" CACHE STRING "Override git commit shown in version output")
set(CSOUND_BUILD_DATE "" CACHE STRING "Override build date shown in version output (e.g. 2026-02-12)")


# secret rabbit code
if (USE_LIBSAMPLERATE)
       find_package(SampleRate MODULE)
endif()

if(SampleRate_FOUND)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DUSE_SRC")
    message(STATUS "Using Secret Rabbit Code")
endif()


if(USE_SHORT_TABLE_LENGTH)
     set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DSHORT_TABLE_LENGTH")
    message(STATUS "Using short max table length")
endif()


if(ALIGN_MEMORY)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DALIGN_MEMORY")
    message(STATUS "Aligning memory to MYFLT size")
else()
    message(STATUS "No memory alignment")
endif()


# Include this after the install path definitions so we can override them here.
# Also after function definitions so we can use them there
# Also after user options so that the default values don't overwrite the custom files values
find_file(CUSTOM_CMAKE "Custom.cmake" HINTS ${CMAKE_HOME_DIRECTORY})

if(CUSTOM_CMAKE)
    message(STATUS "Including Custom.cmake file: ${CUSTOM_CMAKE}")
    include(${CUSTOM_CMAKE})
else()
    message(STATUS "Not using Custom.cmake file.")
endif()


if(BUILD_WITH_LTO)
set(CSOUNDLIB_SHARED_LINK_OPTIONS -flto -Werror=odr
-Werror=lto-type-mismatch -Werror=strict-aliasing)
message(STATUS "Building with link-time optimisations")
else()
set(CSOUNDLIB_SHARED_LINK_OPTIONS "")
message(STATUS "Not building with link-time optimisations")
endif()


# in Release configuration, set NDEBUG
if(${CMAKE_BUILD_TYPE} MATCHES "Release")
    message(STATUS "Building for release")
    add_definitions("-DNDEBUG")
elseif(${CMAKE_BUILD_TYPE} MATCHES "Debug")
    message(STATUS "Building for debug")
    add_definitions("-DBETA")
endif()

# set -Werror if in Debug configuration
#ifdef BARE_METAL
    set(CMAKE_CXX_FLAGS_RELEASE "-Os")
    set(CMAKE_C_FLAGS_RELEASE "-Os")
#else
    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
    set(CMAKE_C_FLAGS_RELEASE "-O3")
#endif
    if(${CMAKE_BUILD_TYPE} MATCHES "Debug")
       set(USE_COMPILER_OPTIMIZATIONS OFF)
        if (DEBUG_ERROR_ON_WARNING)
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Werror")
            set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Werror")
        endif()
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall")
        if(APPLE)
                set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wshorten-64-to-32 -Wpointer-sign")
                set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wshorten-64-to-32 -Wpointer-sign")
               if(USE_ASA)
                message(STATUS  "using address sanitizer")
                set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address")
                set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wshorten-64-to-32 -fsanitize=address")
                else()
                message(STATUS  "not using address sanitizer")
               endif()
        endif()
    endif()

if(USE_COMPILER_OPTIMIZATIONS)
    include(src/cmake/CompilerOptimizations.cmake)
    message(STATUS  "USING COMPILER OPTIMISATIONS")
else()
    message(STATUS  "NOT USING COMPILER OPTIMISATIONS")
endif()

# AVX2 support – x86-64 only, optional, enabled by default
if(USE_AVX2)
    # Restrict to x86-64; CMAKE_SYSTEM_PROCESSOR may be "x86_64" or "AMD64"
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64")
            check_c_compiler_flag("-mavx2" COMPILER_SUPPORTS_AVX2)
            if(COMPILER_SUPPORTS_AVX2)
                set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   -mavx2")
                set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -mavx2")
                message(STATUS "AVX2 enabled (-mavx2)")
            else()
                message(STATUS "AVX2 requested but compiler does not support -mavx2 – skipping")
            endif()
    else()
        message(STATUS "USE_AVX2 is ON but target is not x86-64 (${CMAKE_SYSTEM_PROCESSOR}) – skipping")
    endif()
else()
    message(STATUS "AVX2 support disabled")
endif()

# Apple M1 baseline tuning – macOS arm64 only, optional, enabled by default
if(USE_APPLE_M1_BASELINE)
    if(APPLE AND NOT IOS AND NOT OSXCROSS_TARGET
       AND (CMAKE_OSX_ARCHITECTURES STREQUAL "arm64"
            OR (NOT CMAKE_OSX_ARCHITECTURES AND CMAKE_SYSTEM_PROCESSOR STREQUAL "arm64")))
        check_c_compiler_flag("-mcpu=apple-m1" COMPILER_SUPPORTS_APPLE_M1)
        if(COMPILER_SUPPORTS_APPLE_M1)
            set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   -mcpu=apple-m1")
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -mcpu=apple-m1")
            message(STATUS "Apple M1 baseline tuning enabled (-mcpu=apple-m1)")
        else()
            message(STATUS "USE_APPLE_M1_BASELINE is ON but compiler does not support -mcpu=apple-m1 – skipping")
        endif()
    else()
        message(STATUS "USE_APPLE_M1_BASELINE is ON but not building for macOS arm64 – skipping")
    endif()
else()
    message(STATUS "Apple M1 baseline tuning disabled")
endif()

if(APPLE)
    #list(APPEND CMAKE_REQUIRED_INCLUDES "time.h")
    CHECK_FUNCTION_EXISTS(clock_gettime CLOCK_GETTIME)
    if(${CLOCK_GETTIME})
        message(STATUS  "clock_gettime() found")
        set(CMAKE_C_FLAGS "-DHAVE_CLOCK_GETTIME ${CMAKE_C_FLAGS}")
    else()
        message(STATUS  "clock_gettime() not found")
    endif()
endif()


# library installation directories
option(USE_LIB64 "Set to on to set installation directory for libraries to lib64" OFF)
if(USE_LIB64)
	set(LIBRARY_INSTALL_DIR "${CMAKE_INSTALL_PREFIX}/lib64")
    add_definitions("-DLIB64")
elseif(NOT DEFINED LIBRARY_INSTALL_DIR)
    set(LIBRARY_INSTALL_DIR "${CMAKE_INSTALL_PREFIX}/lib")
endif()
message(STATUS "LIBRARY INSTALL DIR: ${LIBRARY_INSTALL_DIR}")

if(USE_DOUBLE)
    message(STATUS "Building with 64-bit floats")
    set(PLUGIN_INSTALL_DIR "${LIBRARY_INSTALL_DIR}/csound/plugins64-${APIVERSION}")
else()
    message(STATUS "Building with 32-bit floats")
    set(PLUGIN_INSTALL_DIR "${LIBRARY_INSTALL_DIR}/csound/plugins-${APIVERSION}")
endif()







set(BUILD_DIR ${CMAKE_CURRENT_BINARY_DIR})

check_c_compiler_flag(-fvisibility=hidden HAS_VISIBILITY_HIDDEN)
check_cxx_compiler_flag(-fvisibility=hidden HAS_CXX_VISIBILITY_HIDDEN)
if (HAS_VISIBILITY_HIDDEN)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fvisibility=hidden")
endif()
if (HAS_CXX_VISIBILITY_HIDDEN)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fvisibility=hidden ")
endif()

if (PRESERVE_NAN)
    message(STATUS "Preserving NaNs")
    check_c_compiler_flag(-fno-finite-math-only HAS_NO_FINITE_MATH_ONLY)
    check_cxx_compiler_flag(-fno-finite-math-only HAS_CXX_NO_FINITE_MATH_ONLY)
    if (HAS_NO_FINITE_MATH_ONLY)
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fno-finite-math-only")
    endif()
    if (HAS_CXX_NO_FINITE_MATH_ONLY)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-finite-math-only")
    endif()
endif()

check_c_source_compiles("
#if defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__
#error __FINITE_MATH_ONLY__ is enabled
#endif
int main(void) { return 0; }
" CSOUND_C_PRESERVES_NONFINITE)
if (NOT CSOUND_C_PRESERVES_NONFINITE)
    message(FATAL_ERROR "C compiler has finite-math-only enabled; Csound requires NaN and Inf checks")
endif()

check_cxx_source_compiles("
#if defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__
#error __FINITE_MATH_ONLY__ is enabled
#endif
int main() { return 0; }
" CSOUND_CXX_PRESERVES_NONFINITE)
if (NOT CSOUND_CXX_PRESERVES_NONFINITE)
    message(FATAL_ERROR "C++ compiler has finite-math-only enabled; Csound requires NaN and Inf checks")
endif()

check_c_compiler_flag(-std=gnu11 HAS_C11)
if (HAS_C11)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=gnu11")
else()
check_c_compiler_flag(-std=gnu99 HAS_GNU99)
if (HAS_GNU99)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=gnu99")
endif()
endif()


if (HAS_CXX_VISIBILITY_HIDDEN)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fvisibility=hidden")
endif()

if(APPLE)
        message(STATUS "Building for OSX")


        set(DEFAULT_OSX_SYSROOT /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.8.sdk/)
        if(NOT CMAKE_OSX_SYSROOT AND EXISTS ${DEFAULT_OSX_SYSROOT})
            set(CMAKE_OSX_SYSROOT ${DEFAULT_OSX_SYSROOT})
        endif()

        if(CMAKE_OSX_SYSROOT AND NOT CMAKE_OSX_SYSROOT MATCHES ".*OSX10.6.*"
            AND (NOT  CMAKE_OSX_DEPLOYMENT_TARGET))
            set(CMAKE_OSX_DEPLOYMENT_TARGET 10.7)
            message(STATUS "OSX: Setting Deployment Target to 10.7")
        else()
            message(STATUS "OSX: Setting Deployment Target to ${CMAKE_OSX_DEPLOYMENT_TARGET}")
        endif()

        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DHAVE_VECLIB")
        if(NOT VECLIB_PATH)
            set(VECLIB_PATH "/System/Library/Frameworks/")
        endif()
endif()

# Set plugins install directory
if(USE_DOUBLE)
    if(APPLE)
        set(CSOUNDLIB "CsoundLib64")
        set(PLUGIN_INSTALL_DIR "${CS_FRAMEWORK_DEST}/${CSOUNDLIB}.framework/Versions/${APIVERSION}/Resources/Opcodes64")
    else()
        set(CSOUNDLIB "csound64")
    endif()
else()
    if(APPLE)
        set(CSOUNDLIB "CsoundLib")
        set(PLUGIN_INSTALL_DIR "${CS_FRAMEWORK_DEST}/${CSOUNDLIB}.framework/Versions/${APIVERSION}/Resources/Opcodes")
    else()
        set(CSOUNDLIB "csound")
    endif()
endif()

# set default user plugin directory (independent of CS_OPCODE_DIR)
if(APPLE)
    # dir relative to $HOME
    if(USE_DOUBLE)
      set(DEFAULT_USER_PLUGINDIR "Library/csound/${APIVERSION}/plugins64")
   else()
      set(DEFAULT_USER_PLUGINDIR "Library/csound/${APIVERSION}/plugins")
    endif()

    add_definitions("-DCS_DEFAULT_USER_PLUGINDIR=\"${DEFAULT_USER_PLUGINDIR}\"")
endif()

if(CS_OPCODE_DIR STREQUAL "")
if(APPLE)
        get_filename_component(CS_FRAMEWORK_FULL_PATH ${PLUGIN_INSTALL_DIR} ABSOLUTE)

    add_definitions("-DCS_DEFAULT_PLUGINDIR=\"${CS_FRAMEWORK_FULL_PATH}\"")
    set(DEFAULT_OPCODEDIR "${CS_FRAMEWORK_FULL_PATH}")
endif()
else()
   add_definitions("-DCS_DEFAULT_PLUGINDIR=\"${CS_OPCODE_DIR}\"")
   set(DEFAULT_OPCODEDIR "${CS_OPCODE_DIR}")
endif()


# LINUX definition
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
    set(LINUX YES)
    message(STATUS "LINUX operating system found")
else()
    set(LINUX NO)
endif()

if(LINUX)
    set(DEFAULT_OPCODEDIR "${PLUGIN_INSTALL_DIR}")
    add_definitions("-DCS_DEFAULT_PLUGINDIR=\"${DEFAULT_OPCODEDIR}\"")
    # dir relative to $HOME
    if(USE_DOUBLE)
        set(DEFAULT_USER_PLUGINDIR ".local/lib/csound/${APIVERSION}/plugins64")
    else()
        set(DEFAULT_USER_PLUGINDIR ".local/lib/csound/${APIVERSION}/plugins")
    endif()
    add_definitions("-DCS_DEFAULT_USER_PLUGINDIR=\"${DEFAULT_USER_PLUGINDIR}\"")
endif()


if(APPLE OR LINUX)
    message(STATUS "default plugin dir set to ${DEFAULT_OPCODEDIR}")
endif()

if(USE_DEFAULT_OPCODEDIR)
 add_definitions("-DUSE_DEFAULT_OPCODEDIR")
 message(STATUS "using default opcodedir")
endif()



set(BUILD_PLUGINS_DIR ${BUILD_DIR})
set(BUILD_BIN_DIR ${BUILD_DIR})
set(BUILD_LIB_DIR ${BUILD_DIR})

message(STATUS "BUILD_BIN_DIR set to ${BUILD_BIN_DIR}.")
message(STATUS "BUILD_LIB_DIR set to ${BUILD_LIB_DIR}.")
message(STATUS "BUILD_PLUGINS_DIR set to ${BUILD_PLUGINS_DIR}.")

# OS specific checks
TEST_BIG_ENDIAN(BIG_ENDIAN)

## HEADER/LIBRARY/OTHER CHECKS ##
# Check if libsndfile is available, if not, disable build
if(USE_LIBSNDFILE)
        message(STATUS "looking  at ${CMAKE_PREFIX_PATH}")
        find_package(SndFile MODULE)
        message(STATUS "libsndfile found: ${SndFile_LIBRARY}")
endif()
check_deps(USE_LIBSNDFILE SndFile_FOUND)

# this makes sure make_plugin() can find headers
list(APPEND libcsound_private_include_dirs ${SndFile_INCLUDE_DIR})

# carry on setting up libsndifle if so
if(USE_LIBSNDFILE)
    add_compile_definitions("USE_LIBSNDFILE")
    set(CSOUND_PRIVATE_LIBS "${CSOUND_PRIVATE_LIBS} -lsndfile")


    # add to required libraries so we can check for MIDI support
    list(APPEND CMAKE_REQUIRED_LIBRARIES SndFile::sndfile)

    check_c_source_compiles("#include <sndfile.h>
    int main(int argc, char** argv) {
    printf(\"SF_FORMAT_MPEG: %d\", SF_FORMAT_MPEG);
    return 0;
    }" HAVE_SF_FORMAT_MPEG)

    option(USE_MP3 "Use MP3 support in libsndfile" ON)
    check_deps(USE_MP3 HAVE_SF_FORMAT_MPEG)

    if (USE_MP3)
        message(STATUS  "Using libsndfile MP3 support")
        add_compile_definitions("SNDFILE_MP3")
    else()
        message(STATUS  "NOT Using libsndfile MP3 support")
    endif()
endif()

find_package(CURL)

set(THREADS_PREFER_PTHREAD_FLAG ON)

find_package(Threads)
# windows threads aren't supported
assign_bool(NOT_WINDOWS_THREADS NOT CMAKE_USE_WIN32_THREADS_INIT)
check_deps(REQUIRE_PTHREADS Threads_FOUND NOT_WINDOWS_THREADS)

if(REQUIRE_PTHREADS)
    list(APPEND CMAKE_REQUIRED_LIBRARIES Threads::Threads)
endif()

# Now, non required library searches
option(USE_ATOMIC_BUILTIN "Use Atomic Builtins if supported" ON)

if(USE_ATOMIC_BUILTIN)
    include(src/cmake/CheckAtomic.cmake)
    if(HAVE_ATOMIC_BUILTIN)
        message(STATUS "Using atomic builtins.")
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DHAVE_ATOMIC_BUILTIN")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DHAVE_ATOMIC_BUILTIN")
    else()
        message(STATUS "Not using atomic builtins - not found")
    endif()
else()
    message(STATUS "Not using atomic builtins - user disabled")
endif()

find_library(MATH_LIBRARY m)

if (NOT MATH_LIBRARY)
    set(MATH_LIBRARY "")
endif()

if(APPLE)
include(CheckSymbolExists)
check_symbol_exists(lrint math.h FOUND_LRINT)
else()
cmake_push_check_state()
list(APPEND CMAKE_REQUIRED_LIBRARIES ${MATH_LIBRARY})
check_function_exists(lrint FOUND_LRINT)
cmake_pop_check_state()
endif()

# MSVC / VCPKG won't find dirent.h by default. Need to add the path explicitly
find_file(DIRENT_H "dirent.h")

if(DIRENT_H)
else()
        message(WARNING "Dirent.h not found, Csound will not be able to load dynamic plugins such as real-time audio")
endif()

set(HEADERS_TO_CHECK
    unistd.h io.h fcntl.h stdint.h
    sys/time.h sys/types.h termios.h
    values.h winsock.h sys/socket.h
    dirent.h inttypes.h execinfo.h)

foreach(header ${HEADERS_TO_CHECK})
    # Convert to uppercase and replace [./] with _
    string(TOUPPER ${header} tmp)

    string(REGEX REPLACE [./] "_" upper_header ${tmp})
    check_include_file(${header} HAVE_${upper_header})
    if (HAVE_${upper_header})
        add_definitions("-DHAVE_${upper_header}")
    endif()
endforeach()

if (NOT HAVE_INTTYPES_H)
    message(FATAL_ERROR "Csound requires inttypes.h")
endif()

check_deps(USE_LRINT FOUND_LRINT)
if(USE_LRINT)
    add_definitions("-DUSE_LRINT")
endif()

## Check existence of CURL
if(USE_CURL)
    find_package(CURL)

    if(CURL_FOUND)
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DHAVE_CURL")
    else()
        message(STATUS "Not using CURL for urls - not found.")
    endif()
else()
    message(STATUS "Not using CURL for urls - disabled.")
endif()

# Flex/Bison for the new parser

find_package(FLEX)
find_package(BISON)

if(NOT FLEX_EXECUTABLE)
    message(FATAL_ERROR "Csound requires the flex executable")
endif()

if(NOT BISON_EXECUTABLE)
    message(FATAL_ERROR "Csound requires the bison executable")
endif()

## MAIN TARGETS ##

set(libcsound_CFLAGS -D__BUILDING_LIBCSOUND)

if(APPLE)
    set(_csound_install_interface_include_dir
        "${CS_FRAMEWORK_DEST}/${CSOUNDLIB}.framework/Headers")
else()
    set(_csound_install_interface_include_dir "${HEADER_INSTALL_DIR}")
endif()

list(APPEND libcsound_public_include_dirs
    $<BUILD_INTERFACE:${Csound_SOURCE_DIR}/src>
    $<BUILD_INTERFACE:${Csound_SOURCE_DIR}/src/include>
    $<BUILD_INTERFACE:${Csound_SOURCE_DIR}/src/H>
    $<BUILD_INTERFACE:${Csound_SOURCE_DIR}/src/Engine>
    $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}>
    $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/src/include>
    $<INSTALL_INTERFACE:${_csound_install_interface_include_dir}>
)

list(APPEND libcsound_private_include_dirs
    ${Csound_SOURCE_DIR}/src
    "${Csound_SOURCE_DIR}/src/util"
)

#checking pthread functions
if(REQUIRE_PTHREADS AND NOT CMAKE_SYSTEM_NAME_UPPER STREQUAL "WASI")
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DHAVE_PTHREAD")

  if (NOT VCPKG_TARGET_TRIPLET STREQUAL "x64-mingw-static")
    check_function_exists(pthread_spin_lock PTHREAD_SPIN_LOCK_EXISTS)
  endif()

  check_function_exists(pthread_barrier_init PTHREAD_BARRIER_INIT_EXISTS)

  if(PTHREAD_SPIN_LOCK_EXISTS)
     list(APPEND libcsound_CFLAGS -DHAVE_PTHREAD_SPIN_LOCK)
  endif()

  if(PTHREAD_BARRIER_INIT_EXISTS)
     list(APPEND libcsound_CFLAGS -DHAVE_PTHREAD_BARRIER_INIT)
  endif()
endif()

# get the git hash and pass it to csound
set(git_hash_values "none")

if(CSOUND_GIT_HASH)
    string(STRIP "${CSOUND_GIT_HASH}" git_hash_values)
    message(STATUS "HASH (override): ${git_hash_values}")
elseif(USE_GIT_COMMIT)
    find_package(Git)
    message(STATUS "GIT: ${GIT_EXECUTABLE}")

    if(GIT_FOUND)
        execute_process(COMMAND ${GIT_EXECUTABLE} "rev-parse" "HEAD"
                        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
                        OUTPUT_VARIABLE git_hash_value)

        if (git_hash_value)
            string(STRIP ${git_hash_value} git_hash_values)
            message(STATUS "HASH: ${git_hash_values}")
        endif()
    endif()
endif()

set_source_files_properties(src/Top/csound.c PROPERTIES COMPILE_FLAGS -DGIT_HASH_VALUE=${git_hash_values})

# Provide a configurable date token used by src/include/version.h.in.
set(CS_PACKAGE_DATE_DEFINE "__DATE__")
if(CSOUND_BUILD_DATE)
    string(STRIP "${CSOUND_BUILD_DATE}" csound_build_date_value)
    set(CS_PACKAGE_DATE_DEFINE "\"${csound_build_date_value}\"")
    message(STATUS "DATE (override): ${csound_build_date_value}")
endif()

# The csound library
set(libcsound_SRCS
    src/Top/csound.c
    src/Top/csound_perf.c
    src/Top/csound_events.c
    src/Top/csound_rtio.c
    src/Top/csound_messages.c
    src/Top/csound_time.c
    src/Top/argdecode.c
    src/Top/csound_debug.c
    src/Top/csmodule.c
    src/Top/getstring.c
    src/Top/main.c
    src/Top/new_opts.c
    src/Top/one_file.c
    src/Top/opcode.c
    src/Top/threads.c
    src/Top/utility.c
    src/Top/threadsafe.c
    src/Top/server.c
    src/Engine/auxfd.c
    src/Engine/cfgvar.c
    src/Engine/corfiles.c
    src/Engine/entry.c
    src/Engine/extract.c
    src/Engine/environ.c
    src/Engine/fgens.c
    src/Engine/filesys.c
    src/Engine/insert.c
    src/Engine/srconvert.c
    src/Engine/udo.c
    src/Engine/linevent.c
    src/Engine/memalloc.c
    src/Engine/memfiles.c
    src/Engine/musmon.c
    src/Engine/namedins.c
    src/Engine/rdscor.c
    src/Engine/scsort.c
    src/Engine/scxtract.c
    src/Engine/sort.c
    src/Engine/sread.c
    src/Engine/swritestr.c
    src/Engine/twarp.c
    src/Engine/csound_type_system.c
    src/Engine/csound_standard_types.c
    src/Engine/csound_data_structures.c
    src/Engine/ugen.c
    src/InOut/soundfile.c
    src/InOut/libsnd.c
    src/InOut/libsnd_u.c
    src/InOut/midifile.c
    src/InOut/midirecv.c
    src/InOut/midisend.c
    src/InOut/winascii.c
    src/InOut/windin.c
    src/InOut/window.c
    src/InOut/winEPS.c
    src/InOut/circularbuffer.c
    src/OOps/array_ops.c
    src/OOps/aops.c
    src/OOps/assert_ops.c
    src/OOps/bus.c
    src/OOps/cmath.c
    src/OOps/complex_ops.c
    src/OOps/diskin2.c
    src/OOps/disprep.c
    src/OOps/dumpf.c
    src/OOps/fftlib.c
    src/OOps/inst_ops.c
    src/OOps/lpred.c
    src/OOps/pffft.c
    src/OOps/goto_ops.c
    src/OOps/midiinterop.c
    src/OOps/midiops.c
    src/OOps/midiops2.c
    src/OOps/midiops3.c
    src/OOps/midiout.c
    src/OOps/mxfft.c
    src/OOps/oscils.c
    src/OOps/pitch0.c
    src/OOps/pstream.c
    src/OOps/pvfileio.c
    src/OOps/pvsanal.c
    src/OOps/random.c
    src/OOps/readline.c
    src/OOps/remote.c
    src/OOps/schedule.c
    src/OOps/sndinfUG.c
    src/OOps/str_ops.c
    src/OOps/structs.c
    src/OOps/ugens1.c
    src/OOps/ugens2.c
    src/OOps/ugens3.c
    src/OOps/ugens4.c
    src/OOps/ugens5.c
    src/OOps/ugens6.c
    src/OOps/ugtabs.c
    src/OOps/ugrw1.c
    src/OOps/vdelay.c
    src/OOps/compile_ops.c
)


set(vbap_ops
    src/Opcodes/vbap.c
)

set(libcsound_static_SRCS  ${libcsound_SRCS})


    set_source_files_properties(src/Opcodes/sfont.c PROPERTIES
        COMPILE_FLAGS -Wno-address-of-packed-member)

set(physmod_SRCS
    src/Opcodes/physutil.c
    src/Opcodes/modal4.c
    src/Opcodes/physmod.c
    src/Opcodes/mandolin.c
    src/Opcodes/singwave.c
    src/Opcodes/fm4op.c
    src/Opcodes/moog1.c
    src/Opcodes/shaker.c
    src/Opcodes/bowedbar.c
)

set(externs_SRCS
    src/Opcodes/babo.c
    src/Opcodes/bilbar.c
    src/Opcodes/compress.c
    src/Opcodes/eqfil.c
    src/Opcodes/Vosim.c
    src/Opcodes/squinewave.c
    src/Opcodes/pinker.c
    src/Opcodes/cpumeter.c
    src/Opcodes/sc_noise.c
    src/Opcodes/afilters.c
    src/Opcodes/wpfilters.c
    src/Opcodes/lufs.c
    src/Opcodes/date.c
    src/Opcodes/system_call.c
    src/Opcodes/serial.c
    src/Opcodes/counter.c
    src/Opcodes/liveconv.c
    src/Opcodes/sterrain.c
    src/Opcodes/gammatone.c
    src/Opcodes/sfont.c
    src/Opcodes/gendy.c
    src/Opcodes/phisem.c
    src/Opcodes/framebuffer.c
    src/Opcodes/cellular.c
    src/Opcodes/exciter.c
    src/Opcodes/buchla.c
    src/Opcodes/select.c
    src/Opcodes/platerev.c
    src/Opcodes/sequencer.c
    src/Opcodes/grain4.c
    src/Opcodes/loscilx.c
    src/Opcodes/minmax.c
    src/Opcodes/pan2.c
    src/Opcodes/vaops.c
    src/Opcodes/ugakbari.c
    src/Opcodes/harmon.c
    src/Opcodes/pitchtrack.c
    src/Opcodes/partikkel.c
    src/Opcodes/shape.c
    src/Opcodes/tabaudio.c
    src/Opcodes/tabsum.c
    src/Opcodes/crossfm.c
    src/Opcodes/pvlock.c
    src/Opcodes/fareyseq.c
    src/Opcodes/modmatrix.c
    src/Opcodes/scoreline.c
    src/Opcodes/ambicode1.c
    src/Opcodes/arrays.c
    src/Opcodes/emugens/emugens.c
    src/Opcodes/emugens/scugens.c
    src/Opcodes/zak.c
    src/Opcodes/paulstretch.c
)


set(newgabops_SRCS
    src/Opcodes/gab/tabmorph.c
    src/Opcodes/gab/hvs.c
    src/Opcodes/gab/newgabopc.c
)

set(gens_SRCS
    src/Opcodes/ftest.c
    src/Opcodes/fareygen.c
    src/Opcodes/quadbezier.c
)

set(pitch_ops_SRCS
    src/Opcodes/pitch.c
    src/Opcodes/spectra.c
)

set(stdopcod_SRCS
    src/Opcodes/ambicode.c
    src/Opcodes/bbcut.c
    src/Opcodes/biquad.c
    src/Opcodes/butter.c
    src/Opcodes/clfilt.c
    src/Opcodes/cross2.c
    src/Opcodes/dam.c
    src/Opcodes/dcblockr.c
    src/Opcodes/filter.c
    src/Opcodes/flanger.c
    src/Opcodes/follow.c
    src/Opcodes/fout.c
    src/Opcodes/freeverb.c
    src/Opcodes/ftconv.c
    src/Opcodes/ftgen.c
    src/Opcodes/gab/gab.c
    src/Opcodes/gab/vectorial.c
    src/Opcodes/grain.c
    src/Opcodes/locsig.c
    src/Opcodes/lowpassr.c
    src/Opcodes/metro.c
    src/Opcodes/newfils.c
    src/Opcodes/nlfilt.c
    src/Opcodes/oscbnk.c
    src/Opcodes/pluck.c
    src/Opcodes/repluck.c
    src/Opcodes/reverbsc.c
    src/Opcodes/seqtime.c
    src/Opcodes/sndloop.c
    src/Opcodes/sndwarp.c
    src/Opcodes/space.c
    src/Opcodes/spat3d.c
    src/Opcodes/syncgrain.c
    src/Opcodes/ugens7.c
    src/Opcodes/ugens9.c
    src/Opcodes/ugensa.c
    src/Opcodes/uggab.c
    src/Opcodes/ugmoss.c
    src/Opcodes/ugnorman.c
    src/Opcodes/ugsc.c
    src/Opcodes/wave-terrain.c
    src/Opcodes/wterrain2.c
    src/Opcodes/stdopcod.c
    src/Opcodes/dbap.c
    )

set(sock_ops_SRCS
    src/Opcodes/socksend.c
    src/Opcodes/sockrecv.c
)


set(hrtf_ops_SRCS
    src/Opcodes/hrtfopcodes.c
    src/Opcodes/hrtfearly.c
    src/Opcodes/hrtfreverb.c
    src/Opcodes/hrtferX.c
)

set(cs_pvs_ops_SRCS
    src/Opcodes/ifd.c
    src/Opcodes/partials.c
    src/Opcodes/psynth.c
    src/Opcodes/pvsbasic.c
    src/Opcodes/pvscent.c
    src/Opcodes/pvsdemix.c
    src/Opcodes/pvs_ops.c
    src/Opcodes/pvsband.c
    src/Opcodes/pvsbuffer.c
    src/Opcodes/pvsgendy.c
    )

set(oldpvoc_SRCS
    src/Opcodes/dsputil.c
    src/Opcodes/pvadd.c
    src/Opcodes/pvinterp.c
    src/Opcodes/pvocext.c
    src/Opcodes/pvread.c
    src/Opcodes/ugens8.c
    src/Opcodes/vpvoc.c
    src/Opcodes/pvoc.c
)

set(scanops_SRCS
    src/Opcodes/scansyn.c
    src/Opcodes/scansynx.c
)

set(unixops_SRCS
    src/Opcodes/control.c
    src/Opcodes/urandom.c
)

set(mp3in_SRCS
    src/Opcodes/mp3in.c
    src/InOut/libmpadec/layer1.c
    src/InOut/libmpadec/layer2.c
    src/InOut/libmpadec/layer3.c
    src/InOut/libmpadec/synth.c
    src/InOut/libmpadec/tables.c
    src/InOut/libmpadec/mpadec.c
    src/InOut/libmpadec/mp3dec.c)


if(NOT CMAKE_SYSTEM_NAME_UPPER STREQUAL "WASI")
    # Full set of C++ opcodes for non-WASI builds
    set(cppops_SRCS
       src/Opcodes/ampmidid.cpp
       src/Opcodes/mixer.cpp
       src/Opcodes/bformdec2.cpp
       src/Opcodes/doppler.cpp
       src/Opcodes/ftsamplebank.cpp
       src/Opcodes/padsynth_gen.cpp
       src/Opcodes/signalflowgraph.cpp
       src/Opcodes/arrayops.cpp
       src/Opcodes/lfsr.cpp
       src/Opcodes/pvsops.cpp
       src/Opcodes/trigEnvSegs.cpp
       src/Opcodes/tl/fractalnoise.cpp
    )
else()
    # Limited C++ opcodes for WASI builds
    set(cppops_SRCS
        src/Opcodes/arrayops.cpp
        src/Opcodes/bformdec2.cpp
        src/Opcodes/ftsamplebank.cpp
        src/Opcodes/padsynth_gen.cpp
        src/Opcodes/pvsops.cpp
        src/Opcodes/signalflowgraph.cpp
        src/Opcodes/tl/fractalnoise.cpp
        src/Opcodes/trigEnvSegs.cpp)
endif()

list(APPEND libcsound_SRCS)

if(NOT BUILD_PLUGINS)
 list(APPEND libcsound_SRCS ${cppops_SRCS} ${scanops_SRCS} ${physmod_SRCS}
 ${mp3in_SRCS} ${hrtf_ops_SRCS} ${sock_ops_SRCS} ${externs_SRCS}
 ${gens_SRCS} ${cs_pvs_ops_SRCS} ${newgabops_SRCS}  ${oldpvoc_SRCS}
 ${pitch_ops_SRCS} ${vbap_ops} ${stdopcod_SRCS}
)
 list(APPEND libcsound_CFLAGS -DCS_INTERNAL)

 list(APPEND libcsound_static_SRCS ${stdopcod_SRCS} ${cs_pvs_ops_SRCS} ${physmod_SRCS}
${pitch_ops_SRCS}  ${oldpvoc_SRCS} ${scanops_SRCS} ${mp3in_SRCS} ${cppops_SRCS}
${hrtf_ops_SRCS} ${sock_ops_SRCS} ${externs_SRCS} ${gens_SRCS} ${pitch_ops_SRCS}
${newgabops_SRCS}  ${oldpvoc_SRCS} ${vbap_ops}
)
else()
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DBUILD_PLUGINS")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DBUILD_PLUGINS")
endif()



if(UNIX)
if(NOT BUILD_PLUGINS)
 list(APPEND libcsound_SRCS ${unixops_SRCS})
endif()
 list(APPEND libcsound_static_SRCS ${unixops_SRCS})
endif()

if(BUILD_PERFTHREAD_CLASS AND NOT CMAKE_SYSTEM_NAME_UPPER STREQUAL "WASI")
    list(APPEND libcsound_SRCS "src/Top/csPerfThread.cpp")
    list(APPEND libcsound_static_SRCS "src/Top/csPerfThread.cpp")
endif()

# Handling New Parser
set(YACC_SRC ${CMAKE_CURRENT_SOURCE_DIR}/src/Engine/csound_orc.y)
set(YACC_OUT ${CMAKE_CURRENT_BINARY_DIR}/csound_orcparse.c)
set(YACC_OUTH ${CMAKE_CURRENT_BINARY_DIR}/csound_orcparse.h)

set(LEX_SRC ${CMAKE_CURRENT_SOURCE_DIR}/src/Engine/csound_orc.lex)
set(LEX_OUT ${CMAKE_CURRENT_BINARY_DIR}/csound_orclex.c)
set_source_files_properties(${CMAKE_CURRENT_BINARY_DIR}/csound_orclex.c
    PROPERTIES COMPILE_FLAGS "-Wno-implicit-fallthrough -Wno-misleading-indentation")

set(PRELEX_SRC ${CMAKE_CURRENT_SOURCE_DIR}/src/Engine/csound_pre.lex)
set(PRELEX_OUT ${CMAKE_CURRENT_BINARY_DIR}/csound_prelex.c)
set_source_files_properties(${CMAKE_CURRENT_BINARY_DIR}/csound_prelex.c
    PROPERTIES COMPILE_FLAGS "-Wno-implicit-fallthrough")

if(LEXER_DEBUG)
    message(STATUS "Building lexer with debug option")

    add_custom_command(
        OUTPUT ${LEX_OUT}
        DEPENDS ${LEX_SRC}
        COMMAND ${FLEX_EXECUTABLE} ARGS -d -B -t ${LEX_SRC} > ${LEX_OUT}
    )
else()
    add_custom_command(
        OUTPUT ${LEX_OUT}
        DEPENDS ${LEX_SRC}
        COMMAND ${FLEX_EXECUTABLE} ARGS -B -t  ${LEX_SRC} > ${LEX_OUT}
    )
endif()

add_custom_command(
    DEPENDS ${PRELEX_SRC}
    COMMAND ${FLEX_EXECUTABLE} ARGS -B ${PRELEX_SRC} > ${PRELEX_OUT}
    OUTPUT ${PRELEX_OUT}
)

add_custom_command(
    OUTPUT ${YACC_OUT} ${YACC_OUTH}
    DEPENDS ${YACC_SRC} ${LEX_OUT}
    COMMAND ${BISON_EXECUTABLE}
    ARGS -pcsound_orc -d --report=itemset -o ${YACC_OUT} ${YACC_SRC}
)

list(APPEND libcsound_SRCS
    ${LEX_OUT} ${YACC_OUT} ${PRELEX_OUT}
    src/Engine/csound_orc_semantics.c
    src/Engine/csound_orc_expressions.c
    src/Engine/csound_orc_optimize.c
    src/Engine/csound_orc_compile.c
    src/Engine/csound_orc_structs.c
    src/Engine/new_orc_parser.c
    src/Engine/symbtab.c)

list(APPEND libcsound_static_SRCS
    ${LEX_OUT} ${YACC_OUT} ${PRELEX_OUT}
    src/Engine/csound_orc_semantics.c
    src/Engine/csound_orc_expressions.c
    src/Engine/csound_orc_optimize.c
    src/Engine/csound_orc_compile.c
    src/Engine/csound_orc_structs.c
    src/Engine/new_orc_parser.c
    src/Engine/symbtab.c)


set_source_files_properties(${YACC_OUT} GENERATED)
set_source_files_properties(${YACC_OUTH} GENERATED)
set_source_files_properties(${LEX_OUT} GENERATED)
set_source_files_properties(${PRELEX_OUT} GENERATED)


# Handling New Score Parser

##list(APPEND libcsound_CFLAGS -DSCORE_PARSER)

#set(YACC_SCOSRC ${CMAKE_CURRENT_SOURCE_DIR}/src/Engine/csound_sco.y)
#set(YACC_SCOOUT ${CMAKE_CURRENT_BINARY_DIR}/csound_scoparse.c)
#set(YACC_SCOOUTH ${CMAKE_CURRENT_BINARY_DIR}/csound_scoparse.h)

#set(LEX_SCOSRC ${CMAKE_CURRENT_SOURCE_DIR}/src/Engine/csound_sco.lex)
#set(LEX_SCOOUT ${CMAKE_CURRENT_BINARY_DIR}/csound_scolex.c)

set(PRELEX_SCOSRC ${CMAKE_CURRENT_SOURCE_DIR}/src/Engine/csound_prs.lex)
set(PRELEX_SCOOUT ${CMAKE_CURRENT_BINARY_DIR}/csound_prslex.c)

##message("${CMAKE_CURRENT_BINARY_DIR}/csound_prslex.c")
##message("${CMAKE_CURRENT_BINARY_DIR}/csound_scolex.c")
##message("${CMAKE_CURRENT_BINARY_DIR}/csound_scoparse.c")

#add_custom_command(
#    OUTPUT ${LEX_SCOOUT}
#    DEPENDS ${LEX_SCOSRC}
#    COMMAND ${FLEX_EXECUTABLE} ARGS -B -t ${LEX_SCOSRC} > ${LEX_SCOOUT}
#    )

add_custom_command(
    OUTPUT ${PRELEX_SCOOUT}
    DEPENDS ${PRELEX_SCOSRC}
    COMMAND ${FLEX_EXECUTABLE} ARGS -B -t -d ${PRELEX_SCOSRC} > ${PRELEX_SCOOUT}
)

#add_custom_command(
#    OUTPUT ${YACC_SCOOUT} ${YACC_SCOOUTH}
#    DEPENDS ${YACC_SCOSRC} ${LEX_SCOOUT}
#    COMMAND ${BISON_EXECUTABLE}
#    ARGS -pcsound_sco -t -d --report=itemset -o ${YACC_SCOOUT} ${YACC_SCOSRC}
#    )

list(APPEND libcsound_SRCS ${PRELEX_SCOOUT})
    #${LEX_SCOOUT} ${YACC_SCOOUT} ${PRELEX_SCOOUT})

list(APPEND libcsound_static_SRCS ${PRELEX_SCOOUT})
    #${LEX_SCOOUT} ${YACC_SCOOUT} ${PRELEX_SCOOUT})

#set_source_files_properties(${YACC_SCOOUT} GENERATED)
#set_source_files_properties(${LEX_SCOOUT} GENERATED)
set_source_files_properties(${PRELEX_SCOOUT} GENERATED)

if(NEW_PARSER_DEBUG)
    message(STATUS "Building with new parser debugging.")
    list(APPEND libcsound_CFLAGS -DPARSER_DEBUG=1)
else()
    message(STATUS "Not building with new parser debugging.")
endif()

if(BUILD_MULTI_CORE)
    message(STATUS "Building with multicore support.")

    list(APPEND libcsound_SRCS
        src/Engine/cs_new_dispatch.c
        src/Engine/cs_par_base.c
        src/Engine/cs_par_orc_semantic_analysis.c)

    list(APPEND libcsound_static_SRCS
        src/Engine/cs_new_dispatch.c
        src/Engine/cs_par_base.c
        src/Engine/cs_par_orc_semantic_analysis.c)

    list(APPEND libcsound_CFLAGS -DPARCS)

   if(USE_LOCK_BARRIER)
     message(STATUS "Using thread-lock barrier.")
     list(APPEND libcsound_CFLAGS -DPARCS_USE_LOCK_BARRIER)
   else()
    message(STATUS "Using lock-free barrier.")
   endif()

else()
    message(STATUS "Not building with multicore support.")
endif()

set(CSOUNDLIB_STATIC "${CSOUNDLIB}-static")

# ADDING HERE TO GRAB LIST OF HEADERS IN CASE OF BUILDING OSX FRAMEWORK
add_subdirectory(src/include)

if(APPLE)
    string(REGEX REPLACE "([^;]+)(;|$)" "src/include/\\1\\2" csheaders "${csheaders}")
    file(GLOB H_headers "${CMAKE_CURRENT_SOURCE_DIR}/src/H/*.h")
    set(libcsound_SRCS "${libcsound_SRCS};${csheaders};${H_headers};${CMAKE_CURRENT_BINARY_DIR}/src/include/float-version.h;${CMAKE_CURRENT_BINARY_DIR}/src/include/version.h")
endif()


    set(_csound_library_type SHARED)

        add_library(${CSOUNDLIB} ${_csound_library_type} ${libcsound_SRCS})
    target_include_directories(${CSOUNDLIB} PRIVATE ${libcsound_private_include_dirs})
    target_include_directories(${CSOUNDLIB} PUBLIC ${libcsound_public_include_dirs})
    set_target_properties(${CSOUNDLIB} PROPERTIES SOVERSION ${APIVERSION})




if(APPLE)
        target_link_options(${CSOUNDLIB} PRIVATE LINKER:-adhoc_codesign)
        set_target_properties(${CSOUNDLIB} PROPERTIES FRAMEWORK YES)
        set_target_properties(${CSOUNDLIB} PROPERTIES FRAMEWORK_VERSION "${APIVERSION}")
        set_target_properties(${CSOUNDLIB} PROPERTIES PUBLIC_HEADER
            "${csheaders};${CMAKE_CURRENT_BINARY_DIR}/src/include/float-version.h;${CMAKE_CURRENT_BINARY_DIR}/src/include/version.h"
        )
endif()

if(BUILD_PLUGINS)
    message(STATUS "build external opcodes as plugins")
    target_compile_definitions(${CSOUNDLIB} PUBLIC
    "-DBUILD_PLUGINS")
endif()

# Add the install target
        install(TARGETS ${CSOUNDLIB}
            EXPORT CsoundPackageExports
            LIBRARY DESTINATION "${LIBRARY_INSTALL_DIR}"
            ARCHIVE DESTINATION "${LIBRARY_INSTALL_DIR}"
            FRAMEWORK DESTINATION "${CS_FRAMEWORK_DEST}")

if (LINUX)
    set_target_properties(${CSOUNDLIB} PROPERTIES
        INSTALL_RPATH "$ORIGIN"
    )
endif()

set(libcsound_LIBS "")

if(REQUIRE_PTHREADS AND NOT CMAKE_SYSTEM_NAME_UPPER STREQUAL "WASI")
    list(APPEND libcsound_LIBS Threads::Threads)
endif()

if (HAVE_ATOMIC_BUILTIN)
    list(APPEND libcsound_LIBS ${ATOMIC_LIB})
    set(CSOUND_PRIVATE_LIBS "${CSOUND_PRIVATE_LIBS} ${ATOMIC_LIB}")
endif()


if(USE_CURL AND CURL_FOUND)
  list(APPEND libcsound_LIBS ${CURL_LIBRARIES})
  set(CSOUND_PRIVATE_LIBS "${CSOUND_PRIVATE_LIBS} ${CURL_LIBRARIES}")
endif()

    message(STATUS "Not using localization.")

if (HAVE_EXECINFO_H)
    find_library(LIBEXECINFO_LIBRARY execinfo)

    if(LIBEXECINFO_LIBRARY)
       list(APPEND libcsound_LIBS ${LIBEXECINFO_LIBRARY})
       set(CSOUND_PRIVATE_LIBS "${CSOUND_PRIVATE_LIBS} ${LIBEXECINFO_LIBRARY}")
       message(STATUS "  ADDING LIBEXECINFO LIBRARY: ${LIBEXECINFO_LIBRARY}.")
    endif()
endif()

if(LINUX)
    message(STATUS "Building on Linux.")
    add_definitions(-DLINUX -DPIPES -DNO_FLTK_THREADS -D_GNU_SOURCE
    -DHAVE_SOCKETS)
    list(APPEND libcsound_LIBS ${MATH_LIBRARY} dl)
    set(CSOUND_PRIVATE_LIBS "${CSOUND_PRIVATE_LIBS} -lm -ldl -lpthread")

    find_library(LIBRT_LIBRARY rt)

    if(LIBRT_LIBRARY)
        list(APPEND libcsound_LIBS ${LIBRT_LIBRARY})
        set(CSOUND_PRIVATE_LIBS "${CSOUND_PRIVATE_LIBS} ${LIBRT_LIBRARY}")
        message(STATUS "  ADDING LIBRT LIBRARY: ${LIBRT_LIBRARY}.")
    endif()
endif()

if(BSD)
    message(STATUS "Building on BSD.")
    add_definitions(-DBSD)
endif()

if((APPLE AND NOT IOS) OR (OSXCROSS_TARGET))
    message(STATUS "Building on OSX")
    add_definitions(-DMACOSX -DPIPES -DNO_FLTK_THREADS -DHAVE_SOCKETS)
    find_library(ACCELERATE_LIBRARY Accelerate)
    find_path(VECLIB_PATH "Accelerate/Accelerate.h")
    list(APPEND libcsound_private_include_dirs ${VECLIB_PATH})
    list(APPEND libcsound_LIBS ${MATH_LIBRARY} dl ${ACCELERATE_LIBRARY})
    if(APPLE AND NOT IOS)
        set(CSOUND_PRIVATE_LIBS "${CSOUND_PRIVATE_LIBS} -lm -ldl ${ACCELERATE_LIBRARY}")
    endif()
endif()


check_function_exists(strlcat HAVE_STRLCAT)
if(HAVE_STRLCAT)
    add_definitions(-DHAVE_STRLCAT)
endif()

# Locale-aware reading and printing
check_function_exists(strtok_r HAVE_STRTOK_R)
check_function_exists(strtod_l HAVE_STRTOD_L)
check_function_exists(sprintf_l HAVE_SPRINTF_L)

if(HAVE_STRTOK_R)
    add_definitions(-DHAVE_STRTOK_R)
endif()
if(HAVE_STRTOD_L AND NOT EMSCRIPTEN)
    add_definitions(-DHAVE_STRTOD_L)
endif()
if(HAVE_SPRINTF_L)
    add_definitions(-DHAVE_SPRINTF_L)
endif()

# Same for Windows
check_function_exists(_strtok_r HAVE__STRTOK_R)
check_function_exists(_strtod_l HAVE__STRTOD_L)
check_function_exists(_sprintf_l HAVE__SPRINTF_L)

if(HAVE__STRTOK_R)
    add_definitions(-DHAVE__STRTOK_R)
endif()
if(HAVE__STRTOD_L)
    add_definitions(-DHAVE__STRTOD_L)
endif()
if(HAVE__SPRINTF_L)
    add_definitions(-DHAVE__SPRINTF_L)
endif()

# Pass flags according to system capabilities

if((HAVE_WINSOCK_H OR HAVE_SYS_SOCKET_H) AND
   NOT EMSCRIPTEN AND
   NOT CMAKE_SYSTEM_NAME_UPPER STREQUAL "WASI")
    add_definitions(-DHAVE_SOCKETS)
endif()

#if(CMAKE_C_COMPILER MATCHES "gcc")
#    list(APPEND libcsound_CFLAGS -fno-strict-aliasing)
#endif()

if(BIG_ENDIAN)
    list(APPEND libcsound_CFLAGS -DWORDS_BIGENDIAN)
endif()

    target_compile_options(${CSOUNDLIB} PRIVATE ${libcsound_CFLAGS})

        target_link_libraries(${CSOUNDLIB} PRIVATE ${libcsound_LIBS})

if(USE_LIBSNDFILE)
        target_link_libraries(${CSOUNDLIB} PRIVATE SndFile::sndfile)
endif()

if(SampleRate_FOUND)
        target_link_libraries(${CSOUNDLIB} PRIVATE SampleRate::samplerate)
    set(CSOUND_PRIVATE_LIBS "${CSOUND_PRIVATE_LIBS} -lsamplerate")
endif()

    set_target_properties(${CSOUNDLIB} PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${BUILD_BIN_DIR}
        LIBRARY_OUTPUT_DIRECTORY ${BUILD_LIB_DIR}
        ARCHIVE_OUTPUT_DIRECTORY ${BUILD_LIB_DIR})



if(BUILD_STATIC_LIBRARY AND NOT BARE_METAL)
    add_library(${CSOUNDLIB_STATIC} STATIC ${libcsound_static_SRCS})
    target_include_directories(${CSOUNDLIB_STATIC} PRIVATE ${libcsound_private_include_dirs})
    target_include_directories(${CSOUNDLIB_STATIC} PUBLIC ${libcsound_public_include_dirs})
    SET_TARGET_PROPERTIES(${CSOUNDLIB_STATIC} PROPERTIES OUTPUT_NAME ${CSOUNDLIB})
    SET_TARGET_PROPERTIES(${CSOUNDLIB_STATIC} PROPERTIES PREFIX "lib")
    if(BUILD_PLUGINS)
     list(APPEND libcsound_CFLAGS -DCS_INTERNAL)
     endif()
    target_compile_options(${CSOUNDLIB_STATIC} PRIVATE
    ${libcsound_CFLAGS})

    if (USE_LIBSNDFILE)
        target_link_libraries(${CSOUNDLIB_STATIC} PUBLIC SndFile::sndfile)
    endif()

    if(SampleRate_FOUND)
        target_link_libraries(${CSOUNDLIB_STATIC} PUBLIC SampleRate::samplerate)
    endif()

    target_link_libraries(${CSOUNDLIB_STATIC} PUBLIC ${libcsound_LIBS})

    set_target_properties(${CSOUNDLIB_STATIC} PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${BUILD_BIN_DIR}
        LIBRARY_OUTPUT_DIRECTORY ${BUILD_LIB_DIR}
        ARCHIVE_OUTPUT_DIRECTORY ${BUILD_LIB_DIR})

    if (LINUX)
        set_target_properties(${CSOUNDLIB_STATIC} PROPERTIES
            INSTALL_RPATH "$ORIGIN"
        )
    endif()

    # Add the install target
    install(TARGETS ${CSOUNDLIB_STATIC}
        EXPORT CsoundStaticExports
        LIBRARY DESTINATION "${LIBRARY_INSTALL_DIR}"
        ARCHIVE DESTINATION "${LIBRARY_INSTALL_DIR}")
endif()

add_subdirectory(src/Opcodes)
add_subdirectory(src/InOut)
add_subdirectory(src/frontend)
add_subdirectory(src/util)
add_subdirectory(tests/c)
add_subdirectory(tests/commandline)
add_subdirectory(tests/regression)
add_subdirectory(tests/soak)

# uninstall target
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/src/cmake/cmake_uninstall.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
    IMMEDIATE @ONLY)

add_custom_target(uninstall
    COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake)

# target etags/tags
if(UNIX)
    add_custom_target(tags COMMAND etags `find ${CMAKE_CURRENT_SOURCE_DIR} -name \\*.cc -or -name \\*.hh -or -name \\*.cpp -or -name \\*.h -or -name \\*.c | grep -v " " `)
    add_custom_target(etags DEPENDS tags)
endif()

# build a CPack driven installer package
#include (InstallRequiredSystemLibraries)

set (CPACK_PACKAGE_NAME "csound")
set (CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/docs/COPYING")
set (CPACK_PACKAGE_VERSION "7.0.0")
set (CPACK_PACKAGE_VERSION_MAJOR "7")
set (CPACK_PACKAGE_VERSION_MINOR "0")
set (CPACK_PACKAGE_VERSION_PATCH "0")
include (CPack)

# install CMake package configuration files
include(CMakePackageConfigHelpers)

# export targets to CsoundTargets.cmake (separate from config wrapper)
    install(EXPORT CsoundPackageExports
        FILE "CsoundTargets.cmake"
        NAMESPACE "Csound::"
        DESTINATION "share/csound"
    )

# export static library targets (only when BUILD_STATIC_LIBRARY is enabled)
if(BUILD_STATIC_LIBRARY AND NOT BARE_METAL)
    install(EXPORT CsoundStaticExports
        FILE "CsoundStaticTargets.cmake"
        NAMESPACE "Csound::"
        DESTINATION "share/csound"
    )
endif()

# generate relocatable CsoundConfig.cmake from template
configure_package_config_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/src/cmake/CsoundConfig.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/CsoundConfig.cmake"
    INSTALL_DESTINATION "share/csound"
)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/CsoundConfig.cmake"
    DESTINATION "share/csound"
)

# generate and install CsoundConfigVersion.cmake
write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/CsoundConfigVersion.cmake"
    VERSION "${CS_VERSION}.${CS_SUBVER}.${CS_PATCHLEVEL}"
    COMPATIBILITY AnyNewerVersion
)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/CsoundConfigVersion.cmake"
    DESTINATION "share/csound"
)

# install FindCsound.cmake for projects using Module mode
install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/cmake/FindCsound.cmake"
    DESTINATION "share/csound"
)

# configure and install pkg-config file
# Set appropriate link flags for different platforms
if(APPLE AND NOT IOS)
    # On macOS, use framework flags when building as framework
    set(CSOUND_LINK_FLAGS "-F${CS_FRAMEWORK_DEST} -framework ${CSOUNDLIB}")
else()
    # Standard library flags for other platforms
    set(CSOUND_LINK_FLAGS "-L\${libdir} -l${CSOUNDLIB}")
endif()


configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/src/csound.pc.in"
    "${CMAKE_CURRENT_BINARY_DIR}/csound.pc"
    @ONLY
)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/csound.pc"
    DESTINATION "${LIBRARY_INSTALL_DIR}/pkgconfig"
)

# install samples
if(APPLE)
    install(DIRECTORY ${CMAKE_SOURCE_DIR}/samples
            DESTINATION  ${CS_FRAMEWORK_DEST}/${CSOUNDLIB}.framework/Versions/${APIVERSION})
else()
    install(DIRECTORY ${CMAKE_SOURCE_DIR}/samples
            DESTINATION ${CMAKE_INSTALL_PREFIX}/share)
endif()

