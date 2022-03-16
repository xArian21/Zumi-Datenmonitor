from .data_classes import *
import psutil
import picamera
import io
import logging


class SensorConnectivity:
    def __init__(self, zumi, session_id: str):
        logging.debug("zumi: {}, session_id: {}".format(zumi, session_id))
        self.zumi = zumi
        self.session_id = session_id

    def get_system_data(self) -> SystemUtilizationData:
        """Get the current system data

        :return: SystemUtilizationData object
        :rtype: SystemUtilizationData
        """
        return SystemUtilizationData(
            psutil.cpu_percent(1),
            psutil.virtual_memory()[2],
            self.zumi.motor_speeds[0],
            self.zumi.motor_speeds[1],
            self.session_id,
        )

    def get_infrared_data(self) -> IRData:
        """Get the current IR sensor data

        :return: IRData object
        :rtype: IRData
        """
        ir_list = self.zumi.get_all_IR_data()
        return IRData(
            ir_list[0],
            ir_list[1],
            ir_list[2],
            ir_list[3],
            ir_list[4],
            ir_list[5],
            self.session_id,
        )

    def get_mpu_data(self) -> MPUData:
        """Get the current MPU sensor data

        :return: MPUData object
        :rtype: MPUData
        """
        mpu_list = self.zumi.mpu.read_all_MPU_data()
        return MPUData(
            mpu_list[0],
            mpu_list[1],
            mpu_list[2],
            mpu_list[3],
            mpu_list[4],
            mpu_list[5],
            self.session_id,
        )

    def get_camera_data(
        self, width: int = 640, height: int = 480, format: str = "jpeg"
    ) -> CameraData:
        """Take a picture with the PiCamera

        :param width: width of the images, defaults to 640
        :type width: int, optional
        :param height: height of the images, defaults to 480
        :type height: int, optional
        :param format: format of the images, defaults to "jpeg"
        :type format: str, optional
        :return: CameraData object
        :rtype: CameraData
        """
        with picamera.PiCamera() as camera:
            image_stream = io.BytesIO()
            camera.resolution = (width, height)
            camera.rotation = 180
            camera.capture(image_stream, format)
            return CameraData(image_stream.getvalue(), format, self.session_id)
