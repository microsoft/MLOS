// -----------------------------------------------------------------------
// <copyright file="SharedChannelConfig.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;

namespace SmartSharedChannel
{
    /// <summary>
    /// SharedChannel Config.
    /// </summary>
    [CodegenConfig]
    internal partial struct SharedChannelConfig
    {
        /// <summary>
        /// Size of the communication buffer.
        /// </summary>
        [ScalarSetting]
        internal int BufferSize;

        /// <summary>
        /// Number of read threads.
        /// </summary>
        [ScalarSetting]
        internal int ReaderCount;
    }

    /// <summary>
    /// Parameters of shared channel microbenchark.
    /// </summary>
    [CodegenConfig]
    internal partial struct MicrobenchmarkConfig
    {
        /// <summary>
        /// Duration of microbenchmark in seconds.
        /// </summary>
        [ScalarSetting]
        internal int DurationInSec;

        /// <summary>
        /// Number of writer threads.
        /// </summary>
        [ScalarSetting]
        internal int WriterCount;
    }

    // <summary>
    // Shared channel reader statistics.
    // </summary>
    [CodegenConfig]
    internal partial struct SharedChannelReaderStats
    {
        [ScalarSetting]
        internal ulong MessagesRead;

        [ScalarSetting]
        internal ulong SpinCount;
    }
}
