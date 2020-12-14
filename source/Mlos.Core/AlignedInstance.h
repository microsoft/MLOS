//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: AlignedInstance.h
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
// NAME: AlignedInstance
//
// PURPOSE:
//  A container holding a single instance of the object.
//
// NOTES:
//
template<class T>
class AlignedInstance
{
    // Aligned uninitialized storage for T.
    //
    typename std::aligned_storage<sizeof(T), alignof(T)>::type data;

public:
    // Creates an object in aligned storage.
    //
    template<typename... TArg>
    void Initialize(_In_ TArg&&... args)
    {
        // Construct an object in the memory of aligned storage using placement operator new.
        //
        new(&data) T(std::forward<TArg>(args)...);
    }

    // Access an object in aligned storage.
    //
    operator T&()
    {
        return *reinterpret_cast<T*>(&data);
    }

    // Deletes the object from the aligned storage.
    //
    ~AlignedInstance()
    {
        reinterpret_cast<T*>(&data)->~T();
    }
};
}
}
