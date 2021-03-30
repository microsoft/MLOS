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

        [Fact]
        public void VerifyMetadataHash()
        {
            TestComponentConfig config = default;
            ulong hashCode = ((ICodegenKey)config).CodegenTypeHash();
            Assert.Equal<ulong>(expected: 0x92ab3b94501efa6c, actual: hashCode);

            Point point = default;
            ulong pointHashCode = ((ICodegenKey)point).CodegenTypeHash();
            Assert.Equal<ulong>(expected: 0x80D34F1D0805C19D, actual: pointHashCode);
        }

        [Fact]
        public void VerifyStringPtrSerialization()
        {
            var obj = new StringsPair
            {
                String1 = { Value = "Test123" },
                String2 = { Value = "Test234" },
            };

            int size = (int)CodegenTypeExtensions.GetSerializedSize(obj);
            Span<byte> byteBuffer = stackalloc byte[size + 1];
            byteBuffer[size] = (byte)'#';

            unsafe
            {
                fixed (byte* pinnedBuffer = &byteBuffer.GetPinnableReference())
                {
                    IntPtr buffer = new IntPtr(pinnedBuffer);

                    CodegenTypeExtensions.Serialize(obj, buffer);

                    MlosUnitTestProxy.StringsPair proxy = default;
                    proxy.Buffer = buffer;

                    Assert.Equal(obj.String1.Value, proxy.String1.Value);
                    Assert.Equal(obj.String2.Value, proxy.String2.Value);
                }
            }

            Assert.Equal((byte)'#', byteBuffer[size]);
        }

        [Fact]
        public void VerifyWideStringPtrSerialization()
        {
            var obj = new WideStringsPair
            {
                String1 = { Value = "Test123" },
                String2 = { Value = "Test234" },
            };

            int size = (int)CodegenTypeExtensions.GetSerializedSize(obj);
            Span<byte> byteBuffer = stackalloc byte[size + 1];
            byteBuffer[size] = (byte)'#';

            unsafe
            {
                fixed (byte* pinnedBuffer = &byteBuffer.GetPinnableReference())
                {
                    IntPtr buffer = new IntPtr(pinnedBuffer);

                    CodegenTypeExtensions.Serialize(obj, buffer);

                    MlosUnitTestProxy.WideStringsPair proxy = default;
                    proxy.Buffer = buffer;

                    Assert.Equal(obj.String1.Value, proxy.String1.Value);
                    Assert.Equal(obj.String2.Value, proxy.String2.Value);
                }
            }

            Assert.Equal((byte)'#', byteBuffer[size]);
        }
    }
}
