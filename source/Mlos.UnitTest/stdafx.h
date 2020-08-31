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
#pragma warning(push)
#pragma warning(disable: 4996 4251 4275 4244)
#include "gtest/gtest.h"
#pragma warning(pop)

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

using namespace Mlos::Core;
