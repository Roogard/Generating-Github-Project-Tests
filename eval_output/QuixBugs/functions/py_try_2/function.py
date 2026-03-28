def py_try(algo, *args, correct=False):
    if not correct:
        module = __import__("python_programs."+algo)
    else:
        module = __import__("correct_python_programs."+algo)

    fx = getattr(module, algo)

    try:
        return getattr(fx,algo)(*args)
    except:
        return sys.exc_info()