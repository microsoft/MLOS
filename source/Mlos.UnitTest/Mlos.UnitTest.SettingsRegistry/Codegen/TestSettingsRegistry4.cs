// -----------------------------------------------------------------------
// <copyright file="TestSettingsRegistry4.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.UnitTest
{
    /// <summary>
    /// TestAlignedTypeChild.
    /// </summary>
    [CodegenType]
    public partial struct TestAlignedTypeChild
    {
        public char ComponentType;

        [Align(32)]
        public double Delay;
    }

    [CodegenType]
    public partial class TestAlignedType
    {
        public short Id;

        public TestAlignedTypeChild ChildConfig;

        public char Id2;

        [FixedSizeArray(length: 16)]
        public readonly TestAlignedTypeChild[] Configs;
    }

    [CodegenType]
    public partial struct TestAlignedTypeHigherAlignment
    {
        public char Id;

        [Align(32)]
        public int Id2;

        public char Id3;

        [Align(32)]
        public TestAlignedTypeChild Id4;
    }

    [CodegenType]
    public partial class TestAlignedTypeMultipleAlignments
    {
        public short Id1;

        [Align(32)]
        public short Id2;

        [Align(16)]
        public short Id3;

        [Align(32)]
        public short Id4;
    }

    [CodegenType]
    [Align(32)]
    public partial struct TestAlignedStruct
    {
        public short Id1;
    }

    [CodegenType]
    public partial struct EmbeddingAlignedStruct
    {
        public short Id1;

        public TestAlignedStruct AlignedStruct;
    }
}
