//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: FileDescriptorExchange.Linux.h
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
// NAME: FileDescriptorExchange
//
// PURPOSE:
//  Helper class used to exchange the file descriptor via Unix domain socket.
//
// NOTES:
//
class FileDescriptorExchange
{
public:
    FileDescriptorExchange();

    FileDescriptorExchange(const FileDescriptorExchange&) = delete;

    FileDescriptorExchange& operator=(const FileDescriptorExchange&) = delete;

    ~FileDescriptorExchange();

    // Closes the opened socket.
    //
    void Close();

    // Connects to Unix domain socket.
    //
    _Must_inspect_result_
    HRESULT Connect(_In_z_ char* socketName);

    // Gets a file descriptor via Unix domain socket.
    //
    _Must_inspect_result_
    HRESULT GetFileDescriptor(
        _In_z_ const char* sharedMemoryMapName,
        _Out_ int32_t& exchangeFd) const;

    // Sends a file descriptor via Unix domain socket.
    //
    _Must_inspect_result_
    HRESULT SendFileDescriptor(
        _In_z_ const char* sharedMemoryMapName,
        _In_ int32_t exchangeFd) const;

    // Gets the information if we established connection to the agent.
    //
    _Must_inspect_result_
    bool IsServerAvailable() const;

private:
    // Socket file descriptor.
    //
    int m_socketFd;
};
}
}
