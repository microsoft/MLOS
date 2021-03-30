//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: UniqueString.Linux.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"
#include <uuid/uuid.h>

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
    uuid_t guid;
    uuid_generate_random(guid);

    int prefixLength = strlen(prefix);
    MLOS_RETAIL_ASSERT(prefixLength < MaxPrefixLength);

    strcpy(m_text, prefix);

    uuid_unparse(guid, &m_text[prefixLength]);
}
}
}