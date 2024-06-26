import inspect
from typing import Any, Callable, Dict, Optional
import pandas as pd

def to_metadata(metadata: Optional[pd.DataFrame]) -> Optional[List[pd.Series]]:
    if metadata is None:
        return None
    return [idx_series[1] for idx_series in metadata.iterrows()]

def filter_kwargs(function: Callable, **kwargs: Any) -> Dict[str, Any]:
        """
        Filters arguments provided in the kwargs dictionary to be restricted to the arguments legal for
        the called function.

        Parameters
        ----------
        function : Callable
            function over which we filter kwargs for.
        kwargs:
            kwargs that we are filtering for the target function

        Returns
        -------
        dict
            kwargs with the non-legal argument filtered out
        """
        sig = inspect.signature(function)
        filter_keys = [
            param.name
            for param in sig.parameters.values()
            if param.kind == param.POSITIONAL_OR_KEYWORD
        ]
        filtered_dict = {
            filter_key: kwargs[filter_key] for filter_key in filter_keys & kwargs.keys()
        }
        return filtered_dict