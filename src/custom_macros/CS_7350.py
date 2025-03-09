from __future__ import annotations
import rich
import pyperclip
from colors import print_colorized_exception
from keymapperctl import input_raw, output_raw
import asyncio
from openai import AsyncOpenAI
from pathlib import Path
from enum import Enum
import re
import pyperclip
import os


# Legend

# QN = Question Number
# A = Answer
# R = Rubric
# P = Prompt
# G = LLM Graded Response


# region Global constants
MODEL_TO_USE = 'o1-mini' # o1-preview o1-mini gpt-4o gpt-4o-mini

OPENAI_API_KEY_FILE = '/home/tony/openai_api_key.txt'

# endregion Global constants

# region Shared

# read OPENAI_API_KEY from file
with open(OPENAI_API_KEY_FILE, 'r') as file:
    OPENAI_API_KEY = file.read().strip()

client = AsyncOpenAI(
    # This is the default and can be omitted
    # api_key=os.environ.get("OPENAI_API_KEY"),
    api_key=OPENAI_API_KEY
)

class GradingStatus(Enum):
    TO_BE_GRADED = '#004477'
    LLM_GRADING = '#AAAA33'
    LLM_GRADING_FAILED = '#ff4477'
    LLM_GRADED = '#00CC00'

def select_all_copy():
    input_raw('Control{A} 20ms Control{C}')

class ClassLevel(Enum):
    CS7350 = 'CS7350'
    CS5350 = 'CS5350'
    UNKNOWN = 'UNKNOWN'

def get_class_level_from_name_section(name_section: str):
    # in the case of a team, if at least one student is CS7350 then the team is CS7350
    if '7350' in name_section:
        return ClassLevel.CS7350
    elif '5350' in name_section:
        return ClassLevel.CS5350
    else:
        # treat student with no class section as CS7350
        return ClassLevel.CS7350
    
def calculate_score_v2(correctness_list: list[int], show_your_work_detail_level: int, max_score: int = 20):

    if max_score == 0:
        return 0, 0, 0

    max_score_default = 20
    SHOW_YOUR_WORK_BONUS = {
    # detail_level: (scaled_bonus, flat_bonus)
    3: (7, 1),  # very_detailed
    2: (5, 0),  # detailed
    1: (3, 0),  # somewhat_detailed
    0: (0, 0)  # did_not_show_work
}
    MAX_CORRECTNESS_SCORE = 4
    points = sum(correctness_list) / len(correctness_list) / MAX_CORRECTNESS_SCORE * max_score
    base = round(points)
    points = max(points, 0)
    scaled_bonus, flat_bonus = SHOW_YOUR_WORK_BONUS[show_your_work_detail_level]
    scaled_bonus = scaled_bonus / max_score_default * max_score
    flat_bonus = flat_bonus / max_score_default * max_score
    points = points + (1 - (points / max_score)) * scaled_bonus
    points = points + flat_bonus
    points = min(max(points, 0), max_score)
    points = round(points)
    bonus = points - base
    return points, base, bonus

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




def calculate_points_for_text_v2(text: str, question_points) -> str:
    import re

    summary_start_text = "## <mark>START OF SUMMARY"
    summary_start_re = r"START OF SUMMARY Q(\d+)"
    summary_end_text = "## <mark>END OF SUMMARY"
    show_your_work_re = r"show_your_work_detail_level: (\d+)"
    correctness_re = r"Correctness: (\d)"
    points_text = r"- Q\d+ Points ="

    

    score_dict = {}

    lines = text.split('\n')

    if '5350' in lines[0]:
        student_level = ClassLevel.CS5350
    else:
        student_level = ClassLevel.CS7350

    question_number = -1
    correctness_list = []
    show_your_work_detail_level = -1
    current_line_index = 0
    points_line_idx = -1
    while current_line_index < len(lines):
        line = lines[current_line_index]
        if line.startswith(summary_start_text):
            match = re.search(summary_start_re, line)
            if not match:
                rich.print('[#f80]Start of summary line match failed: {line}[/]')
            else:
                question_number = match.group(1)
                question_number = int(question_number)
                correctness_list = []
                show_your_work_detail_level = -1
        if question_number == -1:
            current_line_index += 1
            continue
        match_correctness = re.search(correctness_re, line)
        if match_correctness:
            correctness = match_correctness.group(1)
            correctness = int(correctness)
            correctness_list.append(correctness)
        match_show_your_work = re.search(show_your_work_re, line)
        if match_show_your_work:
            show_your_work_detail_level = match_show_your_work.group(1)
            show_your_work_detail_level = int(show_your_work_detail_level)
        match_points = re.search(points_text, line)
        if match_points:
            points_line_idx = current_line_index
        if line.startswith(summary_end_text):
            max_score = question_points[student_level][question_number - 1]
            score, base, bonus = calculate_score_v2(correctness_list, show_your_work_detail_level, max_score)
            lines[points_line_idx] = f'- Q{question_number} Points = {score} = base: {base} + bonus: {bonus}'
            score_dict[f'Q{question_number}'] = score
        current_line_index += 1

    total_score = sum(score_dict.values())
    question_and_score_list = []
    for question_number, score in score_dict.items():
        question_and_score_list.append(f'{question_number}: {score}')
    question_and_score = ' + '.join(question_and_score_list)
    total_score_line = f'<mark>Total Score = {total_score} = {question_and_score}</mark>\n'
    
    lines.insert(0, total_score_line)
    return '\n'.join(lines)


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


