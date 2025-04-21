cmake_minimum_required(VERSION 3.27 FATAL_ERROR)
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_OSX_DEPLOYMENT_TARGET 12.0) # Monterey

set(CMAKE_CONFIGURATION_TYPES Release Debug)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Possible values are: Release, Debug" FORCE)
endif()

project(cpos LANGUAGES C CXX ASM)
message("Config   : ${CMAKE_BUILD_TYPE}")
message("Compiler : ${CMAKE_CXX_COMPILER_ID}")


set(is_msvc_c_cpp $<AND:${is_c_cpp},$<CXX_COMPILER_ID:MSVC>>)

find_package(Threads REQUIRED)

add_executable(odin src/main.cpp src/libtommath.cpp)

target_include_directories(odin PRIVATE
#  ${CMAKE_SOURCE_DIR}/src
  /opt/homebrew/Cellar/llvm@17/17.0.6/include
)

target_compile_definitions(odin PRIVATE
  __STDC_CONSTANT_MACROS
  __STDC_FORMAT_MACROS
  __STDC_LIMIT_MACROS
)

target_compile_options(odin PRIVATE

  $<$<PLATFORM_ID:Darwin,Linux>:
    -g

    -Wno-switch
    -Wno-macro-redefined
    -Wno-unused-value

    $<$<CONFIG:Debug>:
      -O0
    >
    $<$<CONFIG:Release>:
      -O3
    >
  >
)

target_link_options(odin PRIVATE
  $<$<PLATFORM_ID:Darwin>:
    -framework System
  >

  $<$<PLATFORM_ID:Darwin,Linux>:
    -Wl,-search_paths_first
    -Wl,-headerpad_max_install_names
  >
)

target_link_directories(odin PRIVATE
  /opt/homebrew/Cellar/llvm@17/17.0.6/lib
)

target_link_libraries(odin PRIVATE
  $<$<PLATFORM_ID:Darwin,Linux>:
    Threads::Threads
    iconv
    dl
    m
    # stdc++
  >
  
  $<$<PLATFORM_ID:Darwin>:
    LLVM
  >
)
