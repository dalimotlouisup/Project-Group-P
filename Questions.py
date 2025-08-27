class Question:
    def __init__(self, question_text, answers, correct_answer):
        self._question_text = question_text
        self._answers = answers
        self._correct_answer = correct_answer

    def get_question_text(self):
        return self._question_text

    def get_answers(self):
        return self._answers

    def get_correct_answer(self):
        return self._correct_answer


class EasyQuestion(Question):
    def __init__(self, question_text, answers, correct_answer):
        super().__init__(question_text, answers, correct_answer)

    def get_points(self):
        return 1


class MediumQuestion(Question):
    def __init__(self, question_text, answers, correct_answer):
        super().__init__(question_text, answers, correct_answer)

    def get_points(self):
        return 3


class HardQuestion(Question):
    def __init__(self, question_text, answers, correct_answer):
        super().__init__(question_text, answers, correct_answer)

    def get_points(self):
        return 5
        

