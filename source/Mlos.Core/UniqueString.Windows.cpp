//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: UniqueString.Windows.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: UniqueString::Constructor.
//
// PURPOSE:
//  Constructor.
//
UniqueString::UniqueString(_In_reads_z_(MaxPrefixLength) const char* prefix)
{
    GUID guid;

    HRESULT hr = CoCreateGuid(&guid);
    MLOS_RETAIL_ASSERT(SUCCEEDED(hr));

    int32_t result = snprintf(
        m_text,
        sizeof(m_text),
        "%s_%08x-%04x-%04x-%02x%02x-%02x%02x%02x%02x%02x%02x",
        prefix,
        guid.Data1,
        guid.Data2,
        guid.Data3,
        guid.Data4[0],
        guid.Data4[1],
        guid.Data4[2],
        guid.Data4[3],
        guid.Data4[4],
        guid.Data4[5],
        guid.Data4[6],
        guid.Data4[7]);

    MLOS_RETAIL_ASSERT(result > 0);
}
}
}
