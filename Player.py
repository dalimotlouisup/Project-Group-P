class Player:
    """ This class will keep track of each player's name, grade level, and score """

    def __init__(self, name, grade_level):
        """Initialize player with name, grade level, and starting score."""
        self._name = name
        self._grade_level = grade_level
        self._score = 0

    def get_name(self):
        return self._name

    def get_grade_level(self):
        """Elementary or High School"""
        return self._grade_level

    def get_score(self):
        return self._score

    def add_score(self, points):
        self._score += points

    def reset_score(self):
        """Reset the player's score back to 0."""
        self._score = 0


#Scores File Handling

def save_score(player, filename="scores.txt"):
    """Save the player's score to a text file"""
    with open(filename, "a") as file:
        file.write(f"{player.get_name()}, {player.get_grade_level()}, {player.get_score()}\n")


def load_scores(filename="scores.txt"):
    """Load all scores from the text file and return as a list of tuples"""
    scores = []
    try:
        with open(filename, "r") as file:
            for line in file:
                name, grade_level, score = line.strip().split(", ")
                scores.append((name, grade_level, int(score)))
    except FileNotFoundError:
        print("No scores file found yet.")
    return scores


def show_leaderboard(filename="scores.txt"):
    """Display the top scores sorted from highest to lowest"""
    scores = load_scores(filename)
    # sort by score (3rd item in tuple), reverse = highest first
    scores.sort(key=lambda x: x[2], reverse=True)

    print("\n--- Leaderboard ---")
    for rank, (name, grade_level, score) in enumerate(scores, start=1):
        print(f"{rank}. {name} ({grade_level}) - {score} points")
