//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedChannelMicrobenchmark.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "stdafx.h"

//----------------------------------------------------------------------------
// Smart configurations.
//
StaticSingleton<ComponentConfig<SharedChannelConfig>> g_SharedChannelConfig;
StaticSingleton<ComponentConfig<MicrobenchmarkConfig>> g_MicrobenchmarkConfig;

//----------------------------------------------------------------------------
// NAME: RegisterSmartConfigs
//
// PURPOSE:
//  Registers all the smart spinlock configurations.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
HRESULT RegisterSmartConfigs(MlosContext& mlosContext)
{
    // SharedChannel config.
    //
    {
        ComponentConfig<SharedChannelConfig> sharedChannelConfig(mlosContext);

        sharedChannelConfig.BufferSize = 1024;
        sharedChannelConfig.ReaderCount = 1;

        HRESULT hr = mlosContext.RegisterComponentConfig(sharedChannelConfig);
        if (FAILED(hr))
        {
            return hr;
        }

        g_SharedChannelConfig.Initialize(std::move(sharedChannelConfig));
    }

    // Microbenchmark config.
    //
    {
        ComponentConfig<MicrobenchmarkConfig> microbenchmarkConfig(mlosContext);

        microbenchmarkConfig.WriterCount = 1;
        microbenchmarkConfig.DurationInSec = 10;

        HRESULT hr = mlosContext.RegisterComponentConfig(microbenchmarkConfig);
        if (FAILED(hr))
        {
            return hr;
        }

        g_MicrobenchmarkConfig.Initialize(std::move(microbenchmarkConfig));
    }

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: RunSharedChannelBenchmark
//
// PURPOSE:
//  Run the shared channel benchmark.
//
// RETURNS:
//  Toal number of messages send durning the benchmark run.
//
// NOTES:
//
uint64_t RunSharedChannelBenchmark(
    const SharedChannelConfig& sharedChannelConfig,
    const MicrobenchmarkConfig& microbenchmarkConfig)
{
    Mlos::UnitTest::Point point = { 9, 11 };
    Mlos::UnitTest::Point3D point3d = { 13, 17, 19 };

    // Setup receiver handler to verify.
    // Handler will be called from the receiver thread.
    //
    ObjectDeserializationCallback::Mlos::UnitTest::Point_Callback = [point](Proxy::Mlos::UnitTest::Point&& recvPoint)
        {
            float x = recvPoint.X();
            float y = recvPoint.Y();

            RTL_ASSERT(point.X == x);
            RTL_ASSERT(point.Y == y);
        };

    // Setup receiver handler to verify.
    // Handler will be called from the receiver thread.
    //
    ObjectDeserializationCallback::Mlos::UnitTest::Point3D_Callback = [point3d](Proxy::Mlos::UnitTest::Point3D&& recvPoint)
        {
            double x = recvPoint.X();
            double y = recvPoint.Y();
            double z = recvPoint.Z();

            RTL_ASSERT(point3d.X == x);
            RTL_ASSERT(point3d.Y == y);
            RTL_ASSERT(point3d.Z == z);
        };

    std::vector<byte> vectorBuffer;
    vectorBuffer.resize(sharedChannelConfig.BufferSize);

    BytePtr buffer(&vectorBuffer.front());
    ChannelSynchronization sync = {};
    TestSharedChannel sharedChannel(sync, buffer, sharedChannelConfig.BufferSize);

    // Setup deserialize callbacks to verify received objects.
    //
    ObjectDeserializationCallback::Mlos::Core::TerminateReaderThreadRequestMessage_Callback =
        [&sharedChannel](Proxy::Mlos::Core::TerminateReaderThreadRequestMessage&&)
        {
            // Stop the read thread
            //
            sharedChannel.Sync.TerminateChannel.store(true);
        };

    // Setup writers.
    //
    int32_t readerCount = sharedChannelConfig.ReaderCount;
    std::vector<std::future<bool>> readers;
    readers.reserve(readerCount);

    for (int i = 0; i < readerCount; i++)
    {
        // Create a receiver thread and pass the buffer.
        //
        readers.push_back(
            std::async(
                std::launch::async,
                [&sharedChannel]
        {
            auto globalDispatchTable = GlobalDispatchTable();

            sharedChannel.ProcessMessages(globalDispatchTable.data(), globalDispatchTable.size());

            return true;
        }));
    }

    // Setup writers.
    //
    std::vector<std::future<uint32_t>> writers;
    writers.reserve(microbenchmarkConfig.WriterCount);

    for (int i = 0; i < microbenchmarkConfig.WriterCount; i++)
    {
        writers.push_back(
            std::async(
                std::launch::async,
                [&sharedChannel, &point, &point3d]
        {
            uint32_t i = 0;

            while (!sharedChannel.Sync.TerminateChannel.load(std::memory_order_relaxed))
            {
                sharedChannel.SendMessage(point3d);
                sharedChannel.SendMessage(point3d);
                sharedChannel.SendMessage(point3d);
                sharedChannel.SendMessage(point);
                sharedChannel.SendMessage(point);
                i++;
            }

            return i;
        }));
    }

    std::chrono::seconds timespan(microbenchmarkConfig.DurationInSec);
    std::this_thread::sleep_for(timespan);

    // Stop the writers.
    //
    sharedChannel.Sync.TerminateChannel.store(true, std::memory_order_release);

    // Wait for the writers to join.
    //
    uint64_t writeMessageCount = 0;
    for (std::future<uint32_t>& waiter : writers)
    {
        writeMessageCount += waiter.get();
    }

    // Now stop the readers.
    //
    sharedChannel.SendMessage(Mlos::Core::TerminateReaderThreadRequestMessage());

    // Join threads.
    //
    for (std::future<bool>& reader : readers)
    {
        reader.get();
    }

    return writeMessageCount;
}
