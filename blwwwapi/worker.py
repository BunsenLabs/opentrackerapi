from argparse import Namespace
from blwwwapi.logging import named_logger
from blwwwapi.message import Message
from queue import Queue
from threading import Thread, Event
import pickle

class Worker(Thread):
  def __init__(self, id: str, opts: Namespace, queue: Queue):
    self._id = id
    self._opts = opts
    self._queue = queue
    self._stop_event = Event()
    self._waiter = Event()
    self._logger = named_logger(name=self._id)
    self._lives = 3
    super().__init__(daemon=True)

  def run(self):
    try:
      return self.main()
    except Exception as err:
      self.error("Exception caught in main loop: {}".format(err))
      self._lives -= 1
      if self._lives >= 0:
        self.error("Remaining lives: {}".format(self._lives))
        self.error("Trying to restart main loop...")
        self.run()
      else:
        self.error("Exhausted all lives, dying...")
        return 1
    return 0

  def log(self, msg, *args, **kwargs):
    self._logger.info(msg, *args, **kwargs)

  def error(self, msg, *args, **kwargs):
    self._logger.error(msg, *args, **kwargs)

  def stop(self) -> None:
    self._stop_event.set()
    self._waiter.set()

  def is_stopped(self) -> bool:
    return self._stop_event.is_set()

  def emit(self, payload = { "endpoint": "/", "data": str() }) -> None:
    msg = Message(sender=self._id,verb="PUT",payload=payload)
    self._queue.put((self._id, pickle.dumps(msg, pickle.HIGHEST_PROTOCOL),))
