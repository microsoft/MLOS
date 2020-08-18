// -----------------------------------------------------------------------
// <copyright file="DemoComponentConfig.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;

namespace Mlos.UnitTest
{
    [CodegenConfig]
    internal partial struct DemoComponentConfig
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

        [ScalarSetting]
        internal int KeepRunning;

        [ScalarSetting]
        internal float X1;

        [ScalarSetting]
        internal float X2;

        [ScalarSetting]
        internal float Y;
    }
}