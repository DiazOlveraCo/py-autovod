import queue
import threading
import time
from logger import logger

class Processor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Processor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.video_queue = queue.Queue()
            self.processing = False
            self.initialized = True

    def process(self, video_path):
        """Add a ts file to the queue to be processed with clipception."""
        logger.debug(f"Queuing video: {video_path}")
        self.video_queue.put(video_path)
        
        if not self.processing:
            threading.Thread(target=self._process_queue, daemon=True).start()

    def _process_queue(self):
        """Process in the queue one by one."""
        self.processing = True
        while not self.video_queue.empty():
            video_path = self.video_queue.get()
            logger.debug(f"Processing video: {video_path}")
            
            self._process_single_file(video_path)
            
            print(f"Finished processing: {video_path}")
            self.video_queue.task_done()
        self.processing = False

    def _process_single_file(self, video_path):
        # Write code to process


processor = Processor()