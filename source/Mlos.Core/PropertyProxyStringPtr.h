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
        auto view = *reinterpret_cast<Mlos::Core::StringPtr*>(buffer.Pointer);

        const byte* dataPtr = reinterpret_cast<const byte*>(view.Data) + reinterpret_cast<uint64_t>(buffer.Pointer);

        return Mlos::Core::StringPtr { reinterpret_cast<const char*>(dataPtr), view.Length };
    }

    // Setting the value is not supported.
    //
    const PropertyProxy<Mlos::Core::StringPtr>& operator=(const Mlos::Core::StringPtr /*value*/) = delete;

    // Verify variable data.
    //
    bool VerifyVariableData(uint64_t objectOffset, uint64_t totalDataSize, uint64_t& expectedDataOffset) const
    {
        auto view = *reinterpret_cast<Mlos::Core::StringPtr*>(buffer.Pointer);

        if (view.Length > totalDataSize)
        {
            return false;
        }

        uint64_t offset = reinterpret_cast<uint64_t>(view.Data);
        offset += objectOffset;

        if (expectedDataOffset != offset)
        {
            return false;
        }

        expectedDataOffset += view.Length;
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
        auto view = *reinterpret_cast<Mlos::Core::WideStringPtr*>(buffer.Pointer);

        const byte* dataPtr = reinterpret_cast<const byte*>(view.Data) + reinterpret_cast<uint64_t>(buffer.Pointer);

        return Mlos::Core::WideStringPtr { reinterpret_cast<const wchar_t*>(dataPtr), view.Length / sizeof(wchar_t) };
    }

    // Setting the value is not supported.
    //
    const PropertyProxy<Mlos::Core::WideStringPtr>& operator=(const Mlos::Core::WideStringPtr /*value*/) = delete;

    // Verify variable data.
    //
    bool VerifyVariableData(uint64_t objectOffset, uint64_t totalDataSize, uint64_t& expectedDataOffset) const
    {
        auto view = *reinterpret_cast<Mlos::Core::StringPtr*>(buffer.Pointer);

        if (view.Length > totalDataSize)
        {
            return false;
        }

        uint64_t offset = reinterpret_cast<uint64_t>(view.Data);
        offset += objectOffset;

        if (expectedDataOffset != offset)
        {
            return false;
        }

        expectedDataOffset += view.Length;
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
