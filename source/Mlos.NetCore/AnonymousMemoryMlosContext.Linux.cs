// -----------------------------------------------------------------------
// <copyright file="AnonymousMemoryMlosContext.Linux.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Threading;

using Mlos.Core.Internal;
using Proxy.Mlos.Core.Internal;

using MlosInternal = Mlos.Core.Internal;
using MlosProxyInternal = Proxy.Mlos.Core.Internal;

namespace Mlos.Core.Linux
{
    /// <summary>
    ///  Implementation of an inter-process MlosContext based on anonymous shared memory.
    ///  Shared memory file descriptors are exchanged using Unix domain socket.
    /// </summary>
    public class AnonymousMemoryMlosContext : MlosContext
    {
        private const string GlobalMemoryMapName = "Host_Mlos.GlobalMemory";

        // Path to the folder where Unix domain socket name.
        //
        private const string DefaultSocketFolderPath = "/var/tmp/mlos/";

        /// <summary>
        /// Creates AnonymousMemoryMlosContext.
        /// </summary>
        /// <returns></returns>
        public static AnonymousMemoryMlosContext Create()
        {
            var fdExchangeServer = new FileDescriptorExchangeServer(DefaultSocketFolderPath);

            fdExchangeServer.HandleRequests();

            SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView =
                SharedMemoryRegionView.OpenFromFileDescriptor<MlosProxyInternal.GlobalMemoryRegion>(
                    fdExchangeServer.GetSharedMemoryFd(GlobalMemoryMapName));

            // Create channel synchronization primitives.
            //
            MlosProxyInternal.GlobalMemoryRegion globalMemoryRegion = globalMemoryRegionView.MemoryRegion();

            // Control channel.
            //
            globalMemoryRegion.TryGetSharedMemoryName(
                    new MlosInternal.MemoryRegionId { Type = MemoryRegionType.ControlChannel, Index = 0 },
                    out string sharedMemoryMapName);

            SharedMemoryMapView controlChannelMemoryMapView = SharedMemoryMapView.OpenFromFileDescriptor(
                fdExchangeServer.GetSharedMemoryFd(sharedMemoryMapName));

            // Feedback channel.
            //
            globalMemoryRegion.TryGetSharedMemoryName(
                new MlosInternal.MemoryRegionId { Type = MemoryRegionType.FeedbackChannel, Index = 0 },
                out sharedMemoryMapName);

            SharedMemoryMapView feedbackChannelMemoryMapView = SharedMemoryMapView.OpenFromFileDescriptor(
                fdExchangeServer.GetSharedMemoryFd(sharedMemoryMapName));

            // Shared config.
            //
            globalMemoryRegion.TryGetSharedMemoryName(
                new MlosInternal.MemoryRegionId { Type = MemoryRegionType.SharedConfig, Index = 0 },
                out sharedMemoryMapName);

            SharedMemoryMapView sharedConfigMemoryMapView = SharedMemoryMapView.OpenFromFileDescriptor(
                fdExchangeServer.GetSharedMemoryFd(sharedMemoryMapName));

            var sharedConfigMemoryRegionView = new SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion>(sharedConfigMemoryMapView);

            globalMemoryRegion.TryOpenExisting(
                new MlosInternal.MemoryRegionId { Type = MemoryRegionType.ControlChannel, Index = 0, },
                out NamedEvent controlChannelNamedEvent);

            globalMemoryRegion.TryOpenExisting(
                new MlosInternal.MemoryRegionId { Type = MemoryRegionType.FeedbackChannel, Index = 0, },
                out NamedEvent feedbackChannelNamedEvent);

            return new AnonymousMemoryMlosContext(
                globalMemoryRegionView,
                controlChannelMemoryMapView,
                feedbackChannelMemoryMapView,
                sharedConfigMemoryRegionView,
                controlChannelNamedEvent,
                feedbackChannelNamedEvent,
                fdExchangeServer);
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="AnonymousMemoryMlosContext"/> class.
        /// </summary>
        /// <param name="globalMemoryRegionView"></param>
        /// <param name="controlChannelMemoryMapView"></param>
        /// <param name="feedbackChannelMemoryMapView"></param>
        /// <param name="sharedConfigMemoryRegionView"></param>
        /// <param name="controlChannelNamedEvent"></param>
        /// <param name="feedbackChannelNamedEvent"></param>
        /// <param name="fileDescriptorExchangeServer"></param>
        private AnonymousMemoryMlosContext(
            SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView,
            SharedMemoryMapView controlChannelMemoryMapView,
            SharedMemoryMapView feedbackChannelMemoryMapView,
            SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion> sharedConfigMemoryRegionView,
            NamedEvent controlChannelNamedEvent,
            NamedEvent feedbackChannelNamedEvent,
            FileDescriptorExchangeServer fileDescriptorExchangeServer)
        {
            this.globalMemoryRegionView = globalMemoryRegionView ?? throw new ArgumentNullException(nameof(globalMemoryRegionView));
            this.controlChannelMemoryMapView = controlChannelMemoryMapView ?? throw new ArgumentNullException(nameof(controlChannelMemoryMapView));
            this.feedbackChannelMemoryMapView = feedbackChannelMemoryMapView ?? throw new ArgumentNullException(nameof(feedbackChannelMemoryMapView));

            this.controlChannelNamedEvent = controlChannelNamedEvent ?? throw new ArgumentNullException(nameof(controlChannelNamedEvent));
            this.feedbackChannelNamedEvent = feedbackChannelNamedEvent ?? throw new ArgumentNullException(nameof(feedbackChannelNamedEvent));

            this.fileDescriptorExchangeServer = fileDescriptorExchangeServer;

            // Create the shared config manager.
            //
            SharedConfigManager = new SharedConfigManager();

            // Register shared config memory region.
            //
            SharedConfigManager.RegisterSharedConfigMemoryRegion(sharedConfigMemoryRegionView);

            MlosProxyInternal.GlobalMemoryRegion globalMemoryRegion = globalMemoryRegionView.MemoryRegion();

            // Increase the usage counter. When closing global shared memory, we will decrease the counter.
            // If there is no process using the shared memory, we will clean the OS resources. On Windows OS,
            // this is no-op; on Linux, we unlink created files.
            //
            globalMemoryRegion.AttachedProcessesCount.FetchAdd(1);

            // Create the control channel instance.
            //
            ControlChannel = new SharedChannel<InterProcessSharedChannelPolicy, SharedChannelSpinPolicy>(
                buffer: controlChannelMemoryMapView.Buffer,
                size: (uint)controlChannelMemoryMapView.MemSize,
                sync: globalMemoryRegion.ControlChannelSynchronization)
            {
                ChannelPolicy = { NotificationEvent = controlChannelNamedEvent },
            };

            // Create the feedback channel instance.
            //
            FeedbackChannel = new SharedChannel<InterProcessSharedChannelPolicy, SharedChannelSpinPolicy>(
                buffer: feedbackChannelMemoryMapView.Buffer,
                size: (uint)feedbackChannelMemoryMapView.MemSize,
                sync: globalMemoryRegion.FeedbackChannelSynchronization)
            {
                ChannelPolicy = { NotificationEvent = feedbackChannelNamedEvent },
            };
        }

        /// <inheritdoc/>
        protected override void Dispose(bool disposing)
        {
            if (isDisposed || !disposing)
            {
                return;
            }

            fileDescriptorExchangeServer?.Dispose();
            fileDescriptorExchangeServer = null;

            uint usageCount = GlobalMemoryRegion.AttachedProcessesCount.FetchSub(1);

            if (usageCount == 0)
            {
                controlChannelNamedEvent.CleanupOnClose = true;
                feedbackChannelNamedEvent.CleanupOnClose = true;

                // Close all the shared config memory regions.
                //
                SharedConfigManager.CleanupOnClose = true;
            }

            base.Dispose(disposing: true);
        }

        private FileDescriptorExchangeServer fileDescriptorExchangeServer;
    }
}
