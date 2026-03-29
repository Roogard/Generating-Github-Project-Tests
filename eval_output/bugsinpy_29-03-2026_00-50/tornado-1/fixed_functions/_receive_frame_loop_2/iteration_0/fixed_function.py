@abc.abstractmethod
async def _receive_frame_loop(self) -> None:
    raise NotImplementedError()