def re_student_answer_header(question_number: int):
    return f'## Question {question_number}.{{0,6}}Student Answer'

def re_question_header(question_number: int):
    return f'## Question {question_number}'

def re_reference_answer_header(question_number: int):
    return f'## Question {question_number}.{{0,6}}Reference Answer'

class SectionDefinition:
    def __init__(self, name: str, start_re: str):
        self.name = name
        self.start_re = start_re
        self.end_re = ''
        self.full_re = ''
    
    @staticmethod
    def initialize_section_definitions(section_definitions: list[SectionDefinition]) -> list[SectionDefinition]:
        for i in range(len(section_definitions) - 1):
            section_definitions[i].end_re = section_definitions[i+1].start_re
        section_definitions[-1].end_re = r'\Z'
        for section_definition in section_definitions:
            start_re = section_definition.start_re
            end_re = section_definition.end_re
            # group 2 will be discarded
            section_definition.full_re = f'({start_re}[\s\S]*?)({end_re})'
        return section_definitions


def parse_sections(content: str, section_definitions: list[SectionDefinition]) -> dict[str, str]:
    section_definitions = SectionDefinition.initialize_section_definitions(section_definitions)
    sections = {}
    for section_definition in section_definitions:
        # print out the full_re for debugging, copy this to regex101.com for debugging
        #print(section_definition.full_re)
        pattern = re.compile(section_definition.full_re)
        matches = pattern.finditer(content)
        matches = list(matches)
        if len(matches) != 1:
            sections[section_definition.name] = ''
        else:
            match = matches[0]
            sections[section_definition.name] = match.group(1)
    return sections
    
async def ask_llm(prompt: str, model: str = 'gpt-4o-mini'):
    rich.print('[#ffff00]  [/]    ask_llm      [#ffff00]  [/]')
    completion = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return completion.choices[0].message.content

