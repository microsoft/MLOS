// -----------------------------------------------------------------------
// <copyright file="Native.Linux.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Security.Permissions;

using Microsoft.Win32.SafeHandles;

namespace Mlos.Core.Linux
{
    /// <summary>
    /// Linux PInvoke functions.
    /// </summary>
    internal static unsafe class Native
    {
        private const string RtLib = "rt";

        private const string SystemNative = "System.Native";

        /// <summary>
        /// Represents invalid pointer (void *) -1.
        /// </summary>
        internal static IntPtr InvalidPointer = IntPtr.Subtract(IntPtr.Zero, 1);

#pragma warning disable CA2101 // Specify marshaling for P/Invoke string arguments (CharSet.Ansi is considered unsafe).

        /// <summary>
        /// Receives a message on a socket.
        /// </summary>
        /// <returns>Returns number of bytes read.</returns>
        /// <param name="socketFd"></param>
        /// <param name="msg"></param>
        /// <param name="flags"></param>
        [DllImport(RtLib, EntryPoint = "recvmsg", SetLastError = true)]
        internal static extern ulong ReceiveMessage(IntPtr socketFd, ref MessageHeader msg, MsgFlags flags);

        /// <summary>
        /// Sends a message on a socket.
        /// </summary>
        /// <returns>Returns number of bytes written.</returns>
        /// <param name="socketFd"></param>
        /// <param name="msg"></param>
        /// <param name="flags"></param>
        [DllImport(RtLib, EntryPoint = "sendmsg", SetLastError = true)]
        internal static extern ulong SendMessage(IntPtr socketFd, ref MessageHeader msg, MsgFlags flags);

        /// <summary>
        /// Creates a new POSIX semaphore or opens an existing semaphore.  The semaphore is identified by name.
        /// </summary>
        /// <param name="name"></param>
        /// <param name="openFlags"></param>
        /// <returns></returns>
        [DllImport(RtLib, EntryPoint = "sem_open", CharSet = CharSet.Ansi, SetLastError = true)]
        internal static extern SemaphoreSafeHandle SemaphoreOpen(string name, OpenFlags openFlags);

        /// <summary>
        /// Creates a new POSIX semaphore or opens an existing semaphore.  The semaphore is identified by name.
        /// </summary>
        /// <param name="name"></param>
        /// <param name="openFlags"></param>
        /// <param name="mode"></param>
        /// <param name="value"></param>
        /// <returns></returns>
        [DllImport(RtLib, EntryPoint = "sem_open", CharSet = CharSet.Ansi, SetLastError = true)]
        internal static extern SemaphoreSafeHandle SemaphoreOpen(string name, OpenFlags openFlags, ModeFlags mode, int value);

        /// <summary>
        /// Increments (unlocks) the semaphore pointed to by sem. If the semaphore's value consequently becomes greater than zero,
        /// then another process or thread blocked in a sem_wait(3) call will be woken up and proceed to lock the semaphore.
        /// </summary>
        /// <param name="handle"></param>
        /// <returns>
        /// Returns 0 on success; on error, the value of the semaphore is left unchanged, -1 is returned, and errno is set to indicate the error.
        /// </returns>
        [DllImport(RtLib, EntryPoint = "sem_post", SetLastError = true)]
        internal static extern int SemaphorePost(SemaphoreSafeHandle handle);

        /// <summary>
        /// Decrements (locks) the semaphore pointed to by sem. If the semaphore's value is greater than zero, then the decrement
        /// proceeds, and the function returns, immediately. If the semaphore currently has the value zero, then the call blocks until either it
        /// becomes possible to perform the decrement (i.e., the semaphore value rises above zero), or a signal handler interrupts the call.
        /// </summary>
        /// <param name="handle"></param>
        /// <returns>Return 0 on success; on error, the value of the semaphore is left unchanged, -1 is returned.</returns>
        [DllImport(RtLib, EntryPoint = "sem_wait", SetLastError = true)]
        internal static extern int SemaphoreWait(SemaphoreSafeHandle handle);

