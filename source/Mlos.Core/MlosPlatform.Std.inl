//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: MlosPlatform.Std.inl
//
// Purpose:
//      Provides a platform specific implementation for functions declared in
//      MlosPlatform.h
//
//      This file is expected to be included by the target application, not
//      Mlos.Core.  It is simply provided there as a typical/common reference
//      implementation.
//
//*********************************************************************

#pragma once

#ifdef _WIN64
#include "MlosPlatform.Windows.inl"
#else
#include "MlosPlatform.Linux.inl"
#endif