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

NUM_QUESTIONS = 5
QUESTIONS_TO_GRADE = {3: 'gpt-4o', 4: 'gpt-4o', 5: 'gpt-4o'}
# QUESTIONS_TO_GRADE = {3: 'gpt-4o-mini'}


client = AsyncOpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def calculate_score(correct_answers: int, total_subproblems: int, minor_mistakes: int, major_mistakes: int, show_your_work_detail_level: int):
    MINOR_MISTAKE_MULTIPLIER = 1
    MAJOR_MISTAKE_MULTIPLIER = 2
    SHOW_YOUR_WORK_BONUS = {
        # detail_level: (scaled_bonus, flat_bonus)
        3: (10, 2),  # very_detailed
        2: (8, 1),  # detailed
        1: (6, 0),  # somewhat_detailed
        0: (0, -5)  # did_not_show_work
    }
    assert 0 <= correct_answers <= total_subproblems
    assert 0 <= minor_mistakes
    assert 0 <= major_mistakes
    assert show_your_work_detail_level in SHOW_YOUR_WORK_BONUS.keys()
    scaled_bonus, flat_bonus = SHOW_YOUR_WORK_BONUS[show_your_work_detail_level]

    # Correctness, how many questions out of total subproblems are correct
    points = correct_answers / total_subproblems * 20

    # Reasoning Mistakes, deduct points for minor and major reasoning mistakes
    points = points - minor_mistakes * MINOR_MISTAKE_MULTIPLIER - \
        major_mistakes * MAJOR_MISTAKE_MULTIPLIER
    points = max(points, 0)

    # Show your work bonus, add point for showing your work
    # The scaled component is based on how close the points are to 0, the way a student that showed detailed work but got all the answers wrong can still get a big bonus
    points = points + (1 - (points / 20)) * scaled_bonus
    # The flat bonus is here to allow students that made a few minor mistakes to still get the max score if they showed their work
    # Students that did not show any work will also be penalized here
    points = points + flat_bonus

    points = min(max(points, 0), 20)

    points = round(points)
    return points


def test_calculate_score():
    print(calculate_score(correct_answers=3, total_subproblems=4, minor_mistakes=1,
          major_mistakes=1, show_your_work_detail_level=2))
    print(calculate_score(correct_answers=0, total_subproblems=4,
          minor_mistakes=1, major_mistakes=1, show_your_work_detail_level=3))
    print(calculate_score(correct_answers=4, total_subproblems=4, minor_mistakes=0,
          major_mistakes=0, show_your_work_detail_level=0))
    print(calculate_score(correct_answers=4, total_subproblems=4, minor_mistakes=4,
          major_mistakes=1, show_your_work_detail_level=3))


