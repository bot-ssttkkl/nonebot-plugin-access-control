from functools import partial
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable

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
        self._container: dict[T, Provider[T]] = {}

    @property
    def parent(self) -> "Context":
        return self._parent

    @property
    def root(self) -> "Context":
        if self._parent is None:
            return self
        else:
            return self._parent.root

    def register_provider(self, interface: type[T], provider: Provider[T]):
        self._container[interface] = provider

    def register_instance(self, interface: type[T], bean: T):
        self._container[interface] = InstanceProvider(bean)

    def register_factory(
        self, interface: type[T], factory: Callable[[], T], is_singleton: bool = True
    ):
        self._container[interface] = FactoryProvider(factory, is_singleton)

    def singleton(self, *args, **kwargs) -> Callable[[type[T]], type[T]]:
        def decorator(cls: type[T]) -> type[T]:
            self.register_factory(cls, lambda: cls(*args, **kwargs))
            return cls

        return decorator

    def eager_singleton(self, *args, **kwargs) -> Callable[[type[T]], type[T]]:
        def decorator(cls: type[T]) -> type[T]:
            bean = cls(*args, **kwargs)
            self.register_instance(cls, bean)
            return cls

        return decorator

    def singleton_factory(
        self, interface: type[T], *args, **kwargs
    ) -> Callable[[Callable[[...], T]], Callable[[...], T]]:
        def decorator(factory: Callable[[...], T]) -> Callable[[...], T]:
            self.register_factory(interface, partial(factory, *args, **kwargs))
            return factory

        return decorator

    def eager_singleton_factory(
        self, interface: type[T], *args, **kwargs
    ) -> Callable[[Callable[[...], T]], Callable[[...], T]]:
        def decorator(factory: Callable[[...], T]) -> Callable[[...], T]:
            bean = factory(*args, **kwargs)
            self.register_instance(interface, bean)
            return factory

        return decorator

    def unregister(self, interface: type[T]) -> bool:
        if interface in self._container:
            del self._container[interface]
            return True
        return False

    def bind(self, interface: type[T], impl_interface: type[T2]):
        self._container[interface] = FactoryProvider(
            lambda: self._find_provider(impl_interface).provide(), is_singleton=False
        )

    def bind_singleton_to(
        self, interface: type[T], *args, **kwargs
    ) -> Callable[[type[T2]], type[T2]]:
        def decorator(cls: type[T2]) -> type[T2]:
            self.singleton(*args, **kwargs)(cls)
            self.bind(interface, cls)
            return cls

        return decorator

    def require(self, interface: type[T]) -> T:
        return self._find_provider(interface).provide()

    def _find_provider(self, interface: type[T]) -> Provider[T]:
        if interface in self._container:
            return self._container[interface]
        elif self._parent is not None:
            return self._parent._find_provider(interface)
        else:
            raise KeyError(interface)

    def __getitem__(self, key: type[T]):
        return self.require(key)

    def __contains__(self, key: type[T]) -> bool:
        if key in self._container:
            return True
        elif self._parent is not None:
            return self._parent.__contains__(key)
        else:
            return False


context = Context()

__all__ = ("Context", "context")
