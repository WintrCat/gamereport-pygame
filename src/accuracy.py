import engine

classificationScores = {
    "blunder": 0,
    "mistake": 0.2,
    "inaccuracy": 0.4,
    "good": 0.6,
    "excellent": 0.85,
    "best": 1,
    "great": 1,
    "brilliant": 1,
    "book": 1,
    "forced": 1
}

whiteAccuracy = 0
blackAccuracy = 0

def get_white_accuracy():
    return whiteAccuracy
def set_white_accuracy(accuracy: float):
    global whiteAccuracy
    whiteAccuracy = accuracy

def get_black_accuracy():
    return blackAccuracy
def set_black_accuracy(accuracy: float):
    global blackAccuracy
    blackAccuracy = accuracy

def calculate_accuracy(colour: bool) -> float:
    score = 0
    potentialScore = 0

    classifications = engine.get_analysis_results().classifications
    colourNumber = 0 if colour else 1
    for i, classification in enumerate(classifications):
        if i % 2 == colourNumber:
            score += classificationScores[classification]
            potentialScore += 1

    return round((score / potentialScore) * 100, 1)
