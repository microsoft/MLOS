// -----------------------------------------------------------------------
// <copyright file="ValueHolder.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.Streaming
{
    /// <summary>
    /// Nullable holder.
    /// </summary>
    /// <typeparam name="T">Type of the stored value.</typeparam>
    internal struct ValueHolder<T>
        where T : notnull, IComparable<T>
    {
        internal bool HasValue;
        internal T Value;
    }
}
