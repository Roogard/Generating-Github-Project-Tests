def prettyprint(o):
    if isinstance(o, types.GeneratorType):
        return("(generator) " + str(list(o)))
    else:
        return(str(o))