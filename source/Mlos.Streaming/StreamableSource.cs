// -----------------------------------------------------------------------
// <copyright file="StreamableSource.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Generic;

namespace Mlos.Streaming
{
    /// <summary>
    /// Observerable implementations.
    /// Allows publishing a collections.
    /// </summary>
    /// <typeparam name="T">Collection element type.</typeparam>
    public class StreamableSource<T> : Streamable<T>
    {
        public void Publish(IEnumerable<T> source)
        {
            foreach (T element in source)
            {
                Publish(element);
            }
        }
    }
}
