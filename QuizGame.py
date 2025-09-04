import os
import random
import json
from typing import List, Dict, Tuple, Optional

from Questions import EasyQuestion, MediumQuestion, HardQuestion, Question
from Player import Player, save_score, show_leaderboard

#Difficulties and Grade Levels
DIFF_TO_CLASS = {
    "Easy": EasyQuestion,
    "Medium": MediumQuestion,
    "Hard": HardQuestion,
}

GRADE_LEVELS = ["ELEMENTARY", "HIGH SCHOOL"]
DIFFICULTIES = ["Easy", "Medium", "Hard"]


class QuizGame:
    """
    Class QuizGame is the main class for the program to function.
    """

    def __init__(self, questions_file: str = "Question_Bank.txt"):
        self.questions_file = questions_file
        self._all_questions: Dict[str, Dict[str, List[Question]]] = {  # grade -> diff -> list
            grade: {diff: [] for diff in DIFFICULTIES} for grade in GRADE_LEVELS
        }
        self.question_bank: List[Question] = [] #list of questions
        self.score: int = 0
        self._current_index: int = 0
        self._session_meta: Dict[str, str] = {  # for save/resume
            "grade_level": "",
            "difficulty": "",
        }
        self._load_questions_from_file()

    #File Parsing
    def _load_questions_from_file(self) -> None:
        '''
        Reads the questions found in Question_Bank.txt.
        Uses os module to prevent problems of not detecting the file
        '''
        if not os.path.exists(self.questions_file):
            raise FileNotFoundError(f"Cannot find '{self.questions_file}'. Place it beside QuizGame.py.")

        with open(self.questions_file, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]

        #State machine for sections
        grade: Optional[str] = None
        difficulty: Optional[str] = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            #Detect grade level headers
            if line.upper().startswith("ELEMENTARY LEVEL"):
                grade = "ELEMENTARY"
                difficulty = None
                i += 1
                continue
            if line.upper().startswith("HIGH SCHOOL LEVEL"):
                grade = "HIGH SCHOOL"
                difficulty = None
                i += 1
                continue

            #Detect difficulty headers
            if line.startswith("Easy") and grade:
                difficulty = "Easy"
                i += 1
                continue
            if line.startswith("Medium") and grade:
                difficulty = "Medium"
                i += 1
                continue
            if line.startswith("Hard") and grade:
                difficulty = "Hard"
                i += 1
                continue

            #Parse a question block if inside a valid section
            if grade and difficulty and self._looks_like_qnum(line):
                q_text, answers, correct_letter, consumed = self._parse_question_block(lines, i)
                i = consumed  # move index to the line after the block

                # Map to Question subclass by difficulty
                cls = DIFF_TO_CLASS[difficulty]
                q = cls(q_text, answers, correct_letter)
                self._all_questions[grade][difficulty].append(q)
                continue

            i += 1

    @staticmethod
    #staticmethod bundles utilities within the class
    def _looks_like_qnum(line: str) -> bool:
        #e.g., "1. What is ..." or "1.\tWhat is ..."
        return len(line) > 2 and line.split(".", 1)[0].strip().isdigit()

    @staticmethod
    def _parse_question_block(lines: List[str], start_idx: int) -> Tuple[str, List[str], str, int]:
        """
        Parse one question + 4 choices + Answer: X
        Returns (question_text, answers[list of 4], correct_letter, next_index)
        """
        #Question line contains: "1.\tWhat is the capital ..."
        q_line = lines[start_idx]
        q_text = q_line.split(".", 1)[1].strip()  # take text after the first period

        #Next 4 lines are choices: " a) Cebu" etc.
        answers = []
        idx = start_idx + 1
        for _ in range(4):
            choice_line = lines[idx].strip()
            #Expect pattern like "a) Cebu" or "a)  Cebu"
            if ")" in choice_line:
                after = choice_line.split(")", 1)[1].strip()
            else:
                after = choice_line
            answers.append(after)
            idx += 1

        #Then a line like: " Answer: B"
        ans_line = lines[idx].strip()
        if ":" in ans_line:
            correct = ans_line.split(":", 1)[1].strip()
        else:
            correct = ans_line.strip()
        correct = correct[0].upper()  # just take the first letter

        # Move to the next line after the answer
        return q_text, answers, correct, idx + 1

    #Session Setup
    def configure_session(self, grade_level: str, difficulty: str, limit: Optional[int] = None) -> None:
        if grade_level.upper() not in GRADE_LEVELS:
            raise ValueError(f"grade_level must be one of {GRADE_LEVELS}")
        if difficulty not in DIFFICULTIES:
            raise ValueError(f"difficulty must be one of {DIFFICULTIES}")

        #Build the session question bank
        pool = list(self._all_questions[grade_level.upper()][difficulty])
        if not pool:
            raise ValueError("No questions found for the selected grade level and difficulty.")

        random.shuffle(pool)
        if limit is not None:
            pool = pool[:max(0, int(limit))]

        self.question_bank = pool
        self._current_index = 0     #the current question number
        self.score = 0              #the current score of the player
        self._session_meta["grade_level"] = grade_level.upper()
        self._session_meta["difficulty"] = difficulty

    #Core Spec Methods
    def display_question(self) -> Optional[Question]: 
        """
        Gives one question to the player.
        Returns None if we're out of questions.
        """
        if self._current_index >= len(self.question_bank):
            print("\nNo more questions in this session.\n")
            return None
        q = self.question_bank[self._current_index]

        print("\nQuestion", self._current_index + 1)
        print(q.get_question_text())
        for i, choice in enumerate(q.get_answers(), start=0):
            label = chr(ord('A') + i)
            print(f" {label}) {choice}")
        return q

    def check_answer(self, user_input: str) -> bool:
        """
        Check if the player's answer is correct.
        Accepts 'A'/'B'/'C'/'D' or the full answer text and is NOT case-sensitive.
        Advances to the next question and updates score if correct.
        Returns True if correct, False otherwise.
        """
        if self._current_index >= len(self.question_bank):
            raise IndexError("No current question to answer.")

        q = self.question_bank[self._current_index]
        answers = q.get_answers()
        correct_letter = q.get_correct_answer().upper()

        user_clean = user_input.strip()
        user_letter: Optional[str] = None

        if user_clean:
            #If user typed a letter
            if len(user_clean) == 1 and user_clean.isalpha():
                user_letter = user_clean.upper()
            else:
                #Try match by answer text
                for i, choice in enumerate(answers):
                    if user_clean.lower() == choice.lower():
                        user_letter = chr(ord('A') + i)
                        break

        is_correct = (user_letter == correct_letter)
        if is_correct:
            #Dynamically get points (polymorphism)
            if hasattr(q, "get_points"):
                self.score += q.get_points()
            else:
                self.score += 1
            print("Correct!")
        else:
            print(f"Wrong. The correct answer is {correct_letter}) {answers[ord(correct_letter)-65]}")

        #advance to next question
        self._current_index += 1
        return is_correct

    def get_score(self) -> int:
        '''
        Returns the current score of the player
        '''
        return self.score

    def shuffle_question_bank(self) -> None:
        '''
        Rearrange the list of questions
        '''
        random.shuffle(self.question_bank)
        self._current_index = 0

    def reset_game(self) -> None:
        '''
        Reset the status of the game
        '''
        self.question_bank = []
        self.score = 0
        self._current_index = 0
        self._session_meta = {"grade_level": "", "difficulty": ""}

    #Save/Resume
    def save_game(self, filename: str = "savegame.json") -> None:
        data = {
            "meta": self._session_meta,
            "score": self.score,
            "current_index": self._current_index,
            # Persist questions remaining by serializing minimal fields
            "remaining": [
                {
                    "question_text": q.get_question_text(),
                    "answers": q.get_answers(),
                    "correct": q.get_correct_answer(),
                    "points": getattr(q, "get_points", lambda: 1)(),
                }
                for q in self.question_bank[self._current_index :]
            ],
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Game saved to {filename}.")

    def load_game(self, filename: str = "savegame.json") -> None:
        if not os.path.exists(filename):
            raise FileNotFoundError("No saved game found.")
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._session_meta = data.get("meta", {"grade_level": "", "difficulty": ""})
        self.score = int(data.get("score", 0))
        self._current_index = 0  # we'll rebuild the bank and start index at 0

        restored: List[Question] = []
        for item in data.get("remaining", []):
            q_cls = {
                1: EasyQuestion,
                3: MediumQuestion,
                5: HardQuestion,
            }.get(int(item.get("points", 1)), Question)
            q = q_cls(item["question_text"], item["answers"], item["correct"])  # type: ignore[arg-type]
            restored.append(q)

        self.question_bank = restored
        print("Saved game loaded.")

    #CLI Helpers
    def play(self, player: Player, num_questions: Optional[int] = None) -> None:
        if num_questions is not None:
            # Trim the session to the requested number *from current index*
            remaining = self.question_bank[self._current_index :]
            remaining = remaining[: max(0, int(num_questions))]
            self.question_bank = remaining
            self._current_index = 0

        while True:
            q = self.display_question()
            if q is None:
                break
            # get user input with validation
            answer = self._prompt_answer()
            self.check_answer(answer)

        #Sync score to the player and show summary
        player.reset_score()
        player.add_score(self.score)
        print(f"\n\nSession complete! {player.get_name()} scored {player.get_score()} points.")

    @staticmethod
    def _prompt_answer() -> str:
        while True:
            user_in = input("Your answer (A/B/C/D or full text, or 'S' to save & quit): ").strip()
            if not user_in:
                print("Please enter a choice.")
                continue
            if user_in.lower() == 's':
                return 'S'
            if len(user_in) == 1 and user_in.upper() in {'A','B','C','D'}:
                return user_in.upper()
            # allow full-text answers (not strictly validated here)
            return user_in


#TESTING/UI


def _menu() -> None:
    print("\n==== QUIZ/TRIVIA GAME ====")
    print("1) New Session")
    print("2) Resume Saved Game")
    print("3) Show Leaderboard")
    print("4) Exit")


def _choose(prompt: str, options: List[str]) -> str:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, start=1):
        print(f" {i}) {opt}")
    while True:
        try:
            sel = int(input("Select number: "))
            if 1 <= sel <= len(options):
                return options[sel - 1]
        except ValueError:
            pass
        print("Invalid selection. Try again.")


