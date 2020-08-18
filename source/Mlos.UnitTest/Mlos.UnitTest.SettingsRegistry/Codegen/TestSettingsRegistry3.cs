// -----------------------------------------------------------------------
// <copyright file="TestSettingsRegistry3.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace Mlos.UnitTest
{
    /// <summary>
    /// Configuration defintion, used by the unit test.
    /// </summary>
    [CodegenConfig]
    public partial struct TestComponentConfig
    {
        [ScalarSetting(isPrimaryKey: true)]
        public uint ComponentType;

        [ScalarSetting(isPrimaryKey: true)]
        public uint Category;

        [ScalarSetting]
        public double Delay;
    }

    [CodegenConfig]
    public partial class TestComponentStatistics
    {
        [ScalarSetting(isPrimaryKey: true)]
        public int Id;

        [ScalarSetting]
        public AtomicUInt64 RefCount;

        [ScalarSetting]
        [FixedSizeArray(length: 16)]
        public readonly AtomicUInt64[] Counters;
    }
}
