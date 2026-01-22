from src.queue_manager import QueueManager
from src.config import load_config

config = load_config()
manager = QueueManager(config)
manager.load_state()
manager.clear_queue()
print("Queue cleared!")
