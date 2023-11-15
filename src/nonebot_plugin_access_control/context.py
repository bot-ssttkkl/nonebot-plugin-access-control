from abc import ABC, abstractmethod
from typing import TypeVar, Type, Callable, Generic, Dict

T = TypeVar("T")
T2 = TypeVar("T2")


class Provider(ABC, Generic[T]):
    @abstractmethod
    def provide(self) -> T:
        ...


class InstanceProvider(Provider[T], Generic[T]):
    def __init__(self, instance: T):
        self._instance = instance

    def provide(self) -> T:
        return self._instance


class FactoryProvider(Provider[T], Generic[T]):
    def __init__(self, factory: Callable[[], T], is_singleton: bool = True):
        self._factory = factory
        self._is_singleton = is_singleton

        self._cache = None
        self._cached = False

    def provide(self) -> T:
        if not self._is_singleton:
            return self._factory()

        if not self._cached:
            self._cache = self._factory()  # just let it throw
            self._cached = True
        return self._cache


class Context:
    def __init__(self, parent: "Context" = None):
        self._parent = parent
        self._container: Dict[T, Provider[T]] = {}

    @property
    def parent(self) -> "Context":
        return self._parent

    @property
    def root(self) -> "Context":
        if self._parent is None:
            return self
        else:
            return self._parent.root

    def register_provider(self, interface: Type[T], provider: Provider[T]):
        self._container[interface] = provider

    def register_instance(self, interface: Type[T], bean: T):
        self._container[interface] = InstanceProvider(bean)

    def register_factory(self, interface: Type[T], factory: Callable[[], T], is_singleton: bool = True):
        self._container[interface] = FactoryProvider(factory, is_singleton)

    def register_singleton(self, *args, **kwargs) -> Callable[[Type[T]], Type[T]]:
        def decorator(cls: Type[T]) -> Type[T]:
            self.register_factory(cls, lambda: cls(*args, **kwargs))
            return cls

        return decorator

    def register_eager_singleton(self, *args, **kwargs) -> Callable[[Type[T]], Type[T]]:
        def decorator(cls: Type[T]) -> Type[T]:
            bean = cls(*args, **kwargs)
            self.register_instance(cls, bean)
            return cls

        return decorator

    def unregister(self, interface: Type[T]) -> bool:
        if interface in self._container:
            del self._container[interface]
            return True
        return False

    def bind(self, interface: Type[T], impl_interface: Type[T2]):
        self._container[interface] = FactoryProvider(lambda: self._find_provider(impl_interface).provide(),
                                                     is_singleton=False)

    def bind_singleton_to(self, interface: Type[T], *args, **kwargs) -> Callable[[Type[T2]], Type[T2]]:
        def decorator(cls: Type[T2]) -> Type[T2]:
            self.register_singleton(*args, **kwargs)(cls)
            self.bind(interface, cls)
            return cls

        return decorator

    def require(self, interface: Type[T]) -> T:
        return self._find_provider(interface).provide()

    def _find_provider(self, interface: Type[T]) -> Provider[T]:
        if interface in self._container:
            return self._container[interface]
        elif self._parent is not None:
            return self._parent._find_provider(interface)
        else:
            raise KeyError(interface)

    def __getitem__(self, key: Type[T]):
        return self.require(key)

    def __contains__(self, key: Type[T]) -> bool:
        if key in self._container:
            return True
        elif self._parent is not None:
            return self._parent.__contains__(key)
        else:
            return False


__all__ = ("Context",)
