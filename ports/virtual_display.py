from abc import ABC, abstractmethod

class VirtualDisplay(ABC):
    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...
