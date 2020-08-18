// -----------------------------------------------------------------------
// <copyright file="CardinatilityEstimate.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.Streaming.Estimators;

namespace Mlos.Streaming
{
    public static class CardinalityEstimateExtensions
    {
        public static Streamable<TSource> CardinalityEstimate<TSource, TValue>(this Streamable<TSource> source, Func<TSource, TValue> selector, double stdError)
        {
            var streamable = new CardinalityEstimateImpl<TSource, TValue>(selector, stdError);
            source.Subscribe(streamable);
            return streamable;
        }

        #region Implementation
        private class CardinalityEstimateImpl<TSource, TValue> : Streamable<TSource>, IStreamObserver<TSource>
        {
            private readonly HyperLogLog hyperLogLog;

            private readonly Func<TSource, TValue> selector;

            public CardinalityEstimateImpl(Func<TSource, TValue> selector, double stdError)
            {
                this.selector = selector;
                hyperLogLog = new HyperLogLog(stdError);
            }

            public void Observed(TSource value)
            {
                TValue result = selector(value);

                hyperLogLog.Add(result);

                Publish(value);
            }

            string IStreamObserver.Inspect()
            {
                return hyperLogLog.Count().ToString();
            }
        }
        #endregion
    }
}