        [DllImport(RtLib, EntryPoint = "sem_close", CharSet = CharSet.Ansi, SetLastError = true)]
        internal static extern int SemaphoreClose(IntPtr handle);

        /// <summary>
        /// Removes the named semaphore referred to by name.  The semaphore name is removed immediately.
        /// The semaphore is destroyed once all other processes that have the semaphore open close it.
        /// </summary>
        /// <param name="name"></param>
        /// <returns></returns>
        [DllImport(RtLib, EntryPoint = "sem_unlink", CharSet = CharSet.Ansi, SetLastError = true)]
        internal static extern int SemaphoreUnlink(string name);

        /// <summary>
        /// Creates and opens a new, or opens an existing, POSIX shared memory object.
        /// </summary>
        /// <param name="name"></param>
        /// <param name="openFlags"></param>
        /// <param name="mode"></param>
        /// <returns></returns>
        [DllImport(RtLib, EntryPoint = "shm_open", CharSet = CharSet.Ansi, SetLastError = true)]
        internal static extern SharedMemorySafeHandle SharedMemoryOpen(string name, OpenFlags openFlags, ModeFlags mode);

        [DllImport(RtLib, EntryPoint = "shm_unlink", CharSet = CharSet.Ansi, SetLastError = true)]
        internal static extern int SharedMemoryUnlink(string name);

        [DllImport(RtLib, EntryPoint = "unlink", CharSet = CharSet.Ansi, SetLastError = true)]
        internal static extern int FileSystemUnlink(string name);

        /// <summary>
        /// Gets a file status.
        /// </summary>
        /// <param name="fd"></param>
        /// <param name="output"></param>
        /// <returns>Returns zero on success.</returns>
        [DllImport(SystemNative, EntryPoint = "SystemNative_FStat", SetLastError = true)]
        internal static extern int FileStats(IntPtr fd, out FileStatus output);

        /// <summary>
        /// Map files or devices into the memory.
        /// </summary>
        /// <param name="address"></param>
        /// <param name="length"></param>
        /// <param name="protFlags"></param>
        /// <param name="mapFlags"></param>
        /// <param name="handle"></param>
        /// <param name="offset"></param>
        /// <returns></returns>
        [DllImport(RtLib, EntryPoint = "mmap", CharSet = CharSet.Ansi, SetLastError = true)]
        internal static extern IntPtr MapMemory(IntPtr address, ulong length, ProtFlags protFlags, MapFlags mapFlags, SharedMemorySafeHandle handle, long offset);

        /// <summary>
        /// Truncates a file to a specified length.
        /// </summary>
        /// <param name="handle"></param>
        /// <param name="length"></param>
        /// <returns></returns>
        [DllImport(RtLib, EntryPoint = "ftruncate", SetLastError = true)]
        internal static extern int FileTruncate(SharedMemorySafeHandle handle, long length);

        /// <summary>
        /// Closes a file descriptor.
        /// </summary>
        /// <param name="handle"></param>
        /// <returns></returns>
        [DllImport(RtLib, EntryPoint = "close", CharSet = CharSet.Ansi, SetLastError = true)]
        internal static extern int Close(IntPtr handle);

        [DllImport(RtLib, EntryPoint ="perror", CharSet = CharSet.Ansi)]
        internal static extern void PrintError(string name);

#pragma warning restore CA2101 // Specify marshaling for P/Invoke string arguments
        [Flags]
        internal enum OpenFlags : int
        {
            O_RDONLY = 0,
            O_WRONLY = 1,
            O_RDWR = 2,

            /// <summary>
            /// If pathname does not exist, create it as a regular file.
            /// </summary>
            O_CREAT = 0x40,

            /// <summary>
            /// Ensure that this call creates the file: if this flag is specified in conjunction with O_CREAT,
            /// and pathname already exists, then open() fails with the error EEXIST.
            /// </summary>
            O_EXCL = 0x80,
        }

        [Flags]
        internal enum ModeFlags : uint
        {
            /// <summary>
            /// Execute by owner.
            /// </summary>
            S_IXUSR = 0x0040,

