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

// Serialization methods classes.
// CodeGen will create specialized function templates.
//
namespace ObjectSerialization
{
template<typename T>
constexpr inline size_t GetVariableDataSize(_In_ const T&)
{
    return 0;
}

template<typename T>
constexpr inline size_t GetSerializedSize(_In_ const T& object)
{
    return sizeof(object) + GetVariableDataSize(object);
}

template<typename TProxy>
constexpr inline bool VerifyVariableData(
    _In_ TProxy object,
    _In_ uint64_t objectOffset,
    _In_ uint64_t totalDataSize,
    _Inout_ uint64_t& expectedDataOffset)
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
constexpr inline bool VerifyVariableData(
    _In_ TProxy object,
    _In_ uint64_t frameLength)
{
    uint64_t expectedDataOffset = sizeof(typename TProxy::RealObjectType);
    uint64_t totalDataSize = frameLength - expectedDataOffset;

    bool isValid = VerifyVariableData(object, 0, totalDataSize, expectedDataOffset);

    isValid &= (16 /* sizeof(FrameHeader) */ + expectedDataOffset) <= frameLength;

    return isValid;
}

// Functions serializes variable length fields,
// as part of serialization, updates the offset and the length in var_ref field.
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
inline void Serialize(_In_ Mlos::Core::BytePtr buffer, _In_ const T& object)
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
}
