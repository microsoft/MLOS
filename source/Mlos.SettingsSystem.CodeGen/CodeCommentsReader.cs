// -----------------------------------------------------------------------
// <copyright file="CodeCommentsReader.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Xml;

namespace Mlos.SettingsSystem.CodeGen
{
    /// <summary>
    /// Read code comments from xml resource embedded in script assembly.
    /// </summary>
    internal class CodeCommentsReader
    {
        private readonly Dictionary<string, CodeComment> codeComments = new Dictionary<string, CodeComment>();

        /// <summary>
        /// Load code comments from stream.
        /// </summary>
        /// <param name="xmlDocStream">Stream containing assembly comments in xml format.</param>
        public void LoadFromAssembly(Stream xmlDocStream)
        {
            // Remove all existing comments.
            //
            codeComments.Clear();

            XmlDocument xmlDocument = new XmlDocument();

            // Prevent external entities to avoid secure resolver warnings.
            //
            xmlDocument.XmlResolver = null;

            using XmlTextReader xmlReader = new XmlTextReader(xmlDocStream) { DtdProcessing = DtdProcessing.Prohibit };
            {
                xmlDocument.Load(xmlReader);
            }

            // Parse comments and store it in dictionary.
            foreach (XmlNode memberXmlNode in xmlDocument.SelectNodes("/doc/members/member"))
            {
                // Parse comment.
                var codeComment = new CodeComment
                {
                    Name = memberXmlNode.Attributes["name"].Value,
                    Summary = memberXmlNode.SelectSingleNode("summary")?.InnerText.Trim(),
                    Remarks = memberXmlNode.SelectSingleNode("remarks")?.InnerText.Trim(),
                    Returns = memberXmlNode.SelectSingleNode("returns")?.InnerText.Trim(),
                };

                // Parse parameters if any.
                XmlNodeList paramXmlNodeList = memberXmlNode.SelectNodes("param");
                if (paramXmlNodeList != null)
                {
                    var codeComments = new List<CodeComment>();

                    foreach (XmlNode paramXmlNode in paramXmlNodeList)
                    {
                        string paramName = paramXmlNode.Attributes["name"].Value;

                        codeComments.Add(
                            new CodeComment
                            {
                                Name = paramName,
                                Summary = paramXmlNode.InnerText.Trim(),
                            });
                    }

                    codeComment.Parameters = codeComments;
                }

                codeComments.Add(codeComment.Name, codeComment);
            }
        }

        /// <summary>
        /// Get code comment for given method.
        /// </summary>
        /// <param name="methodInfo"></param>
        /// <returns></returns>
        internal CodeComment? GetCodeComment(MethodInfo methodInfo)
        {
            string arguments = string.Empty;

            if (methodInfo.GetParameters().Any())
            {
                arguments = "(" + string.Join(",", methodInfo.GetParameters().Select(r => r.ParameterType.ToString())) + ")";
            }

            return GetCodeComment(string.Format("M:{0}.{1}{2}", methodInfo.DeclaringType.FullName, methodInfo.Name, arguments));
        }

        /// <summary>
        /// Get code comment for given field.
        /// </summary>
        /// <param name="fieldInfo"></param>
        /// <returns></returns>
        internal CodeComment? GetCodeComment(FieldInfo fieldInfo)
        {
            return GetCodeComment($"F:{fieldInfo.DeclaringType.FullName}.{fieldInfo.Name}");
        }

        /// <summary>
        /// Get code comment for given type.
        /// </summary>
        /// <param name="type"></param>
        /// <returns></returns>
        internal CodeComment? GetCodeComment(Type type)
        {
            return GetCodeComment($"T:{type.FullName}");
        }

        private CodeComment? GetCodeComment(string searchString)
        {
            if (codeComments.TryGetValue(searchString, out CodeComment codeComment))
            {
                return codeComment;
            }
            else
            {
                return null;
            }
        }
    }

    /// <summary>
    /// Structure describing a code comment.
    /// </summary>
    internal struct CodeComment
    {
        /// <summary>
        /// Gets or sets name of the function, property or field where comment was written.
        /// </summary>
        public string Name { get; internal set; }

        /// <summary>
        /// Gets or sets comment summary.
        /// </summary>
        public string Summary { get; internal set; }

        /// <summary>
        /// Gets or sets comment for remarks statement.
        /// </summary>
        public string Remarks { get; internal set; }

        /// <summary>
        /// Gets or sets comment for return statement.
        /// </summary>
        public string Returns { get; internal set; }

        /// <summary>
        /// Gets or sets comments for function parameters.
        /// </summary>
        public List<CodeComment> Parameters { get; internal set; }

        /// <summary>
        /// Format code comment to string.
        /// </summary>
        /// <returns></returns>
        public override string ToString()
        {
            var sb = new StringBuilder();

            if (Summary != null)
            {
                sb.Append(Summary);
            }

            if (Remarks != null)
            {
                sb.Append(Remarks);
            }

            if (Returns != null)
            {
                sb.Append(Returns);
            }

            return sb.ToString();
        }
    }
}
