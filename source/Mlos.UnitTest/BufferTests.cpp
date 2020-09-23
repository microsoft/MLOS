//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: BufferTests.cpp
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

namespace
{
// Verify shared memory.
//
TEST(BufferChannel, CreateMemory)
{
    // Create InterProcessMlosContext.
    //
    InterProcessMlosContextInitializer mlosContextInitializer;
    HRESULT hr = mlosContextInitializer.Initialize();
    EXPECT_EQ(hr, S_OK);

    InterProcessMlosContext mlosContext(std::move(mlosContextInitializer));

    // Register Mlos.UnitTest Settings assembly.
    //
    hr = mlosContext.RegisterSettingsAssembly(
        "Mlos.UnitTest.SettingsRegistry.dll",
        Mlos::UnitTest::ObjectDeserializationHandler::DispatchTableBaseIndex());
    EXPECT_EQ(hr, S_OK);

    // Create shared component configuration.
    // Initialize config with default values.
    //
    ComponentConfig<ChannelReaderStats> localComponentConfig(mlosContext);
    localComponentConfig.SpinCount = 1;
    mlosContext.RegisterComponentConfig(localComponentConfig);

    // Create a feedback channel receiver thread.
    //
    ISharedChannel& feedbackChannel = mlosContext.FeedbackChannel();

    auto globalDispatchTable = GlobalDispatchTable();

    std::future<bool> resultFromReader1 = std::async(
        std::launch::async,
        [&feedbackChannel, &globalDispatchTable]
        {
            feedbackChannel.ProcessMessages(globalDispatchTable.data(), globalDispatchTable.size());

            return true;
        });

    // Create Mlos Smart
    //
    ChannelReaderStats::ProxyObjectType configProxy = localComponentConfig.Proxy();
    EXPECT_EQ(configProxy.SpinCount(), localComponentConfig.SpinCount);

    // Create monitor thread to timeout the test if there is no progress.
    //
    std::future<bool> testTimeout = std::async(
        std::launch::async,
        [&mlosContext, &configProxy]
        {
            std::this_thread::sleep_for(std::chrono::seconds(10));

            if (configProxy.SpinCount() == 1)
            {
                // There is no progress, terminate thread.
                //
                mlosContext.FeedbackChannel().Sync.TerminateChannel = true;
                mlosContext.TerminateControlChannel();

                return true;
            }
            else
            {
                return false;
            }
        });

    while (mlosContext.IsControlChannelActive())
    {
        // Run python script.
        //
        Mlos::UnitTest::UpdateConfigTestMessage updateConfigTestMsg = { 0 };
        mlosContext.SendControlMessage(updateConfigTestMsg);

        localComponentConfig.Update();

        uint64_t spinCount = configProxy.SpinCount();
        if (spinCount > 1000 * 10)
        {
            break;
        }

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

    // Finally, verify the shared and local config have the same value.
    // SpinCount in Proxy config could be higher if the Mlos.Agent processed a message between Update call and comparison.
    //
    localComponentConfig.Update();
    EXPECT_LE(localComponentConfig.SpinCount, configProxy.SpinCount());

    // First terminate feedback channel.
    // Wait untill there are no active readers on the channel.
    //
    mlosContext.TerminateFeedbackChannel();

    // Wait for the reader shutdown.
    //
    resultFromReader1.wait();
    EXPECT_EQ(resultFromReader1.get(), true);

    // Verify the test did not timeout.
    //
    EXPECT_EQ(testTimeout.get(), false);

    // Finally, terminate the agent.
    //
    mlosContext.TerminateControlChannel();
}
}
