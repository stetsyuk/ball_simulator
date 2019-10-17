import tkinter as tk
import abc
import uuid
import random as rnd
import time


def random_color():
    return "#{:06x}".format(rnd.randrange(0, 1<<24))


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

    def render_debug(self):
        pass


class NotImplementedError(RuntimeError):
    pass


class Vector2d:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __iadd__(self, other):
        if isinstance(other, Vector2d):
            self.x += other.x
            self.y += other.y
            return self
        else:
            raise TypeError("Only vector can be added to vector")

    def __add__(self, other):
        if isinstance(other, Vector2d):
            s = Vector2d(self.x, self.y)
            s.x += other.x
            s.y += other.y
            return s
        else:
            raise TypeError("Only vector can be added to vector")

    def __mul__(self, other):
        s = Vector2d(self.x, self.y)
        s.x *= other
        s.y *= other
        return s

    def __imul__(self, other):
        self.x *= other
        self.y *= other
        return self

    def __abs__(self):
        return abs(complex(self.x, self.y))


class IIntersectable(IObject, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def contains(self, point: Vector2d):
        pass


class IClickable(IObject):
    def clicked(self):
        pass


class FrameStats(IRenderable):
    def render(self):
        pass

    def render_debug(self):
        duration = self.game.tick_stamp - self.game.last_tick_stamp
        text = "Tick duration: {0} ms\nFPS: {1}".format(int(1000*duration), int(1.0/duration))

        self.game.next_frame_canvas.create_text(650, 50, text=text, font=("Arial", 20), justify=tk.RIGHT)


class Ball(IRenderable, IIntersectable, IClickable):
    def __init__(self, game, position: Vector2d, radius: float):
        self.position = position
        self.radius = radius
        self.color = random_color()
        self._destroyed = False

        self.velocity = Vector2d(rnd.randrange(-50, 50), rnd.randrange(-50, 50))
        super().__init__(game)

    def render(self):
        self.game.next_frame_canvas.create_oval(self.position.x - self.radius, self.position.y - self.radius,
                                                self.position.x + self.radius, self.position.y + self.radius,
                                                fill=self.color, width=0)

    def render_debug(self):
        self.game.next_frame_canvas.create_oval(self.position.x - 2, self.position.y - 2,
                                                self.position.x + 2, self.position.y + 2,
                                                fill='black', width=0)
        self.game.next_frame_canvas.create_text(self.position.x, self.position.y + 15,
                                                text=str(self.uuid).split('-')[0], fill='black')

        vel_base = self.position + self.velocity * self.radius * (1 / abs(self.velocity))
        self.game.next_frame_canvas.create_line(vel_base.x, vel_base.y,
                                                vel_base.x + self.velocity.x, vel_base.y + self.velocity.y,
                                                width='3')

    def contains(self, point: Vector2d):
        return self.radius > abs(complex(self.position.x - point.x, self.position.y - point.y))

    @property
    def destroyed(self):
        return self._destroyed

    def tick(self):
        self.position += self.velocity * 0.02

        if self.position.x + self.radius > self.game.maxw:
            self.velocity.x *= -1

        if self.position.y + self.radius > self.game.maxh:
            self.velocity.y *= -1

        if self.position.x - self.radius < 0:
            self.velocity.x *= -1

        if self.position.y - self.radius < 0:
            self.velocity.y *= -1

    def clicked(self):
        print("Clicked ball {0}".format(str(self.uuid)))
        self.position.x = rnd.randrange(100, 700)
        self.position.y = rnd.randrange(100, 600)
        self.velocity = Vector2d(rnd.randrange(-50, 50), rnd.randrange(-50, 50))


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
    def __init__(self, debug=False):
        self.root = tk.Tk()
        self.root.geometry('800x600')

        self._frames = [tk.Canvas(self.root, bg='white')]
        self._frame_index = 0

        self.frame_canvas.pack(fill=tk.BOTH, expand=1)

        self.objects = {}

        self.debug = debug
        self.pause = False

        self.maxh, self.maxw = 600, 800

        self.last_tick_stamp = time.time()
        self.tick_stamp = time.time()

        ctr = FrameStats(self)
        self.objects[ctr.uuid] = ctr

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

        self.tick_stamp = time.time()

        if not self.pause:
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
                if self.debug:
                    obj.render_debug()

        self.last_tick_stamp = self.tick_stamp
        self.root.after(10, self.tick)

    def clicked(self, event):
        point = Vector2d(event.x, event.y)
        for key in self.objects:
            obj = self.objects[key]
            if isinstance(obj, IIntersectable) and isinstance(obj, IClickable) and obj.contains(point):
                obj.clicked()

    def toggle_pause(self, *args):
        self.pause = not self.pause

    def toggle_debug(self, *args):
        self.debug = not self.debug

    def run(self):
        factory = BallFactory(self)
        for i in range(5):
            factory.create_random_ball()

        self.root.bind('<Button-1>', self.clicked)
        self.root.bind('<space>', self.toggle_pause)
        self.root.bind('<d>', self.toggle_debug)
        self.root.after(10, self.tick)
        self.root.mainloop()


if __name__ == '__main__':
    game = Game(debug=True)
    game.run()