# -*- coding: utf-8 -*-
import logger
from cell_workers.utils import distance, i2f, format_dist
from human_behaviour import sleep
from step_walker import StepWalker


class SpiralNavigator(object):
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.config = bot.config

        self.steplimit = self.config.max_steps
        self.origin_lat = self.bot.position[0]
        self.origin_lon = self.bot.position[1]

        self.points = self._generate_spiral(
            self.origin_lat,
            self.origin_lon,
            0.0018,
            self.steplimit
        )
        self.ptr = 0
        self.direction = 1
        self.cnt = 0
        self._step_walker = None

    # Source: https://github.com/tejado/pgoapi/blob/master/examples/spiral_poi_search.py
    @staticmethod
    def _generate_spiral(starting_lat, starting_lng, step_size, step_limit):
        coords = [{'lat': starting_lat, 'lng': starting_lng}]
        steps, x, y, d, m = 1, 0, 0, 1, 1

        while steps < step_limit:
            while 2 * x * d < m and steps < step_limit:
                x = x + d
                steps += 1
                lat = x * step_size + starting_lat
                lng = y * step_size + starting_lng
                coords.append({'lat': lat, 'lng': lng})
            while 2 * y * d < m and steps < step_limit:
                y = y + d
                steps += 1
                lat = x * step_size + starting_lat
                lng = y * step_size + starting_lng
                coords.append({'lat': lat, 'lng': lng})

            d *= -1
            m += 1
        return coords

    def _distance(self, lat, lng):
        return distance(
            i2f(self.api._position_lat),
            i2f(self.api._position_lng),
            lat,
            lng
        )

    def take_step(self):
        point = self.points[self.ptr]

        self.cnt += 1
        if self.cnt == 1:
            logger.log('Scanning area for objects....')

        # Scan location math
        if self._step_walker:
            if self._step_walker.step():
                self._step_walker = None
        else:
            if self.config.walk > 0:
                self._step_walker = StepWalker(
                    self.bot,
                    self.config.walk,
                    i2f(self.api._position_lat),
                    i2f(self.api._position_lng),
                    point['lat'],
                    point['lng']
                )

                dist = self._distance(point['lat'], point['lng'])
                if self.cnt == 1:
                    logger.log(
                        'Walking from {} to {} {}'.format(
                            (i2f(self.api._position_lat),
                                i2f(self.api._position_lng)),
                            (point['lat'], point['lng']),
                            format_dist(dist, self.config.distance_unit)
                        )
                    )
            else:
                self.api.set_position(point['lat'], point['lng'])
                sleep(1)

            if ((self.ptr + self.direction == len(self.points)) or
                    (self.ptr + self.direction == -1)):
                self.direction *= -1
            self.ptr += self.direction
            self.cnt = 0

        return i2f(self.api._position_lat), i2f(self.api._position_lng)
