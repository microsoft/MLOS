// -----------------------------------------------------------------------
// <copyright file="ComponentAssembly.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace Mlos.Core.Internal
{
    [CodegenConfig]
    public partial struct RegisteredSettingsAssemblyConfig
    {
        [ScalarSetting(isPrimaryKey: true)]
        internal uint AssemblyIndex;

        /// <summary>
        /// Full path to the client application.
        /// </summary>
        [ScalarSetting]
        internal StringPtr ApplicationFilePath;

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
    /// Request message to register component type assembly.
    /// </summary>
    [CodegenMessage]
    internal partial struct RegisterAssemblyRequestMessage
    {
        /// <summary>
        /// Assembly index.
        /// </summary>
        internal uint AssemblyIndex;
    }
}
