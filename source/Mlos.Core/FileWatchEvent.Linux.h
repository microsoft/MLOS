//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: FileWatchEvent.Linux.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: FileWatchEvent
//
// PURPOSE:
//  inotify based event.
//
// NOTES:
//
class FileWatchEvent
{
public:
    FileWatchEvent();

    FileWatchEvent(_In_ FileWatchEvent&& fileWatchEvent) noexcept;

    FileWatchEvent(_In_ const FileWatchEvent&) = delete;

    ~FileWatchEvent();

    void Close();

    void Abort();

    _Must_inspect_result_
    HRESULT Initialize(
        _In_z_ const char* directoryPath,
        _In_z_ const char* openFileName);

    _Must_inspect_result_
    HRESULT Wait();

    const char* WatchFilePath() const;

    // Gets a value that indicates whether the file watcher is invalid.
    //
    bool IsInvalid() const
    {
        return m_fdNotify == INVALID_FD_VALUE;
    }

private:
    _Must_inspect_result_
    HRESULT CreateWatchFile();

private:
    int32_t m_fdNotify;
    char* m_directoryPath;
    char* m_watchFilePath;
};
}
}