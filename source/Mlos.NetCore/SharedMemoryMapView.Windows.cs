// -----------------------------------------------------------------------
// <copyright file="SharedMemoryMapView.Windows.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;

namespace Mlos.Core.Windows
{
    /// <summary>
    /// Windows implementation of shared memory map view.
    /// </summary>
    public class SharedMemoryMapView : Mlos.Core.SharedMemoryMapView
    {
        /// <summary>
        /// Creates a new shared memory view.
        /// </summary>
        /// <param name="sharedMemoryMapName"></param>
        /// <param name="sharedMemorySize"></param>
        /// <returns></returns>
        public static new SharedMemoryMapView CreateNew(string sharedMemoryMapName, ulong sharedMemorySize)
        {
            return CreateOrOpen(sharedMemoryMapName, sharedMemorySize);
        }

        /// <summary>
        /// Creates or opens a shared memory view.
        /// </summary>
        /// <param name="sharedMemoryMapName"></param>
        /// <param name="sharedMemorySize"></param>
        /// <returns></returns>
        public static new SharedMemoryMapView CreateOrOpen(string sharedMemoryMapName, ulong sharedMemorySize)
        {
            SharedMemorySafeHandle sharedMemoryHandle;
            using (SecurityDescriptorSafePtr securityDescriptor = Security.CreateDefaultSecurityDescriptor())
            {
                var securityAttr = new Native.SECURITY_ATTRIBUTES
                {
                    Length = (uint)Marshal.SizeOf<Native.SECURITY_ATTRIBUTES>(),
                    InheritHandle = false,
                    SecurityDescriptor = securityDescriptor.DangerousGetHandle(),
                };

                uint sharedMemorySizeHigh;
                uint sharedMemorySizeLow;
                Utils.SplitULong(sharedMemorySize, out sharedMemorySizeHigh, out sharedMemorySizeLow);

                sharedMemoryHandle = Native.CreateFileMapping(
                    Native.InvalidPointer,
                    ref securityAttr,
                    Native.FileMapProtection.PageReadWrite,
                    sharedMemorySizeHigh,
                    sharedMemorySizeLow,
                    sharedMemoryMapName);
            }

            if (sharedMemoryHandle.IsInvalid)
            {
                throw new FileNotFoundException(
                    $"Failed to CreateFileMapping {sharedMemoryMapName}",
                    innerException: new Win32Exception(Marshal.GetLastWin32Error()));
            }

            Security.VerifyHandleOwner(sharedMemoryHandle);

            return new SharedMemoryMapView(sharedMemoryHandle, sharedMemorySize);
        }

        /// <summary>
        /// Opens an existing shared memory view.
        /// </summary>
        /// <param name="sharedMemoryMapName"></param>
        /// <param name="sharedMemorySize"></param>
        /// <returns></returns>
        public static new SharedMemoryMapView OpenExisting(string sharedMemoryMapName, ulong sharedMemorySize)
        {
            SharedMemorySafeHandle sharedMemoryHandle = Native.OpenFileMapping(
                Native.MemoryMappedFileAccess.FileMapRead | Native.MemoryMappedFileAccess.FileMapWrite,
                false,
                sharedMemoryMapName);

            if (sharedMemoryHandle.IsInvalid)
            {
                throw new FileNotFoundException(
                    $"Failed to OpenFileMapping {sharedMemoryMapName}",
                    innerException: new Win32Exception(Marshal.GetLastWin32Error()));
            }

            Security.VerifyHandleOwner(sharedMemoryHandle);

            return new SharedMemoryMapView(sharedMemoryHandle, sharedMemorySize);
        }

        private SharedMemoryMapView(SharedMemorySafeHandle sharedMemoryHandle, ulong sharedMemorySize)
        {
            this.sharedMemoryHandle = sharedMemoryHandle;

            memoryMappingHandle = Native.MapViewOfFile(
                sharedMemoryHandle,
                Native.MemoryMappedFileAccess.FileMapAllAccess,
                fileOffsetHigh: 0,
                fileOffsetLow: 0,
                numberOfBytesToMap: (int)sharedMemorySize);

            Buffer = memoryMappingHandle.DangerousGetHandle();

            MemSize = sharedMemorySize;
        }

        /// <summary>
        /// Protected implementation of Dispose pattern.
        /// </summary>
        /// <param name="disposing"></param>
        protected override void Dispose(bool disposing)
        {
            if (isDisposed || !disposing)
            {
                return;
            }

            // Close the memory mapping.
            //
            memoryMappingHandle?.Dispose();

            // Close the shared memory.
            //
            sharedMemoryHandle?.Dispose();

            isDisposed = true;
        }

        private readonly MemoryMappingSafeHandle memoryMappingHandle;

        private readonly SharedMemorySafeHandle sharedMemoryHandle;
    }
}
