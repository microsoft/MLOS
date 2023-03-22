"""
Test
"""
# pylint: disable=all

from abc import ABCMeta, abstractmethod

from typing import Protocol, runtime_checkable


@runtime_checkable
class MyBaseClass(Protocol):
    """MyBaseClass"""

    def do_a_non_abstract_thing(self):
        print(f"{__class__.__name__}:{__name__}")


@runtime_checkable
class MyInterface(MyBaseClass, Protocol, metaclass=ABCMeta):
    """MyInterface"""

    @abstractmethod
    def do_something(self):
        pass


@runtime_checkable
class MyOuterface(Protocol, metaclass=ABCMeta):
    """MyOuterface"""

    @abstractmethod
    def do_something_else(self):
        pass


class MySubInterface(MyInterface, Protocol, metaclass=ABCMeta):
    """MySubInterface"""

    @abstractmethod
    def do_more_things(self):
        pass


class MySubImplementation(MyInterface):
    """MySubImplementation"""

    def do_something():
        print(f"{__class__.__name__}:{__name__}")

    def do_more_things():
        print(f"{__class__.__name__}:{__name__}")


class MyImplicitImplementation():
    """MyImplicitImplementation"""

    def do_something(self):
        print(f"{__class__.__name__}:{__name__}")

    def do_something_else(self):
        print(f"{__class__.__name__}:{__name__}")


class MyExplicitImplementation(MyInterface, MyOuterface):
    """MyExplicitImplementation"""

    def do_something(self):
        print(f"{__class__.__name__}:{__name__}")

    def do_something_else(self):
        print(f"{__class__.__name__}:{__name__}")


def somethinger(somethingable: MyInterface):
    """Somethinger"""
    assert isinstance(somethingable, MyInterface)
    somethingable.do_something()


def something_elser(something_elseable: MyOuterface):
    """Something_elser"""
    assert isinstance(something_elseable, MyOuterface)
    something_elseable.do_something_else()


def sub_somethinger(sub_somethinger: MySubInterface):
    """Sub_Somethinger"""
    assert isinstance(sub_somethinger, MySubInterface)
    sub_somethinger.do_something()
    sub_somethinger.do_more_things()


def main():
    """Main"""

    myBaseClass = MyBaseClass()
    myBaseClass.do_a_non_abstract_thing()

    implicitImplementation = MyImplicitImplementation()
    implicitImplementation.do_something()

    explicitImplementation = MyExplicitImplementation()

    subInterfaceInstance = MySubImplementation()
    subInterfaceInstance.do_a_non_abstract_thing()

    somethinger(implicitImplementation)
    something_elser(implicitImplementation)

    somethinger(explicitImplementation)
    something_elser(explicitImplementation)

    sub_somethinger(subInterfaceInstance)

if __name__ == '__main__':
    main()
