// -----------------------------------------------------------------------
// <copyright file="Merge.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;

namespace Mlos.Streaming
{
    public static class MergeExtensions
    {
        /// <summary>
        /// Merges two IEnumerable collections based on given key.
        /// </summary>
        /// <remarks>
        /// Streamable collections cannot be merge directly. As the collections are pushed based we do not know when can we start comparing the elements.
        /// First we need to aggrate a stream them into a buffer. Once we decide that both buffers are ready we can pass them to the MergeOnKey observerable.
        /// </remarks>
        /// <typeparam name="T1">Element type of the first collection.</typeparam>
        /// <typeparam name="T2">Element type of the second collection.</typeparam>
        /// <typeparam name="TKey">Element type where the stream elements are compared.</typeparam>
        /// <typeparam name="TResult">Result element.</typeparam>
        /// <param name="source"></param>
        /// <param name="keySelector1"></param>
        /// <param name="keySelector2"></param>
        /// <param name="mergeFunc"></param>
        /// <returns></returns>
        public static Streamable<TResult> MergeOnKey<T1, T2, TKey, TResult>(
            this Streamable<IEnumerable<T1>, IEnumerable<T2>> source,
            Func<T1, TKey> keySelector1,
            Func<T2, TKey> keySelector2,
            Func<T1, T2, TResult> mergeFunc)
            where TKey : IComparable<TKey>
        {
            var streamable = new MergeOnKeyImpl<T1, T2, TKey, TResult>(keySelector1, keySelector2, mergeFunc);
            source.Subscribe(streamable.Observed);
            return streamable;
        }

        #region Implementation
        private class MergeOnKeyImpl<T1, T2, TKey, TResult> : Streamable<TResult>, IStreamObserver<IEnumerable<T1>, IEnumerable<T2>>
            where TKey : IComparable<TKey>
        {
            private Func<T1, TKey> keySelector1;
            private Func<T2, TKey> keySelector2;
            private Func<T1, T2, TResult> mergeFunc;

            public MergeOnKeyImpl(Func<T1, TKey> keySelector1, Func<T2, TKey> keySelector2, Func<T1, T2, TResult> mergeFunc)
            {
                this.keySelector1 = keySelector1;
                this.keySelector2 = keySelector2;
                this.mergeFunc = mergeFunc;
            }

            public void Observed(IEnumerable<T1> source1, IEnumerable<T2> source2)
            {
                IEnumerator<T1> enumerator1 = source1.GetEnumerator();
                IEnumerator<T2> enumerator2 = source2.GetEnumerator();

                bool isElement1 = enumerator1.MoveNext();
                bool isElement2 = enumerator2.MoveNext();

                while (true)
                {
                    if (isElement1 && isElement2)
                    {
                        T1 element1 = enumerator1.Current;
                        TKey key1 = keySelector1(element1);

                        T2 element2 = enumerator2.Current;
                        TKey key2 = keySelector2(element2);

                        int compareResult = key1.CompareTo(key2);
                        if (compareResult == 0)
                        {
                            Publish(mergeFunc(element1, element2));

                            isElement1 = enumerator1.MoveNext();
                            isElement2 = enumerator2.MoveNext();
                        }
                        else if (compareResult < 0)
                        {
                            Publish(mergeFunc(element1, default));

                            isElement1 = enumerator1.MoveNext();
                        }
                        else if (compareResult > 0)
                        {
                            Publish(mergeFunc(default, element2));

                            isElement2 = enumerator2.MoveNext();
                        }
                    }
                    else if (isElement1)
                    {
                        Publish(mergeFunc(enumerator1.Current, default));

                        isElement1 = enumerator1.MoveNext();
                    }
                    else if (isElement2)
                    {
                        Publish(mergeFunc(default, enumerator2.Current));

                        isElement2 = enumerator2.MoveNext();
                    }
                    else
                    {
                        break;
                    }
                }
            }

            string IStreamObserver.Inspect()
            {
                return string.Empty;
            }
        }
        #endregion
    }
}
