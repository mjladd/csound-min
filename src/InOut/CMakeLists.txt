# REAL TIME AUDIO AND MIDI

message(STATUS "")
message(STATUS "## REALTIME AUDIO AND MIDI ##")

option(USE_PIPEWIRE "Build the PipeWire I/O module" ON)
option(USE_PULSEAUDIO "Build the PulseAudio I/O module" ON)
option(USE_PORTAUDIO "Build the PortAudio I/O module" ON)
option(USE_PORTMIDI "Build the PortMIDI I/O module" ON)
option(USE_IPMIDI "Build the IPMIDI I/O module" ON)
option(USE_JACK "Build the jack I/O module and opcodes" ON)
option(USE_ALSA "Build the ALSA I/O module" ON)
option(USE_COREMIDI "Build the CoreMIDI I/O Module" ON)
option(USE_AUDIOUNIT "Build the CoreAudio AudioUnit I/O module (requires CoreAudio)" ON)

list(APPEND CMAKE_REQUIRED_INCLUDES "/usr/local/include")

# FIND LIBRARIES AND HEADERS

if(USE_PORTAUDIO)
        find_package(portaudio MODULE)
endif()

if(USE_PORTMIDI)
        find_package(PortMidi MODULE)
endif()

if(USE_JACK)
    find_package(Jack MODULE)
endif()

# BUILD TARGETS

if(APPLE)
    find_package(CoreFoundation MODULE)

    find_package(CoreMIDI MODULE)
    check_deps(USE_COREMIDI CoreMIDI_FOUND CoreFoundation_FOUND)
    if(USE_COREMIDI)
        make_plugin(cmidi cmidi.c)
            target_link_libraries(cmidi PRIVATE CoreMIDI::coremidi CoreFoundation::corefoundation)
    endif()

    find_package(CoreAudio MODULE)
    find_package(AudioUnit MODULE)
    check_deps(USE_AUDIOUNIT CoreAudio_FOUND AudioUnit_FOUND CoreFoundation_FOUND)
    if (USE_AUDIOUNIT)
        make_plugin(rtauhal rtauhal.c)
            target_link_libraries(rtauhal PRIVATE AudioUnit::audiounit CoreFoundation::corefoundation CoreAudio::coreaudio)
    endif()
endif()

if(USE_ALSA AND LINUX)
        find_package(ALSA REQUIRED)

    make_plugin(rtalsa rtalsa.c ALSA::ALSA)
endif()


find_package(PulseAudio)
check_deps(USE_PULSEAUDIO PulseAudio_FOUND)

if(USE_PULSEAUDIO)
    make_plugin(rtpulse rtpulse.c PulseAudio::PulseAudio)
endif()

find_package(PipeWire)
check_deps(USE_PIPEWIRE PipeWire_FOUND)

if(USE_PIPEWIRE)
  make_plugin(rtpw rtpw.c PipeWire::PipeWire)
endif()

check_deps(USE_PORTAUDIO portaudio_FOUND)
if(USE_PORTAUDIO)

    make_plugin(rtpa rtpa.c)
if(APPLE)
    find_package(CoreFoundation MODULE)
    find_package(CoreAudio MODULE)
    find_package(AudioUnit MODULE)
     target_link_libraries(rtpa PRIVATE AudioUnit::audiounit
     CoreFoundation::corefoundation CoreAudio::coreaudio "-framework AudioToolbox")
 endif()
    # use the static library if available
    target_link_libraries(rtpa PRIVATE $<IF:$<TARGET_EXISTS:portaudio_static>,portaudio_static,portaudio>)
endif()

check_deps(USE_PORTMIDI PortMidi_FOUND)
if(USE_PORTMIDI)
    make_plugin(pmidi pmidi.c)
    target_link_libraries(pmidi PRIVATE PortMidi::portmidi)
if(APPLE)
    get_filename_component(portmidi_dir ${PortMidi_LIBRARY} DIRECTORY)
    set_target_properties(pmidi PROPERTIES INSTALL_RPATH ${portmidi_dir} )
endif()
endif()

if(USE_IPMIDI)

    make_plugin(ipmidi ipmidi.c "${ipmidi_LIBS}")
endif()

check_deps(USE_JACK Jack_FOUND)
if(USE_JACK)
    set(rtjack_SRCS rtjack.c alphanumcmp.c)
    make_plugin(rtjack "${rtjack_SRCS}")
    target_link_libraries(rtjack PRIVATE Jack::jack)
endif()



