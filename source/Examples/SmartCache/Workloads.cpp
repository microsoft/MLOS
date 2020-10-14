//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: Workloads.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "stdafx.h"
#include "SmartCacheImpl.h"
#include "Workloads.h"

void CyclicalWorkload(int32_t sequenceNumber, SmartCacheImpl<int32_t, int32_t>& smartCache)
{
    for (int32_t i = 1; i < sequenceNumber; i++)
    {
        int32_t* element = smartCache.Get(i);
        if (element == nullptr)
        {
            smartCache.Push(i, i);
        }
    }
}
