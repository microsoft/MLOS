//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedChannelTests.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "stdafx.h"

template<int T>
class TestFlatBuffer : public BytePtr
{
public:
    TestFlatBuffer()
      : BytePtr(nullptr)
    {
        Pointer = &(*array.begin());
    }

private:
    std::array<byte, T> array = { 0 };
};

namespace
{
#ifndef DEBUG
// Verify buffer size.
// SharedChannel asserts if the provided size is not optimal.
// In the retail build, channel size shrinks the to largest usable size.
// Test for retail build only to avoid assert.
//
TEST(SharedChannel, VerifyBufferSize)
{
    // To correctly handle position counter overflow, the buffer size must fulfill the following condition:
    // (uint32_t::max + 1 ).% Buffer.Size = 0
    //
    {
        TestFlatBuffer<21> buffer;
        ChannelSynchronization sync = {};
        TestSharedChannel sharedChannel(sync, buffer, 21);

        EXPECT_EQ(sharedChannel.Size, 16);
    }
    {
        TestFlatBuffer<4095> buffer;
        ChannelSynchronization sync = {};
        TestSharedChannel sharedChannel(sync, buffer, 4095);

        EXPECT_EQ(sharedChannel.Size, 2048);
    }
}
#endif // !DEBUG

// Verify channel restart.
//
TEST(SharedChannel, VerifyChannelRestart)
{
    auto globalDispatchTable = GlobalDispatchTable();

    // Define objects (used as a messages).
    //
    Mlos::UnitTest::Point point = { 13, 17 };

    // Create the test channel.
    //
    TestFlatBuffer<128> buffer;
    ChannelSynchronization sync = {};
    TestSharedChannel sharedChannel(sync, buffer, 128);

    // Write the first message.
    //
    sharedChannel.SendMessage(point);

    // Read the first message, do not advance the free region.
    //
    sharedChannel.WaitAndDispatchFrame(globalDispatchTable.data(), globalDispatchTable.size());

    // Write second message.
    //
    sharedChannel.SendMessage(point);

    // Write the third message as partially written.
    //
    uint32_t writePosition = sync.WritePosition;
    sharedChannel.SendMessage(point);
    *reinterpret_cast<uint32_t*>(buffer.Pointer + writePosition) |= 1;

    // Write the fourth message.
    //
    sharedChannel.SendMessage(point);

    // Simulate start processing of the written frames.
    //
    sync.ReadPosition.store(sync.WritePosition.load());

    // Simulate channel restart.
    //
    sharedChannel.InitializeChannel();

    // First frame is fully processed.
    // Read position points to first unprocessed frame.
    //
    EXPECT_EQ(sharedChannel.Sync.FreePosition, 24);
    EXPECT_EQ(sharedChannel.Sync.ReadPosition, 24);

    // Next message was fully written, expect it to be processed.
    //
    bool isProcessed = false;
    ObjectDeserializationCallback::Mlos::UnitTest::Point_Callback = [&isProcessed](Proxy::Mlos::UnitTest::Point&& recvPoint)
        {
            UNUSED(recvPoint);
            isProcessed = true;
        };

    sharedChannel.WaitAndDispatchFrame(globalDispatchTable.data(), globalDispatchTable.size());
    EXPECT_EQ(isProcessed, true);

    // Next message was partially written, so it will not be processed.
    //
    isProcessed = false;
    sharedChannel.WaitAndDispatchFrame(globalDispatchTable.data(), globalDispatchTable.size());
    EXPECT_EQ(isProcessed, false);

    // Last message was fully written, expect it to be processed.
    //
    sharedChannel.WaitAndDispatchFrame(globalDispatchTable.data(), globalDispatchTable.size());
    EXPECT_EQ(isProcessed, true);

    // We should process all the written frames.
    //
    EXPECT_EQ(sync.ReadPosition.load(), sync.WritePosition.load());

    // Cleanup process frames.
    //
    sharedChannel.AdvanceFreePosition();
    EXPECT_EQ(sync.FreePosition.load(), sync.WritePosition.load());
}

// Verify synchronization positions.
// Send and receive objects and each step will verify if shared channel sync positions are correct.
//
TEST(SharedChannel, VerifySyncPositions)
{
    auto globalDispatchTable = GlobalDispatchTable();

    // Create small buffer.
    //
    TestFlatBuffer<128> buffer;
    ChannelSynchronization sync = {};
    TestSharedChannel sharedChannel(sync, buffer, 128);

    Mlos::UnitTest::Point point = { 13, 17 };
    Mlos::UnitTest::Point3D point3d = { 39, 41, 43 };

    // Setup empty callbacks.
    //
    ObjectDeserializationCallback::Mlos::UnitTest::Point_Callback = [](Proxy::Mlos::UnitTest::Point&&) {};
    ObjectDeserializationCallback::Mlos::UnitTest::Point3D_Callback = [](Proxy::Mlos::UnitTest::Point3D&&) {};

    // Send first message.
    //
    sharedChannel.SendMessage(point);
    EXPECT_EQ(sharedChannel.Sync.WritePosition, 24);

    // Send second message.
    //
    sharedChannel.SendMessage(point3d);
    EXPECT_EQ(sharedChannel.Sync.WritePosition, 64);

    // Send third message.
    //
    sharedChannel.SendMessage(point3d);
    EXPECT_EQ(sharedChannel.Sync.WritePosition, 104);

    // Reader made no progress.
    //
    EXPECT_EQ(sharedChannel.Sync.FreePosition, 0);
    EXPECT_EQ(sharedChannel.Sync.ReadPosition, 0);

    // Read one message, there is no space left in the buffer to write a new message.
    //
    sharedChannel.WaitAndDispatchFrame(globalDispatchTable.data(), globalDispatchTable.size());
    EXPECT_EQ(sharedChannel.Sync.FreePosition, 0);
    EXPECT_EQ(sharedChannel.Sync.ReadPosition, 24);
    EXPECT_EQ(sharedChannel.Sync.WritePosition, 104);

    // Send fourth message. This one will force the writer to update FreePosition.
    //
    sharedChannel.SendMessage(point);
    EXPECT_EQ(sharedChannel.Sync.FreePosition, 24);
    EXPECT_EQ(sharedChannel.Sync.ReadPosition, 24);
    EXPECT_EQ(sharedChannel.Sync.WritePosition, 128);
}

// Verify if structures containing fixed size arrays can be serialized and read by the receiver.
//
TEST(SharedChannel, VerifySendingReceivingArrayStruct)
{
    auto globalDispatchTable = GlobalDispatchTable();

    // Create small buffer.
    //
    TestFlatBuffer<128> buffer;
    ChannelSynchronization sync = {};
    TestSharedChannel sharedChannel(sync, buffer, 128);

    Mlos::UnitTest::Line line;
    line.Points[0] = { 3, 5 };
    line.Points[1] = { 7, 9 };
    line.Height = { 1.3f, 3.9f };
    line.Colors = { Mlos::UnitTest::Colors::Red, Mlos::UnitTest::Colors::Blue };

    // Setup empty callbacks.
    //
    ObjectDeserializationCallback::Mlos::UnitTest::Line_Callback = [line](Proxy::Mlos::UnitTest::Line&& recvLine)
        {
            EXPECT_EQ(recvLine.Points()[0].X(), 3.0);
            EXPECT_EQ(recvLine.Points()[0].Y(), 5);
            EXPECT_EQ(recvLine.Points()[1].X(), 7);
            EXPECT_EQ(recvLine.Points()[1].Y(), 9);
            EXPECT_EQ(recvLine.Height()[0], 1.3f);
            EXPECT_EQ(recvLine.Height()[1], 3.9f);
            EXPECT_EQ(recvLine.Colors()[0], Mlos::UnitTest::Colors::Red);
            EXPECT_EQ(recvLine.Colors()[1], Mlos::UnitTest::Colors::Blue);

            EXPECT_EQ(recvLine.Points()[0].X(), line.Points[0].X);
            EXPECT_EQ(recvLine.Points()[0].Y(), line.Points[0].Y);
            EXPECT_EQ(recvLine.Points()[1].X(), line.Points[1].X);
            EXPECT_EQ(recvLine.Points()[1].Y(), line.Points[1].Y);
            EXPECT_EQ(recvLine.Height()[0], line.Height[0]);
            EXPECT_EQ(recvLine.Colors()[0], line.Colors[0]);
            EXPECT_EQ(recvLine.Colors()[1], line.Colors[1]);
        };

    // Send object.
    //
    sharedChannel.SendMessage(line);
    EXPECT_EQ(sharedChannel.Sync.WritePosition, 64);

    // Receive and verify object.
    //
    sharedChannel.WaitAndDispatchFrame(globalDispatchTable.data(), globalDispatchTable.size());
}

// Stress test.
//
TEST(SharedChannel, StressSendReceive)
{
    auto globalDispatchTable = GlobalDispatchTable();

    Mlos::UnitTest::Point point = { 13, 17 };

    Mlos::UnitTest::Point3D point3d = { 39, 41, 43 };

    // Setup receiver handler to verify.
    // Handler will be called from the receiver thread.
    //
    ObjectDeserializationCallback::Mlos::UnitTest::Point_Callback = [point](Proxy::Mlos::UnitTest::Point&& recvPoint)
        {
            float x = recvPoint.X();
            float y = recvPoint.Y();

            EXPECT_EQ(point.X, x);
            EXPECT_EQ(point.Y, y);
        };

    // Setup receiver handler to verify.
    // Handler will be called from the receiver thread.
    //
    ObjectDeserializationCallback::Mlos::UnitTest::Point3D_Callback = [point3d](Proxy::Mlos::UnitTest::Point3D&& recvPoint)
        {
            double x = recvPoint.X();
            double y = recvPoint.Y();
            double z = recvPoint.Z();

            EXPECT_EQ(point3d.X, x);
            EXPECT_EQ(point3d.Y, y);
            EXPECT_EQ(point3d.Z, z);
        };

    TestFlatBuffer<4096> buffer;
    ChannelSynchronization sync = {};
    TestSharedChannel sharedChannel(sync, buffer, 4096);

    // Setup deserialize callbacks to verify received objects.
    //
    ObjectDeserializationCallback::Mlos::Core::TerminateReaderThreadRequestMessage_Callback =
        [&sharedChannel](Proxy::Mlos::Core::TerminateReaderThreadRequestMessage&&)
        {
            // Stop the read thread
            //
            sharedChannel.Sync.TerminateChannel.store(true);
        };

    // Create a receiver thread and pass the buffer.
    //
    std::future<bool> resultFromReader1 = std::async(
        std::launch::async,
        [&sharedChannel, &globalDispatchTable]
        {
            sharedChannel.ProcessMessages(globalDispatchTable.data(), globalDispatchTable.size());

            return true;
        });

    std::future<bool> resultFromReader2 = std::async(
        std::launch::async,
        [&sharedChannel, &globalDispatchTable]
        {
            sharedChannel.ProcessMessages(globalDispatchTable.data(), globalDispatchTable.size());

            return true;
        });

    // Use uint32_t (not const) to allow clang capture the variable.
    //
    uint32_t numberOfIterations = 10 * 1000 * 1000;

    std::future<bool> resultFromWriter1 = std::async(
        std::launch::async,
        [&sharedChannel, &point, &point3d, &numberOfIterations]
        {
            for (uint32_t i = 0; i < numberOfIterations; i++)
            {
                if (i % (1000 * 100) == 0)
                {
                    printf("%i\n", i);
                }

                sharedChannel.SendMessage(point3d);
                sharedChannel.SendMessage(point3d);
                sharedChannel.SendMessage(point3d);
                sharedChannel.SendMessage(point);
                sharedChannel.SendMessage(point);
            }

            return true;
        });

    std::future<bool> resultFromWriter2 = std::async(
        std::launch::async,
        [&sharedChannel, &point, &point3d, &numberOfIterations]
        {
            for (uint32_t i = 0; i < numberOfIterations; i++)
            {
                if (i % (1000 * 1000) == 0)
                {
                    printf("%i\n", i);
                }

                sharedChannel.SendMessage(point3d);
                sharedChannel.SendMessage(point3d);
                sharedChannel.SendMessage(point3d);
                sharedChannel.SendMessage(point);
                sharedChannel.SendMessage(point);
            }
            return true;
        });

    bool result =
        resultFromWriter1.get() &&
        resultFromWriter2.get();

    sharedChannel.SendMessage(Mlos::Core::TerminateReaderThreadRequestMessage());

    // Join threads.
    //
    result =
        resultFromReader1.get() &&
        resultFromReader2.get();
}
}
