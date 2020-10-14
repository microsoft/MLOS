//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: stdafx.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

// Include GTest framework.
//
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable: 4251 4275 4244)
#endif
#include "gtest/gtest.h"
#ifdef _MSC_VER
#pragma warning(pop)
#endif

#include <array>
#include <functional>
#include <future>

// Mlos.Core.
//
#include "Mlos.Core.h"

// Global dispatch table.
//
#include "GlobalDispatchTable.h"

// Mlos.Core.
//
#include "Mlos.Core.inl"

// Macros.
//
#define UNUSED(x) (void)x

using namespace Mlos::Core;
