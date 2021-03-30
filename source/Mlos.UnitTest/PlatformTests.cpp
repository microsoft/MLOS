//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: PlatformTests.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "stdafx.h"

namespace
{
void* IncreaseNumber(void* p)
{
    (*static_cast<int32_t*>(p))++;
    return nullptr;
}

TEST(PlatformTests, CreateThread)
{
    int number = 0;

    ThreadHandle handle1;
    ThreadHandle handle2;

    HRESULT hr = MlosCore::MlosPlatform::CreateThread(IncreaseNumber, &number, handle1);
    EXPECT_EQ(hr, S_OK);

    hr = MlosCore::MlosPlatform::CreateThread(IncreaseNumber, &number, handle2);
    EXPECT_EQ(hr, S_OK);

    hr = MlosCore::MlosPlatform::JoinThread(handle1);
    EXPECT_EQ(hr, S_OK);

    hr = MlosCore::MlosPlatform::JoinThread(handle2);
    EXPECT_EQ(hr, S_OK);

    EXPECT_EQ(number, 2);
}
}
