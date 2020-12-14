//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: AlignedVector.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: AlignedVector
//
// PURPOSE:
//  A fixed size container holding a given number of objects.
//
// NOTES:
//
template<class T, std::size_t N>
class AlignedVector
{
    // Properly aligned uninitialized storage for N objects of T type.
    //
    typename std::aligned_storage<sizeof(T), alignof(T)>::type data[N];
    std::size_t m_size = 0;

public:
    // Appends an object to the aligned storage.
    //
    template<typename... TArgs>
    _Must_inspect_result_
    bool EmplaceBack(_In_ TArgs&&... args)
    {
        if (m_size >= N)
        {
            assert(false);
            return false;
        }

        // Construct value in memory of aligned storage using placement operator new.
        //
        new(&data[m_size]) T(std::forward<TArgs>(args)...);
        ++m_size;

        return true;
    }

    // Gets a reference to the object in aligned storage at the given index.
    //
    T& operator[](std::size_t index) const
    {
        return *const_cast<T*>(reinterpret_cast<const T*>(&data[index]));
    }

    // Deletes all the objects from the aligned storage.
    //
    ~AlignedVector()
    {
        for (std::size_t index = 0; index < m_size; ++index)
        {
            reinterpret_cast<T*>(&data[index])->~T();
        }
    }
};
}
}
