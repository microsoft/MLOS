// -----------------------------------------------------------------------
// <copyright file="Join.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Generic;

namespace Mlos.Streaming
{
    public static partial class Join
    {
        /// <summary>
        /// Brings two observerable streams into two buffers.
        /// Once any of the buffers reaches given capacity, both buffers are published as collections.
        /// </summary>
        /// <typeparam name="T1">Element type of the first Streamable stream.</typeparam>
        /// <typeparam name="T2">Element type of the second Streamable stream.</typeparam>
        /// <param name="source1"></param>
        /// <param name="source2"></param>
        /// <param name="bufferSize"></param>
        /// <returns></returns>
        public static Streamable<IEnumerable<T1>, IEnumerable<T2>> CombineIntoBuffer<T1, T2>(Streamable<T1> source1, Streamable<T2> source2, int bufferSize)
        {
            var streamable = new CombineIntoBufferImpl<T1, T2>(bufferSize);
            source1.Subscribe(streamable.Observed1);
            source2.Subscribe(streamable.Observed2);
            return streamable;
        }

        #region Implementation
        private class CombineIntoBufferImpl<T1, T2> : Streamable<IEnumerable<T1>, IEnumerable<T2>>
        {
            private int bufferSize;
            private List<T1> collection1 = new List<T1>();
            private List<T2> collection2 = new List<T2>();

            internal CombineIntoBufferImpl(int bufferSize)
            {
                this.bufferSize = bufferSize;
            }

            internal void Observed1(T1 value)
            {
                collection1.Add(value);

                if (collection1.Count + collection2.Count == bufferSize)
                {
                    Publish(collection1, collection2);
                    collection1.Clear();
                    collection2.Clear();
                }
            }

            internal void Observed2(T2 value)
            {
                collection2.Add(value);

                if (collection1.Count + collection2.Count == bufferSize)
                {
                    Publish(collection1, collection2);
                    collection1.Clear();
                    collection2.Clear();
                }
            }
        }
        #endregion
    }
}
