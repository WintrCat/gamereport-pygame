import threading
import pickle
import time
import engine
import accuracy

currentlySaving = False

def is_currently_saving():
    return currentlySaving

def dump():
    global currentlySaving
    currentlySaving = True
    pickle.dump(engine.get_analysis_results(), open("save.asys", "wb"))
    time.sleep(2)
    currentlySaving = False

def load():
    results: engine.AnalysisResults = pickle.load(open("save.asys", "rb"))
    engine.set_analysis_results(results)
    accuracy.set_white_accuracy(results.accuracies[0])
    accuracy.set_black_accuracy(results.accuracies[1])

def threadedDump():
    t = threading.Thread(target=dump)
    t.start()