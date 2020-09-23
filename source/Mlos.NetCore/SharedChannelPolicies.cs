// -----------------------------------------------------------------------
// <copyright file="SharedChannelPolicies.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Threading;

namespace Mlos.Core
{
    /// <summary>
    /// Shared channel policy interface.
    /// </summary>
    public interface ISharedChannelPolicy
    {
        /// <summary>
        /// Called when received a frame with mismatch codegen type metadata.
        /// </summary>
        void ReceivedInvalidFrame();

        /// <summary>
        /// Notify reader that there is a frame to process.
        /// </summary>
        void NotifyExternalReader();

        /// <summary>
        /// Called when reader thread is no longer processing the messages.
        /// </summary>
        void WaitForFrame();
    }

    /// <summary>
    /// Shared channel spin policy interface.
    /// </summary>
    public interface ISharedChannelSpinPolicy
    {
        #region Reader policy

        /// <summary>
        /// Called when there is no frame in the buffer.
        /// </summary>
        void WaitForNewFrame();

        /// <summary>
        /// Called when reader acquire the frame but the frame is not yet completed.
        /// </summary>
        /// <remarks>
        /// This wait is expected to be short.
        /// </remarks>
        void WaitForFrameCompletion();

        #endregion

        #region Writer policy

        /// <summary>
        /// Another writer acquired the write region.
        /// </summary>
        void FailedToAcquireWriteRegion();

        /// <summary>
        /// There is a frame in the buffer however other thread acquire the read first.
        /// </summary>
        void FailedToAcquireReadRegion();

        #endregion
    }

    /// <summary>
    /// InternalSharedChannelPolicy.
    /// </summary>
    /// <remarks>
    /// For testing purposes.
    /// </remarks>
    public struct InternalSharedChannelPolicy : ISharedChannelPolicy
    {
        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void ReceivedInvalidFrame()
        {
            // Invalid frame. Terminate.
            //
            Debugger.Launch();
            Environment.Exit(-1);
        }

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void NotifyExternalReader()
        {
        }

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void WaitForFrame()
        {
        }
    }

    /// <summary>
    /// #TODO NotificationEvent needs to be set.
    /// </summary>
    public struct InterProcessSharedChannelPolicy : ISharedChannelPolicy
    {
        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void ReceivedInvalidFrame()
        {
            // Invalid frame. Terminate.
            //
            Environment.Exit(0);
        }

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void NotifyExternalReader()
        {
            NotificationEvent.Signal();
        }

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void WaitForFrame()
        {
            NotificationEvent.Wait();
        }

        /// <summary>
        /// Inter process synchronization object.
        /// </summary>
        public NamedEvent NotificationEvent;
    }

    /// <summary>
    /// Spin policy for the shared channel.
    /// </summary>
    public struct SharedChannelSpinPolicy : ISharedChannelSpinPolicy
    {
        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void WaitForNewFrame()
        {
        }

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void WaitForFrameCompletion()
        {
        }

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void FailedToAcquireReadRegion()
        {
            spinWait.SpinOnce();
        }

        /// <inheritdoc/>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void FailedToAcquireWriteRegion()
        {
            spinWait.SpinOnce();
        }

        private SpinWait spinWait;
    }
}
