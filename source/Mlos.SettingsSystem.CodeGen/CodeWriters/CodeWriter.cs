// -----------------------------------------------------------------------
// <copyright file="CodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Linq;
using System.Text;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters
{
    /// <summary>
    /// Base class for all code writers.
    /// </summary>
    internal abstract class CodeWriter
    {
        /// <summary>
        /// Does code writer support source type.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        public abstract bool Accept(Type sourceType);

        /// <summary>
        /// Write beginning of the file.
        /// </summary>
        public abstract void WriteBeginFile();

        /// <summary>
        /// Write end of the file.
        /// </summary>
        public abstract void WriteEndFile();

        /// <summary>
        /// Write namespace opening before type definition.
        /// </summary>
        /// <param name="namespace"></param>
        public abstract void WriteOpenTypeNamespace(string @namespace);

        /// <summary>
        /// Write namespace closing after type definition.
        /// </summary>
        /// <param name="namespace"></param>
        public abstract void WriteCloseTypeNamespace(string @namespace);

        /// <summary>
        /// Write code comments.
        /// </summary>
        /// <param name="codeComment"></param>
        public abstract void WriteComments(CodeComment codeComment);

        /// <summary>
        /// Write class beginning.
        /// </summary>
        /// <param name="sourceType"></param>
        public abstract void BeginVisitType(Type sourceType);

        /// <summary>
        /// Write class closing brackets.
        /// </summary>
        /// <param name="sourceType"></param>
        public abstract void EndVisitType(Type sourceType);

        /// <summary>
        /// Write a struct field definition.
        /// </summary>
        /// <param name="cppField"></param>
        public abstract void VisitField(CppField cppField);

        /// <summary>
        /// Writes a blank line.
        /// </summary>
        protected void WriteLine() => stringBuilder.AppendLine();

        /// <summary>
        /// Writes an indented line with the given string.
        /// </summary>
        /// <param name="value"></param>
        protected void WriteLine(string value) => stringBuilder.AppendLine($"{IndentationString}{value}");

        /// <summary>
        /// Writes an indented block of lines.
        /// </summary>
        /// <param name="lines">One or more blocks of lines to append.</param>
        /// <remarks>
        /// Expected to be used with block string literals like so:
        /// <![CDATA[
        /// WriteBlock($@"
        /// // Here's a block of comments and code.
        /// //
        /// cout << "Hello World" << endl;
        /// ");
        /// ]]>
        /// As such the first empty line is trimmed.
        /// </remarks>
        protected void WriteBlock(params string[] lines)
        {
            // If given an array of lines, join then by newlines, then split
            // them again to get a single flat array of lines.
            //
            lines = string.Join(Environment.NewLine, lines).Split(new string[] { Environment.NewLine, "\r" }, StringSplitOptions.RemoveEmptyEntries);

            string firstNonEmptyLine = lines.FirstOrDefault(r => !string.IsNullOrEmpty(r));

            int startIndex = 0;
            if (firstNonEmptyLine != null)
            {
                startIndex = firstNonEmptyLine.Select((c, index) => (!char.IsWhiteSpace(c) && !char.IsControl(c)) ? index : -1).FirstOrDefault(r => r != -1);
            }

            // Add each line to the output, making sure that it is indented to
            // the appropriate level.
            //
            for (int i = 0; i < lines.Length; i++)
            {
                if (i == 0 && string.IsNullOrEmpty(lines[0]))
                {
                    // Skip the first empty line.
                    //
                    continue;
                }
                else if (string.IsNullOrWhiteSpace(lines[i]))
                {
                    // Do not indent empty lines.
                    //
                    WriteLine();
                }
                else
                {
                    WriteLine(lines[i].Substring(startIndex));
                }
            }

            WriteLine();
        }

        /// <summary>
        /// Return a generated code as a string.
        /// </summary>
        /// <returns></returns>
        public string GetGeneratedString() { return stringBuilder.ToString(); }

        /// <summary>
        /// Gets an output file postfix.
        /// </summary>
        public abstract string FilePostfix
        {
            get;
        }

        /// <summary>
        /// What type of character to use for indentation (space).
        /// </summary>
        private const char IndentationChar = ' ';

        /// <summary>
        /// How many spaces to use for each level of indentation.
        /// </summary>
        private const int IndentationScalar = 4;

        private readonly StringBuilder stringBuilder = new StringBuilder();

        /// <summary>
        /// Gets or sets indentation level.
        /// </summary>
        protected int IndentationLevel { get; set; }

        /// <summary>
        /// Gets an indentation string.
        /// </summary>
        private string IndentationString => new string(IndentationChar, IndentationLevel * IndentationScalar);
    }
}