            /// <summary>
            /// Write by owner.
            /// </summary>
            S_IWUSR = 0x80,

            /// <summary>
            /// Read by owner.
            /// </summary>
            S_IRUSR = 0x0100,

            S_IRWXU = S_IRUSR | S_IWUSR | S_IXUSR,
        }

        /// <summary>
        /// Desired memory protection of memory mapping.
        /// </summary>
        [Flags]
        internal enum ProtFlags : int
        {
            PROT_NONE = 0x0,

            PROT_READ = 0x1,
            PROT_WRITE = 0x2,
            PROT_EXEC = 0x4,

            /// <summary>
            /// Extend change to start of growsdown vma (mprotect only).
            /// </summary>
            PROT_GROWSDOWN = 0x1000000,

            /// <summary>
            /// Extend change to start of growsup vma (mprotect only).
            /// </summary>
            PROT_GROWNSUP = 0x2000000,
        }

        /// <summary>
        /// Additional parameters for mmap.
        /// </summary>
        [Flags]
        internal enum MapFlags : int
        {
            /// <summary>
            /// Compability flag.
            /// </summary>
            MAP_FILE = 0,

            /// <summary>
            /// Share this mapping. Mutually exclusive with MAP_PRIVATE.
            /// </summary>
            MAP_SHARED = 0x1,

            /// <summary>
            /// Create a private copy-on-write mapping. Mutually exclusive with MAP_SHARED.
            /// </summary>
            MAP_PRIVATE = 0x2,

            /// <summary>
            /// Mask for type fields.
            /// </summary>
            MAP_TYPE = 0xf,

            /// <summary>
            /// Place mapping at exactly the address specified in addr.
            /// </summary>
            MAP_FIXED = 0x10,

            /// <summary>
            /// Mapping is not backed by any file. Content is initialized to zero.
            /// </summary>
            MAP_ANONYMOUS = 0x20,
        }

        [Flags]
        internal enum ShmIpcFlags : int
        {
            /// <summary>
            /// Mark the segment to be destroyed.  The segment will actually be destroyed only after the last process detaches it.
            /// </summary>
            IPC_RMID = 0x0,

            /// <summary>
            /// Set the user ID of the owner, the group ID of the owner, and the permissions for the shared memory segment to the values
            /// in the shm_perm.uid, shm_perm.gid, and shm_perm.mode members of the shmid_ds data structure pointed to by *buf.
            /// </summary>
            IPC_SET = 0x1,
        }

        [Flags]
        internal enum MsgFlags : int
        {
            /// <summary>
            /// Process out-of-band data.
            /// </summary>
            MSG_OOB = 0x01,

            /// <summary>
            /// Peek at incoming messages.
            /// </summary>
            MSG_PEEK = 0x02,

            /// <summary>
            /// Don't use local routing.
            /// </summary>
            MSG_DONTROUTE = 0x04,

            /// <summary>
            /// Control data lost before delivery.
            /// </summary>
            MSG_CTRUNC = 0x08,

            /// <summary>
            /// Supply or ask second address.
            /// </summary>
            MSG_PROXY = 0x10,

            MSG_TRUNC = 0x20,
        }
    }

