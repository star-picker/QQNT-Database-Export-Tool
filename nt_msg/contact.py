from abc import ABC, abstractmethod

from sqlalchemy.orm.query import Query


class Communicant(ABC):
    @abstractmethod
    def messages(self) -> Query:
        raise NotImplementedError


class Contact(Communicant):
    ...


class Group(Communicant):
    ...
