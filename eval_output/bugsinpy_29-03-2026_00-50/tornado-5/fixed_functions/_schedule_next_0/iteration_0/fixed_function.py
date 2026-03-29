def _schedule_next(self):
        if self._running:
            self._update_next(self.io_loop.time())
            self._timeout = self.io_loop.add_timeout(self._next_timeout, self._run)