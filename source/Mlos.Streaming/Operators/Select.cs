// -----------------------------------------------------------------------
// <copyright file="Select.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.Streaming
{
    public static class SelectExtensions
    {
        public static Streamable<TResult> Select<TSource, TResult>(this Streamable<TSource> source, Func<TSource, TResult> selector)
        {
            var streamable = new SelectImpl<TSource, TResult>(selector);
            source.Subscribe(streamable);
            return streamable;
        }

        #region Implementation
        private class SelectImpl<TSource, TResult> : Streamable<TResult>, IStreamObserver<TSource>
        {
            private readonly Func<TSource, TResult> selector;

            public SelectImpl(Func<TSource, TResult> selector)
            {
                this.selector = selector;
            }

            public void Observed(TSource value)
            {
                TResult result = selector(value);

                Publish(result);
            }

            string IStreamObserver.Inspect()
            {
                return string.Empty;
            }
        }
        #endregion
    }
}
