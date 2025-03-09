from __future__ import annotations
import rich
from colors import print_colorized_exception
import asyncio

import custom_macros.CS_7350 as CS_7350

cs_7350_a1_q2 = CS_7350.cs_7350_a1_q2

cs7350a2 = CS_7350.cs7350a2
cs7350a3 = CS_7350.cs7350a3
cs7350a4 = CS_7350.cs7350a4

def try_async_macro(macro):
    try:
        asyncio.create_task(macro())
    except Exception as e:
        print_colorized_exception(e)



def MACRO_1():
    rich.print('[bold on #004477]      MACRO_1      [/]')
    try_async_macro(cs7350a4.parse_rubric)
    try_async_macro(cs7350a4.parse_student_assignments)


def MACRO_2():
    rich.print('[bold on #004477]      MACRO_2      [/]')
    try_async_macro(cs7350a4.make_entries)


def MACRO_3():
    rich.print('[bold on #004477]      MACRO_3      [/]')
    try_async_macro(cs7350a4.grade_with_llm)


def MACRO_4():
    rich.print('[bold on #004477]      MACRO_4      [/]')
    try_async_macro(cs7350a4.calculate_points)



def MACRO_5():
    rich.print('[bold on #004477]      MACRO_5      [/]')
    try_async_macro(cs7350a4.calculate_points)

