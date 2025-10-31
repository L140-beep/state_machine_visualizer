from typing import Literal, List
from abc import ABC, abstractmethod


class ElementsList(ABC):
    def __init__(self):
        ...

    @abstractmethod
    def append(self, *args):
        ...

    @abstractmethod
    def draw(self):
        ...


class CyberBearMessage(ElementsList):
    ...


class StringSettings():
    ...
