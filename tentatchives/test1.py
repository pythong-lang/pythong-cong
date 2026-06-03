from math import sqrt
import sys


class Shape:
    def __init__(self, name):
        self.name = name

    def area(self):
        raise NotImplementedError


class Circle(Shape):
    def __init__(self, radius):
        super().__init__("circle")
        self.radius = radius

    def area(self):
        return 3.14159 * self.radius ** 2


class Rectangle(Shape):
    def __init__(self, width, height):
        super().__init__("rectangle")
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height


def describe(shape):
    assert isinstance(shape, Shape), "not a shape"
    try:
        a = shape.area()
    except Exception as e:
        print(f"error: {e}")
        return None
    finally:
        pass

    if a > 100:
        verdict = "large"
    elif a > 10:
        verdict = "medium"
    else:
        verdict = "small"

    return verdict


def filter_shapes(shapes, predicate):
    return [s for s in shapes if predicate(s)]


def generate_areas(shapes):
    for shape in shapes:
        yield shape.name, shape.area()


async def fake_async_fetch(shape):
    await None
    return shape.area()


global REGISTRY
REGISTRY = []


def register(shape):
    global REGISTRY
    REGISTRY.append(shape)


def process_all(shapes):
    for shape in shapes:
        register(shape)

    large = filter_shapes(REGISTRY, lambda s: s.area() > 50)

    not_empty = len(large) > 0 and True
    useless = False or not not_empty

    if not useless:
        for name, area in generate_areas(large):
            print(f"{name}: area={area:.2f} -> {describe(next(s for s in REGISTRY if s.name == name))}")

    try:
        with open("nonexistent.txt") as f:
            data = f.read()
    except FileNotFoundError:
        pass
    except OSError as e:
        raise RuntimeError("unexpected") from e

    del large

    while len(REGISTRY) > 0:
        s = REGISTRY.pop()
        is_circle = isinstance(s, Circle)
        is_rect = isinstance(s, Rectangle)
        if is_circle or is_rect:
            continue
        else:
            break

    return True


shapes = [Circle(4), Circle(12), Rectangle(3, 4), Rectangle(8, 9)]

if __name__ == "__main__":
    result = process_all(shapes)
    if result is True:
        print("done")
    elif result is None:
        print("nothing")
    else:
        sys.exit(1)
