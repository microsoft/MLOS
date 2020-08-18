// -----------------------------------------------------------------------
// <copyright file="Aggregates.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Linq;

namespace Mlos.Streaming
{
    public static class AggregatesExtensions
    {
        public static Streamable<T> Min<T>(this Streamable<T> source)
            where T : IComparable<T>
        {
            var streamable = new MinImpl<T>();
            source.Subscribe(streamable);
            return streamable;
        }

        public static Streamable<T> Min<T>(this Streamable<IEnumerable<T>> source)
            where T : IComparable<T>
        {
            var streamable = new MinEnumerableImpl<T>();
            source.Subscribe(streamable);
            return streamable;
        }

        public static Streamable<T> Max<T>(this Streamable<T> source)
            where T : IComparable<T>
        {
            var streamable = new MaxImpl<T>();
            source.Subscribe(streamable);
            return streamable;
        }

        public static Streamable<T> Max<T>(this Streamable<IEnumerable<T>> source)
            where T : IComparable<T>
        {
            var streamable = new MaxEnumerableImpl<T>();
            source.Subscribe(streamable);
            return streamable;
        }

        #region Implementation
        private class MinImpl<T> : Streamable<T>, IStreamObserver<T>
            where T : IComparable<T>
        {
            private ValueHolder<T> minValue = default;

            public void Observed(T value)
            {
                if (!minValue.HasValue || minValue.Value.CompareTo(value) > 0)
                {
                    minValue.Value = value;
                    minValue.HasValue = true;
                }

                Publish(value);
            }

            string IStreamObserver.Inspect()
            {
                return minValue.ToString();
            }
        }

        private class MinEnumerableImpl<T> : Streamable<T>, IStreamObserver<IEnumerable<T>>
            where T : IComparable<T>
        {
            private ValueHolder<T> minValue = default;

            public void Observed(IEnumerable<T> collection)
            {
                T value = collection.Min();

                if (!minValue.HasValue || minValue.Value.CompareTo(value) > 0)
                {
                    minValue.Value = value;
                    minValue.HasValue = true;
                }

                Publish(value);
            }

            string IStreamObserver.Inspect()
            {
                return minValue.ToString();
            }
        }

        private class MaxImpl<T> : Streamable<T>, IStreamObserver<T>
            where T : IComparable<T>
        {
            private ValueHolder<T> maxValue = default;

            public void Observed(T value)
            {
                if (!maxValue.HasValue || maxValue.Value.CompareTo(value) < 0)
                {
                    maxValue.Value = value;
                    maxValue.HasValue = true;
                }

                Publish(value);
            }

            string IStreamObserver.Inspect()
            {
                return maxValue.ToString();
            }
        }

        private class MaxEnumerableImpl<T> : Streamable<T>, IStreamObserver<IEnumerable<T>>
            where T : IComparable<T>
        {
            private ValueHolder<T> maxValue = default;

            public void Observed(IEnumerable<T> collection)
            {
                T value = collection.Max();

                if (!maxValue.HasValue || maxValue.Value.CompareTo(value) > 0)
                {
                    maxValue.Value = value;
                    maxValue.HasValue = true;
                }

                Publish(value);
            }

            string IStreamObserver.Inspect()
            {
                return maxValue.ToString();
            }
        }
        #endregion
    }
}
