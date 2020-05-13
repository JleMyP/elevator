from enum import IntEnum
from typing import Callable, NamedTuple, Set, Optional

__all__ = ['Direction', 'HardwareElevator', 'Elevator']


class Direction(IntEnum):
    DOWN = -1
    NONE = 0
    UP = 1

    @staticmethod
    def negate(direction: 'Direction'):
        if direction == Direction.UP:
            return Direction.DOWN
        if direction == Direction.DOWN:
            return Direction.UP
        return direction


class PassengersQueue:
    def __init__(self):
        self.queue: Set[int] = set()

    def __contains__(self, floor: int):
        return floor in self.queue

    @property
    def empty(self):
        return not self.queue

    def append(self, floor: int):
        self.queue.add(floor)

    def remove(self, floor: int):
        self.queue.remove(floor)

    def has_up(self, current_floor: int):
        for passenger in self.queue:
            if passenger > current_floor:
                return True
        return False

    def has_down(self, current_floor: int):
        for passenger in self.queue:
            if passenger < current_floor:
                return True
        return False


class Caller(NamedTuple):
    priority: int
    floor: int
    direction: Direction


class CallersQueue:
    def __init__(self):
        self.counter = 0
        self.queue: Set[Caller] = set()

    def __contains__(self, floor: int) -> bool:
        for caller in self.queue:
            if caller.floor == floor:
                return True
        return False

    @property
    def empty(self):
        return not self.queue

    def append(self, floor: int, direction: Direction):
        self.counter += 1
        self.queue.add(Caller(self.counter, floor, direction))

    def remove(self, floor: int):
        for caller in self.queue:
            if caller.floor == floor:
                self.queue.remove(caller)
                return

    def get_first(self):
        if self.queue:
            ordered = sorted(self.queue, key=lambda caller: caller.priority)
            return ordered[0].floor

    def change_direction(self, floor: int, direction: Direction):
        """ Смена желаемого направения вызывающего без потери приоритета """
        for caller in self.queue:
            if caller.floor == floor:
                caller.direction = direction
                return

    def has_above(self, current_floor: int, direction: Direction) -> bool:
        for caller in self.queue:
            if caller.floor > current_floor and caller.direction == direction:
                return True
        return False

    def has_below(self, current_floor: int, direction: Direction) -> bool:
        for caller in self.queue:
            if caller.floor < current_floor and caller.direction == direction:
                return True
        return False

    def get_floor_direction(self, floor: int) -> Optional[Direction]:
        for caller in self.queue:
            if caller.floor == floor:
                return caller.direction


class HardwareElevator:
    def move_up(self): ...
    def move_down(self): ...
    def stop_and_open_doors(self): ...
    def get_current_floor(self) -> int: ...
    def get_current_direction(self) -> Direction: ...

    def add_handler(self, event_type: str, handler: Callable): ...
    def remove_handler(self, event_type: str, handler: Callable): ...


