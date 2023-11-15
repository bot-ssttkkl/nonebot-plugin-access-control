from inspect import signature


def call_with_params(func, kwargs):
    filtered_kwargs = {}

    sig = signature(func)
    for p in sig.parameters:
        filtered_kwargs[p] = kwargs[p]

    return func(**filtered_kwargs)
