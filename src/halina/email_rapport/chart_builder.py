import asyncio
import datetime
import logging
from typing import List, Dict, Union
import plotly.graph_objects as go

from halina.email_rapport.data_collector_classes.fwhm_point import FwhmPoint
from halina.email_rapport.data_collector_classes.power_point import PowerPoint
from halina.email_rapport.data_collector_classes.weather_point import WeatherPoint

logger = logging.getLogger(__name__.rsplit('.')[-1])


class ChartBuilder:
    _SCALE_MARGIN = 0.5
    _WIND_AREA2 = 14  # wind speed red area
    _WIND_AREA1 = 11  # wind speed yellow area
    _MARGIN_DICT = dict(l=40, r=20, t=28, b=35)
    _HEIGHT = 200
    _WIDTH = 800
    _POWER = {
        'state_of_charge': {'color': '#0000FF', 'name': 'Battery [%]'},
        'solar_power': {'color': '#FFA500', 'name': 'Solar [W]'},
        'power_consume': {'color': '#7CFC00', 'name': 'Consume [W]'}
    }

    def __init__(self):
        self._title: str = "Weather"
        self._data_weather: List[WeatherPoint] = []
        self._image_wind_byte = None
        self._image_temperature_byte = None
        self._image_humidity_byte = None
        self._image_pressure_byte = None
        self._image_fwhm_byte = None
        self._image_power_byte = None
        self._timezone_axes = 0
        self._data_fwhm: Dict[str, Dict[str, Union[str, List[FwhmPoint]]]] = {}
        self._data_power: List[PowerPoint] = []

    def get_image_wind_byte(self):
        return self._image_wind_byte

    def get_image_temperature_byte(self):
        return self._image_temperature_byte

    def get__image_humidity_byte(self):
        return self._image_humidity_byte

    def get_image_pressure_byte(self):
        return self._image_pressure_byte

    def get_image_fwhm_byte(self):
        return self._image_fwhm_byte

    def get_image_power_byte(self):
        return self._image_power_byte

    def set_data_weather(self, data_weather: List[WeatherPoint]) -> None:
        self._data_weather = data_weather

    def set_data_power(self, data_power: List[PowerPoint]) -> None:
        self._data_power = data_power

    def set_data_fwhm(self, data_fwhm: Dict[str, Dict[str, Union[str, List[FwhmPoint]]]]) -> None:
        self._data_fwhm = data_fwhm

    def data_weather(self, data_weather: List[WeatherPoint]):
        self.set_data_weather(data_weather=data_weather)
        return self

    @staticmethod
    def hex_to_rgba(hex_color: str, alpha: float) -> str:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    async def build(self) -> None:
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
        if max_wind > ChartBuilder._WIND_AREA2:
            wind_red_area_top = max_wind + ChartBuilder._SCALE_MARGIN
        else:
            wind_red_area_top = ChartBuilder._WIND_AREA2 + ChartBuilder._SCALE_MARGIN

        # wind
        fig_wind = go.Figure(layout_yaxis_range=[0, wind_red_area_top])
        fig_wind.update_layout(
            title_text='<b>Wind [m/s]</b>', title_x=0.5,
            # xaxis_title=f"<b>UTC{'+' if tim_ax >= 0 else ''}{tim_ax}</b>",
            width=800,
            height=200,
            margin=self._MARGIN_DICT
        )
        fig_wind.add_trace(go.Scatter(x=hours, y=winds))
        fig_wind.add_hrect(y0=ChartBuilder._WIND_AREA1, y1=ChartBuilder._WIND_AREA2,
                           line_width=0, fillcolor="yellow", opacity=0.2)
        fig_wind.add_hrect(y0=ChartBuilder._WIND_AREA2, y1=wind_red_area_top,
                           line_width=0, fillcolor="red", opacity=0.2)
        self._image_wind_byte = fig_wind.to_image(format="png")
        await asyncio.sleep(0)

        # temperature
        fig_temperature = go.Figure()
        fig_temperature.update_layout(
            title_text='<b>Temperature [C]</b>', title_x=0.5,
            # xaxis_title=f"<b>UTC{'+' if tim_ax >= 0 else ''}{tim_ax}</b>",
            width=800,
            height=200,
            margin=self._MARGIN_DICT
            )
        fig_temperature.add_trace(go.Scatter(x=hours, y=temperatures))
        self._image_temperature_byte = fig_temperature.to_image(format="png")
        await asyncio.sleep(0)

        # humidity
        fig_humidity = go.Figure()
        fig_humidity.update_layout(
            title_text='<b>Humidity [%]</b>', title_x=0.5,
            # xaxis_title=f"<b>UTC{'+' if tim_ax >= 0 else ''}{tim_ax}</b>",
            width=800,
            height=200,
            margin=self._MARGIN_DICT
            )
        fig_humidity.add_trace(go.Scatter(x=hours, y=humiditys))
        self._image_humidity_byte = fig_humidity.to_image(format="png")
        await asyncio.sleep(0)

        # pressure
        fig_pressure = go.Figure()
        fig_pressure.update_layout(
            title_text='<b>Pressure [hPa]</b>', title_x=0.5,
            # xaxis_title=f"<b>UTC{'+' if tim_ax >= 0 else ''}{tim_ax}</b>",
            width=800,
            height=200,
            margin=self._MARGIN_DICT
            )
        fig_pressure.add_trace(go.Scatter(x=hours, y=pressures))
        self._image_pressure_byte = fig_pressure.to_image(format="png")

        # fwhm
        fig_fwhm = go.Figure()
        fig_fwhm.update_layout(
            title_text='<b>FWHM [arcsec]</b>', title_x=0.5,
            # xaxis_title=f"<b>UTC{'+' if tim_ax >= 0 else ''}{tim_ax}</b>",
            width=800,
            height=200,
            margin=self._MARGIN_DICT,
            legend=dict(
                x=0.01,
                y=0.99,
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.6)",
                borderwidth=0
            )
        )
        fig_fwhm.update_xaxes(
            range=[hours[0], hours[-1]]
        )
        for _tel, _tel_dat in self._data_fwhm.items():
            fwhm = []
            hours = []

            try:
                color = _tel_dat['color']
            except (LookupError, ValueError, TypeError):
                color = '#A9A9A9'

            try:
                fwhm_data = _tel_dat['fwhm_data']
            except (LookupError, ValueError, TypeError):
                fwhm_data = []
            for fwhm_point in fwhm_data:
                try:
                    fwhm.append(fwhm_point.fwhm * fwhm_point.scale)
                    hours.append(fwhm_point.date)
                except (ValueError, TypeError):
                    pass
            alpha=0.2
            if _tel == 'jk15':
                alpha = 0.5
            fig_fwhm.add_trace(go.Scatter(
                x=hours,
                y=fwhm,
                mode="markers",
                name=_tel,
                marker=dict(
                    color=self.hex_to_rgba(hex_color=color, alpha=alpha),
                    size=5,
                    line=dict(
                        color=color,
                        width=0.5
                    )
                )
            ))
        self._image_fwhm_byte = fig_fwhm.to_image(format="png")


        # power
        # {'ts': [2025, 12, 29, 12, 0, 4, 954440], 'version': '3.2.1',
        # 'measurements': {'state_of_charge': 77, 'pv_power': 15549, 'battery_charge': 11161, 'battery_discharge': 0}}
        logger.info(f'Starting power plot, points: {len(self._data_power)}')
        fig_power = go.Figure()
        fig_power.update_layout(
            title_text='<b>Power</b>', title_x=0.5,
            # xaxis_title=f"<b>UTC{'+' if tim_ax >= 0 else ''}{tim_ax}</b>",
            width=800,
            height=200,
            margin=self._MARGIN_DICT,
            legend=dict(
                x=0.99,
                y=0.99,
                xanchor="right",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.4)",
                borderwidth=0
            )
        )

        state_of_charge = []
        solar_power = []
        power_consume = []
        hours = []

        for _pow_point in self._data_power:

            try:
                state_of_charge.append(_pow_point.state_of_charge)
                pv = _pow_point.pv_power
                if pv < 0:
                    pv = 0
                solar_power.append(pv)
                p_consume = _pow_point.battery_discharge + pv - _pow_point.battery_charge
                power_consume.append(p_consume)
                hours.append(_pow_point.date)
            except (ValueError, TypeError):
                pass

        fig_power.update_xaxes(
            range=[hours[0], hours[-1]]
        )

        fig_power.add_trace(go.Scatter(
            x=hours,
            y=state_of_charge,
            name=self._POWER['state_of_charge']['name'],
            mode="lines",
            yaxis="y",
            line=dict(
                color=self._POWER['state_of_charge']['color'],
                width=1
            )
        ))
        fig_power.add_trace(go.Scatter(
            x=hours,
            y=solar_power,
            name=self._POWER['solar_power']['name'],
            mode="lines",
            yaxis="y2",
            line=dict(
                color=self._POWER['solar_power']['color'],
                width=1
            )
        ))
        fig_power.add_trace(go.Scatter(
            x=hours,
            y=power_consume,
            name=self._POWER['power_consume']['name'],
            mode="lines",
            yaxis="y2",
            line=dict(
                # color=self._POWER['power_consume']['color'],
                color=self.hex_to_rgba(hex_color=self._POWER['power_consume']['color'], alpha=0.5),
                width=1,

            )
        ))

        fig_power.update_layout(
            xaxis=dict(),
            yaxis=dict(
                # title="Skala 1"
            ),
            yaxis2=dict(
                # title="Skala 2",
                overlaying="y",
                side="right"
            ),
        )
        self._image_power_byte = fig_power.to_image(format="png")

        stop = datetime.datetime.now(datetime.timezone.utc)
        logger.info(f"Plots was created. Proces takes: {(stop - start).total_seconds()}")
