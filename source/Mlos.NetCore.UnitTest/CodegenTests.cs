// -----------------------------------------------------------------------
// <copyright file="CodegenTests.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.Core;
using Mlos.UnitTest;
using Xunit;

namespace Mlos.NetCore.UnitTest
{
    public class CodegenTests
    {
        [Fact]
        public void VerifyMetadataHash()
        {
            TestComponentConfig config = default;
            ulong hashCode = ((ICodegenKey)config).CodegenTypeHash();
            Assert.Equal<ulong>(0x92ab3b94501efa6c, hashCode);

            Point point = default;
            ulong pointHashCode = ((ICodegenKey)point).CodegenTypeHash();
            Assert.Equal<ulong>(0x7b7fb0279242f8d7, pointHashCode);
        }
    }
}
