// -----------------------------------------------------------------------
// <copyright file="Streamable.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.Streaming
{
    /// <summary>
    /// Interface for 'Push' type streams.
    /// </summary>
    /// <remarks>
    /// Interface does not provide subscribe methods to register the observer.
    /// This is implemented in base abstract Streamable class.
    /// </remarks>
    internal interface IStreamable
    {
        /// <summary>
        /// Returns a stream observer.
        /// </summary>
        /// <returns></returns>
        IStreamObserver GetStreamObserver();
    }

    /// <summary>
    /// Base abstract class for 'Push' type streams.
    /// </summary>
    /// <typeparam name="T">Type of the element in the stream.</typeparam>
    public abstract class Streamable<T> : IStreamable
    {
        private Action<T> publish;

        public void Publish(T value)
        {
            publish?.Invoke(value);
        }

        public void Subscribe(IStreamObserver<T> observer)
        {
            publish = observer.Observed;
        }

        public void Subscribe(Action<T> onObserved)
        {
            publish = onObserved;
        }

        IStreamObserver IStreamable.GetStreamObserver()
        {
            return publish?.Target as IStreamObserver;
        }

        public void Inspect()
        {
            IStreamObserver streamObserver = publish.Target as IStreamObserver;

            while (streamObserver != null)
            {
                string result = streamObserver.Inspect();

                IStreamable streamable = streamObserver as IStreamable;

                if (streamable == null)
                {
                    // Last element in the chain.
                    //
                    return;
                }

                // Follow the chain.
                //
                streamObserver = streamable.GetStreamObserver();
            }
        }
    }

    /// <summary>
    /// Base abstract class for 'Push' type streams.
    /// </summary>
    /// <typeparam name="T1">First type of the element in the stream.</typeparam>
    /// <typeparam name="T2">Second type of the element in the stream.</typeparam>
    public abstract class Streamable<T1, T2> : IStreamable
    {
        private Action<T1, T2> publish;

        public void Publish(T1 value1, T2 value2)
        {
            publish?.Invoke(value1, value2);
        }

        public void Subscribe(IStreamObserver<T1, T2> observer)
        {
            publish = observer.Observed;
        }

        public void Subscribe(Action<T1, T2> onObserved)
        {
            publish = onObserved;
        }

        IStreamObserver IStreamable.GetStreamObserver()
        {
            return publish.Target as IStreamObserver;
        }
    }
}
