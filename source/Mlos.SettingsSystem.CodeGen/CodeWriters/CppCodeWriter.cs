// -----------------------------------------------------------------------
// <copyright file="CppCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Linq;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters
{
    /// <summary>
    /// Base class for writing cpp classes.
    /// </summary>
    internal abstract class CppCodeWriter : CodeWriter
    {
        /// <inheritdoc />
        public override void WriteOpenTypeNamespace(string @namespace)
        {
            foreach (string subNamespace in @namespace.Split('.'))
            {
                WriteLine($"namespace {subNamespace}");
                WriteLine("{");
            }

            WriteLine();
        }

        /// <inheritdoc />
        public override void WriteCloseTypeNamespace(string @namespace)
        {
            WriteLine();

            foreach (string subNamespace in @namespace.Split('.').Reverse())
            {
                WriteLine("} // end namespace " + subNamespace);
            }

            WriteLine();
        }

        /// <inheritdoc />
        public override void WriteComments(CodeComment codeComment)
        {
            WriteLine();

            foreach (string comment in new[] { codeComment.Summary, codeComment.Remarks })
            {
                if (comment == null)
                {
                    continue;
                }

                foreach (string lineComment in comment.Split(new[] { Environment.NewLine }, StringSplitOptions.None))
                {
                    WriteLine($"// {lineComment.Trim()}");
                }

                WriteLine("//");
            }
        }

        /// <inheritdoc />
        public override void EndVisitType(Type sourceType)
        {
            IndentationLevel--;

            WriteLine("}; // end type " + sourceType.Name);
            WriteLine();
        }

        /// <inheritdoc />
        public override string FilePostfix => "_base.h";
    }
}
