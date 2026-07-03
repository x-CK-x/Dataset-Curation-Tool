from collections import OrderedDict

import torch


class LRUCache:
    def __init__(self, max_size: int=128):
        self.cache = OrderedDict()
        self.max_size = max_size

    def _to_cache(self, value):
        return value

    def _from_cache(self, value):
        return value

    def get(self, key):
        if key not in self.cache:
            return None
        # Move key to end to mark it as recently used
        self.cache.move_to_end(key)
        value = self.cache[key]
        return self._from_cache(value)

    def put(self, key, value):
        if key in self.cache:
            # Overwrite and mark as recently used
            self.cache.move_to_end(key)
        value = self._to_cache(value)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            # Remove least recently used item
            self.cache.popitem(last=False)

    def __contains__(self, key):
        return key in self.cache

    def __len__(self):
        return len(self.cache)

    def clear(self):
        self.cache.clear()


class DeviceLRUCache(LRUCache):
    def __init__(self,
                 device: torch.device,
                 rest_device: torch.device = torch.device('cpu'),
                 cache_dtype: torch.dtype = torch.float32,
                 max_size: int = 128):
        super().__init__(max_size=max_size)
        self._rest_device = rest_device
        self._device = device
        self._cache_dtype = cache_dtype

    def _to_cache(self, value: torch.Tensor) -> torch.Tensor:
        return value.to(self._rest_device).to(self._cache_dtype)

    def _from_cache(self, value) -> torch.Tensor:
        return value.to(self._device).to(torch.float32)