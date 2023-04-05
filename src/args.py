import sys
import pickle
import engine

# PARSE COMMAND-LINE ARGUMENTS
def parseArguments():
    saveFileSpecified = False
    argMode = ""
    for argument in sys.argv:
        if argument == "-d" or argument == "--depth":
            argMode = "depth"
            continue
        elif argument == "-f" or argument == "--file":
            argMode = "file"
            continue

        if argMode == "depth":
            argMode = ""
            if argument.isdigit():
                engine.get().set_depth(int(argument))
            else:
                engine.get().set_depth(18)
        elif argMode == "file":
            argMode = ""
            try:
                engine.set_analysis_results(pickle.load(open("save.asys", "rb")))
                saveFileSpecified = True
            except:
                print("Analysis savefile failed to load.")

    if not saveFileSpecified:
        engine.startAnalysisThread()