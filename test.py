import unittest
from contextlib import contextmanager
from unittest.mock import Mock

from main import HardwareElevator, Elevator, Direction


class TestElevator(unittest.TestCase):
    def setUp(self):
        self.hw = Mock(spec=HardwareElevator)

    def _configure_hw(self, floor: int, direction: Direction):
        self.hw.configure_mock(**{
            'get_current_floor.return_value': floor,
            'get_current_direction.return_value': direction,
        })

    def _reset_all_calls(self):
        self.hw.move_up.reset_mock()
        self.hw.move_down.reset_mock()
        self.hw.stop_and_open_doors.reset_mock()

    @contextmanager
    def _without_calls(self):
        self._reset_all_calls()
        yield
        self.hw.move_up.assert_not_called()
        self.hw.move_down.assert_not_called()
        self.hw.stop_and_open_doors.assert_not_called()

    @contextmanager
    def _up_called(self):
        self._reset_all_calls()
        yield
        self.hw.move_up.assert_called()
        self.hw.move_down.assert_not_called()
        self.hw.stop_and_open_doors.assert_not_called()

    @contextmanager
    def _down_called(self):
        self._reset_all_calls()
        yield
        self.hw.move_up.assert_not_called()
        self.hw.move_down.assert_called()
        self.hw.stop_and_open_doors.assert_not_called()

    @contextmanager
    def _stop_called(self):
        self._reset_all_calls()
        yield
        self.hw.move_up.assert_not_called()
        self.hw.move_down.assert_not_called()
        self.hw.stop_and_open_doors.assert_called()

    def _take_to(self, floor: int, from_floor: int = 1):
        self._configure_hw(from_floor, Direction.NONE)
        self.elevator = Elevator(1, 10, self.hw)
        self.elevator.floor_button_pressed(from_floor,
                                           Direction.UP if floor > from_floor else Direction.DOWN)
        self.elevator.on_doors_closed(from_floor)
        self.elevator.cabin_button_pressed(floor)

    def test_call_min_floor(self):
        """ Вызываем лифт на минимальном этаже вниз. Лифт на этом же этаже """
        self._configure_hw(1, Direction.NONE)
        self.elevator = Elevator(1, 3, self.hw)

        with self._stop_called():
            self.elevator.floor_button_pressed(1, Direction.DOWN)
        with self._without_calls():
            self.elevator.on_doors_closed(1)
        with self._up_called():
            self.elevator.cabin_button_pressed(2)

    def test_call_max_floor(self):
        """ Вызываем лифт на максимальном этаже вверх. Лифт на этом же этаже """
        self._configure_hw(3, Direction.NONE)
        self.elevator = Elevator(1, 3, self.hw)

        with self._stop_called():
            self.elevator.floor_button_pressed(3, Direction.UP)
        with self._without_calls():
            self.elevator.on_doors_closed(1)
        with self._down_called():
            self.elevator.cabin_button_pressed(2)

    def test_current(self):
        """ Зашел на 1, двери закрылись, нажал 1 """
        self._configure_hw(1, Direction.NONE)
        self.elevator = Elevator(1, 10, self.hw)
        self.elevator.floor_button_pressed(1, Direction.UP)
        self.elevator.on_doors_closed(1)

        with self._stop_called():
            self.elevator.cabin_button_pressed(1)

    def test_call_current_up(self):
        """ Вызываем лифт на минимальном этаже вверх. Лифт на этом же этаже """
        self._configure_hw(1, Direction.NONE)
        self.elevator = Elevator(1, 3, self.hw)

        with self._stop_called():
            self.elevator.floor_button_pressed(1, Direction.UP)
        with self._without_calls():
            self.elevator.on_doors_closed(1)
        with self._up_called():
            self.elevator.cabin_button_pressed(2)

    def test_call_above_up_press_before_closed(self):
        """ Вызываем на 5-ом, лифт на 1-ом, едем на 10. Тыкаем этаж до закрытия дверей """
        self._configure_hw(1, Direction.NONE)
        self.elevator = Elevator(1, 10, self.hw)

        with self._up_called():
            self.elevator.floor_button_pressed(5, Direction.UP)
        with self._stop_called():
            self.elevator.on_before_floor(5, Direction.UP)
        with self._without_calls():
            self.elevator.cabin_button_pressed(10)
        with self._up_called():
            self.elevator.on_doors_closed(5)

    def test_call_above_up_press_after_closed(self):
        """ Вызываем на 5-ом, лифт на 1-ом, едем на 10. Тыкаем этаж после закрытия дверей """
        self._configure_hw(1, Direction.NONE)
        self.elevator = Elevator(1, 10, self.hw)

        with self._up_called():
            self.elevator.floor_button_pressed(5, Direction.UP)
        with self._stop_called():
            self.elevator.on_before_floor(5, Direction.UP)
        with self._without_calls():
            self.elevator.on_doors_closed(5)
        with self._up_called():
            self.elevator.cabin_button_pressed(10)

    def test_pass_not_sail(self):
        """ Едем с 1-го на 5-ый. На 3-ем вызывают вниз, едем до 5-го без остановок.
        на 5-ом едем вниз до 3, подбираем """
        self._take_to(5)

        with self._without_calls():
            self._configure_hw(1, Direction.UP)
            self.elevator.floor_button_pressed(3, Direction.DOWN)
            self.elevator.on_before_floor(2, Direction.UP)
            self._configure_hw(2, Direction.UP)
            self.elevator.on_before_floor(3, Direction.UP)
            self._configure_hw(3, Direction.UP)
            self.elevator.on_before_floor(4, Direction.UP)
        with self._stop_called():
            self.elevator.on_before_floor(5, Direction.UP)
        with self._down_called():
            self.elevator.on_doors_closed(5)
        with self._without_calls():
            self.elevator.on_before_floor(4, Direction.DOWN)
        with self._stop_called():
            self.elevator.on_before_floor(3, Direction.DOWN)

    def test_unnamed_1(self):
        """ Едем с 1 на 6. Вызвал с 1 и с последнего. после 6 едем вверх """
        self._take_to(6)

        with self._without_calls():
            self._configure_hw(1, Direction.UP)
            self.elevator.on_before_floor(2, Direction.UP)
            self._configure_hw(2, Direction.UP)
            self.elevator.floor_button_pressed(1, Direction.UP)
            self.elevator.floor_button_pressed(10, Direction.DOWN)

            for floor in range(2, 5):
                self._configure_hw(floor, Direction.UP)
                self.elevator.on_before_floor(floor + 1, Direction.UP)

        with self._stop_called():
            self._configure_hw(5, Direction.UP)
            self.elevator.on_before_floor(6, Direction.UP)
        with self._up_called():
            self._configure_hw(6, Direction.NONE)
            self.elevator.on_doors_closed(6)

    def test_unnamed_2(self):
        """ Едем вверх. Выбраны 4 и 7. На 4 один выходит, один заходит и нажимает 3. едем вверх """
        self._take_to(4)
        self.elevator.cabin_button_pressed(7)

        with self._without_calls():
            for floor in range(1, 3):
                self._configure_hw(floor, Direction.UP)
                self.elevator.on_before_floor(floor + 1, Direction.UP)
        with self._stop_called():
            self._configure_hw(3, Direction.UP)
            self.elevator.on_before_floor(4, Direction.UP)
        with self._up_called():
            self._configure_hw(4, Direction.NONE)
            self.elevator.cabin_button_pressed(3)
            self.elevator.on_doors_closed(4)

    def test_unnamed_3(self):
        """ На 10 заходят двое. Нажимают 5 и 10. едем до 5, потом не едем наверх """
        self._configure_hw(10, Direction.NONE)
        self.elevator = Elevator(1, 10, self.hw)
        self.elevator.floor_button_pressed(10, Direction.DOWN)

        with self._without_calls():
            self.elevator.cabin_button_pressed(5)
            self.elevator.cabin_button_pressed(10)

        with self._down_called():
            self.elevator.on_doors_closed(10)

        with self._without_calls():
            for floor in range(10, 6, -1):
                self._configure_hw(floor, Direction.DOWN)
                self.elevator.on_before_floor(floor - 1, Direction.DOWN)

        with self._stop_called():
            self._configure_hw(6, Direction.DOWN)
            self.elevator.on_before_floor(5, Direction.DOWN)

        with self._without_calls():
            self.elevator.on_doors_closed(5)

    def test_unnamed_4(self):
        """ Едет на 8 и 10. На 8 этаже один выходит другой заходит. закрывем, нажимают 9. останавливаемся на 9 """
        self._take_to(8, from_floor=7)
        self.elevator.cabin_button_pressed(10)
        self._configure_hw(7, Direction.UP)
        self.elevator.on_before_floor(8, Direction.UP)
        self._configure_hw(8, Direction.NONE)

        with self._without_calls():
            self.elevator.cabin_button_pressed(9)
        with self._up_called():
            self.elevator.on_doors_closed(8)
        with self._stop_called():
            self._configure_hw(8, Direction.UP)
            self.elevator.on_before_floor(9, Direction.UP)

    def test_unnamed_5(self):
        """ Лифт на 5. вызывают на 4 вниз и на 1 вверх. на 4 заходит и нажимает 5. едем вверх """
        self._configure_hw(5, Direction.NONE)
        self.elevator = Elevator(1, 10, self.hw)

        with self._down_called():
            self.elevator.floor_button_pressed(4, Direction.DOWN)
            self.elevator.floor_button_pressed(1, Direction.UP)

        with self._stop_called():
            self.elevator.on_before_floor(4, Direction.DOWN)

        self._configure_hw(4, Direction.NONE)
        with self._without_calls():
            self.elevator.cabin_button_pressed(5)
        with self._up_called():
            self.elevator.on_doors_closed(4)


if __name__ == '__main__':
    unittest.main()
