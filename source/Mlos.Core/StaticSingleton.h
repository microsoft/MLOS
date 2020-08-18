//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: StaticSingleton.h
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
template<class T>
class StaticSingleton
{
    // Properly aligned uninitialized storage for T.
    //
    typename std::aligned_storage<sizeof(T), alignof(T)>::type data;

public:
    // Create an object in aligned storage.
    //
    template<typename... Args>
    void Initialize(T&& instance)
    {
        // Construct value in memory of aligned storage using inplace operator new.
        //
        new(&data) T(std::forward<T>(instance));
    }

    // Access an object in aligned storage.
    //
    operator T&()
    {
        return *reinterpret_cast<T*>(&data);
    }

    // Delete objects from aligned storage.
    //
    ~StaticSingleton()
    {
        reinterpret_cast<T*>(&data)->~T();
    }
};
}
}
