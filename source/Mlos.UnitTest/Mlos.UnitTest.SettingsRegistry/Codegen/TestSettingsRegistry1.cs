// -----------------------------------------------------------------------
// <copyright file="TestSettingsRegistry1.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace Mlos.UnitTest
{
    /// <summary>
    /// Composite structure. Verifies all inner structures has correct offsets.
    /// </summary>
    /// <remarks>
    /// We are using structures defined later in the code.
    /// </remarks>
    [CodegenMessage]
    internal partial class CompositeStructure
    {
        internal WideStringPtr Name;
        internal Point Point2d;
        internal Point3D Point3d;
        internal Line Line;
        internal Index2D Index2D;
        internal Index3D Index3D;
        internal StringPtr Version;
    }

    // Fixed struct holding a variable length struct.
    //
    [CodegenMessage]
    internal partial class CompositeStructure2
    {
        internal char Letter;
        internal short ShortInteger;
        internal CompositeStructure BaseComp;
        internal WideStringPtr Title;
        internal Point PointNext;
    }

    /// <summary>
    /// Point struct.
    /// </summary>
    [CodegenType]
    internal partial struct Point
    {
        /// <summary>
        /// Field X.
        /// </summary>
        internal float X;

        /// <summary>
        /// Field Y.
        ///
        /// Field Y (2).
        /// </summary>
        internal float Y;
    }

    /// <summary>
    /// Line struct.
    /// </summary>
    [CodegenMessage]
    internal partial class Line
    {
        internal int Id;

        [FixedSizeArray(length: 2)]
        internal readonly Point[] Points;

        [FixedSizeArray(length: 2)]
        internal readonly float[] Height;

        [FixedSizeArray(length: 2)]
        internal readonly Colors[] Colors;
    }

    [CodegenMessage]
    internal partial class StringViewElement
    {
        internal int Id;

        internal StringPtr String;
    }

    [CodegenMessage]
    internal partial class StringViewElements
    {
        internal int Id;

        internal StringViewElement Item1;

        internal char Id2;

        internal StringViewElement Item2;
    }

    [CodegenMessage]
    internal partial class StringViewArray
    {
        internal int Id;

        [FixedSizeArray(length: 5)]
        internal readonly StringPtr[] Strings;
    }

    [CodegenMessage]
    internal partial class WideStringViewArray
    {
        internal int Id;

        [FixedSizeArray(length: 5)]
        internal readonly WideStringPtr[] Strings;
    }

    [CodegenMessage]
    internal partial class WideStringMultiMessage
    {
        internal int Id;

        [FixedSizeArray(length: 1)]
        internal readonly WideStringViewArray[] StringMessages;
    }

    [CodegenMessage]
    internal partial class Graph
    {
        [FixedSizeArray(length: 16)]
        internal readonly Point[] Points;
    }

    [CodegenMessage]
    internal partial class OuterGraphs
    {
        internal char Id;

        internal Graph Graph1;

        internal Graph Graph2;
    }
}