class Entry:
    '''
    An entry keeps track of the parsing and grading status of a single file (student submission)
    '''

    llm_semaphore = asyncio.Semaphore(1)
    lock = asyncio.Lock()

    def __init__(self, filename, student_sections: dict[str, str], rubric_sections: dict[str, str], prompt_head: str, num_questions: int, grader: CS7350_Grader):

        self.filename = filename
        self.prompt_head = prompt_head

        self.student_sections = student_sections
        self.rubric_sections = rubric_sections
        self.num_questions = num_questions
        self.grader = grader

        self.class_level = get_class_level_from_name_section(student_sections['Header'])
        self.prompts = self.prepare_prompts()
        self.graded_sections = {}
        
        self.llm_graded_document = ''



        self.grading_statuses : dict[str, GradingStatus] = {}
        for i in range(1, self.num_questions + 1):
            self.grading_statuses[f'G{i}'] = GradingStatus.TO_BE_GRADED

        self.responses = {} # key is Gi

        self.print_status()



    def prepare_prompts(self):
        prompts = {}

        for i in range(1, self.num_questions+1):
            prompt_name = f'P{i}'
            prompt_content = self.prompt_head
            prompt_content += '\n'
            prompt_content += self.rubric_sections[f'Q{i}']
            prompt_content += f'\nThis is a {self.class_level.value} student, grade accordingly.\n'
            prompt_content += self.student_sections[f'A{i}']
            prompt_content += '\n'
            prompt_content += self.rubric_sections[f'R{i}']
            prompts[prompt_name] = prompt_content
            #print(prompt_content)
            #print('>>>>>>>>>>>')
        return prompts


    def verify_grading_response(self, response: str, question_number: int):
        '''
        check if the response is a valid grading response for the given question number
        response must start with:
        <mark>START OF SUMMARY Qi</mark>
        and end with:
        <mark>END OF SUMMARY Qi</mark>
        '''
        response = response.strip()
        start = f'<mark>START OF SUMMARY Q{question_number}</mark>'
        end = f'<mark>END OF SUMMARY Q{question_number}</mark>'
        if start not in response or end not in response:
            print(response)
            return False
        return True


    async def grade_with_llm(self, question_number: int):
        prompt_name = f'P{question_number}'
        grade_key = f'G{question_number}'
        async with Entry.lock:
            if self.grading_statuses[grade_key] != GradingStatus.TO_BE_GRADED:
                rich.print(f'[bold on #ff4477]  {self.filename}  [/]')
                rich.print(f'[bold on #ff4477]  question {
                           question_number} is not in TO_BE_GRADED state [/]')
                return
            self.grading_statuses[grade_key] = GradingStatus.LLM_GRADING

        async with Entry.llm_semaphore:

            prompt = self.prompts[prompt_name]
            model = MODEL_TO_USE
            response = await ask_llm(prompt, model)
            self.responses[grade_key] = response
            if response == None:
                response = ''
            async with Entry.lock:
                if not self.verify_grading_response(response, question_number):
                    self.grading_statuses[grade_key] = GradingStatus.LLM_GRADING_FAILED
                else:
                    self.grading_statuses[grade_key] = GradingStatus.LLM_GRADED
            self.grader.print_status()
            # if all is graded, construct the full graded document and move to graded_llm folder
            if self.is_all_graded():
                self.llm_graded_document = self.construct_llm_graded_document()
                self.save_to_graded_llm_folder(self.llm_graded_document)

    def is_all_graded(self):
        for grade_key in self.grading_statuses.keys():
            if self.grading_statuses[grade_key] != GradingStatus.LLM_GRADED:
                return False
        return True
    
    def construct_llm_graded_document(self):
        document = ''
        document += '<mark>Student Level: ' + self.class_level.value + ' </mark>\n\n'
        document += self.student_sections['Header']
        for question_number in range(1, self.num_questions + 1):
            grade_key = f'G{question_number}'
            document += self.rubric_sections[f'Q{question_number}']
            document += self.student_sections[f'A{question_number}']
            document += '\n\n'
            document += self.responses[grade_key]
            document += '\n\n'
        return document


    def save_to_graded_llm_folder(self, document: str):
        graded_llm_filepath = self.grader.graded_llm_dir / self.filename
        with open(graded_llm_filepath, 'w') as file:
            file.write(document)
        

    def mark_as_human_graded(self):
        for question_number in A1_QUESTIONS_TO_GRADE.keys():
            section_name = self.student_answer_template.format(question_number)
            self.grading_statuses[section_name] = GradingStatus.HUMAN_GRADED

    def build_full_graded_document(self):
        sections_list = []

        for question_number in range(1, A1_NUM_QUESTIONS + 1):
            question_name = self.question_start_template.format(
                question_number)
            answer_name = self.student_answer_template.format(question_number)

            sections_list.append('\n'.join(self.sections[question_name]))

            if question_number in A1_QUESTIONS_TO_GRADE.keys():
                sections_list.append(self.responses[answer_name])
            else:
                sections_list.append('\n'.join(self.sections[answer_name]))

        return '\n'.join(sections_list)

    def print_status(self):
        filename = self.filename
        level = self.class_level.value
        
        status_string = f'[bold on #004477]{filename[:20]} {level} [/]'
        for i in range(1, self.num_questions + 1):
            key = f'G{i}'
            status_string += f' [bold on {self.grading_statuses[key].value}]{key} [/]'
        rich.print(status_string)


