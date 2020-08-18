// -----------------------------------------------------------------------
// <copyright file="Buffers.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Generic;
using System.Linq;

namespace Mlos.Streaming
{
    public static class StreamableBuffersExtensions
    {
        public static Streamable<IEnumerable<T>> Buffer<T>(this Streamable<T> source, int bufferSize)
        {
            var streamable = new BufferImpl<T>(bufferSize);
            source.Subscribe(streamable);
            return streamable;
        }

        #region Implementation
        private class BufferImpl<T> : Streamable<IEnumerable<T>>, IStreamObserver<T>
        {
            private int bufferSize;
            private List<T> collection = new List<T>();

            public BufferImpl(int bufferSize)
            {
                this.bufferSize = bufferSize;
            }

            public void Observed(T value)
            {
                collection.Add(value);

                if (collection.Count == bufferSize)
                {
                    Publish(collection);
                    collection.Clear();
                }
            }

            string IStreamObserver.Inspect()
            {
                return $"bufferSize:{collection.Count}";
            }
        }
        #endregion
    }
}
