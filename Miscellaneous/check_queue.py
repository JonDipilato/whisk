from src.queue_manager import QueueManager
from src.config import load_config

m = QueueManager(load_config())
m.load_state()
m.show_status()
