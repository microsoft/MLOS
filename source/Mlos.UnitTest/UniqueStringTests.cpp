//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: UniqueStringTests.cpp
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
TEST(UniqueStringTests, VerifyUniqueString)
{
    MlosCore::UniqueString str1("");
    MlosCore::UniqueString str2("");

    // Expect length of printed Guid.
    //
    EXPECT_EQ(36, strlen(str1.Str()));
    EXPECT_EQ(36, strlen(str2.Str()));

    // Strings should be different.
    //
    EXPECT_NE(0, strcmp(str1.Str(), str2.Str()));
}

TEST(UniqueStringTests, VerifyUniqueStringPrefix)
{
    MlosCore::UniqueString str("A_B_C_D_");

    // Expect length of printed Guid + length of "A_B_C_D_" string.
    //
    EXPECT_EQ(36 + 8, strlen(str.Str()));

    // Strings should be different.
    //
    EXPECT_NE(0, strcmp("A_B_C_D_", str.Str()));
}
}


