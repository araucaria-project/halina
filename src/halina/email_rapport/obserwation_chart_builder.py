import asyncio
import datetime
import logging
import pandas as pd
import plotly.express as px
from typing import List
from pyaraucaria.ephemeris import moon_phase
from halina.date_utils import DateUtils
from halina.email_rapport.data_collector_classes.weather_point import WeatherPoint
from halina.email_rapport.data_collector_classes.observation_chart_data import ObservationChartData

logger = logging.getLogger(__name__.rsplit('.')[-1])


class ObservationChartBuilder:
    _SUNSET_SUNRISE_MARGIN = 20  # min
    _SCALE_MARGIN = 0.5
    _WIND_AREA2_LVL = 14  # wind speed red area
    _WIND_AREA1_LVL = 11  # wind speed yellow area
    _NO_SHOW_OBJECT_TYPE = ['snap', 'focus']
    _SHAPE_OBJECT_TYPE = {'science': '',
                          'flat': '/',
                          'zero': '.',
                          'focus': '+'}
    _COLOR_MAP_SUN = {
        "Night": "#004b72",
        "Day": "#e9c76e"
    }
    _WIND_AREA0 = 'AREA0'
    _WIND_AREA1 = 'AREA1'
    _WIND_AREA2 = 'AREA2'
    _WIND_AREAS_MAP = {
        _WIND_AREA0: '#64c466',  # green
        _WIND_AREA1: '#f6ce46',  # yellow
        _WIND_AREA2: '#ea4d3d',  # red
    }
    _RAISE_MOON_SYMBOL = '↗'
    _SET_MOON_SYMBOL = '↘'

    @staticmethod
    def _GET_MOON_PHASE_SYMBOL(phase: float):
        symbol = ''
        if 0 >= phase <= 10:
            symbol = '🌑'
        elif 10 > phase <= 40:
            symbol = '🌘'
        elif 40 > phase <= 60:
            symbol = '🌗'
        elif 60 > phase <= 90:
            symbol = '🌖'
        elif 90 > phase <= 100:
            symbol = '🌕'
        return symbol

    def __init__(self):
        self._timezone_axes = 0
        self._data_weather: List[WeatherPoint] = []
        self._tel_data: List[ObservationChartData] = []
        self._observation_chart = []

    def get_observation_chart(self):
        return self._observation_chart

    def set_telescope_data(self, objects_data):
        self._tel_data = objects_data

    def set_data_weather(self, data_weather):
        self._data_weather = data_weather

    async def build(self):
        if not self._data_weather:
            return None
        if not self._tel_data:
            return None

        # calculate moonset and moonrise - if can not calculate moonrise and moonset stop generate chart
        sunset, sunrise = self._get_sunrise_and_sunset()
        if sunrise is None or sunset is None:
            return None
        # calculate sunset and sunrise - if can not calculate sunrise and sunset stop generate chart
        moonrise, moonset = self._get_moonrise_moonset()
        if moonrise is None or moonset is None:
            return None
        moon_ph = self._get_moon_phase()
        if moon_ph is None:
            return None
        sun_chart_title = 'Sun' if not moon_ph else f'Sun/{ObservationChartBuilder._GET_MOON_PHASE_SYMBOL(moon_ph)}'

        # calculate chart range x axe
        chart_start_time = sunset - datetime.timedelta(minutes=ObservationChartBuilder._SUNSET_SUNRISE_MARGIN)
        chart_end_time = sunrise + datetime.timedelta(minutes=ObservationChartBuilder._SUNSET_SUNRISE_MARGIN)

        await asyncio.sleep(0)
        # ---------  object chart part ---------
        object_chart_points, color_map = self._get_object_points_and_color_map()
        data_frame = pd.DataFrame(object_chart_points)
        fig = px.timeline(data_frame, x_start="Start", x_end="Finish", y="Resource", color='Filter',
                          color_discrete_map=color_map, pattern_shape_map=ObservationChartBuilder._SHAPE_OBJECT_TYPE,
                          pattern_shape='Type', height=350, range_x=[chart_start_time, chart_end_time])
        # bargap = gap between vertical charts
        # template = none - change background color to white and line style also !! GOOD
        fig.update_layout(bargap=0.05, yaxis_title=None, template="none", yaxis_tickfont_size=26)
        fig.update(layout_showlegend=False)
        fig.update_xaxes(tickformat="%H:%M", tickfont_size=26)
        await asyncio.sleep(0)
        # ----------- sunrise / sunset part ---------
        sun_chart_points = [
            dict(Day='Day', Start=chart_start_time, Finish=sunset, Resource=sun_chart_title),
            dict(Day='Night', Start=sunset, Finish=sunrise, Resource=sun_chart_title),
            dict(Day='Day', Start=sunrise, Finish=chart_end_time, Resource=sun_chart_title),
        ]
        sun_data = pd.DataFrame(sun_chart_points)
        sun_part = px.timeline(
            sun_data,
            x_start='Start', x_end='Finish', y='Resource', color='Day',
            color_discrete_map=ObservationChartBuilder._COLOR_MAP_SUN, range_x=[chart_start_time, chart_end_time])
        fig = fig.add_traces(
            [*sun_part.data]
        )

        await asyncio.sleep(0)
        # ----------- moonrise / moonset part ---------
        moon_chart_points = [
            dict(Day='MoonRise', Start=moonrise, Resource=sun_chart_title,
                 Text=ObservationChartBuilder._RAISE_MOON_SYMBOL),
            dict(Day='MoonSet', Start=moonset, Resource=sun_chart_title, Text=ObservationChartBuilder._SET_MOON_SYMBOL)
        ]
        moon_data = pd.DataFrame(moon_chart_points)
        moon_part = px.scatter(moon_data, x='Start', y='Resource', text='Text', log_x=True)
        moon_part.update_traces(textfont_size=23, textfont_color="#f7f7f7")
        fig = fig.add_traces(
            [*moon_part.data]
        )

        await asyncio.sleep(0)
        # ----------- wind part ---------
        wind_chart_points = self._create_data_for_wind_chart(chart_start_time, chart_end_time)
        wind_data = pd.DataFrame(wind_chart_points)
        wind_part = px.timeline(
            wind_data,
            x_start='Start', x_end='Finish', y='Resource', range_x=[chart_start_time, chart_end_time], color='Area',
            color_discrete_map=ObservationChartBuilder._WIND_AREAS_MAP)
        fig = fig.add_traces(
            [*wind_part.data]
        )
        self._observation_chart = fig.to_image(format="png", width=1920, height=350)

    def _get_sunrise_and_sunset(self):
        sunset = None
        sunrise = None
        if len(self._tel_data) > 0:
            lat = self._tel_data[0].tel_lat
            lon = self._tel_data[0].tel_lon
            elev = self._tel_data[0].tel_elev
            if lat is not None and lon is not None and elev is not None:
                sunset = DateUtils.yesterday_sunset_in_utc(lat=lat, lon=lon, elev=elev)
                sunrise = DateUtils.yesterday_sunrise_in_utc(lat=lat, lon=lon, elev=elev)
        return sunset, sunrise

    def _get_object_points_and_color_map(self):
        object_chart_points = []
        color_map = {}
        for tel in self._tel_data:
            tel_name = tel.tel_name
            color_map = color_map | tel.filter_color_map

            for obj in tel.objects:
                # skip some fits like snap
                if obj.type in ObservationChartBuilder._NO_SHOW_OBJECT_TYPE:
                    continue
                # create one block representing one exposition
                object_chart_points.append(
                    dict(Object=obj.name, Start=obj.start, Finish=obj.end, Resource=tel_name, Filter=obj.filter,
                         Type=obj.type)
                )
        return object_chart_points, color_map

    def _create_data_for_wind_chart(self, chart_start_time, chart_end_time):
        data = []
        wind_start = chart_start_time
        last_area = ObservationChartBuilder._check_wind_area(self._data_weather[0].wind)
        for wet_p in self._data_weather:
            now_area = ObservationChartBuilder._check_wind_area(wet_p.wind)
            # here wind change area
            if now_area != last_area:
                data.append(dict(Area=last_area, Start=wind_start, Finish=wet_p.date, Resource='Wind'))
                last_area = now_area
                wind_start = wet_p.date
        # last area
        data.append(dict(Area=last_area, Start=wind_start, Finish=chart_end_time, Resource='Wind'))
        return data

    @staticmethod
    def _check_wind_area(wind):
        if wind < ObservationChartBuilder._WIND_AREA1_LVL:
            area = ObservationChartBuilder._WIND_AREA0
        elif wind < ObservationChartBuilder._WIND_AREA2_LVL:
            area = ObservationChartBuilder._WIND_AREA1
        else:
            area = ObservationChartBuilder._WIND_AREA2
        return area

    def _get_moonrise_moonset(self):
        moonset = None
        moonrise = None
        if len(self._tel_data) > 0:
            lat = self._tel_data[0].tel_lat
            lon = self._tel_data[0].tel_lon
            elev = self._tel_data[0].tel_elev
            if lat is not None and lon is not None and elev is not None:
                moonset = DateUtils.yesterday_moonset_in_utc(lat=lat, lon=lon, elev=elev)
                moonrise = DateUtils.yesterday_moonrise_in_utc(lat=lat, lon=lon, elev=elev)
        return moonrise, moonset

    def _get_moon_phase(self):
        phase = None
        if len(self._tel_data) > 0:
            lat = self._tel_data[0].tel_lat
            lon = self._tel_data[0].tel_lon
            elev = self._tel_data[0].tel_elev
            if lat is not None and lon is not None and elev is not None:
                phase = moon_phase(date_utc=DateUtils.yesterday_midday_utc(),
                                   latitude=lat,
                                   longitude=lon,
                                   elevation=elev
                                   )
        return phase
