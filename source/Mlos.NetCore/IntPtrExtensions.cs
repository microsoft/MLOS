// -----------------------------------------------------------------------
// <copyright file="IntPtrExtensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.Core
{
    /// <summary>
    /// IntPtr extension and helper methods.
    /// </summary>
    internal static class IntPtrExtensions
    {
        internal static long Offset(this IntPtr pointerA, IntPtr pointerB)
        {
            return pointerA.ToInt64() - pointerB.ToInt64();
        }
    }
}
