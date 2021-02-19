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

#include <fcntl.h>

namespace
{
TEST(FileWatchEventTests, VerifyNotification)
{
    MlosCore::FileWatchEvent fileWatchEvent;

    const char* folderPath = "/var/tmp/mlos_test/";
    const char* fileName = "file.notify";

    MlosCore::UniqueString eventName;
    MlosCore::NamedEvent event;

    HRESULT hr = event.CreateOrOpen(eventName.Str());
    EXPECT_EQ(hr, S_OK);

    hr = fileWatchEvent.Initialize(
        folderPath,
        fileName);
    EXPECT_EQ(hr, S_OK);

    std::future<bool> fileModifier = std::async(
        std::launch::async,
        [&fileWatchEvent, &event]
        {
            MlosCore::MlosPlatform::SleepMilliseconds(100);
            // 1. Open a file, that will trigger the notification.
            //
            const char* filePath = fileWatchEvent.WatchFilePath();
            int fd = open(filePath, O_RDWR);
            EXPECT_NE(INVALID_FD_VALUE, fd);
            close(fd);

            // 2. Delete a file
            //
            int result = remove(filePath);
            EXPECT_EQ(0, result);

            // Signal main thread so it will wait for the notification.
            //
            HRESULT hr = event.Signal();
            EXPECT_EQ(hr, S_OK);

            MlosCore::MlosPlatform::SleepMilliseconds(100);
            open(filePath, O_RDWR);
            EXPECT_NE(INVALID_FD_VALUE, fd);
            close(fd);

            return true;
        });

    // 1. Regular file notification wait.
    //
    hr = fileWatchEvent.Wait();
    EXPECT_EQ(hr, S_OK);

    // 2. Handle the case when the file is deleted.
    //
    hr = event.Wait();
    EXPECT_EQ(hr, S_OK);
    fileModifier.wait();

    event.Close(true);
}
}