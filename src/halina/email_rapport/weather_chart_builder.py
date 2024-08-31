import asyncio
import datetime
import logging
from typing import List
import plotly.graph_objects as go

from halina.email_rapport.data_collector_classes.weather_point import WeatherPoint

logger = logging.getLogger(__name__.rsplit('.')[-1])


class WeatherChartBuilder:
    _SCALE_MARGIN = 0.5
    _WIND_AREA2 = 14  # wind speed red area
    _WIND_AREA1 = 12  # wind speed yellow area

    def __init__(self):
        self._title: str = "Weather"
        self._data_weather: List[WeatherPoint] = []
        self._image_wind_byte = None
        self._image_temperature_byte = None
        self._image_humidity_byte = None
        self._image_pressure_byte = None
        self._timezone_axes = 0

    def get_image_wind_byte(self):
        return self._image_wind_byte

    def get_image_temperature_byte(self):
        return self._image_temperature_byte

    def get__image_humidity_byte(self):
        return self._image_humidity_byte

    def get_image_pressure_byte(self):
        return self._image_pressure_byte

    def set_data_weather(self, data_weather: List[WeatherPoint]):
        self._data_weather = data_weather

    def data_weather(self, data_weather: List[WeatherPoint]):
        self.set_data_weather(data_weather=data_weather)
        return self

    async def build(self):
        tim_ax = self._timezone_axes
        if not self._data_weather:
            return None
        # TODO if creating plot will take to much time, should think about run it in multiprocessing
        #  (not recognised implementation) or thread (dificult to implement)
        hours = []
        winds = []
        temperatures = []
        humiditys = []
        pressures = []

        max_wind = 0
        start = datetime.datetime.now(datetime.timezone.utc)
        for dat in self._data_weather:
            if max_wind < dat.wind:
                max_wind = dat.wind
            hours.append(dat.date)
            winds.append(dat.wind)
            temperatures.append(dat.temperature)
            humiditys.append(dat.humidity)
            pressures.append(dat.pressure)

        stop = datetime.datetime.now(datetime.timezone.utc)
        logger.info(f"preparing data for plots completed. Proces takes: {(stop - start).total_seconds()}")
        start = datetime.datetime.now(datetime.timezone.utc)

        # wind
        fig_wind = go.Figure(layout_yaxis_range=[0, max_wind + WeatherChartBuilder._SCALE_MARGIN])
        fig_wind.update_layout(title_text='<b>Wind [m/s]</b>', title_x=0.5,
                               xaxis_title=f"<b>UTC{'+' if tim_ax >= 0 else ''}{tim_ax}</b>")
        fig_wind.add_trace(go.Scatter(x=hours, y=winds))
        fig_wind.add_hrect(y0=WeatherChartBuilder._WIND_AREA1, y1=WeatherChartBuilder._WIND_AREA2,
                           line_width=0, fillcolor="yellow", opacity=0.2)
        fig_wind.add_hrect(y0=WeatherChartBuilder._WIND_AREA2, y1=max_wind + WeatherChartBuilder._SCALE_MARGIN,
                           line_width=0, fillcolor="red", opacity=0.2)
        self._image_wind_byte = fig_wind.to_image(format="png")
        await asyncio.sleep(0)

        # temperature
        fig_temperature = go.Figure()
        fig_temperature.update_layout(title_text='<b>Temperature [C]</b>', title_x=0.5,
                                      xaxis_title=f"<b>UTC{'+' if tim_ax >= 0 else ''}{tim_ax}</b>")
        fig_temperature.add_trace(go.Scatter(x=hours, y=temperatures))
        self._image_temperature_byte = fig_temperature.to_image(format="png")
        await asyncio.sleep(0)

        # humidity
        fig_humidity = go.Figure()
        fig_humidity.update_layout(title_text='<b>Humidity [%]</b>', title_x=0.5,
                                   xaxis_title=f"<b>UTC{'+' if tim_ax >= 0 else ''}{tim_ax}</b>")
        fig_humidity.add_trace(go.Scatter(x=hours, y=humiditys))
        self._image_humidity_byte = fig_humidity.to_image(format="png")
        await asyncio.sleep(0)

        # pressure
        fig_pressure = go.Figure()
        fig_pressure.update_layout(title_text='<b>Pressure [hPa]</b>', title_x=0.5,
                                   xaxis_title=f"<b>UTC{'+' if tim_ax >= 0 else ''}{tim_ax}</b>")
        fig_pressure.add_trace(go.Scatter(x=hours, y=pressures))
        self._image_pressure_byte = fig_pressure.to_image(format="png")

        stop = datetime.datetime.now(datetime.timezone.utc)
        logger.info(f"Plots was created. Proces takes: {(stop - start).total_seconds()}")
