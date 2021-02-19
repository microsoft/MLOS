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
HRESULT FileDescriptorExchange::Connect(_In_z_ char* socketName)
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

// Structure used for storage of ancillary data object information of type int32_t.
//
union ControlMessage
{
    struct cmsghdr Header;
    char message[CMSG_SPACE(sizeof(int32_t))];
};

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

    struct cmsghdr* cmptr;

    ControlMessage controlMessage {};

    if (exchangeFd != INVALID_FD_VALUE)
    {
        msg.msg_control = controlMessage.message;
        msg.msg_controllen = sizeof(controlMessage.message);

        cmptr = CMSG_FIRSTHDR(&msg);
        cmptr->cmsg_len = CMSG_LEN(sizeof(int));
        cmptr->cmsg_level = SOL_SOCKET;
        cmptr->cmsg_type = SCM_RIGHTS;
        int32_t* commandDataPtr = reinterpret_cast<int32_t*>(CMSG_DATA(cmptr));
        *commandDataPtr = exchangeFd;
    }

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

    struct msghdr message {};
    struct iovec iov[IoVecLength];

    ControlMessage controlMessage {};

    struct cmsghdr* cmptr = nullptr;

    message.msg_control = controlMessage.message;
    message.msg_controllen = sizeof(controlMessage.message);

    message.msg_name = nullptr;
    message.msg_namelen = 0;

    iov[0].iov_base = bufferPtr;
    iov[0].iov_len = bufferSize;
    message.msg_iov = iov;
    message.msg_iovlen = IoVecLength;

    ssize_t receivedBytes = recvmsg(socketFd, &message, 0);
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
        cmptr = CMSG_FIRSTHDR(&message);
    }

    if (cmptr != nullptr)
    {
        if (cmptr->cmsg_len == CMSG_LEN(sizeof(int)) &&
            cmptr->cmsg_type == SCM_RIGHTS)
        {
            int32_t* commandDataPtr = reinterpret_cast<int32_t*>(CMSG_DATA(cmptr));
            receivedFd = *commandDataPtr;
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
    _In_z_ const char* sharedMemoryMapName,
    _Out_ int32_t& exchangeFd) const
{
    HRESULT hr = S_OK;

    // Ask for the shared memory using a name.
    //
    hr = SendMessageAndFileDescriptor(
        m_socketFd,
        const_cast<char*>(sharedMemoryMapName),
        strlen(sharedMemoryMapName),
        INVALID_FD_VALUE);

    if (SUCCEEDED(hr))
    {
        //
        //
        Mlos::Core::Internal::FileDescriptorExchangeMessage msg = {};

        hr = ReceiveMessageAndFileDescriptor(
            m_socketFd,
            &msg,
            sizeof(msg),
            exchangeFd);
    }

    if (SUCCEEDED(hr))
    {
        // Agent does not have memory region.
        //
        if (exchangeFd == INVALID_FD_VALUE)
        {
            hr = E_NOT_SET;
        }
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
    _In_z_ const char* sharedMemoryMapName,
    _In_ int32_t exchangeFd) const
{
    HRESULT hr = S_OK;

    hr = SendMessageAndFileDescriptor(
        m_socketFd,
        const_cast<char*>(sharedMemoryMapName),
        strlen(sharedMemoryMapName),
        exchangeFd);

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