class CS7350_Grader:
    '''
    All should be done in the context of vscode
    '''

    def __init__(self, 
                 assignment_number: int,
                 num_questions: int,
                 student_section_definitions: list[SectionDefinition], 
                 rubric_section_definitions: list[SectionDefinition], 
                 rubric_file: str, 
                 prompt_file: str,
                 grading_dir: str,
                 graded_llm_dir: str,
                 graded_human_dir: str, 
                 question_points = None):
        self.entries: dict[str, Entry] = {}
        self.assignment_number = assignment_number
        self.num_questions = num_questions
        self.student_section_definitions = student_section_definitions
        self.rubric_section_definitions = rubric_section_definitions
        self.rubric_file = Path(rubric_file)
        self.prompt_file = Path(prompt_file)
        self.grading_dir = Path(grading_dir)
        self.graded_llm_dir = Path(graded_llm_dir)
        self.graded_human_dir = Path(graded_human_dir)
        self.question_points = question_points
        self.rubric_sections = {}
        self.prompt_content = ''
        self.student_sections = {}

        for filepath in [self.graded_llm_dir, self.graded_human_dir]:
            if not os.path.exists(filepath):
                os.makedirs(filepath)

        with open(self.prompt_file, 'r') as file:
            self.prompt_content = file.read()

    def print_sections_summary(self, name: str, content: str, sections: dict[str, str], color_default: str = '#004477'):
        filename_short = name[:10]
        content_newlines = content.count('\n')
        status_string = f'[bold on {color_default}]{filename_short} {content_newlines}[/]'
        for section_name, section_content in sections.items():
            color_section = color_default
            if section_content == '':
                color_section = '#ff4499'
            section_newlines = section_content.count('\n')
            status_string += f' [bold on {color_section}]{section_name} {section_newlines}[/]'
        rich.print(status_string)

    async def parse_rubric(self):
        with open(self.rubric_file, 'r') as file:
            rubric_content = file.read()
    
        self.rubric_sections = parse_sections(rubric_content, self.rubric_section_definitions)
        self.print_sections_summary('rubric', rubric_content, self.rubric_sections, color_default='#114422')

    
    async def parse_student_assignments(self):
        '''parse all the student assignments in the grading directory'''
        filenames = os.listdir(self.grading_dir)
        filenames.sort()
        row_colors  = ['#004477', '#002255']
        student_idx = 0
        for filename in filenames:
            if filename.endswith('.md'):
                with open(os.path.join(self.grading_dir, filename), 'r') as file:
                    content = file.read()
                student_sections = parse_sections(content, self.student_section_definitions)
                self.print_sections_summary(filename, content, student_sections, row_colors[student_idx % len(row_colors)])
                student_idx += 1
                self.student_sections[filename] = student_sections
    
    async def make_entries(self):
        for filename, student_sections in self.student_sections.items():
            entry = Entry(filename, student_sections, self.rubric_sections, self.prompt_content, self.num_questions, self)
            self.entries[filename] = entry


    async def print_assignment_number(self):
        '''print the assignment number'''
        rich.print(f'[bold on #004477]  Assignment {self.assignment_number}  [/]')

    async def get_vscode_filename(self):
        '''get the filename of the current file in vscode'''
        output_raw('(Control){G} C')
        await asyncio.sleep(0.05)
        filepath = pyperclip.paste()
        filename = Path(filepath).name
        return filename

    async def select_all_copy(self):
        '''select all text and copy to clipboard'''
        output_raw('Control{A} 20ms Control{C}')
        await asyncio.sleep(0.05)
        content = pyperclip.paste()
        return content
    
    async def parse_files(self):
        '''parse all the files in the current directory'''


    async def calculate_points(self):
        '''calculate the points for files in graded_llm folder and save to graded_human folder'''
        filenames = os.listdir(self.graded_llm_dir)
        filenames.sort()
        for filename in filenames:
            filepath = self.graded_llm_dir / filename
            # check if filepath is a file
            if not os.path.isfile(filepath):
                continue
            with open(filepath, 'r') as file:
                content = file.read()
            content = calculate_points_for_text_v2(content, self.question_points)
            graded_human_filepath = self.graded_human_dir / filename
            with open(graded_human_filepath, 'w') as file:
                file.write(content)

    async def grade_with_llm(self):
        '''grade the current file with llm, uses the prepared prompt'''

        for entry in self.entries.values():
            for i in range(1, self.num_questions + 1):
                asyncio.create_task(entry.grade_with_llm(i))
            await asyncio.sleep(0.1)
        self.print_status()

    async def diff_response_with_current(self):
        filename = await self.get_vscode_filename()
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


