from __future__ import annotations
import pyperclip
import rich
from colors import print_colorized_exception
import re
from keymapperctl import input_raw, output_raw
import asyncio
from pathlib import Path
from enum import Enum

import os
from openai import AsyncOpenAI


client = AsyncOpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)


async def ask_llm(prompt: str, model: str = "gpt-4o-mini"):
    rich.print('[#ffff00]  [/]    ask_llm      [#ffff00]  [/]')
    completion = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful teaching assistant grading student answers."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return completion.choices[0].message.content


async def cs_7350_a1_q2():
    '''
    macro to grade cs 7350 assignment 1 question 2

    place cursor on the line with the student answer, e.g.

    9 2 3 20 4 8 7 11 5 12 15 1 13 10 19 18 17 14 16 6


    run macro

    macro will copy the current line to the clipboard
    remove all non-numeric characters
    compute the levenshtein distance between the student answer and the ground truth
    then print the student score in the following format

> - Your answer: 9 2 3 20 4 8 7 11 5 12 15 1 13 10 19 18 17 14 16 6
> - True answer: 9 2 3 20 4 8 7 11 5 12 15 1 13 10 19 18 17 14 16 6
> - The levenshtein distance between your answer and the correct answer is **0**.
> - see https://en.wikipedia.org/wiki/Levenshtein_distance
>
> - Points = 10 - max(10, levenshtein_distance / 2)
> - <mark>Points = 10</mark>

    '''

    def replace_non_numeric(s):
        # Use regex to replace non-numeric characters with a space
        return re.sub(r'[^0-9]', ' ', s)

    def levenshtein_distance(list1, list2):
        len1, len2 = len(list1), len(list2)

        # Create a 2D DP array to store distances
        dp = [[0 for _ in range(len2 + 1)] for _ in range(len1 + 1)]

        # Initialize the first row and column
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j

        # Compute the distance
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if list1[i - 1] == list2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]  # No change needed
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j],  # Deletion
                                       dp[i][j - 1],  # Insertion
                                       dp[i - 1][j - 1])  # Substitution

        return dp[len1][len2]

    output_raw('Control{C}')

    await asyncio.sleep(0.2)

    ground_truth = '9 2 3 20 4 8 7 11 5 12 15 1 13 10 19 18 17 14 16 6'

    clip = pyperclip.paste()
    student_answer = replace_non_numeric(clip)

    ground_truth_list = ground_truth.split()
    student_answer_list = student_answer.split()
    student_answer = ' '.join(student_answer_list)

    distance = levenshtein_distance(ground_truth_list, student_answer_list)
    print(f"Levenshtein Distance: {distance}")
    print('<mark>')
    response = f'''

> - Your answer: {student_answer}
> - True answer: {ground_truth}
> - The levenshtein distance between your answer and the correct answer is **{distance}**.
> - see https://en.wikipedia.org/wiki/Levenshtein_distance
>
> - Points = 10 - max(10, levenshtein_distance / 2)
> - <mark>Points = {10 - min(10, distance // 2)}</mark>
'''

    print(response)
    pyperclip.copy(response)

    await asyncio.sleep(0.2)

    output_raw('Control{V}')


def select_all_copy():
    input_raw('Control{A} 20ms Control{C}')


class QuestionStatus(Enum):
    TO_BE_GRADED = 'TO_BE_GRADED'
    GRADED = 'GRADED'
    GRADING = 'GRADING'
    ERROR = 'ERROR'


NUM_QUESTIONS = 5
QUESTIONS_TO_GRADE = {3: 'gpt-4o-mini', 4: 'gpt-4o-mini', 5: 'gpt-4o-mini'}


