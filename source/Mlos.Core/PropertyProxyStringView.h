//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: PropertyProxyStringView.h
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
#include "PropertyProxy.h"
#include "StringTypes.h"

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: PropertyProxy<std::string_view>
//
// PURPOSE:
//  Property accessor for string_view field.
//
// NOTES:
//  Setting the value is not supported, as this is view to variable length field.
//
template<>
class PropertyProxy<std::string_view> : protected PropertyProxyBase
{
public:
    typedef std::string_view RealObjectType;

    PropertyProxy(BytePtr buffer, uint32_t offset)
      : PropertyProxyBase(buffer, offset)
    {}

    // Get the value.
    //
    operator std::string_view() const
    {
        // Get the value_ref and update the data pointer.
        //
        Mlos::Core::StringPtr& view = *reinterpret_cast<Mlos::Core::StringPtr*>(buffer.Pointer);

        const byte* dataPtr = reinterpret_cast<const byte*>(view.Data) + reinterpret_cast<uint64_t>(buffer.Pointer);

        return std::string_view(reinterpret_cast<const char*>(dataPtr), view.Length);
    }

    // Setting the value is not supported.
    //
    const PropertyProxy<std::string_view>& operator=(const std::string_view /*value*/) = delete;

    // Verify variable data.
    //
    bool VerifyVariableData(uint64_t objectOffset, uint64_t totalDataSize, uint64_t& expectedDataOffset) const
    {
        Mlos::Core::StringPtr& view = *reinterpret_cast<Mlos::Core::StringPtr*>(buffer.Pointer);

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
// NAME: PropertyProxy<std::wstring_view>
//
// PURPOSE:
//  Property accessor for wstring_view field.
//
// NOTES:
//  Setting the value is not supported, as this is view to variable length field.
//
template<>
class PropertyProxy<std::wstring_view> : protected PropertyProxyBase
{
public:
    typedef std::wstring_view RealObjectType;

    PropertyProxy(BytePtr buffer, uint32_t offset)
      : PropertyProxyBase(buffer, offset)
    {}

    // Get the value.
    //
    operator std::wstring_view() const
    {
        // Get the value_ref and update the data pointer.
        //
        Mlos::Core::WideStringPtr& view = *reinterpret_cast<Mlos::Core::WideStringPtr*>(buffer.Pointer);

        const byte* dataPtr = reinterpret_cast<const byte*>(view.Data) + reinterpret_cast<uint64_t>(buffer.Pointer);

        return std::wstring_view(reinterpret_cast<const wchar_t*>(dataPtr), view.Length / sizeof(wchar_t));
    }

    // Setting the value is not supported.
    //
    const PropertyProxy<std::wstring_view>& operator=(const std::wstring_view /*value*/) = delete;

    // Verify variable data.
    //
    bool VerifyVariableData(uint64_t objectOffset, uint64_t totalDataSize, uint64_t& expectedDataOffset) const
    {
        Mlos::Core::WideStringPtr& view = *reinterpret_cast<Mlos::Core::WideStringPtr*>(buffer.Pointer);

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
    Mlos::Core::PropertyProxy<std::string_view> object,
    uint64_t objectOffset,
    uint64_t totalDataSize,
    uint64_t& expectedDataOffset)
{
    return object.VerifyVariableData(objectOffset, totalDataSize, expectedDataOffset);
}

template<>
inline bool VerifyVariableData(
    Mlos::Core::PropertyProxy<std::wstring_view> object,
    uint64_t objectOffset,
    uint64_t totalDataSize,
    uint64_t& expectedDataOffset)
{
    return object.VerifyVariableData(objectOffset, totalDataSize, expectedDataOffset);
}
}
