// -----------------------------------------------------------------------
// <copyright file="CodegenTypeTests.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.Core;
using Mlos.Core.Collections;
using Mlos.UnitTest;

using Xunit;

using MlosUnitTestProxy = Proxy.Mlos.UnitTest;

namespace Mlos.NetCore.UnitTest
{
    public class CodegenTypeTests
    {
        internal struct VerifyPrimaryKeyHashFunctions<THash>
            where THash : IHash<uint>
        {
            internal void ComparePrimaryKey()
            {
                TestComponentConfig config = default;
                config.ComponentType = 1;
                config.Category = 2;
                config.Delay = 3.14;

                TestComponentConfig.CodegenKey configKey = default;
                configKey.ComponentType = 1;
                configKey.Category = 2;

                TestComponentConfig.CodegenKey configInvalidKey = default;
                configInvalidKey.ComponentType = 1;
                configInvalidKey.Category = 3;

                MlosUnitTestProxy.TestComponentConfig configProxy = default;

                unsafe
                {
                    IntPtr ptr = new IntPtr(&config);
                    configProxy.Buffer = ptr;
                }

                uint hashValue1 = configProxy.GetKeyHashValue<THash>();
                uint hashValue2 = configKey.GetKeyHashValue<THash>();
                uint hashValue3 = configInvalidKey.GetKeyHashValue<THash>();

                Assert.Equal(hashValue1, hashValue2);
                Assert.NotEqual(hashValue1, hashValue3);
            }
        }

        [Fact]
        public void VerifyConfigKeyHashValue()
        {
            VerifyPrimaryKeyHashFunctions<FNVHash<uint>> test;
            test.ComparePrimaryKey();
        }
    }
}
