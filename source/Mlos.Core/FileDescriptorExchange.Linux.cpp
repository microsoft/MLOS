//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: FileDescriptorExchange.Linux.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

#include <sys/socket.h>
#include <sys/types.h>
#include <sys/un.h>
#include <fcntl.h>
#include <unistd.h>

namespace Mlos
{
namespace Core
{
// Number of scatter/gather I/O buffers.
//
constexpr int32_t IoVecLength = 1;

//----------------------------------------------------------------------------
// NAME: FileDescriptorExchange constructor
//
// PURPOSE:
//
// NOTES:
//
FileDescriptorExchange::FileDescriptorExchange()
 : m_socketFd(INVALID_FD_VALUE)
{
}

//----------------------------------------------------------------------------
// NAME: FileDescriptorExchange destructor
//
// PURPOSE:
//
// NOTES:
//
FileDescriptorExchange::~FileDescriptorExchange()
{
    Close();
}

//----------------------------------------------------------------------------
// NAME: FileDescriptorExchange::Close
//
// PURPOSE:
//
// NOTES:
//
void FileDescriptorExchange::Close()
{
    // Close the opened socket.
    //
    if (m_socketFd != INVALID_FD_VALUE)
    {
        close(m_socketFd);
        m_socketFd = INVALID_FD_VALUE;
    }
}

//----------------------------------------------------------------------------
// NAME: SendMessageAndFileDescriptor
//
// PURPOSE:
//  Connects to Unix domain socket.
//
// NOTES:
//
_Must_inspect_result_
HRESULT FileDescriptorExchange::Connect(_In_z_ const char* socketName)
{
    // Close established connection.
    //
    Close();

    HRESULT hr = S_OK;

    // Create a Unix domain socket.
    //
    m_socketFd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (m_socketFd == -1)
    {
        hr = HRESULT_FROM_ERRNO(errno);
    }

    // Connect to the socket.
    //
    if (SUCCEEDED(hr))
    {
        struct sockaddr_un socketAddress = {};
        socketAddress.sun_family = AF_UNIX;
        strncpy(socketAddress.sun_path, socketName, sizeof(sockaddr_un::sun_path) - 1);

        if (connect(m_socketFd, reinterpret_cast<struct sockaddr*>(&socketAddress), sizeof(struct sockaddr_un)) == -1)
        {
            hr = HRESULT_FROM_ERRNO(errno);
            Close();
        }
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: SendMessageAndFileDescriptor
//
// PURPOSE:
//  Sends a file descriptor via Unix domain socket.
//
// NOTES:
//  socketFd - socket file descriptor
//  exchangeFd - shared memory file descriptor
//
_Must_inspect_result_
HRESULT SendMessageAndFileDescriptor(
    _In_ int32_t socketFd,
    _In_reads_bytes_(dataSize) void* dataPtr,
    _In_ ssize_t dataSize,
    _In_ int32_t exchangeFd)
{
    struct msghdr msg {};
    struct iovec iov[IoVecLength];

    union
    {
        struct cmsghdr cm;
        char control[CMSG_SPACE(sizeof(int))];
    } control_un;
    struct cmsghdr* cmptr;

    msg.msg_control = control_un.control;
    msg.msg_controllen = sizeof(control_un.control);

    cmptr = CMSG_FIRSTHDR(&msg);
    cmptr->cmsg_len = CMSG_LEN(sizeof(int));
    cmptr->cmsg_level = SOL_SOCKET;
    cmptr->cmsg_type = SCM_RIGHTS;
    int* cm_data_ptr = reinterpret_cast<int*>(CMSG_DATA(cmptr));
    *cm_data_ptr = exchangeFd;

    msg.msg_name = nullptr;
    msg.msg_namelen = 0;

    iov[0].iov_base = dataPtr;
    iov[0].iov_len = dataSize;

    msg.msg_iov = iov;
    msg.msg_iovlen = IoVecLength;

    ssize_t sendBytes = sendmsg(socketFd, &msg, 0);
    if (sendBytes == -1)
    {
        return HRESULT_FROM_ERRNO(errno);
    }

    // Fail if received unexpected message.
    //
    if (sendBytes != dataSize)
    {
        return E_NOT_SET;
    }

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: ReceiveMessageAndFileDescriptor
//
// PURPOSE:
//  Sends a file descriptor via Unix domain socket.
//
// NOTES:
//  socketFd - socket file descriptor
//  receivedFd - received shared memory file descriptor
//
_Must_inspect_result_
HRESULT ReceiveMessageAndFileDescriptor(
    _In_ int32_t socketFd,
    _Inout_ void* bufferPtr,
    _In_ ssize_t bufferSize,
    _Inout_ int32_t& receivedFd)
{
    HRESULT hr = S_OK;
    receivedFd = INVALID_FD_VALUE;

    struct msghdr msg {};
    struct iovec iov[IoVecLength];

    union
    {
        struct cmsghdr cm;
        char control[CMSG_SPACE(sizeof(int))];
    } control_un;
    struct cmsghdr* cmptr = nullptr;

    msg.msg_control = control_un.control;
    msg.msg_controllen = sizeof(control_un.control);

    msg.msg_name = nullptr;
    msg.msg_namelen = 0;

    iov[0].iov_base = bufferPtr;
    iov[0].iov_len = bufferSize;
    msg.msg_iov = iov;
    msg.msg_iovlen = IoVecLength;

    ssize_t receivedBytes = recvmsg(socketFd, &msg, 0);
    if (receivedBytes == -1)
    {
        hr = HRESULT_FROM_ERRNO(errno);
    }

    if (SUCCEEDED(hr))
    {
        // Fail if received unexpected message.
        //
        if (receivedBytes != bufferSize)
        {
            hr = E_NOT_SET;
        }
    }

    if (SUCCEEDED(hr))
    {
        cmptr = CMSG_FIRSTHDR(&msg);
    }

    if (cmptr != nullptr)
    {
        if (cmptr->cmsg_len == CMSG_LEN(sizeof(int)) &&
            cmptr->cmsg_type == SCM_RIGHTS)
        {
            int* cm_data_ptr = reinterpret_cast<int*>(CMSG_DATA(cmptr));
            receivedFd = *cm_data_ptr;
        }
        else
        {
            // Received unexpected but valid message.
            //
            hr = S_FALSE;
        }
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: FileDescriptorExchange::GetFileDescriptor
//
// PURPOSE:
//  Gets a file descriptor via Unix domain socket.
//
// NOTES:
//  id
//  exchangeFd - file descriptor
//
_Must_inspect_result_
HRESULT FileDescriptorExchange::GetFileDescriptor(
    _In_ Internal::MemoryRegionId memoryRegionId,
    _Out_ int32_t& exchangeFd,
    _Out_ size_t& memoryRegionSize) const
{
    HRESULT hr = S_OK;

    // Send the message.
    //
    Mlos::Core::Internal::FileDescriptorExchangeMessage msg = {};

    msg.MemoryRegionId = memoryRegionId;
    msg.ContainsFd = false;

    hr = SendMessageAndFileDescriptor(m_socketFd, &msg, sizeof(msg), 0);

    if (SUCCEEDED(hr))
    {
        hr = ReceiveMessageAndFileDescriptor(m_socketFd, &msg, sizeof(msg), exchangeFd);
    }

    if (SUCCEEDED(hr))
    {
        // Agent does not have memory region.
        //
        if (!msg.ContainsFd)
        {
            hr = E_NOT_SET;
        }
    }

    if (SUCCEEDED(hr))
    {
        memoryRegionSize = msg.MemoryRegionSize;
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: FileDescriptorExchange::SendFileDescriptor
//
// PURPOSE:
//  Sends a file descriptor via Unix domain socket.
//
// NOTES:
//  id
//  exchangeFd - file descriptor
//
_Must_inspect_result_
HRESULT FileDescriptorExchange::SendFileDescriptor(
    _In_ Internal::MemoryRegionId memoryRegionId,
    _In_ int32_t exchangeFd,
    _In_ size_t memoryRegionSize) const
{
    HRESULT hr = S_OK;

    // Send the message.
    //
    Mlos::Core::Internal::FileDescriptorExchangeMessage msg = {};

    msg.MemoryRegionId = memoryRegionId;
    msg.MemoryRegionSize = memoryRegionSize;
    msg.ContainsFd = true;

    hr = SendMessageAndFileDescriptor(m_socketFd, &msg, sizeof(msg), exchangeFd);

    return hr;
}

//----------------------------------------------------------------------------
// NAME: FileDescriptorExchange::IsServerAvailable
//
// PURPOSE:
//  Gets the information if we established connection to the agent.
//
// NOTES:
//
_Must_inspect_result_
bool FileDescriptorExchange::IsServerAvailable() const
{
    return m_socketFd != INVALID_FD_VALUE;
}
}
}
