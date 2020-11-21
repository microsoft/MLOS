// -----------------------------------------------------------------------
// <copyright file="SmartComponentExampleConfig.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;

namespace ExternalIntegrationExample
{
    /// <summary>
    /// An example settings config structure for a smart component in the external project.
    /// </summary>
    [CodegenConfig]
    internal partial struct SmartComponentExampleConfig
    {
        /// <summary>
        /// Set by the agent upon suggesting new config.
        /// </summary>
        [ScalarSetting]
        internal long NewConfigId;

        /// <summary>
        /// Set by the component, upon consuming the config.
        /// </summary>
        [ScalarSetting]
        internal long ActiveConfigId;

        /// <summary>
        /// The size for the smart component example.
        /// </summary>
        [ScalarSetting]
        internal long Size;
    }
}
