// -----------------------------------------------------------------------
// <copyright file="CSharpObjectCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CSharpTypesCodeWriters
{
    /// <summary>
    /// Writes a default constructor for CodegenType classes.
    /// </summary>
    /// <remarks>
    /// CodegenType structures are ignored by this CodeWriter.
    /// </remarks>
    internal class CSharpObjectCodeWriter : CSharpCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType() && sourceType.IsClass;

        /// <inheritdoc />
        public override void WriteBeginFile()
        {
            // Make sure to write the base class file header first.
            //
            base.WriteBeginFile();

            WriteBlock(@"
                using System;
                using System.Runtime.CompilerServices;

                using Mlos.Core;
                using Mlos.SettingsSystem.Attributes;
                using Mlos.SettingsSystem.StdTypes;");
        }

        /// <inheritdoc />
        public override void WriteOpenTypeNamespace(string @namespace)
        {
            WriteLine($"namespace {@namespace}");
            WriteLine("{");

            ++IndentationLevel;
        }

        /// <inheritdoc />
        public override void WriteCloseTypeNamespace(string @namespace)
        {
            --IndentationLevel;
            WriteLine($"}} // end namespace {Constants.ProxyNamespace}.{@namespace}");

            WriteLine();
        }

        /// <inheritdoc />
        public override void WriteComments(CodeComment codeComment)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType);

            string typeName = sourceType.Name;

            WriteBlock($@"
                /// <summary>
                /// Constructor.
                /// </summary>
                public {typeName}()
                {{");

            IndentationLevel++;
        }

        /// <inheritdoc/>
        public override void EndVisitType(Type sourceType)
        {
            IndentationLevel--;
            WriteLine("}");

            WriteCloseTypeDeclaration(sourceType);
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            // Nothing.
            //
            if (!cppField.FieldInfo.FieldType.IsClass &&
                !cppField.FieldInfo.IsFixedSizedArray())
            {
                // Primitive types and structures does not need to be allocated.
                //
                return;
            }

            Type fieldType = cppField.FieldInfo.FieldType;

            if (cppField.FieldInfo.IsFixedSizedArray())
            {
                // Create fixed length array.
                //
                fieldType = fieldType.GetElementType();

                FixedSizeArrayAttribute arrayAttribute = cppField.FieldInfo.GetCustomAttribute<FixedSizeArrayAttribute>();

                WriteBlock($@"this.{cppField.FieldInfo.Name} = new {fieldType.FullName}[{arrayAttribute.Length}];");

                if (fieldType.IsClass)
                {
                    WriteBlock($@"this.{cppField.FieldInfo.Name}.Create();");
                }
            }
            else
            {
                WriteBlock($@"this.{cppField.FieldInfo.Name} = new {fieldType.FullName}();");
            }
        }
    }
}
