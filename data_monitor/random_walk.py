from datetime import datetime, timedelta
from zumi.zumi import Zumi
from time import sleep, time
import random
import logging
from typing import Callable

__zumi = None
"""Will be initialized when running random_walk"""


def __detect_obstacle(
    infrared_left: int, infrared_right: int, threshold: float = 0.9
) -> bool:
    """Detects if there is an obstacle using infrared sensors

    :param infrared_left: front left infrared sensor value
    :type infrared_left: int
    :param infrared_right: front right infrared sensor value
    :type infrared_right: int
    :param threshold: Compare new sensor values to $threshhold * $old_value, defaults to 0.9
    :type threshold: float, optional
    :return: If an obstance has been detected or not
    :rtype: bool
    """
    logging.debug(
        "infrared_left: {}, infrared_right: {}, threshold: {}".format(
            infrared_left, infrared_right, threshold
        )
    )
    infrared_new = __zumi.get_all_IR_data()
    if infrared_new[5] < (infrared_left * threshold):
        logging.info(
            "{}: The left IR sensor has detected an obstacle.".format(
                datetime.utcnow().isoformat(" ")
            )
        )
    if infrared_new[0] < (infrared_right * threshold):
        logging.info(
            "{}: The right IR sensor has detected an obstacle.".format(
                datetime.utcnow().isoformat(" ")
            )
        )
    return infrared_new[5] < (infrared_left * threshold) or infrared_new[0] < (
        infrared_right * threshold
    )


def __drive_until_end_or_obstacle(duration: int, driving_function: callable) -> None:
    """runs the driving_function for the given duration in deciseconds or until an obstacle is detected

    :param duration: How long the driving function should run, in deciseconds
    :type duration: int
    :param driving_function: A driving function
    :type driving_function: callable
    """
    for _ in range(duration):
        driving_function()
        ir = __zumi.get_all_IR_data()
        sleep(0.1)
        if __detect_obstacle(infrared_left=ir[5], infrared_right=ir[0], threshold=0.9):
            __avoid_collision()
            break
    __zumi.stop()


def __avoid_collision() -> None:
    """Avoids an collision after an obstacle was detected"""
    __zumi.stop()
    angle = random.randrange(90, 270)
    if random.choice(["Left", "Right"]) == "Left":
        logging.info(
            "{}: Turning left about {} degrees to avoid collision.".format(
                datetime.utcnow().isoformat(" "), angle
            )
        )
        __zumi.turn_left(angle)
    else:
        logging.info(
            "{}: Turning right about {} degrees to avoid collision.".format(
                datetime.utcnow().isoformat(" "), angle
            )
        )
        __zumi.turn_right(angle)


def __go_straight(min_duration: int, max_duration: int, speed=80) -> None:
    """Goes Straight until an Obstacle is detected or time runs out

    :param min_duration: Minimum duration the Zumi should go straight, in deciseconds
    :type min_duration: int
    :param max_duration: Maximum duration the Zumi should go straight, in deciseconds
    :type max_duration: int
    :param speed: Speed of the Zumi, defaults to 80
    :type speed: int, optional
    """
    duration = round(random.randint(min_duration, max_duration) / 10)
    logging.info(
        "{}: Going straight for {} seconds at a speed of {}.".format(
            datetime.utcnow().isoformat(" "), duration, speed
        )
    )
    return __drive_until_end_or_obstacle(
        duration, lambda: __zumi.control_motors(speed, speed + 15)
    )


def __reverse(duration: int = 10, speed: int = 80) -> None:
    """Reverses a short distance

    :param duration: How long the Zumi should go reverse, in deciseconds, defaults to 10
    :type duration: int, optional
    :param speed: Speed of the Zumi, defaults to 80
    :type speed: int, optional
    """
    duration = round(duration / 10)
    logging.info(
        "{}: Reverse for {} seconds at a speed of {}.".format(
            datetime.utcnow().isoformat(" "), duration / 10, speed
        )
    )
    for _ in range(duration):
        __zumi.control_motors(-speed, -10)  # FIXME #TEST
        sleep(0.3)
    __zumi.stop()


def __turn_around(angle_range=90) -> None:
    """Turns around with an added uncertainty in either direction of angleRange

    :param angle_range: Turn angle in degrees, in either direction (Values between 0 and 90), defaults to 90
    :type angle_range: int, optional
    """
    deviation = random.randint(0, angle_range)
    angle = 180 - deviation
    if random.choice(["Left", "Right"]) == "Left":
        logging.info(
            "{}: Turning left about {} degrees.".format(
                datetime.utcnow().isoformat(" "), angle
            )
        )
        __zumi.turn_left(angle)
    else:
        logging.info(
            "{}: Turning right about {} degrees.".format(
                datetime.utcnow().isoformat(" "), angle
            )
        )
        __zumi.turn_right(angle)


def __random_curve(min_duration: int, max_duration: int, speed=80) -> None:
    """Does a curve either right or left for a random amount of time

    :param min_duration: Minimum duration the Zumi should make a curve, in deciseconds
    :type min_duration: int
    :param max_duration: Maximum duration the Zumi should make a curve, in deciseconds
    :type max_duration: int
    :param speed: Speed of the Zumi, defaults to 80
    :type speed: int, optional
    """
    logging.debug(
        "min_duration: {}, max_duration: {}, speed: {}".format(
            min_duration, max_duration, speed
        )
    )
    duration = round(random.randint(min_duration, max_duration) / 10)
    speed_left = random.randint(20, speed)
    speed_right = random.randint(20, speed)
    print("making a curve for {} seconds at a speed of {}".format(duration, speed))
    return __drive_until_end_or_obstacle(
        duration, lambda: __zumi.control_motors(right=speed_right - 10, left=speed_left)
    )


def __look_around() -> None:
    """Let the Zumi turn on the spot for a random degree"""
    __zumi.turn(
        __zumi.read_z_angle() + random.choice([360, -360]), duration=3, max_speed=5
    )


def __choose_random_action(actions: list, weights: list) -> Callable:
    """Choose a random action of a list of actions and their given weights

    :param actions: List of actions
    :type actions: list
    :param weights: List of weights for the actions
    :type weights: list
    :raises Exception: when the number of action differs from number of weights
    :return: Function that was chosen at random
    :rtype: Callable
    """
    if len(actions) != len(weights):
        raise Exception("actionlist and weightlist need to have the same length")
    seed = random.random() * sum(weights)
    accWeight = 0
    for a, w in zip(actions, weights):
        accWeight += w
        if accWeight > seed:
            return a


def random_walk(zumi: Zumi, execution_time: timedelta) -> None:
    """Lets the Zumi choose different movement function at random

    :param zumi: The Zumi object
    :type zumi: Zumi
    :param execution_time: How long the rnadom walk should last
    :type execution_time: timedelta
    """
    logging.info(
        "{}: Random walk has started with a runtime of {} seconds.".format(
            datetime.utcnow().isoformat(" "), execution_time
        )
    )
    global __zumi
    __zumi = zumi
    end = time() + execution_time.seconds
    while True:
        if time() >= end:
            break
        next_action = __choose_random_action(
            [__go_straight, __random_curve, __look_around], [45, 50, 5]
        )
        next_action(min_duration=40, max_duration=80)