class Entry:

    llm_semaphore = asyncio.Semaphore(1)
    lock = asyncio.Lock()

    def __init__(self, filename, content: str):
        self.filename = filename
        self.content = content
        self.student_answer_template = '## Question {} Student Answer'
        self.question_start_template = '## Question {} (20 points)'
        self.prompt_file = '/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-1/Assignment-1-prompt.md'
        self.question_file_template = '/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-1/Assignment-1-q{}.md'
        self.sections = self.parse_sections()

        self.question_statuses: dict[int, QuestionStatus] = {}
        self.question_statuses = {
            i: QuestionStatus.TO_BE_GRADED for i in range(1, NUM_QUESTIONS + 1)}

        self.prompts = self.prepare_prompts()
        self.responses = {}

    def prepare_prompts(self):
        prompts = {}
        ANSWER_START = '\n>>> START\n'
        ANSWER_END = '\n>>> END\n'

        with open(self.prompt_file, 'r') as file:
            main_prompt = file.read()

        for question_number, model in QUESTIONS_TO_GRADE.items():
            question_file = self.question_file_template.format(question_number)

            with open(question_file, 'r') as file:
                question_prompt = file.read()

            section_name = self.student_answer_template.format(question_number)
            student_answer = self.sections[section_name]
            student_answer = '\n'.join(student_answer)

            prompts[section_name] = main_prompt + \
                question_prompt + \
                ANSWER_START + \
                student_answer + \
                ANSWER_END

        for section_name, prompt in prompts.items():
            rich.print(f'[bold on #004477]    {section_name}  [/]')
            print(prompt)

        return prompts

    def parse_sections(self):
        sections = {}
        lines = self.content.split('\n')

        section_start = 0
        current_question_number = 1

        looking_for = 'STUDENT_ANSWER'  # QUESTION_START

        for line_num, line in enumerate(lines):
            line = line.strip()
            if looking_for == 'STUDENT_ANSWER':
                if line == self.student_answer_template.format(current_question_number):
                    section_name = self.question_start_template.format(
                        current_question_number)
                    sections[section_name] = lines[section_start:line_num]
                    section_start = line_num
                    looking_for = 'QUESTION_START'
                    current_question_number += 1
            elif looking_for == 'QUESTION_START':
                if line == self.question_start_template.format(current_question_number):
                    section_name = self.student_answer_template.format(
                        current_question_number-1)
                    sections[section_name] = lines[section_start:line_num]
                    section_start = line_num
                    looking_for = 'STUDENT_ANSWER'

        # final section
        section_name = self.student_answer_template.format(
            current_question_number-1)
        sections[section_name] = lines[section_start:]

        bad_parse_result = False

        if len(sections) != NUM_QUESTIONS * 2:
            bad_parse_result = True

        for section_name, section_lines in sections.items():
            if len(section_lines) < 3:
                bad_parse_result = True

        if bad_parse_result:

            rich.print(f'[bold on #ff4477]  {self.filename}  [/]')
            for section_name, section_lines in sections.items():
                rich.print(f'[bold on #ff4477]    {section_name} : {
                    len(section_lines)} lines   [/]')

        return sections

    async def grade_with_llm(self, question_number: int):
        async with Entry.lock:
            if self.question_statuses[question_number] != QuestionStatus.TO_BE_GRADED:
                rich.print(f'[bold on #ff4477]  {self.filename}  [/]')
                rich.print(f'[bold on #ff4477]  question {
                           question_number} is already being graded  [/]')
                return
            self.question_statuses[question_number] = QuestionStatus.GRADING

        async with Entry.llm_semaphore:

            section_name = self.student_answer_template.format(question_number)
            prompt = self.prompts[section_name]
            model = QUESTIONS_TO_GRADE[question_number]
            response = await ask_llm(prompt, model)
            self.responses[section_name] = response
            print(response)

            async with Entry.lock:
                self.question_statuses[question_number] = QuestionStatus.GRADED

            rich.print(f'[bold on #004477] {self.filename}\n   question {
                question_number} done grading  [/]')


class CS7350A1:
    '''
    All should be done in the context of vscode
    '''

    def __init__(self):
        self.entries: dict[str, Entry] = {}

    async def get_filename(self):
        output_raw('(Control){G} C')
        await asyncio.sleep(0.05)
        filepath = pyperclip.paste()
        filename = Path(filepath).name
        return filename

    async def select_all_copy(self):
        output_raw('Control{A} 20ms Control{C}')
        await asyncio.sleep(0.05)
        content = pyperclip.paste()
        return content

    async def prepare_prompt(self):
        filename = await self.get_filename()
        content = await self.select_all_copy()
        self.entries[filename] = Entry(filename, content)

        rich.print(f'[bold on #004477]  entries: {
                   len(self.entries)}  [/]')

        for entry_name, entry in self.entries.items():
            rich.print(f'[bold on #004477]    {entry_name}    [/]')
            PRINT_SECTIONS = False

            for section_name, section in entry.sections.items():
                if PRINT_SECTIONS:
                    rich.print(f'[bold on #004477]      {section_name} : {
                        len(section)} lines   [/]')

    async def grade_with_llm(self):
        filename = await self.get_filename()
        entry = self.entries.get(filename)

        if entry is None:
            rich.print(f'[bold on #ff4477]  {filename}  [/]')
            rich.print(f'[bold on #ff4477]  entry not found  [/]')
            return

        for question_number in QUESTIONS_TO_GRADE:
            asyncio.create_task(entry.grade_with_llm(question_number))


cs7350a1 = CS7350A1()


def try_async_macro(macro):
    try:
        asyncio.create_task(macro())
    except Exception as e:
        print_colorized_exception(e)


def MACRO_1():
    rich.print('[bold on #004477]      MACRO_1      [/]')
    try_async_macro(cs7350a1.prepare_prompt)


def MACRO_2():
    rich.print('[bold on #004477]      MACRO_2      [/]')
    try_async_macro(cs7350a1.grade_with_llm)


def MACRO_3():
    rich.print('[bold on #004477]      MACRO_3      [/]')


def MACRO_4():
    rich.print('[bold on #004477]      MACRO_4      [/]')


def MACRO_5():
    rich.print('[bold on #004477]      MACRO_5      [/]')
