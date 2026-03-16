cmake_minimum_required(VERSION 3.10)
project(MinefieldPathfinder)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(CGAL REQUIRED)
find_package(Boost REQUIRED COMPONENTS graph)
find_package(Threads REQUIRED)

# Add executable - using the correct filename
add_executable(minefield_comparison minefield_comparison_full.cpp)

# Link libraries
target_link_libraries(minefield_comparison 
    CGAL::CGAL 
    Boost::graph
    Threads::Threads
    gmp
    mpfr
)

# Set compiler optimization flags
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(minefield_comparison PRIVATE -O3 -march=native -mtune=native)
elseif(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(minefield_comparison PRIVATE -g -O0)
endif()

# Set compiler warnings
target_compile_options(minefield_comparison PRIVATE -Wall -Wextra -Wpedantic)

# Print configuration
message(STATUS "===================================")
message(STATUS "IARC Mission 10 Pathfinder Build")
message(STATUS "===================================")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "CGAL version: ${CGAL_VERSION}")
message(STATUS "Boost version: ${Boost_VERSION}")
message(STATUS "===================================")