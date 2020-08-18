cmake_minimum_required(VERSION 3.15)
project(MlosCore)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fdeclspec")

include_directories(.)
include_directories(../../out/Mlos.CodeGen.out/Release/)

include(../../build/clang_tools.cmake)

add_library(
        MlosCore
        BytePtr.h
        ComponentConfig.h
        FNVHashFunction.h
        GlobalMemoryRegion.cpp
        GlobalMemoryRegion.h
        Hash.h
        Mlos.Core.cpp
        Mlos.Core.h
        MlosContext.cpp
        MlosContext.h
        NamedEvent.Linux.cpp
        NamedEvent.Linux.h
        ObjectDeserializationCallback.h
        ObjectSerialization.h
        ObjectSerializationStringView.h
        PropertyProxy.h
        PropertyProxyStringView.h
        SharedChannel.cpp
        SharedChannel.h
        SharedChannelPolicies.h
        SharedConfigMemoryRegion.cpp
        SharedConfigMemoryRegion.h
        SharedMemoryMapView.Linux.cpp
        SharedMemoryMapView.Linux.h
        SharedMemoryRegionView.h
        StaticSingleton.h
        StaticVector.h
        StringTypes.h
        Utils.h)

set_property(TARGET MlosCore PROPERTY CXX_STANDARD 17)
