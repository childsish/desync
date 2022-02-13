from typing import Any, Dict, Optional


class Cache:
    def __init__(self, outputs: Optional[Dict[int, Dict[int, Any]]] = None):
        self._outputs = {} if outputs is None else outputs

    def set_outputs(self, func_hash: int, input_hash: int, outputs: Any):
        self._outputs.setdefault(func_hash, {})
        self._outputs[func_hash][input_hash] = outputs

    def get_outputs(self, func_hash, input_hash):
        return self._outputs.get(func_hash, {}).get(input_hash, None)

    def has_outputs(self, func_hash, input_hash):
        return input_hash in self._outputs.get(func_hash, {})
