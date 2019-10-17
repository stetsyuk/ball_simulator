import tkinter as tk
import abc
import uuid
import collections
import random as rnd
import math


def random_color():
    return "#{:06x}".format(rnd.randrange(0, 2**24))


class IObject:
    def __init__(self, game):
        self.uuid = uuid.uuid4()
        self.game = game
        game.objects[self.uuid] = self

    def tick(self):
        pass

    @property
    def destroyed(self):
        return False


class IRenderable(IObject, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def render(self):
        pass


class Vector2d:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class IIntersectable(IObject, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def contains(self, point: Vector2d):
        pass


class IClickable(IObject):
    def clicked(self):
        pass


class Ball(IRenderable, IIntersectable, IClickable):
    def __init__(self, game, position: Vector2d, radius: float):
        self.position = position
        self.radius = radius
        self.color = random_color()
        self._destroyed = False
        super().__init__(game)

    def render(self):
        self.game.next_frame_canvas.create_oval(self.position.x - self.radius, self.position.y - self.radius,
                                                self.position.x + self.radius, self.position.y + self.radius,
                                                fill=self.color, width=0)

    def contains(self, point: Vector2d):
        return self.radius > abs(complex(self.position.x - point.x, self.position.y - point.y))

    @property
    def destroyed(self):
        return self._destroyed

    def tick(self):
        self.position.x += rnd.randrange(-1, 2)
        self.position.y += rnd.randrange(-1, 2)

    def clicked(self):
        print("Clicked ball {0}".format(str(self.uuid)))
        self.position.x = rnd.randrange(100, 700)
        self.position.y = rnd.randrange(100, 600)


class BallFactory:
    def __init__(self, game):
        self.game = game

    def create_random_ball(self):
        radius = rnd.randrange(10, 50)
        position = Vector2d(rnd.randrange(100, 700), rnd.randrange(100, 500))
        ball = Ball(self.game, position, radius)
        self.game.objects[ball.uuid] = ball
        return ball


class Game:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry('800x600')

        self._frames = [tk.Canvas(self.root, bg='white')]
        self._frame_index = 0

        self.frame_canvas.pack(fill=tk.BOTH, expand=1)

        self.objects = {}

    def sanitize_frame_index(self, index=None):
        if index is None:
            index = self._frame_index
        return index % len(self._frames)

    @property
    def frame_canvas(self):
        return self._frames[self._frame_index]

    @property
    def next_frame_canvas(self):
        return self._frames[self.sanitize_frame_index(self._frame_index)]

    def switch_frame(self):
        # self.frame_canvas.pack_forget()
        self.frame_canvas.delete(tk.ALL)
        self._frame_index += 1
        self._frame_index = self.sanitize_frame_index()
        # self.frame_canvas.pack(fill=tk.BOTH, expand=1)

    def tick(self):
        self.switch_frame()
        for key in self.objects:
            self.objects[key].tick()

        dead = []
        for key in self.objects:
            if self.objects[key].destroyed:
                dead.append(key)

        for key in dead:
            del self.objects[key]

        for key in self.objects:
            obj = self.objects[key]
            if isinstance(obj, IRenderable):
                obj.render()

        self.root.after(100, self.tick)

    def clicked(self, event):
        point = Vector2d(event.x, event.y)
        for key in self.objects:
            obj = self.objects[key]
            if isinstance(obj, IIntersectable) and isinstance(obj, IClickable) and obj.contains(point):
                obj.clicked()

    def run(self):
        factory = BallFactory(self)
        for i in range(5):
            factory.create_random_ball()

        self.root.bind('<Button-1>', self.clicked)
        self.root.after(10, self.tick)
        self.root.mainloop()


if __name__ == '__main__':
    game = Game()
    game.run()