class Elevator:
    """
    ехали вверх и есть пассажиры вверх - едем вверх и по пути высаживаем их и собираем попутчиков
    ехали вниз и есть пассажиры вниз - едем вниз и по пути высаживаем их и собираем попутчиков
    ехали вверх, но пассажиры хотят вниз - едем вниз
    ехали вниз, но пассажиры хотят вверх - едем вверх
    пассажиров нет
        ехали вверх
            1 - выше нас есть вызывающие желающие наверх - едем вверх
            2 - выше нас есть вызывающие желающие вниз - едем вверх
            3 - ниже нас есть вызывающие желающие вниз - едем вниз
            4 - ниже нас есть вызывающие желающие навверх - едем ввех
        ехали вниз
            1 - ниже нас есть вызывающие желающие вниз - едем вниз
            2 - ниже нас есть вызывающие желающие навверх - едем ввех
            3 - выше нас есть вызывающие желающие наверх - едем вверх
            4 - выше нас есть вызывающие желающие вниз - едем вверх
        никуда не ехали
            в порядке вызова
    """
    def __init__(self, min_floor: int, max_floor: int, hw: HardwareElevator):
        self._min_floor = min_floor
        self._max_floor = max_floor
        self._doors_is_closed = True
        self._hw = hw
        self._hw.add_handler('doorsClosed', self.on_doors_closed)
        self._hw.add_handler('beforeFloor', self.on_before_floor)
        self._last_direction = Direction.NONE

        self.passengers_queue = PassengersQueue()
        self.callers_queue = CallersQueue()

    def __del__(self):
        self._hw.remove_handler('doorsClosed', self.on_doors_closed)
        self._hw.remove_handler('beforeFloor', self.on_before_floor)

    def move_up(self):
        self._hw.move_up()
        self._last_direction = Direction.UP

    def move_down(self):
        self._hw.move_down()
        self._last_direction = Direction.DOWN

    def stop(self):
        if self._doors_is_closed:
            self._doors_is_closed = False
            self._hw.stop_and_open_doors()

    def _check_floor_bound(self, floor: int):
        return self._min_floor <= floor <= self._max_floor

    def move_next(self, floor):
        """
        Приоритеты:
        - развезти пассажиров-попутчиков с текущим направлением
        - развести остальных пассажиров
        - подобрать вызывающих-попутчиков с текущим направлением
        - подобрать остальных вызывающих в порядке вызова
        """
        has_up = self.passengers_queue.has_up(floor)
        has_down = self.passengers_queue.has_down(floor)
        if self._last_direction == Direction.UP and has_up:
            self.move_up()
        elif self._last_direction == Direction.DOWN and has_down:
            self.move_down()
        elif has_up:
            self.move_up()
        elif has_down:
            self.move_down()
        else:
            cq = self.callers_queue
            if cq.empty:
                return

            if self._last_direction == Direction.NONE:
                next_floor = self.callers_queue.get_first()
                if next_floor < floor:
                    self.move_down()
                else:
                    self.move_up()
                return

            above_want_up = (cq.has_above(floor, Direction.UP), self.move_up)
            above_want_down = (cq.has_above(floor, Direction.DOWN), self.move_up)
            below_want_up = (cq.has_below(floor, Direction.UP), self.move_down)
            below_want_down = (cq.has_below(floor, Direction.DOWN), self.move_down)

            priority = ()
            if self._last_direction == Direction.UP:
                priority = (above_want_up, above_want_down, below_want_up, below_want_down)
            elif self._last_direction == Direction.DOWN:
                priority = (below_want_down, below_want_up, above_want_up, above_want_down)

            for condition, func in priority:
                if condition:
                    func()
                    return

            self._last_direction = Direction.NONE

    def on_doors_closed(self, floor: int):
        self._doors_is_closed = True
        self.move_next(floor)

    def on_before_floor(self, floor: int, direction: Direction):
        # высаживаем пассажира
        if floor in self.passengers_queue:
            self.passengers_queue.remove(floor)
            self.stop()

        # подпибираем попутчика
        floor_direction = self.callers_queue.get_floor_direction(floor)
        if direction == floor_direction:
            self.callers_queue.remove(floor)
            self.stop()

    def floor_button_pressed(self, floor: int, direction: Direction):
        # дурак. исправим за него
        if (floor == self._min_floor and direction == Direction.DOWN or
                floor == self._max_floor and direction == Direction.UP):
            direction = Direction.negate(direction)

        # меняем направление, если он передумал
        prev_direction = self.callers_queue.get_floor_direction(floor)
        if prev_direction and prev_direction != direction:
            self.callers_queue.change_direction(floor, direction)

        current_direction = self._hw.get_current_direction()
        current_floor = self._hw.get_current_floor()
        if floor == current_floor and (direction == current_direction or
                                       current_direction == Direction.NONE):  # попутчик или лифт стоял
            self.stop()
        else:
            self.callers_queue.append(floor, direction)
            if self._doors_is_closed and self._hw.get_current_direction() == Direction.NONE:
                self.move_next(current_floor)

    def cabin_button_pressed(self, floor: int):
        if not self._check_floor_bound(floor):
            return

        current_floor = self._hw.get_current_floor()
        if floor in self.passengers_queue:  # отмена этажа
            self.passengers_queue.remove(floor)
        elif floor == current_floor:  # высаживаем, не добавляя в очередь
            self.stop()
        else:
            self.passengers_queue.append(floor)
            if self._doors_is_closed and self._hw.get_current_direction() == Direction.NONE:
                self.move_next(current_floor)
