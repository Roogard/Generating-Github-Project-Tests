def periodic_ping(self) -> None:
        """Send a ping to keep the websocket alive

        Called periodically if the websocket_ping_interval is set and non-zero.
        """
        if self.is_closing() and self.ping_callback is not None:
            self.ping_callback.stop()
            return

        # Check for timeout on pong. Make sure that we really have
        # sent a recent ping in case the machine with both server and
        # client has been suspended since the last ping.
        now = IOLoop.current().time()
        since_last_pong = now - self.last_pong
        since_last_ping = now - self.last_ping
        assert self.ping_interval is not None
        assert self.ping_timeout is not None
        if (
            since_last_ping < 2 * self.ping_interval
            and since_last_pong > self.ping_timeout
        ):
            self.close()
            return

        self.write_ping(b"")
        self.last_ping = now