# endregion Shared


# region A1









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






#cs7350a1 = CS7350_Grader(1)







# endregion A1

# region A2

a2_student_section_definitions = [
    SectionDefinition(name='Name', 
                      start_re=r'\A'),
    SectionDefinition(name='Inst',
                      start_re=r'## Instructions'),
    SectionDefinition(name='Q1',
                      start_re=re_question_header(1)),
    SectionDefinition(name='A1', 
                      start_re=re_student_answer_header(1)),
    SectionDefinition(name='Q2',
                      start_re=re_question_header(2)),
    SectionDefinition(name='A2', 
                      start_re=re_student_answer_header(2)),
    SectionDefinition(name='Q3',
                      start_re=re_question_header(3)),
    SectionDefinition(name='A3', 
                      start_re=re_student_answer_header(3)),
    SectionDefinition(name='Q4',
                      start_re=re_question_header(4)),
    SectionDefinition(name='A4', 
                      start_re=re_student_answer_header(4)),
    SectionDefinition(name='A5',
                      start_re=re_question_header(5)),
]

a2_rubric_section_definitions = [
    SectionDefinition(name='Header', 
                      start_re=r'\A'),
    SectionDefinition(name='Q1',
                      start_re=re_question_header(1)),
    SectionDefinition(name='R1', 
                      start_re=re_reference_answer_header(1)),
    SectionDefinition(name='Q2',
                      start_re=re_question_header(2)),
    SectionDefinition(name='R2', 
                      start_re=re_reference_answer_header(2)),
    SectionDefinition(name='Q3',
                      start_re=re_question_header(3)),
    SectionDefinition(name='R3', 
                      start_re=re_reference_answer_header(3)),
    SectionDefinition(name='Q4',
                      start_re=re_question_header(4)),
    SectionDefinition(name='R4', 
                      start_re=re_reference_answer_header(4)),
    SectionDefinition(name='Q5',
                      start_re=re_question_header(5)),
    SectionDefinition(name='R5',
                      start_re=re_reference_answer_header(5)),
]



cs7350a2 = CS7350_Grader(assignment_number=2,
                          num_questions=5,
                          student_section_definitions=a2_student_section_definitions, 
                          rubric_section_definitions=a2_rubric_section_definitions, 
                          rubric_file='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-2/Assignment-2-rubric.md', 
                          prompt_file='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-2/Assignment-2-prompt.md',
                          grading_dir='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-2/regrade',
                          graded_llm_dir='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-2/regraded_llm',
                          graded_human_dir='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-2/regraded_human')


# endregion A2

# region A3
a3_student_section_definitions = [
    SectionDefinition(name='Header', 
                      start_re=r'\A'),
    SectionDefinition(name='Q1',
                      start_re=re_question_header(1)),
    SectionDefinition(name='A1', 
                      start_re=re_student_answer_header(1)),
    SectionDefinition(name='Q2',
                      start_re=re_question_header(2)),
    SectionDefinition(name='A2', 
                      start_re=re_student_answer_header(2)),
    SectionDefinition(name='Q3',
                      start_re=re_question_header(3)),
    SectionDefinition(name='A3', 
                      start_re=re_student_answer_header(3)),
    SectionDefinition(name='Q4',
                      start_re=re_question_header(4)),
    SectionDefinition(name='A4', 
                      start_re=re_student_answer_header(4)),
    SectionDefinition(name='Q5',
                      start_re=re_question_header(5)),
    SectionDefinition(name='A5',
                      start_re=re_student_answer_header(5)),
    SectionDefinition(name='Q6',
                      start_re=re_question_header(6)),
    SectionDefinition(name='A6',
                      start_re=re_student_answer_header(6)),
]

a3_rubric_section_definitions = [
    SectionDefinition(name='Header', 
                      start_re=r'\A'),
    SectionDefinition(name='Q1',
                      start_re=re_question_header(1)),
    SectionDefinition(name='R1', 
                      start_re=re_reference_answer_header(1)),
    SectionDefinition(name='Q2',
                      start_re=re_question_header(2)),
    SectionDefinition(name='R2', 
                      start_re=re_reference_answer_header(2)),
    SectionDefinition(name='Q3',
                      start_re=re_question_header(3)),
    SectionDefinition(name='R3', 
                      start_re=re_reference_answer_header(3)),
    SectionDefinition(name='Q4',
                      start_re=re_question_header(4)),
    SectionDefinition(name='R4', 
                      start_re=re_reference_answer_header(4)),
    SectionDefinition(name='Q5',
                      start_re=re_question_header(5)),
    SectionDefinition(name='R5',
                      start_re=re_reference_answer_header(5)),
    SectionDefinition(name='Q6',
                      start_re=re_question_header(6)),
    SectionDefinition(name='R6',
                      start_re=re_reference_answer_header(6)),
]

