# CMakeLists.txt - CSD Tests Configuration
#
# This file configures CSD (Csound Document) tests for different platforms.
#
# Usage:
#   make csdtests         - Run CSD tests normally (non-verbose)
#   make csdtests-verbose - Run CSD tests with verbose output

find_package(Python3 COMPONENTS Interpreter QUIET)

configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/test_realtime_compile_opcodes.orc
  ${CMAKE_CURRENT_BINARY_DIR}/test_realtime_compile_opcodes.orc
  COPYONLY
)

if(Python3_Interpreter_FOUND)
  # Build the common test arguments
  set(COMMON_TEST_ARGS --csound-executable=${CMAKE_BINARY_DIR}/csound --source-dir=${CMAKE_CURRENT_SOURCE_DIR})

  # Platform-specific csdtests targets
    # Default for Unix-like systems (Linux, macOS)
    list(APPEND PLATFORM_ARGS --opcode7dir64=${CMAKE_BINARY_DIR})
    add_custom_target(csdtests
      ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test.py
      ${COMMON_TEST_ARGS}
      ${PLATFORM_ARGS}
      VERBATIM
    )
    # Verbose variant target
    add_custom_target(csdtests-verbose
      ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test.py
      --verbose
      --csound-executable=${CMAKE_BINARY_DIR}/csound
      --opcode7dir64=${CMAKE_BINARY_DIR}
      --source-dir=${CMAKE_CURRENT_SOURCE_DIR}
      VERBATIM
    )
  add_custom_target(csdtest-harness-tests
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_harness.py
    VERBATIM
  )
  add_dependencies(csdtests csdtest-harness-tests)
  add_dependencies(csdtests-verbose csdtest-harness-tests)
  if(TARGET csound-bin)
    add_dependencies(csdtests csound-bin)
    add_dependencies(csdtests-verbose csound-bin)
  endif()
else()
  message(STATUS "Python3 not found; not creating commandline test targets.")
endif()

