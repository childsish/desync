import threading
import contextlib


class ResourceManager:
    def __init__(self, **kwargs: int):
        self.max_resources = kwargs
        self.available_resources = kwargs.copy()
        self.update = threading.Event()

    @contextlib.contextmanager
    def request(self, **kwargs):
        granted = self._process_request(kwargs)
        while any(value is None for value in granted.values()):
            self.update.clear()
            self.update.wait()
            granted = self._process_request(kwargs)
        for resource, value in granted.items():
            self.available_resources[resource] -= value
        yield granted
        for resource, value in granted.items():
            self.available_resources[resource] += value
        self.update.set()

    def _process_request(self, request):
        granted = {}
        for key, value in request.items():
            parts = key.split('_', 1)
            if len(parts) == 1:
                if value > self.max_resources[key]:
                    raise ValueError(f'requesting {value} {key}, but a maximum of {self.available_resources[key]} are available')
                elif value <= self.available_resources[key]:
                    granted[key] = value
                else:
                    granted[key] = None
            elif parts[0] == 'min':
                if value > self.max_resources[parts[0]]:
                    raise ValueError(f'requesting a minimum of {value} {key}, but a maximum of {self.available_resources[key]} are available')
                elif value <= self.available_resources[parts[1]]:
                    granted[parts[1]] = max(value, self.available_resources[parts[1]])
                else:
                    granted[parts[1]] = None
            elif parts[0] == 'max' and self.available_resources[parts[1]] > 0:
                granted[parts[1]] = min(value, self.available_resources[parts[1]])
            else:
                granted[parts[1]] = None
        return granted
