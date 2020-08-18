//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: StringTypes.h
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
// NAME: StringPtr
//
// PURPOSE:
//
// NOTES:
//
struct StringPtr
{
public:
    const char* Data;
    uint64_t Length;

    StringPtr& operator=(const StringPtr& other)
    {
        Data = other.Data;
        Length = other.Length;

        return *this;
    }

    StringPtr& operator=(const char* string)
    {
        Data = string;
        Length = string != nullptr ? strlen(string) : 0;

        return *this;
    }
};

//----------------------------------------------------------------------------
// NAME: WideStringPtr
//
// PURPOSE:
//
// NOTES:
//
struct WideStringPtr
{
public:
    const wchar_t* Data;
    uint64_t Length;

    WideStringPtr& operator=(const WideStringPtr& other)
    {
        Data = other.Data;
        Length = other.Length;

        return *this;
    }

    WideStringPtr& operator=(const wchar_t* string)
    {
        Data = string;
        Length = string != nullptr ? wcslen(string) : 0;

        return *this;
    }
};
}
}
