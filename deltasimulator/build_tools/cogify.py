import cogapp
from io import StringIO
import textwrap


def cogify(template, globals=None, cog=cogapp.cogapp.Cog(), verbose=False):
    """
    Passes the string str through the cog template engine.

    Parameters
    ----------
    template : str
        cog template string.
    globals : Optional[dict]
        dict for variable lookup within the cog template.
        pass globals=locals() at the call site to make local names
        available to the template. Otherwise no names will be present.
    cog
        Cog instance to use: pass in a alternative if you wish to change
        the behaviour of the engine.

    Returns
    -------
    bytes
        a bytes object of the string encoded as utf-8.


    .. note::
        Leading whitespace is stripped from every line: you can allign a
        multiline string to pass to this function with the containing block and
        it will be fixed up.

    .. note::
        cog.outl() is required for getting strings into the output area.

    .. warning::
        Ensure there are no explicit newlines within a cog python block.
        If strings with newlines are present, they break python code formatting.
    """
    if globals is None:
        globals = dict()
    template = textwrap.dedent(template)
    fOld = StringIO(template)
    fNew = StringIO()
    try:
        if not verbose:
            cog.options.bDeleteCode = True
        cog.processFile(fOld, fNew, fname=None, globals=globals)
        return fNew.getvalue().encode("utf-8")
    except cogapp.cogapp.CogUserException as ex:
        if "DeltaRuntimeExit" in ex.args[0]:
            raise ValueError(
                "DeltaRuntimeExit raised during build process.") from ex
        else:
            raise ValueError("Exception raised during build process.") from ex
