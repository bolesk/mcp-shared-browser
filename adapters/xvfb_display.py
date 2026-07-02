from pyvirtualdisplay import Display
from ports import VirtualDisplay

class XvfbDisplay(VirtualDisplay):
    def __init__(self, size: tuple = (1920, 1080)):
        self._size = size
        self._display: Display | None = None

    async def start(self) -> None:
        self._display = Display(visible=False, size=self._size)
        self._display.start()

    async def stop(self) -> None:
        if self._display:
            self._display.stop()
            self._display = None
