// -----------------------------------------------------------------------
// <copyright file="IStreamObserver.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.Streaming
{
    /// <summary>
    /// Base interface for observing 'Push' type streams.
    /// </summary>
    public interface IStreamObserver
    {
        /// <summary>
        /// Collect state of the observer
        /// #TODO work in progress.
        /// </summary>
        /// <returns></returns>
        public string Inspect();
    }

    /// <summary>
    /// Interface for observing 'Push' type streams.
    /// </summary>
    /// <typeparam name="T">type of the element in the stream.</typeparam>
    public interface IStreamObserver<T> : IStreamObserver
    {
        void Observed(T value);
    }

    /// <summary>
    /// Interface for observing 'Push' type streams.
    /// </summary>
    /// <typeparam name="T1">First type of the element in the stream.</typeparam>
    /// <typeparam name="T2">Second type of the element in the stream.</typeparam>
    public interface IStreamObserver<T1, T2> : IStreamObserver
    {
        void Observed(T1 value1, T2 value2);
    }
}