def calculate_points_for_text(text: str):

    # remove first line if it starts with <mark>Total Score
    if text.startswith('<mark>Total Score'):
        text_lines = text.split('\n')[1:]
        text = '\n'.join(text_lines)

    import re

    # Find all sections that start with <mark> START OF SUMMARY </mark> and end with <mark> END OF SUMMARY </mark>
    summary_pattern = re.compile(
        r'START OF SUMMARY(.*?)END OF SUMMARY', re.DOTALL)
    summary_matches = summary_pattern.finditer(text)

    if not summary_matches:
        return text

    for summary_match in summary_matches:
        summary_text = summary_match.group(1)

        # Extract the total_subproblems, correct_answers, minor_mistakes, major_mistakes, show_your_work_detail_level
        total_subproblems_match = re.search(
            r'total_subproblems: (\d+)', summary_text)
        correct_answers_match = re.search(
            r'correct_answers: (\d+)', summary_text)
        minor_mistakes_match = re.search(
            r'minor_mistakes: (\d+)', summary_text)
        major_mistakes_match = re.search(
            r'major_mistakes: (\d+)', summary_text)
        show_your_work_detail_level_match = re.search(
            r'show_your_work_detail_level: (\d+)', summary_text)
        question_number_match = re.search(
            r'(Q\d+) Points =', summary_text)

        assert total_subproblems_match is not None
        assert correct_answers_match is not None
        assert minor_mistakes_match is not None
        assert major_mistakes_match is not None
        assert show_your_work_detail_level_match is not None
        assert question_number_match is not None
        total_subproblems = int(total_subproblems_match.group(1))
        correct_answers = int(correct_answers_match.group(1))
        minor_mistakes = int(minor_mistakes_match.group(1))
        major_mistakes = int(major_mistakes_match.group(1))
        show_your_work_detail_level = int(
            show_your_work_detail_level_match.group(1))
        question_number = question_number_match.group(1)
        # print(f"total_subproblems: {total_subproblems}")
        # print(f"correct_answers: {correct_answers}")
        # print(f"minor_mistakes: {minor_mistakes}")
        # print(f"major_mistakes: {major_mistakes}")
        # print(f"show_your_work_detail_level: {show_your_work_detail_level}")
        # print(f"question_number: {question_number}")

        # Calculate the score
        score = calculate_score(correct_answers, total_subproblems,
                                minor_mistakes, major_mistakes, show_your_work_detail_level)
        # print(f"score: {score}")

        # Update the text with the calculated score
        text = re.sub(f'<mark>{question_number} Points = -?\d+</mark>',
                      f'<mark>{question_number} Points = {score}</mark>', text)

    scores_builder = []
    total_score = 0
    # gather all the points that are in the format <mark> Points: X </mark> and print them
    points_pattern = re.compile(r'<mark>Points = (\d+)')
    points_matches = points_pattern.finditer(text)
    for points_match in points_matches:
        score = points_match.group(1)
        # print(f"score: {score}")
        scores_builder.append(score)
        total_score += int(score)

    # gather all the points that are in the format <mark> QN Points: X </mark>  including QN if present

    points_pattern = re.compile(r'<mark>(Q\d+) Points = (-?\d+)</mark>')
    points_matches = points_pattern.finditer(text)
    for points_match in points_matches:
        question_number = points_match.group(
            1) if points_match.group(1) else 'N/A'
        score = points_match.group(2)
        print(f'question_number: {question_number}, score: {score}')
        scores_builder.append(question_number + ': ' + score)
        total_score += int(score)

    scores_builder = f'<mark>Total Score = {str(total_score)} = {
        " + ".join(scores_builder)}</mark>'

    return scores_builder + '\n' + text


async def ask_llm(prompt: str, model: str = 'gpt-4o-mini'):
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