def main():
    game = QuizGame()

    while True:
        _menu()
        choice = input("Enter choice: ").strip()

        if choice == '1':
            name = input("Enter player name: ").strip() or "Player"
            grade = _choose("Choose grade level:", GRADE_LEVELS)
            diff = _choose("Choose difficulty:", DIFFICULTIES)
            try:
                limit = input("How many questions? (blank = all): ").strip()
                limit_int = int(limit) if limit else None
            except ValueError:
                limit_int = None

            player = Player(name, grade)
            try:
                game.configure_session(grade, diff, limit=limit_int)
            except ValueError as e:
                print("Error:", e)
                continue

            #Play loop with save/quit option
            while True:
                q = game.display_question()
                if q is None:
                    break
                answer = game._prompt_answer()
                if answer.upper() == 'S':
                    game.save_game()
                    print("Returning to main menu...")
                    break
                game.check_answer(answer)

            #If finished naturally, record score
            if game._current_index >= len(game.question_bank):
                player.reset_score()
                player.add_score(game.get_score())
                print(f"\nSession complete! {player.get_name()} scored {player.get_score()} points.")
                # Save to leaderboard
                try:
                    save_score(player)
                    print("Score saved.")
                except Exception as e:
                    print("Could not save score:", e)

        elif choice == '2':
            try:
                game.load_game()
            except Exception as e:
                print("Error:", e)
                continue

            name = input("Enter player name: ").strip() or "Player"
            grade = game._session_meta.get("grade_level", "ELEMENTARY") or "ELEMENTARY"
            player = Player(name, grade)

            #Continue playing
            while True:
                q = game.display_question()
                if q is None:
                    break
                answer = game._prompt_answer()
                if answer.upper() == 'S':
                    game.save_game()
                    print("Returning to main menu...")
                    break
                game.check_answer(answer)

            if game._current_index >= len(game.question_bank):
                player.reset_score()
                player.add_score(game.get_score())
                print(f"\nSession complete! {player.get_name()} scored {player.get_score()} points.")
                try:
                    save_score(player)
                    print("Score saved.")
                except Exception as e:
                    print("Could not save score:", e)

        elif choice == '3':
            try:
                show_leaderboard()
            except Exception as e:
                print("Error:", e)

        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
