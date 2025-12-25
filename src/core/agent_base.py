"""
Base Agent Class
Enforces a common interface for all agents in the system.
"""
from abc import ABC, abstractmethod

class Agent(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def process(self, *args, **kwargs):
        """
        Main processing method for the agent.
        Must be implemented by subclasses.
        """
        pass

    def log(self, message):
        print(f"[{self.name}] {message}")
