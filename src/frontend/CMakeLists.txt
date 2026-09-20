option(BUILD_CSOUND_COMMAND "Build the Csound command" ON)

## Csound Commandline Executable ##
if(BUILD_CSOUND_COMMAND)
    set(CS_MAIN_SRCS csound_main.c)
  if(CMAKE_SYSTEM_NAME MATCHES "Linux")
    find_package(Threads)
    list(APPEND CS_MAIN_SRCS sched.c)
  endif()

  # We need a different name to avoid clashes with float libcsound
  make_executable(csound-bin "${CS_MAIN_SRCS}" "${CSOUNDLIB};${MATH_LIBRARY}" csound)


  if(CMAKE_SYSTEM_NAME MATCHES "Linux")
    target_link_libraries(csound-bin PRIVATE Threads::Threads)
  endif()
endif()



