// -----------------------------------------------------------------------
// <copyright file="HyperLogLog.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;

namespace Mlos.Streaming.Estimators
{
    /// <summary>
    /// Implementation of HyperLogLog algorithm. Aproximates the number of distinct elements in the multiset.
    /// </summary>
    /// <remarks>
    /// More details:
    /// http://algo.inria.fr/flajolet/Publications/FlFuGaMe07.pdf
    /// https://en.wikipedia.org/wiki/HyperLogLog.
    /// </remarks>
    public class HyperLogLog
    {
        private static int GetRank(uint hash, int max)
        {
            int r = 1;
            while ((hash & 1) == 0 && r <= max)
            {
                ++r;
                hash >>= 1;
            }

            return r;
        }

        public static uint GetHashCode(string text)
        {
            uint hash = 0;

            for (int i = 0, l = text.Length; i < l; i++)
            {
                hash += text[i];
                hash += hash << 10;
                hash ^= hash >> 6;
            }

            hash += hash << 3;
            hash ^= hash >> 6;
            hash += hash << 16;

            return hash;
        }

        private readonly double mapSize;
        private readonly double alphaM;
        private readonly int kComplement;
        private readonly Dictionary<int, int> lookup = new Dictionary<int, int>();

        public HyperLogLog(double stdError)
        {
            mapSize = 1.04 / stdError;
            double k = (long)Math.Ceiling(Math.Log2(mapSize * mapSize));

            kComplement = 32 - (int)k;
            mapSize = (long)Math.Pow(2, k);

            // Aproximate alpha m value with the following formula:
            //
            alphaM = mapSize == 16 ? 0.673
                  : mapSize == 32 ? 0.697
                  : mapSize == 64 ? 0.709
                  : 0.7213 / (1 + (1.079 / mapSize));

            for (int i = 0; i < mapSize; i++)
            {
                lookup[i] = 0;
            }
        }

        public double Count()
        {
            double c = 0;
            double estimator;

            for (var i = 0; i < mapSize; i++)
            {
                c += 1.0 / Math.Pow(2, lookup[i]);
            }

            estimator = alphaM * mapSize * mapSize / c;

            // Make corrections & smoothen things.
            if (estimator <= 5.0 * mapSize / 2.0)
            {
                // Calculate register count with zero value.
                //
                double regWithZeroCount = 0;

                for (var i = 0; i < mapSize; i++)
                {
                    if (lookup[i] == 0)
                    {
                        regWithZeroCount++;
                    }
                }

                if (regWithZeroCount > 0)
                {
                    estimator = mapSize * Math.Log(mapSize / regWithZeroCount);
                }
            }
            else if (estimator > (uint.MaxValue / 30.0))
            {
                // Very large cardinalities approaching the limit of the size of the registers.
                //
                estimator = -uint.MaxValue * Math.Log(1 - (estimator / uint.MaxValue));
            }

            return (int)estimator;
        }

        public void Add(object value)
        {
            uint hashCode = GetHashCode(value.ToString());
            int j = (int)(hashCode >> kComplement);

            lookup[j] = Math.Max(lookup[j], GetRank(hashCode, kComplement));
        }
    }
}
