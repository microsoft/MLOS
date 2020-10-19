// -----------------------------------------------------------------------
// <copyright file="TestSettingsRegistry2.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.InteropServices;

using Mlos.SettingsSystem.Attributes;

#pragma warning disable 1591 // Missing XML comment for publicly visible type or member {T}.

namespace Mlos.UnitTest
{
    /// <summary>
    /// 3D Point class.
    /// </summary>
    [CodegenType]
    internal partial struct Point3D
    {
        /// <summary>
        /// Field X.
        /// </summary>
        internal double X;

        /// <summary>
        /// Field Y.
        /// </summary>
        internal double Y;

        /// <summary>
        /// Field Y.
        /// </summary>
        internal double Z;
    }

    [CodegenType]
    [StructLayout(LayoutKind.Sequential, Size = 11)]
    internal partial struct Index2D
    {
        internal int I;
        internal int J;
    }

    [CodegenType]
    internal partial struct Index3D
    {
        internal int I;
        internal int J;
        internal int K;
    }

    [Flags]
    public enum Colors : ulong
    {
        /// <summary>
        /// Represents red color.
        /// </summary>
        Red = 2,

        /// <summary>
        /// Represents green color.
        /// </summary>
        Green = 4,

        /// <summary>
        /// Represents blue color.
        /// </summary>
        Blue = 8,
    }

    [CodegenType]
    internal partial struct Point4D
    {
        internal Point3D Point3D;
        internal Colors Color;
    }
}
