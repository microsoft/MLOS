//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: PropertyProxyStringPtr.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once
#include "PropertyProxy.h"
#include "StringTypes.h"

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: PropertyProxy<Mlos::Core::StringPtr>
//
// PURPOSE:
//  Property accessor for StringPtr field.
//
// NOTES:
//  Setting the value is not supported, as this is view to variable length field.
//
template<>
class PropertyProxy<Mlos::Core::StringPtr> : protected PropertyProxyBase
{
public:
    typedef Mlos::Core::StringPtr RealObjectType;

    PropertyProxy(BytePtr buffer, uint32_t offset)
      : PropertyProxyBase(buffer, offset)
    {}

    // Get the value.
    //
    operator Mlos::Core::StringPtr() const
    {
        // Get the value_ref and update the data pointer.
        //
        uint64_t offset = *reinterpret_cast<uint64_t*>(buffer.Pointer);
        uint64_t dataSize = *reinterpret_cast<uint64_t*>(buffer.Pointer + sizeof(uint64_t));

        const byte* dataPtr = reinterpret_cast<const byte*>(buffer.Pointer) + offset;

        return Mlos::Core::StringPtr(reinterpret_cast<const char*>(dataPtr), dataSize);
    }

    // Setting the value is not supported.
    //
    const PropertyProxy<Mlos::Core::StringPtr>& operator=(const Mlos::Core::StringPtr /*value*/) = delete;

    // Verify variable data.
    //
    bool VerifyVariableData(uint64_t objectOffset, uint64_t totalDataSize, uint64_t& expectedDataOffset) const
    {
        uint64_t offset = *reinterpret_cast<uint64_t*>(buffer.Pointer);
        uint64_t dataSize = *reinterpret_cast<uint64_t*>(buffer.Pointer + sizeof(uint64_t));

        if (dataSize > totalDataSize)
        {
            return false;
        }

        offset += objectOffset;

        if (expectedDataOffset != offset)
        {
            return false;
        }

        expectedDataOffset += dataSize;
        return true;
    }
};

//----------------------------------------------------------------------------
// NAME: PropertyProxy<Mlos::Core::WStringPtr>
//
// PURPOSE:
//  Property accessor for WideStringPtr field.
//
// NOTES:
//  Setting the value is not supported, as this is view to variable length field.
//
template<>
class PropertyProxy<Mlos::Core::WideStringPtr> : protected PropertyProxyBase
{
public:
    typedef Mlos::Core::WideStringPtr RealObjectType;

    PropertyProxy(BytePtr buffer, uint32_t offset)
      : PropertyProxyBase(buffer, offset)
    {}

    // Get the value.
    //
    operator Mlos::Core::WideStringPtr() const
    {
        // Get the value_ref and update the data pointer.
        //
        uint64_t offset = *reinterpret_cast<uint64_t*>(buffer.Pointer);
        uint64_t dataSize = *reinterpret_cast<uint64_t*>(buffer.Pointer + sizeof(uint64_t));

        const byte* dataPtr = reinterpret_cast<const byte*>(buffer.Pointer) + offset;

        return Mlos::Core::WideStringPtr(reinterpret_cast<const wchar_t*>(dataPtr), dataSize / sizeof(wchar_t));
    }

    // Setting the value is not supported.
    //
    const PropertyProxy<Mlos::Core::WideStringPtr>& operator=(const Mlos::Core::WideStringPtr /*value*/) = delete;

    // Verify variable data.
    //
    bool VerifyVariableData(uint64_t objectOffset, uint64_t totalDataSize, uint64_t& expectedDataOffset) const
    {
        uint64_t offset = *reinterpret_cast<uint64_t*>(buffer.Pointer);
        uint64_t dataSize = *reinterpret_cast<uint64_t*>(buffer.Pointer + sizeof(uint64_t));

        if (dataSize > totalDataSize)
        {
            return false;
        }

        offset += objectOffset;

        if (expectedDataOffset != offset)
        {
            return false;
        }

        expectedDataOffset += dataSize;
        return true;
    }
};
}
}

namespace ObjectSerialization
{
template<>
inline bool VerifyVariableData(
    Mlos::Core::PropertyProxy<Mlos::Core::StringPtr> object,
    uint64_t objectOffset,
    uint64_t totalDataSize,
    uint64_t& expectedDataOffset)
{
    return object.VerifyVariableData(objectOffset, totalDataSize, expectedDataOffset);
}

template<>
inline bool VerifyVariableData(
    Mlos::Core::PropertyProxy<Mlos::Core::WideStringPtr> object,
    uint64_t objectOffset,
    uint64_t totalDataSize,
    uint64_t& expectedDataOffset)
{
    return object.VerifyVariableData(objectOffset, totalDataSize, expectedDataOffset);
}
}
