// -----------------------------------------------------------------------
// <copyright file="DummyTests.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Generic;
using System.Linq;

using Mlos.Streaming;

using Xunit;

namespace Mlos.NetCore.UnitTest
{
    public class DummyTests
    {
        [Fact]
        [Trait("Category", "SkipForCI")]
        public void TestSkipped()
        {
            // This test is intended to be skipped and is only here to allow the
            // other tests to be matched when we use a default filter of
            // --filter='Category!=SkipForCI'.
        }
    }
}