class Status(Enum):
    ERROR_PARSING_TEXT = '#ff4477'
    TO_BE_GRADED = '#004477'
    LLM_GRADED = '#00CC00'
    LLM_GRADING = '#AAAA33'
    HUMAN_GRADED = '#444444'
    SKIPPED = '#333333'


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

        self.question_statuses: dict[str, Status] = self.get_initial_statuses(
            self.sections)

        self.prompts = self.prepare_prompts()
        self.responses = {}

    def get_initial_statuses(self, sections):
        statuses = {}

        for question_number in range(1, NUM_QUESTIONS + 1):
            question_name = self.question_start_template.format(
                question_number)
            if self.sections.get(question_name) is None:
                statuses[question_name] = Status.ERROR_PARSING_TEXT
            else:
                statuses[question_name] = Status.SKIPPED

            answer_name = self.student_answer_template.format(question_number)
            if self.sections.get(answer_name) is None:
                statuses[answer_name] = Status.ERROR_PARSING_TEXT
            elif question_number in QUESTIONS_TO_GRADE.keys():
                statuses[answer_name] = Status.TO_BE_GRADED
            else:
                statuses[answer_name] = Status.SKIPPED

        return statuses

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

            if section_name not in self.sections:
                continue

            student_answer = self.sections[section_name]
            student_answer = '\n'.join(student_answer)

            prompts[section_name] = main_prompt + \
                question_prompt + \
                ANSWER_START + \
                student_answer + \
                ANSWER_END

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

        return sections

    async def grade_with_llm(self, question_number: int):
        section_name = self.student_answer_template.format(question_number)
        async with Entry.lock:
            if self.question_statuses[section_name] != Status.TO_BE_GRADED:
                rich.print(f'[bold on #ff4477]  {self.filename}  [/]')
                rich.print(f'[bold on #ff4477]  question {
                           question_number} is not in TO_BE_GRADED state [/]')
                return
            self.question_statuses[section_name] = Status.LLM_GRADING

        async with Entry.llm_semaphore:

            prompt = self.prompts[section_name]
            model = QUESTIONS_TO_GRADE[question_number]
            response = await ask_llm(prompt, model)
            self.responses[section_name] = response

            async with Entry.lock:
                self.question_statuses[section_name] = Status.LLM_GRADED
            cs7350a1.print_status()

    def is_all_graded(self):

        for question_number in QUESTIONS_TO_GRADE.keys():
            section_name = self.student_answer_template.format(question_number)
            if self.question_statuses[section_name] != Status.LLM_GRADED:
                return False

        return True

    def mark_as_human_graded(self):
        for question_number in QUESTIONS_TO_GRADE.keys():
            section_name = self.student_answer_template.format(question_number)
            self.question_statuses[section_name] = Status.HUMAN_GRADED

    def build_full_graded_document(self):
        sections_list = []

        for question_number in range(1, NUM_QUESTIONS + 1):
            question_name = self.question_start_template.format(
                question_number)
            answer_name = self.student_answer_template.format(question_number)

            sections_list.append('\n'.join(self.sections[question_name]))

            if question_number in QUESTIONS_TO_GRADE.keys():
                sections_list.append(self.responses[answer_name])
            else:
                sections_list.append('\n'.join(self.sections[answer_name]))

        return '\n'.join(sections_list)

    def print_status(self):
        filename = self.filename
        is_error = any(
            status == Status.ERROR_PARSING_TEXT for status in self.question_statuses.values())

        if is_error:
            file_status = Status.ERROR_PARSING_TEXT.value
        elif any(status == Status.LLM_GRADING for status in self.question_statuses.values()):
            file_status = Status.LLM_GRADING.value
        elif self.is_all_graded():
            file_status = Status.LLM_GRADED.value
        elif all(status == Status.HUMAN_GRADED for status in self.question_statuses.values()):
            file_status = Status.HUMAN_GRADED.value
        else:
            file_status = Status.TO_BE_GRADED.value

        status_string = f'[bold on {file_status}]{filename[:20]}[/]'
        for question_number in range(1, NUM_QUESTIONS + 1):
            question_name = self.question_start_template.format(
                question_number)
            question_status = self.question_statuses[question_name].value
            status_string += f' [bold on {question_status}]Q{
                question_number}[/]'

            answer_name = self.student_answer_template.format(question_number)
            answer_status = self.question_statuses[answer_name].value
            status_string += f' [bold on {answer_status}]A{question_number}[/]'

        rich.print(status_string)


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
        self.print_status()

    async def calculate_points(self):
        content = await self.select_all_copy()
        # find sections that start with <mark> START OF SUMMARY </mark> and end with <mark> END OF SUMMARY </mark>
        content = calculate_points_for_text(content)
        pyperclip.copy(content)
        await asyncio.sleep(0.1)
        output_raw('Control{A} 20ms Control{V} 20ms Control{Home}')

    async def grade_with_llm(self):
        filename = await self.get_filename()
        entry = self.entries.get(filename)

        if entry is None:
            rich.print(f'[bold on #ff4477]  {filename}  [/]')
            rich.print(f'[bold on #ff4477]  entry not found  [/]')
            return

        for question_number in QUESTIONS_TO_GRADE:
            asyncio.create_task(entry.grade_with_llm(question_number))
        await asyncio.sleep(0.1)
        self.print_status()

    async def diff_response_with_current(self):
        filename = await self.get_filename()
        entry = self.entries.get(filename)

        if entry is None:
            rich.print(f'[bold on #ff4477]  {filename}  [/]')
            rich.print(f'[bold on #ff4477]  entry not found  [/]')
            return

        if not entry.is_all_graded():
            rich.print(f'[#000000 on #FFFF00]  {filename}  [/]')
            rich.print(f'[#000000 on #FFFF00]  Not done grading  [/]')
            return

        full_graded_document = entry.build_full_graded_document()
        pyperclip.copy(full_graded_document)

        await asyncio.sleep(0.1)

        output_raw('Control{G} D')

        entry.mark_as_human_graded()
        self.print_status()

    def print_status(self):
        for filename, entry in self.entries.items():
            entry.print_status()


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
    try_async_macro(cs7350a1.diff_response_with_current)


def MACRO_4():
    rich.print('[bold on #004477]      MACRO_4      [/]')
    try_async_macro(cs7350a1.calculate_points)


def MACRO_5():
    rich.print('[bold on #004477]      MACRO_5      [/]')
    try_async_macro(cs_7350_a1_q2)