    /// <summary>
    /// Semaphore handle.
    /// </summary>
    [SecurityPermission(SecurityAction.InheritanceDemand, UnmanagedCode = true)]
    [SecurityPermission(SecurityAction.Demand, UnmanagedCode = true)]
    internal class SemaphoreSafeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SemaphoreSafeHandle()
            : base(true)
        {
        }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.Success)]
        protected override bool ReleaseHandle()
        {
            return Native.SemaphoreClose(handle) == 0;
        }
    }

    /// <summary>
    /// Shared memory handle.
    /// </summary>
    [SecurityPermission(SecurityAction.InheritanceDemand, UnmanagedCode = true)]
    [SecurityPermission(SecurityAction.Demand, UnmanagedCode = true)]
    internal class SharedMemorySafeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        /// <summary>
        /// Invalid handle.
        /// </summary>
        internal static readonly SharedMemorySafeHandle Invalid = new SharedMemorySafeHandle();

        internal SharedMemorySafeHandle()
            : base(true)
        {
        }

        internal SharedMemorySafeHandle(IntPtr fileDescriptor)
            : base(true)
        {
            SetHandle(fileDescriptor);
        }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.Success)]
        protected override bool ReleaseHandle()
        {
            return Native.Close(handle) == 0;
        }
    }

    /// <summary>
    /// File stats structure.
    /// </summary>
    [StructLayout(LayoutKind.Sequential)]
    internal struct FileStatus
    {
        internal int Flags;
        internal int Mode;
        internal uint Uid;
        internal uint Gid;
        internal long Size;
        internal long ATime;
        internal long ATimeNsec;
        internal long MTime;
        internal long MTimeNsec;
        internal long CTime;
        internal long CTimeNsec;
        internal long BirthTime;
        internal long BirthTimeNsec;
        internal long Dev;
        internal long Ino;
        internal uint UserFlags;
    }

    /// <summary>
    /// Definition of structure iovec.
    /// This must match the definitions in struct_iovec.h.
    /// </summary>
    [StructLayout(LayoutKind.Sequential, Pack=8)]
    internal struct IoVec
    {
        /// <summary>
        /// Pointer to data.
        /// </summary>
        internal IntPtr IovBase;

        /// <summary>
        /// Length of data.
        /// </summary>
        internal ulong IovLength;
    }

    [StructLayout(LayoutKind.Sequential, Pack=8)]
    internal struct MessageHeader
    {
        /// <summary>
        /// Address to send to/receive from.
        /// </summary>
        internal IntPtr MessageName;

        /// <summary>
        /// Length of address data.
        /// </summary>
        internal uint MessageNameLength;

        /// <summary>
        /// Vector of data to send/receive into.
        /// </summary>
        internal unsafe IoVec* MessageIoVec;

        /// <summary>
        /// Number of elements in the vector.
        /// </summary>
        public ulong MessageIoVecLength;

        /// <summary>
        /// Ancillary data (eg BSD file descriptor passing).
        /// </summary>
        internal unsafe ControlMessageHeader* MessageControl;

        /// <summary>
        /// Ancillary data buffer length.
        /// </summary>
        internal ulong MessageControlLength;

        /// <summary>
        /// Flags on received message.
        /// </summary>
        internal int MessageFlags;
    }

    /// <summary>
    /// Socket level message types.
    /// This must match the definitions in linux/socket.h.
    /// </summary>
    internal enum SocketLevelMessageType : int
    {
        /// <summary>
        /// Transfer file descriptors.
        /// </summary>
        ScmRights = 0x01,

        /// <summary>
        /// Credentials passing.
        /// </summary>
        ScmCredentials = 0x02,
    }

    /// <summary>
    /// Structure used for storage of ancillary data object information.
    /// </summary>
    /// <remarks>
    /// Struct cmsghdr.
    /// </remarks>
    [StructLayout(LayoutKind.Sequential, Pack=8)]
    internal struct ControlMessageHeader
    {
        /// <summary>
        /// Length of data in cmsg_data plus length of cmsghdr structure.
        /// </summary>
        internal ulong ControlMessageLength;

        /// <summary>
        /// Originating protocol.
        /// </summary>
        internal int ControlMessageLevel;

        /// <summary>
        /// Protocol specific type.
        /// </summary>
        internal SocketLevelMessageType ControlMessageType;
    }

    /// <summary>
    /// Structure used for storage of ancillary data object information of type {T}.
    /// </summary>
    /// <typeparam name="T">Type of stored object.</typeparam>
    [StructLayout(LayoutKind.Sequential, Pack=1)]
    internal struct ControlMessage<T>
        where T : struct
    {
        /// <summary>
        /// Cmsghdr struct.
        /// </summary>
        internal ControlMessageHeader Header;

        /// <summary>
        /// Value included in the message.
        /// </summary>
        internal T Value;
    }
}
