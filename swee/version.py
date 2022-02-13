from typing import Optional, Tuple


class Version:
    def __init__(
        self,
        major_hash: int,
        minor_hash: Tuple[int, ...],
        *,
        major_version: Optional[int] = None,
        minor_version: Optional[int] = None,
    ):
        self._major_hash = major_hash
        self._minor_hash = minor_hash
        self._major_version = 1 if major_version is None else major_version
        self._minor_version = 0 if minor_version is None else minor_version

    @property
    def major_version(self) -> int:
        return self._major_version

    @property
    def minor_version(self) -> int:
        return self._minor_version

    @property
    def major_hash(self) -> int:
        return self._major_hash

    @property
    def minor_hash(self) -> Tuple[int, ...]:
        return self._minor_hash

    def __str__(self):
        return f'{self.major_version}.{self.minor_version}'

    def set_old_version(self, old_version: Optional['Version']):
        self._major_version = old_version.major_version + (self.major_hash != old_version.major_hash)
        self._minor_version = 0 if self.major_version != old_version.major_version else \
            old_version._minor_version + (self.minor_hash != old_version.minor_hash)
