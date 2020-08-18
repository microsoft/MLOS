// -----------------------------------------------------------------------
// <copyright file="Consume.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.Streaming
{
    public static class ConsumeExtensions
    {
        public static void Consume<T>(this Streamable<T> source, Action<T> action)
        {
            var streamable = new ConsumeImpl<T>(action);
            source.Subscribe(streamable);
        }

        #region IStreamObserver implementation
        private class ConsumeImpl<T> : IStreamObserver<T>
        {
            private Action<T> action;

            internal ConsumeImpl(Action<T> action)
            {
                this.action = action;
            }

            public string Inspect()
            {
                return string.Empty;
            }

            public void Observed(T value)
            {
                action?.Invoke(value);
            }
        }
        #endregion
    }
}
