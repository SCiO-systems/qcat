import warnings
from contextlib import contextmanager


@contextmanager
def ignored(*exceptions):
    """
    Context manager to ignore particular exceptions.

    Example:

        obj = None
        with ignored(MyModel.DoesNotExist):
            obj = MyModel.objects.get(id=1)

    :param exceptions: A variable number of exception classes.
    """
    warnings.warn(
        "Use contextlib.suppress instead of this!", DeprecationWarning
    )
    try:
        yield
    except exceptions:
        pass
