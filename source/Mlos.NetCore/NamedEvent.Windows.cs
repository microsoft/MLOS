// -----------------------------------------------------------------------
// <copyright file="NamedEvent.Windows.cs" company="Microsoft Corporation">
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
    public class NamedEvent : Core.NamedEvent
    {
        /// <summary>
        /// Creates or opens a named event.
        /// </summary>
        /// <param name="name"></param>
        /// <returns></returns>
        public static new NamedEvent CreateOrOpen(string name)
        {
            return new NamedEvent(name);
        }

        private NamedEvent(string name)
        {
            using (SecurityDescriptorSafePtr securityDescriptor = Security.CreateDefaultSecurityDescriptor())
            {
                var securityAttr = new Native.SECURITY_ATTRIBUTES
                {
                    Length = (uint)Marshal.SizeOf<Native.SECURITY_ATTRIBUTES>(),
                    InheritHandle = false,
                    SecurityDescriptor = securityDescriptor.DangerousGetHandle(),
                };

                eventHandle = Native.CreateEvent(
                    ref securityAttr,
                    manualReset: false,
                    initialState: false,
                    name);

                if (eventHandle.IsInvalid)
                {
                    throw new IOException(
                        $"Failed to create a NamedEvent {name}",
                        innerException: new Win32Exception(Marshal.GetLastWin32Error()));
                }

                Security.VerifyHandleOwner(eventHandle);
            }
        }

        /// <inheritdoc/>
        public override bool Signal()
        {
            return Native.SetEvent(eventHandle);
        }

        /// <inheritdoc/>
        public override bool Wait()
        {
            return Native.WaitForSingleObject(eventHandle, Native.Infinite) != 0;
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

            eventHandle?.Dispose();
            eventHandle = null;

            isDisposed = true;
        }

        private EventSafeHandle eventHandle;
    }
}
