import copy
import random


def create_gaps(quotations_to_learn, difficulty):
    for quotation in quotations_to_learn:
        if type(quotation['quotation']) != list:
            quotation_as_list = quotation['quotation'].split()
            quotation['quotation'] = quotation_as_list

    quotations_to_edit = copy.deepcopy(quotations_to_learn)
    quotations_for_completion = {'quotations': []}

    if difficulty == 'easy':
        for quotation in quotations_to_edit:
            to_remove = random.randint(0, int(len(quotation['quotation']) - 1))
            quotation_to_complete = quotation
            quotation_to_complete['quotation'][to_remove] = 'X'
            quotations_for_completion['quotations'].append(quotation_to_complete)

    elif difficulty == 'medium':

        for quotation in quotations_to_edit:
            for num in range(0, len(quotation) // 2):
                to_remove = random.randint(0, int(len(quotation['quotation']) - 1))
                quotation_to_complete = quotation
                quotation_to_complete['quotation'][to_remove] = 'X'
            quotations_for_completion['quotations'].append(quotation_to_complete)

    elif difficulty == 'hard':

        for quotation in quotations_to_edit:
            for num in range(0, len(quotation) - 2):
                to_remove = random.randint(0, int(len(quotation['quotation']) - 1))
                quotation_to_complete = quotation
                quotation_to_complete['quotation'][to_remove] = 'X'
            quotations_for_completion['quotations'].append(quotation_to_complete)

    return quotations_for_completion


def verify_answers(answers):
    pass


def quiz_percentage(quiz_results):
    max_score = len(quiz_results)
    actual_score = 0

    for result in quiz_results:
        if result["correct"] == 1:
            actual_score += 1

    percent_score = (actual_score / max_score) * 100

    return percent_score


def progress_bar_percent(result):
    return 25 * (round(result / 25))


def overall_percentage(running_avg, attempt_numbers, new_avg):
    if running_avg is None:
        return new_avg
    else:
        new_running_avg = round((running_avg * (attempt_numbers - 1) + new_avg) / attempt_numbers)
        return new_running_avg
