//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MetadataTests.cpp
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
TEST(MetadataTests, VerifyProxyAccess)
{
    Mlos::UnitTest::CompositeStructure2 object;

    object.Title = L"Title_123";
    object.BaseComp.Name = L"Test_Name5678";
    object.BaseComp.Version = "1.0.0";

    auto length = ObjectSerialization::GetSerializedSize(object);

    std::vector<byte> byteBuffer;
    byteBuffer.resize(length);

    BytePtr buffer(&byteBuffer.front());
    ObjectSerialization::Serialize(buffer, object);

    Proxy::Mlos::UnitTest::CompositeStructure2 proxy(buffer, 0);

    EXPECT_EQ(proxy.Title(), object.Title);
    EXPECT_EQ(proxy.BaseComp().Name(), object.BaseComp.Name);
    EXPECT_EQ(proxy.BaseComp().Version(), object.BaseComp.Version);
}

TEST(MetadataTests, VerifyProxyAccessEnumArray)
{
    Mlos::UnitTest::Line object;
    object.Points = { Mlos::UnitTest::Point { 3, 4 }, Mlos::UnitTest::Point { 6, 7 } };
    object.Colors = { Mlos::UnitTest::Colors::Green, Mlos::UnitTest::Colors::Red };

    EXPECT_EQ(object.Colors[0], Mlos::UnitTest::Colors::Green);
    EXPECT_EQ(object.Colors[1], Mlos::UnitTest::Colors::Red);

    std::vector<byte> byteBuffer;
    byteBuffer.resize(ObjectSerialization::GetSerializedSize(object));

    BytePtr buffer(&byteBuffer.front());
    ObjectSerialization::Serialize(buffer, object);

    Proxy::Mlos::UnitTest::Line proxy(buffer, 0);

    // Verify proxy values.
    //
    EXPECT_EQ(proxy.Points()[0].X(), 3);
    EXPECT_EQ(proxy.Points()[0].Y(), 4);
    EXPECT_EQ(proxy.Points()[1].X(), 6);
    EXPECT_EQ(proxy.Points()[1].Y(), 7);

    EXPECT_EQ(proxy.Colors()[0], object.Colors[0]);
    EXPECT_EQ(proxy.Colors()[1], object.Colors[1]);
}

TEST(MetadataTests, VerifyProxyAccessStringArray)
{
    Mlos::UnitTest::WideStringViewArray object;

    object.Strings[0] = L"Test_Name9876";
    object.Strings[1] = L"Test_Name19876";
    object.Strings[2] = L"Test_Name1239876";
    object.Strings[3] = L"Test_Name45659876";
    object.Strings[4] = L"Test_Name901239876";

    std::vector<byte> byteBuffer;
    byteBuffer.resize(ObjectSerialization::GetSerializedSize(object));

    BytePtr buffer(&byteBuffer.front());
    ObjectSerialization::Serialize(buffer, object);

    Proxy::Mlos::UnitTest::WideStringViewArray proxy(buffer, 0);

    for (int i = 0; i < 5; i++)
    {
        EXPECT_EQ(proxy.Strings()[i], object.Strings[i]);
    }
}

// Verify struct alignment.
//
static_assert(offsetof(struct ::Mlos::UnitTest::TestAlignedTypeHigherAlignment, Id2) == 32, "Invalid offset");
static_assert(offsetof(struct ::Mlos::UnitTest::TestAlignedTypeHigherAlignment, Id3) == 36, "Invalid offset");
static_assert(offsetof(struct ::Mlos::UnitTest::TestAlignedTypeHigherAlignment, Id4) == 64, "Invalid offset");
static_assert(offsetof(struct ::Mlos::UnitTest::TestAlignedTypeMultipleAlignments, Id2) == 32, "Invalid offset");
static_assert(offsetof(struct ::Mlos::UnitTest::TestAlignedTypeMultipleAlignments, Id3) == 48, "Invalid offset");
static_assert(offsetof(struct ::Mlos::UnitTest::TestAlignedTypeMultipleAlignments, Id4) == 64, "Invalid offset");

TEST(MetadataTests, VerifyStructAligment)
{
    Mlos::UnitTest::TestAlignedType object = {};
    object.Configs[2].ComponentType = 'a';
    object.Configs[4].ComponentType = 'b';

    // Serialize to the buffer.
    //
    std::vector<byte> byteBuffer;
    byteBuffer.resize(ObjectSerialization::GetSerializedSize(object));

    const BytePtr buffer(&byteBuffer.front());
    ObjectSerialization::Serialize(buffer, object);

    // Create a proxy object.
    //
    Proxy::Mlos::UnitTest::TestAlignedType proxy(buffer, 0);
    EXPECT_EQ(proxy.Configs()[2].ComponentType(), object.Configs[2].ComponentType);
    EXPECT_EQ(proxy.Configs()[4].ComponentType(), object.Configs[4].ComponentType);
}

TEST(MetadataTests, VerifyStringPtrSerialization)
{
    {
        Mlos::UnitTest::StringsPair object = {};
        object.String1 = "Test_string1";
        object.String2 = "Test_string2";

        // Serialize to the buffer.
        //
        std::vector<byte> byteBuffer;
        byteBuffer.resize(ObjectSerialization::GetSerializedSize(object));

        const BytePtr buffer(&byteBuffer.front());
        ObjectSerialization::Serialize(buffer, object);

        // Create a proxy object.
        //
        Proxy::Mlos::UnitTest::StringsPair proxy(buffer, 0);
        EXPECT_EQ(proxy.String1(), object.String1);
        EXPECT_EQ(proxy.String2(), object.String2);
    }

    // First is nullptr.
    //
    {
        Mlos::UnitTest::StringsPair object = {};
        object.String1 = nullptr;
        object.String2 = "Test_string2";

        // Serialize to the buffer.
        //
        std::vector<byte> byteBuffer;
        byteBuffer.resize(ObjectSerialization::GetSerializedSize(object));

        const BytePtr buffer(&byteBuffer.front());
        ObjectSerialization::Serialize(buffer, object);

        // Create a proxy object.
        //
        Proxy::Mlos::UnitTest::StringsPair proxy(buffer, 0);
        EXPECT_EQ(proxy.String1(), object.String1);
        EXPECT_EQ(proxy.String2(), object.String2);
    }
}
}
