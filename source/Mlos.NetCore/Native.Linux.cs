// -----------------------------------------------------------------------
// <copyright file="Native.Linux.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
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

        /// <summary>
        /// Represents invalid pointer (void *) -1.
        /// </summary>
        internal static IntPtr InvalidPointer = IntPtr.Subtract(IntPtr.Zero, 1);

#pragma warning disable CA2101 // Specify marshaling for P/Invoke string arguments (CharSet.Ansi is considered unsafe).

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
        /// Returns 0 on success; on error, the value of the semaphore is left unchanged, -1 is returned, and errno is set to indicate theerror.
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
            PROT_GROWNSDOWN = 0x1000000,
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
        public SharedMemorySafeHandle()
            : base(true)
        {
        }

        protected override bool ReleaseHandle()
        {
            return Native.Close(handle) == 0;
        }
    }
}
