//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: FileWatchEvent.Linux.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

#include <sys/inotify.h>
#include <sys/stat.h>
#include <cerrno>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <unistd.h>

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: FileWatchEvent constructor
//
// PURPOSE:
//
// NOTES:
//
FileWatchEvent::FileWatchEvent()
 :  m_fdNotify(INVALID_FD_VALUE),
    m_directoryPath(nullptr),
    m_watchFilePath(nullptr)
{
}

//----------------------------------------------------------------------------
// NAME: FileWatchEvent move constructor
//
// PURPOSE:
//
// NOTES:
//
FileWatchEvent::FileWatchEvent(_Inout_ FileWatchEvent&& fileWatchEvent) noexcept
 :  m_fdNotify(std::exchange(fileWatchEvent.m_fdNotify, INVALID_FD_VALUE)),
    m_directoryPath(std::exchange(fileWatchEvent.m_directoryPath, nullptr)),
    m_watchFilePath(std::exchange(fileWatchEvent.m_watchFilePath, nullptr))
{
}

//----------------------------------------------------------------------------
// NAME: FileWatchEvent destructor
//
// PURPOSE:
//
// NOTES:
//
FileWatchEvent::~FileWatchEvent()
{
    Close();
}

//----------------------------------------------------------------------------
// NAME: FileWatchEvent::Close
//
// PURPOSE:
//
// NOTES:
//
void FileWatchEvent::Close()
{
    int fdNotify = std::exchange(m_fdNotify, INVALID_FD_VALUE);
    close(fdNotify);

    if (m_watchFilePath != nullptr)
    {
        remove(m_watchFilePath);
        free(m_watchFilePath);
        m_watchFilePath = nullptr;
    }

    if (m_directoryPath != nullptr)
    {
        rmdir(m_directoryPath);
        free(m_directoryPath);
        m_directoryPath = nullptr;
    }
}

//----------------------------------------------------------------------------
// NAME: FileWatchEvent::Abort
//
// PURPOSE:
//  Aborts the wait.
//
// NOTES:
//  Method is thread safe.
//
void FileWatchEvent::Abort()
{
    int fdNotify = std::exchange(m_fdNotify, INVALID_FD_VALUE);
    close(fdNotify);

    if (m_watchFilePath != nullptr)
    {
        remove(m_watchFilePath);
    }

    if (m_directoryPath != nullptr)
    {
        rmdir(m_directoryPath);
    }
}

//----------------------------------------------------------------------------
// NAME: FileWatchEvent::Initialize
//
// PURPOSE:
//
// NOTES:
//
_Must_inspect_result_
HRESULT FileWatchEvent::Initialize(
    _In_z_ const char* directoryPath,
    _In_z_ const char* openFileName)
{
    HRESULT hr = S_OK;

    m_directoryPath = strdup(directoryPath);
    if (m_directoryPath == nullptr)
    {
        hr = E_OUTOFMEMORY;
    }

    if (SUCCEEDED(hr))
    {
        if (asprintf(&m_watchFilePath, "%s/%s", directoryPath, openFileName) == -1)
        {
            hr = E_OUTOFMEMORY;
        }
    }

    if (SUCCEEDED(hr))
    {
        m_fdNotify = inotify_init();
    }

    if (m_fdNotify == INVALID_FD_VALUE)
    {
        hr = HRESULT_FROM_ERRNO(errno);
    }

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: FileWatchEvent::Wait
//
// PURPOSE:
//
// NOTES:
//
_Must_inspect_result_
HRESULT FileWatchEvent::Wait()
{
    HRESULT hr;

    if (m_fdNotify == INVALID_FD_VALUE)
    {
        return HRESULT_FROM_ERRNO(EBADF);
    }

    // Create a watch file.
    //
    hr = CreateWatchFile();
    if (FAILED(hr))
    {
        return hr;
    }

    // Create notification.
    //
    int32_t fdWatch = INVALID_FD_VALUE;

    constexpr int NotifyEventSize = sizeof(struct inotify_event);
    constexpr int NotifyEventBufferSize = 2 * (NotifyEventSize + NAME_MAX + 1);

    char eventsBuffer[NotifyEventBufferSize];

    bool waitForSocket = true;

    // Wait for the agent when it is ready to get the file descriptors.
    //
    while (waitForSocket)
    {
        if (fdWatch == INVALID_FD_VALUE)
        {
            // Create the file watch.
            //
            hr = CreateWatchFile();
            if (FAILED(hr))
            {
                break;
            }

            fdWatch = inotify_add_watch(
                m_fdNotify,
                m_watchFilePath,
                IN_OPEN | IN_DELETE_SELF);
        }

        if (fdWatch == INVALID_FD_VALUE)
        {
            hr = HRESULT_FROM_ERRNO(errno);
            break;
        }

        int32_t length = read(m_fdNotify, eventsBuffer, NotifyEventBufferSize);
        if (length < 0)
        {
            // Wait for the notification failed.
            //
            hr = HRESULT_FROM_ERRNO(errno);
            break;
        }

        if (m_fdNotify == INVALID_FD_VALUE)
        {
            // Wait has been aborted.
            //
            hr = HRESULT_FROM_ERRNO(EBADF);
            break;
        }

        int32_t i = 0;

        // actually read return the list of change events happens. Here, read the change event one by one and process it accordingly.
        while (waitForSocket && i < length)
        {
            struct inotify_event* pEvent = reinterpret_cast<struct inotify_event *>(&eventsBuffer[i]);

            if (pEvent->mask & IN_OPEN)
            {
                // The file was opened.
                //
                waitForSocket = false;
                break;
            }
            else if (pEvent->mask & IN_DELETE_SELF)
            {
                // The file has been deleted, remove the watch and create a new one.
                //
                inotify_rm_watch(m_fdNotify, fdWatch);

                fdWatch = INVALID_FD_VALUE;
            }

            i += NotifyEventSize + pEvent->len;
        }
    }

    // Close inotify.
    //
    if (SUCCEEDED(hr))
    {
        inotify_rm_watch(m_fdNotify, fdWatch);
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: FileWatchEvent::CreateWatchFile
//
// PURPOSE:
//
// NOTES:
//
_Must_inspect_result_
HRESULT FileWatchEvent::CreateWatchFile()
{
    // Try to create a folder where the file is located, ignore the errors.
    //
    mkdir(m_directoryPath, S_IRWXU | S_IRWXG | S_IRGRP | S_IWGRP);

    // Create the empty file.
    //
    int32_t fdWatchFile = creat(m_watchFilePath, S_IRWXU | S_IRWXG | S_IRGRP | S_IWGRP);
    if (fdWatchFile == INVALID_FD_VALUE)
    {
        // Return the failure.
        //
        return HRESULT_FROM_ERRNO(errno);
    }

    // Close the descriptors before opening a watch to avoid close notification.
    //
    close(fdWatchFile);

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: FileWatchEvent::WatchFilePath
//
// PURPOSE:
//  Returns a path to a file which is being watched.
//
// NOTES:
//
const char* FileWatchEvent::WatchFilePath() const
{
    return m_watchFilePath;
}
}
}