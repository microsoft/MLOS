//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MessageVerificationTests.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "stdafx.h"
#include <chrono>
#include <thread>

using namespace Mlos::Core;

// Include codegen files.
//
#include "GlobalDispatchTable.h"

namespace
{
// Check the message variable data verification method.
//
TEST(MessageVerification, VerifyVariableDataMessages)
{
    // Create InternalProcessMlosContext.
    //
    InternalMlosContextInitializer mlosContextInitializer;
    HRESULT hr = mlosContextInitializer.Initialize();
    EXPECT_EQ(hr, S_OK);

    InternalMlosContext mlosContext(std::move(mlosContextInitializer));

    // Create a feedback channel receiver thread.
    //
    ISharedChannel& controlChannel = mlosContext.ControlChannel();

    auto globalDispatchTable = GlobalDispatchTable();

    std::future<bool> resultFromReader = std::async(
        std::launch::async,
        [&controlChannel, &globalDispatchTable]
        {
            controlChannel.ProcessMessages(globalDispatchTable.data(), globalDispatchTable.size());

            return true;
        });

    for (int i = 0; i < 1000; i++)
    {
        {
            Mlos::UnitTest::WideStringViewArray object;

            object.Strings[0] = L"Test_Name9876";
            object.Strings[1] = L"Test_Name19876";
            object.Strings[2] = L"Test_Name1239876";
            object.Strings[3] = L"Test_Name45659876";
            object.Strings[4] = L"Test_Name901239876";
            mlosContext.SendControlMessage(object);
        }

        {
            Mlos::UnitTest::Line object;
            object.Points = { Mlos::UnitTest::Point { 3, 4 }, Mlos::UnitTest::Point { 6, 7 } };
            object.Colors = { Mlos::UnitTest::Colors::Green, Mlos::UnitTest::Colors::Red };
            mlosContext.SendControlMessage(object);
        }
    }

    // First terminate feedback channel.
    // Wait until there are no active readers on the channel.
    //
    mlosContext.TerminateControlChannel();

    // Wait for the reader shutdown.
    //
    resultFromReader.wait();
    EXPECT_EQ(resultFromReader.get(), true);
}

// Detect invalid message.
//
TEST(MessageVerification, DetectInvalidDataMessages)
{
    // Create InternalProcessMlosContext.
    //
    InternalMlosContextInitializer mlosContextInitializer;
    HRESULT hr = mlosContextInitializer.Initialize();
    EXPECT_EQ(hr, S_OK);

    InternalMlosContext mlosContext(std::move(mlosContextInitializer));

    int32_t frameLength;
    {
        // Create a message then invalidate internal offsets.
        //
        Mlos::UnitTest::StringViewElement object;

        object.String = "Test_Name9876";
        mlosContext.SendControlMessage(object);

        frameLength = static_cast<int32_t>(sizeof(FrameHeader) + ObjectSerialization::GetSerializedSize(object));
        frameLength = align<sizeof(int32_t)>(frameLength);
    }

    ISharedChannel& controlChannel = mlosContext.ControlChannel();
    int32_t offset = controlChannel.Sync.WritePosition;
    offset = (offset - frameLength + controlChannel.Size) % controlChannel.Size;

    byte* ptr = reinterpret_cast<TestSharedChannel&>(controlChannel).Buffer.Pointer;
    ptr += sizeof(FrameHeader) + offsetof(struct ::Mlos::UnitTest::StringViewElement, String);
    *ptr += 1;

    auto globalDispatchTable = GlobalDispatchTable();

    // Read the message.
    //
    std::future<bool> resultFromReader = std::async(
        std::launch::async,
        [&controlChannel, &globalDispatchTable]
        {
            controlChannel.ProcessMessages(globalDispatchTable.data(), globalDispatchTable.size());

            return true;
        });

    // First terminate feedback channel.
    // Wait until there are no active readers on the channel.
    //
    // mlosContext.TerminateControlChannel();

    // Wait for the reader shutdown.
    //
    resultFromReader.wait();
    try
    {
        bool result = resultFromReader.get();

        // Fail if we will not get the exception.
        //
        EXPECT_EQ(result, false);
    }
    catch (const std::exception&)
    {
        // We expect failure.
        //
    }
}
}
