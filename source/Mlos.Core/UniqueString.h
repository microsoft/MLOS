//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: UniqueString.h
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
// NAME: UniqueString
//
// PURPOSE:
//  Class provides a unique string using guid.
//
// NOTES:
//
class UniqueString
{
    constexpr static int32_t MaxPrefixLength = 10;
    constexpr static const char* DefaultPrefix = "MLOS_";

public:
    UniqueString(_In_reads_z_(MaxPrefixLength) const char* prefix = DefaultPrefix);

    const char* Str() const
    {
        return m_text;
    }

private:
    char m_text[64];
};
}
}
