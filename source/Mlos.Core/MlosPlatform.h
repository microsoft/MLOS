//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MlosPlatform.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

// Define RETAIL_ASSERT.
//
#define RETAIL_ASSERT(result) { if (!result) Mlos::Core::MlosPlatform::TerminateProcess(); }

namespace Mlos
{
namespace Core
{
namespace Internal
{
// External implementation.
//
extern void MlosPlatformTerminateProcess();
extern void MlosPlatformWait(uint32_t milliseconds);
}
//----------------------------------------------------------------------------
// NAME: MlosPlatform
//
// PURPOSE:
//
// NOTES:
//
class MlosPlatform
{
public:
    // Terminate the current process.
    //
    static inline void TerminateProcess()
    {
        Mlos::Core::Internal::MlosPlatformTerminateProcess();
    }

    // Suspends the execution of the current thread for millisecond intervals.
    //
    static inline void SleepMilliseconds(uint32_t milliseconds)
    {
        Mlos::Core::Internal::MlosPlatformWait(milliseconds);
    }
};
}
}
