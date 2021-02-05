//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: BytePtr.h
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
// NAME: BytePtr
//
// PURPOSE:
//  BytePtr definition. Equivalent of C# IntPtr.
//  Keeps the C# and Cpp code uniform.
//
// NOTES:
//
class BytePtr
{
public:
    BytePtr(_In_opt_ const void* buffer)
      : Pointer(static_cast<byte*>(const_cast<void*>(buffer)))
    {}

public:
    byte* Pointer;

    // Gets a value that indicates whether the buffer is invalid.
    //
    inline bool IsInvalid() const
    {
        return Pointer == nullptr;
    }
};
}
}
