from ports import VirtualDisplay

class NoopDisplay(VirtualDisplay):
    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass
