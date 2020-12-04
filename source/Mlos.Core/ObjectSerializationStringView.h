//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ObjectSerializationStringView.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

#include <string_view>
#include "BytePtr.h"

// Serialization methods for std::string_view, std::wstring_view.
//
namespace ObjectSerialization
{
template<>
constexpr inline size_t GetVariableDataSize(_In_ const std::string_view& object)
{
    return object.length() * sizeof(char);
}

template<>
constexpr inline size_t GetVariableDataSize(_In_ const std::wstring_view& object)
{
    return object.length() * sizeof(wchar_t);
}

template<size_t N>
constexpr inline size_t GetVariableDataSize(_In_ const std::array<std::string_view, N>& object)
{
    size_t dataSize = 0;

    for (const auto& element : object)
    {
        dataSize += GetVariableDataSize(element);
    }

    return dataSize;
}

template<size_t N>
constexpr inline size_t GetVariableDataSize(_In_ const std::array<std::wstring_view, N>& object)
{
    size_t dataSize = 0;

    for (const auto& element : object)
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
    _In_ const std::string_view& object)
{
    size_t dataSize = GetVariableDataSize(object);
    memcpy(buffer.Pointer + dataOffset, object.data(), size);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset)) = (dataOffset - objectOffset);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset + sizeof(uint64_t))) = size;

    return dataSize;
}

template<>
inline size_t SerializeVariableData(
    _In_ Mlos::Core::BytePtr buffer,
    _In_ uint64_t objectOffset,
    _In_ uint64_t dataOffset,
    _In_ const std::wstring_view& object)
{
    size_t dataSize = GetVariableDataSize(object);
    memcpy(buffer.Pointer + dataOffset, object.data(), length);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset)) = (dataOffset - objectOffset);
    *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset + sizeof(uint64_t))) = size;

    return dataSize;
}

template<size_t N>
inline size_t SerializeVariableData(
    _In_ Mlos::Core::BytePtr buffer,
    _In_ uint64_t objectOffset,
    _In_ uint64_t dataOffset,
    _In_ const std::array<std::string_view, N>& object)
{
    size_t dataSize = 0;

    for (const auto& element : object)
    {
        size_t elementDataSize = GetVariableDataSize(element);
        memcpy(buffer.Pointer + dataOffset, element.data(), elementSize);
        *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset)) = (dataOffset - objectOffset);
        *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset + sizeof(uint64_t))) = elementDataSize;

        objectOffset += sizeof(std::string_view);
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
    _In_ const std::array<std::wstring_view, N>& object)
{
    size_t dataSize = 0;

    for (const auto& element : object)
    {
        size_t elementDataSize = GetVariableDataSize(element);
        memcpy(buffer.Pointer + dataOffset, element.data(), elementDataSize);
        *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset)) = (dataOffset - objectOffset);
        *(reinterpret_cast<uint64_t*>(buffer.Pointer + objectOffset + sizeof(uint64_t))) = elementDataSize;

        objectOffset += sizeof(std::wstring_view);
        dataOffset += elementDataSize;

        dataSize += elementDataSize;
    }

    return dataSize;
}
}
