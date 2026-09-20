option(BUILD_CSOUND_COMMAND "Build the Csound command" ON)

string(TOUPPER "${CMAKE_SYSTEM_NAME}" CMAKE_SYSTEM_NAME_UPPER)

## Csound Commandline Executable ##
if(BUILD_CSOUND_COMMAND)
    set(CS_MAIN_SRCS csound/csound_main.c)
  if(CMAKE_SYSTEM_NAME MATCHES "Linux")
    find_package(Threads)
    list(APPEND CS_MAIN_SRCS csound/sched.c)
  endif()

  # We need a different name to avoid clashes with float libcsound
  make_executable(csound-bin "${CS_MAIN_SRCS}" "${CSOUNDLIB};${MATH_LIBRARY}" csound)


  if(CMAKE_SYSTEM_NAME MATCHES "Linux")
    target_link_libraries(csound-bin PRIVATE Threads::Threads)
  endif()
  if(NOT CMAKE_SYSTEM_NAME_UPPER STREQUAL "WASI")
  endif()
endif()



