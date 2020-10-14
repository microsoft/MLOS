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

    StringPtr()
      : Data(nullptr),
        Length(0)
    {
    }

    StringPtr(const StringPtr& other)
      : Data(other.Data),
        Length(other.Length)
    {
    }

    StringPtr(const char* data, uint64_t length)
      : Data(data),
        Length(length)
    {
    }

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
// NAME: StringPtr::operator==
//
// PURPOSE:
//  Compares two instances of StringPtr.
//
// NOTES:
//
inline bool operator==(const StringPtr& lhs, const StringPtr& rhs)
{
    return lhs.Length == rhs.Length && (lhs.Length == 0 || (strncmp(lhs.Data, rhs.Data, lhs.Length) == 0));
}

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

    WideStringPtr()
      : Data(nullptr),
        Length(0)
    {
    }

    WideStringPtr(const WideStringPtr& other)
      : Data(other.Data),
        Length(other.Length)
    {
    }

    WideStringPtr(const wchar_t* data, uint64_t length)
      : Data(data),
        Length(length)
    {
    }

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

//----------------------------------------------------------------------------
// NAME: WideStringPtr::operator==
//
// PURPOSE:
//  Compares two instances of WideStringPtr.
//
// NOTES:
//
inline bool operator==(const WideStringPtr& lhs, const WideStringPtr& rhs)
{
    return lhs.Length == rhs.Length && (lhs.Length == 0 || (wcsncmp(lhs.Data, rhs.Data, lhs.Length) == 0));
}
}
}
