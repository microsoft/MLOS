// -----------------------------------------------------------------------
// <copyright file="SettingsRegistryAssembly.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace Mlos.Core.Internal
{
    /// <summary>
    /// The structure contains information about registered assembly settings.
    /// </summary>
    /// <remarks>
    /// Registered settings assemblies are stored in the global memory shared dictionary.
    /// </remarks>
    [CodegenConfig]
    public partial struct RegisteredSettingsAssemblyConfig
    {
        [ScalarSetting(isPrimaryKey: true)]
        internal uint AssemblyIndex;

        /// <summary>
        /// Assembly name.
        /// </summary>
        [ScalarSetting]
        internal StringPtr AssemblyFileName;

        /// <summary>
        /// Base indexes for assembly dispatch table.
        /// </summary>
        [ScalarSetting]
        internal uint DispatchTableBaseIndex;
    }

    /// <summary>
    /// Request message to register settings assembly.
    /// </summary>
    [CodegenMessage]
    internal partial struct RegisterSettingsAssemblyRequestMessage
    {
        /// <summary>
        /// Assembly index.
        /// </summary>
        internal uint AssemblyIndex;
    }
}
