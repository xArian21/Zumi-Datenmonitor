from datetime import datetime


class TimeseriesData:
    """
    The super class of all time series Data classes
    contains datetime.utcnow with milliseconds
    """

    def __init__(self, session_id: str, timestamp: datetime):
        self.timestamp = timestamp
        self.session_id = session_id


class IRData(TimeseriesData):
    """ir data range: 0-255"""

    def __init__(
        self,
        front_right: int,
        bottom_right: int,
        back_right: int,
        bottom_left: int,
        back_left: int,
        front_left: int,
        session_id: str,
        timestamp: datetime = None,
    ):
        if timestamp is None:
            super().__init__(session_id, datetime.utcnow())
        else:
            super().__init__(session_id, timestamp)
        self.ir_front_right = front_right
        self.ir_front_left = front_left
        self.ir_bottom_right = bottom_right
        self.ir_bottom_left = bottom_left
        self.ir_back_right = back_right
        self.ir_back_left = back_left


class MPUData(TimeseriesData):
    """Gyro data range 0-360, accelerator data range 0-5"""

    def __init__(
        self,
        gyro_x_angle: float,
        gyro_y_angle: float,
        gyro_z_angle: float,
        acc_x_axis: int,
        acc_y_axis: int,
        acc_z_axis: int,
        session_id: str,
        timestamp: datetime = None,
    ):
        if timestamp is None:
            super().__init__(session_id, datetime.utcnow())
        else:
            super().__init__(session_id, timestamp)
        self.gyro_x_angle = gyro_x_angle
        self.gyro_y_angle = gyro_y_angle
        self.gyro_z_angle = gyro_z_angle
        self.acc_x_axis = acc_x_axis
        self.acc_y_axis = acc_y_axis
        self.acc_z_axis = acc_z_axis


class SystemUtilizationData(TimeseriesData):
    """
    Contains CPU utilization in percent (0-100)
    and RAM utilization in MB (0-512)
    """

    def __init__(
        self,
        cpu_utilization: int,
        ram_utilization: int,
        motor_speed_right: int,
        motor_speed_left: int,
        session_id: str,
        timestamp: datetime = None,
    ):
        if timestamp is None:
            super().__init__(session_id, datetime.utcnow())
        else:
            super().__init__(session_id, timestamp)
        self.cpu_utilization = cpu_utilization
        self.ram_utilization = ram_utilization
        self.motor_speed_right = motor_speed_right
        self.motor_speed_left = motor_speed_left


class CameraData(TimeseriesData):
    """
    Contains camera image as string representation of the bytes object
    """

    def __init__(
        self,
        image: str,
        format: str,
        session_id: str,
        timestamp: datetime = None,
    ):
        if timestamp is None:
            super().__init__(session_id, datetime.utcnow())
        else:
            super().__init__(session_id, timestamp)
        self.image = image
        self.format = format
