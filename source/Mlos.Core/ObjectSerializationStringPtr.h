//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ObjectSerializationStringPtr.h
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
template<>
constexpr inline size_t GetVariableDataSize(_In_ const Mlos::Core::StringPtr& object)
{
    return object.Length * sizeof(char);
}

template<>
constexpr inline size_t GetVariableDataSize(_In_ const Mlos::Core::WideStringPtr& object)
{
    return object.Length * sizeof(wchar_t);
}

template<size_t N>
constexpr inline size_t GetVariableDataSize(_In_ const std::array<Mlos::Core::StringPtr, N>& object)
{
    size_t dataSize = 0;

    for (const Mlos::Core::StringPtr& element : object)
    {
        dataSize += GetVariableDataSize(element) + sizeof(char);
    }

    return dataSize;
}

template<size_t N>
constexpr inline size_t GetVariableDataSize(_In_ const std::array<Mlos::Core::WideStringPtr, N>& object)
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
    _In_ Mlos::Core::BytePtr buffer,
    _In_ uint64_t objectOffset,
    _In_ uint64_t dataOffset,
    _In_ const Mlos::Core::StringPtr& object)
{
    const size_t dataSize = GetVariableDataSize(object);
    memcpy(buffer.Pointer + dataOffset, object.Data, dataSize);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset)) = (dataOffset - objectOffset);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset + sizeof(uint64_t))) = dataSize;

    return dataSize;
}

template<>
inline size_t SerializeVariableData(
    _In_ Mlos::Core::BytePtr buffer,
    _In_ uint64_t objectOffset,
    _In_ uint64_t dataOffset,
    _In_ const Mlos::Core::WideStringPtr& object)
{
    const size_t dataSize = GetVariableDataSize(object);
    memcpy(buffer.Pointer + dataOffset, object.Data, dataSize);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset)) = (dataOffset - objectOffset);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset + sizeof(uint64_t))) = dataSize;

    return dataSize;
}

template<size_t N>
inline size_t SerializeVariableData(
    _In_ Mlos::Core::BytePtr buffer,
    _In_ uint64_t objectOffset,
    _In_ uint64_t dataOffset,
    _In_ const std::array<Mlos::Core::StringPtr, N>& object)
{
    size_t dataSize = 0;

    for (const Mlos::Core::StringPtr& element : object)
    {
        const size_t elementDataSize = GetVariableDataSize(element);
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
    _In_ Mlos::Core::BytePtr buffer,
    _In_ uint64_t objectOffset,
    _In_ uint64_t dataOffset,
    _In_ const std::array<Mlos::Core::WideStringPtr, N>& object)
{
    size_t dataSize = 0;

    for (const Mlos::Core::WideStringPtr& element : object)
    {
        const size_t elementDataSize = GetVariableDataSize(element);
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
