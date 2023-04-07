import threading
import pickle
import time
import engine

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
    engine.set_analysis_results(pickle.load(open("save.asys", "rb")))

def threadedDump():
    t = threading.Thread(target=dump)
    t.start()