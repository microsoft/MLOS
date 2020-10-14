//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ObjectSerialization.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

#include "BytePtr.h"
#include "StringTypes.h"

// Serialization methods classes.
// CodeGen will create specialized function templates.
//
namespace ObjectSerialization
{
template<typename T>
constexpr inline size_t GetVariableDataSize(const T&)
{
    return 0;
}

template<typename T>
constexpr inline size_t GetSerializedSize(const T& object)
{
    return sizeof(object) + GetVariableDataSize(object);
}

template<typename TProxy>
constexpr inline bool VerifyVariableData(
    TProxy object,
    uint64_t objectOffset,
    uint64_t totalDataSize,
    uint64_t& expectedDataOffset)
{
    // Verification of fixed size structure is no-op.
    // Ignore the arguments.
    //
    MLOS_UNUSED_ARG(object);
    MLOS_UNUSED_ARG(objectOffset);
    MLOS_UNUSED_ARG(totalDataSize);
    MLOS_UNUSED_ARG(expectedDataOffset);

    return true;
}

template<typename TProxy>
constexpr inline bool VerifyVariableData(TProxy object, uint64_t frameLength)
{
    uint64_t expectedDataOffset = sizeof(typename TProxy::RealObjectType);
    uint64_t totalDataSize = frameLength - expectedDataOffset;

    bool isValid = VerifyVariableData(object, 0, totalDataSize, expectedDataOffset);

    isValid &= (16 /* sizeof(FrameHeader) */ + expectedDataOffset) <= frameLength;

    return isValid;
}

// Serialize just the variable part of the object.
// Function is responsible for updating offset and length in var_ref field.
//
template<typename T>
inline size_t SerializeVariableData(
    Mlos::Core::BytePtr,
    uint64_t /* objectOffset */,
    uint64_t /* dataOffset */,
    const T& /* object*/)
{
    // Nothing.
    //

    return 0;
}

template<typename T>
inline void Serialize(Mlos::Core::BytePtr buffer, const T& object)
{
    // Serialize fixed size part of the object.
    //
    memcpy(buffer.Pointer, &object, sizeof(object));

    // Serialize variable length part of the object.
    //
    constexpr uint64_t objectOffset = 0;
    constexpr uint64_t dataOffset = sizeof(object);
    SerializeVariableData<T>(buffer, objectOffset, dataOffset, object);
}

template<>
constexpr inline size_t GetVariableDataSize(const Mlos::Core::StringPtr& object)
{
    return object.Length * sizeof(char);
}

template<>
constexpr inline size_t GetVariableDataSize(const Mlos::Core::WideStringPtr& object)
{
    return object.Length * sizeof(wchar_t);
}

template<size_t N>
constexpr inline size_t GetVariableDataSize(const std::array<Mlos::Core::StringPtr, N>& object)
{
    size_t dataSize = 0;

    for (const Mlos::Core::StringPtr& element : object)
    {
        dataSize += GetVariableDataSize(element);
    }

    return dataSize;
}

template<size_t N>
constexpr inline size_t GetVariableDataSize(const std::array<Mlos::Core::WideStringPtr, N>& object)
{
    size_t dataSize = 0;

    for (const Mlos::Core::WideStringPtr& element : object)
    {
        dataSize += GetVariableDataSize(element);
    }

    return dataSize;
}

template<>
inline size_t SerializeVariableData(
    Mlos::Core::BytePtr buffer,
    uint64_t objectOffset,
    uint64_t dataOffset,
    const Mlos::Core::StringPtr& object)
{
    size_t dataSize = GetVariableDataSize(object);
    memcpy(buffer.Pointer + dataOffset, object.Data, dataSize);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset)) = (dataOffset - objectOffset);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset + sizeof(uint64_t))) = dataSize;

    return dataSize;
}

template<>
inline size_t SerializeVariableData(
    Mlos::Core::BytePtr buffer,
    uint64_t objectOffset,
    uint64_t dataOffset,
    const Mlos::Core::WideStringPtr& object)
{
    size_t dataSize = GetVariableDataSize(object);
    memcpy(buffer.Pointer + dataOffset, object.Data, dataSize);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset)) = (dataOffset - objectOffset);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset + sizeof(uint64_t))) = dataSize;

    return dataSize;
}

template<size_t N>
inline size_t SerializeVariableData(
    Mlos::Core::BytePtr buffer,
    uint64_t objectOffset,
    uint64_t dataOffset,
    const std::array<Mlos::Core::StringPtr, N>& object)
{
    size_t dataSize = 0;

    for (const Mlos::Core::StringPtr& element : object)
    {
        size_t elementDataSize = GetVariableDataSize(element);
        memcpy(buffer.Pointer + dataOffset, element.Data, elementDataSize);
        *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset)) = (dataOffset - objectOffset);
        *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset + sizeof(uint64_t))) = elementDataSize;

        objectOffset += sizeof(Mlos::Core::StringPtr);
        dataOffset += elementDataSize;

        dataSize += elementDataSize;
    }

    return dataSize;
}

template<size_t N>
inline size_t SerializeVariableData(
    Mlos::Core::BytePtr buffer,
    uint64_t objectOffset,
    uint64_t dataOffset,
    const std::array<Mlos::Core::WideStringPtr, N>& object)
{
    size_t dataSize = 0;

    for (const Mlos::Core::WideStringPtr& element : object)
    {
        size_t elementDataSize = GetVariableDataSize(element);
        memcpy(buffer.Pointer + dataOffset, element.Data, elementDataSize);
        *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset)) = (dataOffset - objectOffset);
        *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset + sizeof(uint64_t))) = elementDataSize;

        objectOffset += sizeof(Mlos::Core::WideStringPtr);
        dataOffset += elementDataSize;

        dataSize += elementDataSize;
    }

    return dataSize;
}
}
