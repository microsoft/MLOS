//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: StaticVector.h
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
template<class T, std::size_t N>
class StaticVector
{
    // Properly aligned uninitialized storage for N T's.
    //
    typename std::aligned_storage<sizeof(T), alignof(T)>::type data[N];
    std::size_t m_size = 0;

public:
    // Create an object in aligned storage.
    //
    template<typename... Args>
    _Check_return_
    bool EmplaceBack(Args&&... args)
    {
        if (m_size >= N)
        {
            assert(false);
            return false;
        }

        // Construct value in memory of aligned storage using inplace operator new.
        //
        new(&data[m_size]) T(std::forward<Args>(args)...);
        ++m_size;

        return true;
    }

    // Access an object in aligned storage.
    //
    T& operator[](std::size_t pos) const
    {
        return *const_cast<T*>(reinterpret_cast<const T*>(&data[pos]));
    }

    // Delete objects from aligned storage.
    //
    ~StaticVector()
    {
        for (std::size_t pos = 0; pos < m_size; ++pos)
        {
            reinterpret_cast<T*>(&data[pos])->~T();
        }
    }
};
}
}