a3_question_points = {ClassLevel.CS5350: [20, 0, 20, 20, 20, 20],
                      ClassLevel.CS7350: [10, 10, 20, 20, 20, 20]}



cs7350a3 = CS7350_Grader(assignment_number=3,
                          num_questions=6,
                          student_section_definitions=a3_student_section_definitions, 
                          rubric_section_definitions=a3_rubric_section_definitions, 
                          rubric_file='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-3/Assignment-3-rubric.md', 
                          prompt_file='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-3/Assignment-3-prompt.md',
                          grading_dir='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-3/grading',
                          graded_llm_dir='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-3/graded_llm',
                          graded_human_dir='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-3/graded_human',
                          question_points=a3_question_points)
# endregion A3


# region A4
a4_student_section_definitions = [
    SectionDefinition(name='Header', 
                      start_re=r'\A'),
    SectionDefinition(name='Q1',
                      start_re=re_question_header(1)),
    SectionDefinition(name='A1', 
                      start_re=re_student_answer_header(1)),
    SectionDefinition(name='Q2',
                      start_re=re_question_header(2)),
    SectionDefinition(name='A2', 
                      start_re=re_student_answer_header(2)),
    SectionDefinition(name='Q3',
                      start_re=re_question_header(3)),
    SectionDefinition(name='A3', 
                      start_re=re_student_answer_header(3)),
    SectionDefinition(name='Q4',
                      start_re=re_question_header(4)),
    SectionDefinition(name='A4', 
                      start_re=re_student_answer_header(4)),
    SectionDefinition(name='Q5',
                      start_re=re_question_header(5)),
    SectionDefinition(name='A5',
                      start_re=re_student_answer_header(5)),
    SectionDefinition(name='Q6',
                      start_re=re_question_header(6)),
    SectionDefinition(name='A6',
                      start_re=re_student_answer_header(6)),
]

a4_rubric_section_definitions = [
    SectionDefinition(name='Header', 
                      start_re=r'\A'),
    SectionDefinition(name='Q1',
                      start_re=re_question_header(1)),
    SectionDefinition(name='R1', 
                      start_re=re_reference_answer_header(1)),
    SectionDefinition(name='Q2',
                      start_re=re_question_header(2)),
    SectionDefinition(name='R2', 
                      start_re=re_reference_answer_header(2)),
    SectionDefinition(name='Q3',
                      start_re=re_question_header(3)),
    SectionDefinition(name='R3', 
                      start_re=re_reference_answer_header(3)),
    SectionDefinition(name='Q4',
                      start_re=re_question_header(4)),
    SectionDefinition(name='R4', 
                      start_re=re_reference_answer_header(4)),
    SectionDefinition(name='Q5',
                      start_re=re_question_header(5)),
    SectionDefinition(name='R5',
                      start_re=re_reference_answer_header(5)),
    SectionDefinition(name='Q6',
                      start_re=re_question_header(6)),
    SectionDefinition(name='R6',
                      start_re=re_reference_answer_header(6)),
]

a4_question_points = {ClassLevel.CS5350: [20, 20, 20, 20, 20, 0],
                      ClassLevel.CS7350: [20, 20, 20, 10, 20, 10]}



cs7350a4 = CS7350_Grader(assignment_number=4,
                          num_questions=6,
                          student_section_definitions=a4_student_section_definitions, 
                          rubric_section_definitions=a4_rubric_section_definitions, 
                          rubric_file='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-4/Assignment-4-rubric.md', 
                          prompt_file='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-4/Assignment-4-prompt.md',
                          grading_dir='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-4/grading',
                          graded_llm_dir='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-4/graded_llm',
                          graded_human_dir='/home/tony/gdrive/SMU Classes/TA 2024 Fall/Algorithm Engineering CS5350 CS7350/Assignment-4/graded_human',
                          question_points=a4_question_points)
# endregion A4

