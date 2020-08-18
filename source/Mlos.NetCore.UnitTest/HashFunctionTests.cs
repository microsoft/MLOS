// -----------------------------------------------------------------------
// <copyright file="HashFunctionTests.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using Mlos.Core.Collections;

using Xunit;

namespace Mlos.NetCore.UnitTest
{
    public class HashFunctionTests
    {
        [Fact]
        public void FNV1()
        {
            byte[] arr = new byte[] { 1, 2, 3, 4, 5 };

            var span = new ReadOnlySpan<byte>(arr);

            ReadOnlySpan<uint> span2 = MemoryMarshal.Cast<byte, uint>(span);

            Dictionary<uint, int> dict1 = new Dictionary<uint, int>();
            Dictionary<ulong, int> dict2 = new Dictionary<ulong, int>();

            for (int i = 0; i < 1000; i++)
            {
                {
                    uint resUInt = default(FNVHash<uint>).GetHashValue(i);

                    resUInt = resUInt % 1024;

                    if (dict1.ContainsKey(resUInt) == false)
                    {
                        dict1.Add(resUInt, 0);
                    }

                    dict1[resUInt]++;
                }

                {
                    uint resUInt = default(FNVHash<uint>).GetHashValue(i);

                    resUInt = resUInt % 1024;

                    if (dict2.ContainsKey(resUInt) == false)
                    {
                        dict2.Add(resUInt, 0);
                    }

                    dict2[resUInt]++;
                }
            }
        }

        [Fact]
        public void MurMur2Hash()
        {
            uint a = MurMurHash2aFunction<uint, UIntHashValueOperators>.GetHashValue(MemoryMarshal.Cast<char, byte>("abc".AsSpan()));
        }
    }
}
