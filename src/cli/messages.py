from textual.message import Message


class CalculateLinearRegressionAction(Message):
    def __init__(self):
        super().__init__()


class TriggerCalibrationMessageAction(Message):
    def __init__(self):
        super().__init__()


class AverageRawReadingUpdated(Message):
    def __init__(self, pressure: float, raw_readings: list[float], pt_id: str) -> None:
        self.pressure = pressure
        self.raw_readings = raw_readings
        self.pt_id = pt_id
        super().__init__()


class TableRowUpdated(Message):
    def __init__(self, pressure: float, raw_readings: list[float], pt_id: str) -> None:
        self.pressure = pressure
        self.raw_readings = raw_readings
        self.pt_id = pt_id
        super().__init__()


class PressureUpdated(Message):
    def __init__(self, pressure: float) -> None:
        self.pressure = pressure
        super().__init__()
