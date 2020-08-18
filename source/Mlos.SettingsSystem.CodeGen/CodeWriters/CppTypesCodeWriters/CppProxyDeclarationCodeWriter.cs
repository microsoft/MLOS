// -----------------------------------------------------------------------
// <copyright file="CppProxyDeclarationCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppTypesCodeWriters
{
    /// <summary>
    /// Code writer class for proxy view declaration.
    /// </summary>
    internal class CppProxyDeclarationCodeWriter : CppCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <summary>
        /// Write beginning of the file.
        /// </summary>
        /// <remarks>
        /// Proxy structures are defined in namespace Proxy.
        /// </remarks>
        public override void WriteBeginFile()
        {
            WriteBlock(@"
                /// Declaration for all proxy structures.
                ///");

            WriteOpenTypeNamespace(Constants.ProxyNamespace);
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            WriteCloseTypeNamespace(Constants.ProxyNamespace);
            WriteLine();
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            string cppClassName = sourceType.Name;

            WriteLine($"struct {cppClassName};");
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
        }

        /// <inheritdoc />
        public override void EndVisitType(Type sourceType)
        {
        }

        /// <inheritdoc />
        public override void WriteComments(CodeComment codeComment)
        {
        }
    }
}
