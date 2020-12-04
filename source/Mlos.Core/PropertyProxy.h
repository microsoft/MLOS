//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: PropertyProxy.h
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
#include "ObjectSerialization.h"

namespace Mlos
{
namespace Core
{
// Base class for Property accessors.
//
class PropertyProxyBase
{
public:
    PropertyProxyBase(
        _In_ BytePtr buffer,
        _In_ uint32_t offset)
      : buffer(buffer.Pointer + offset)
    {}

protected:
    BytePtr buffer;
};

// Property accessor class
// Used to access field in flattened structures.
//
template<typename T>
class PropertyProxy : public PropertyProxyBase
{
public:
    typedef T RealObjectType;

    PropertyProxy(
        _In_ BytePtr buffer,
        _In_ uint32_t offset)
      : PropertyProxyBase(buffer, offset)
    {}

    // Get the value.
    //
    inline operator T() const
    {
        return *reinterpret_cast<T*>(buffer.Pointer);
    }

    // Set the value.
    //
    inline const PropertyProxy<T>& operator=(_In_ const T value)
    {
        *reinterpret_cast<T*>(buffer.Pointer) = value;

        return *this;
    }
};

// Property array accessor class.
//
template<typename TProxy, uint32_t N>
class PropertyArrayProxy : protected PropertyProxyBase
{
public:
    PropertyArrayProxy(
        _In_ BytePtr buffer,
        _In_ uint32_t offset)
      : PropertyProxyBase(buffer, offset)
    {}

    TProxy operator[](_In_ uint32_t index) noexcept
    {
        return TProxy(buffer, index * sizeof(typename TProxy::RealObjectType));
    }
};
}
}

namespace ObjectSerialization
{
template<typename TProxy, uint32_t N>
inline bool VerifyVariableData(
    _In_ Mlos::Core::PropertyArrayProxy<TProxy, N> array,
    _In_ uint64_t objectOffset,
    _In_ uint64_t totalDataSize,
    _Inout_ uint64_t& expectedDataOffset)
{
    size_t codegenTypeSize = sizeof(typename TProxy::RealObjectType);

    for (uint32_t i = 0; i < N; i++)
    {
        if (!VerifyVariableData(array[i], objectOffset + i * codegenTypeSize, totalDataSize, expectedDataOffset))
        {
            return false;
        }
    }

    return true;
}
}
