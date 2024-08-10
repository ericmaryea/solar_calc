#!python3
from math import pi, sqrt
import numpy as np


def rad(degrees):
    return degrees * pi / 180

def deg(radians):
    return radians * 180 / pi

def declination_angle(day, is_leap_year = False):
    """Returns the solar declination angle in radians

    Arguments:
    - day: number of day since Jan 1 00:00:00 UTC
    - is_leap_year: Determines divisor for number of days
    """
    day_divisor = 365
    if is_leap_year:
        day_divisor = 366

    return np.asin(
        np.sin(rad(-23.44)) * np.cos(rad(
            360 / day_divisor * (day + 10)
            + 360 / pi * 0.0167 * np.sin(rad(360 / day_divisor * (day - 2)))
        ))
    )

def c_lst(time, day, longitude, tz_offset, is_leap_year=False):
    """Returns local solar time in minutes corrected for longitude and latitude

    Arguments:
    - time: Local time in minutes since 00:00:00
    - day: day since Jan 1 00:00:00
    - longitude: Longitude in degrees
    - tz_offset: Time zone offset from UTC
    - is_leap_year: Determines divisor for number of days
    """
    day_divisor = 365
    if is_leap_year:
        day_divisor = 366  

    # Fractional year in radians
    fractional_year = 2 * pi / day_divisor * (
        day - 1 + (time / 60 - 12) / 24
    )

    # correction for earth's orbit/tilt in minutes
    eot = 229.18 * (
        0.000075
        + 0.001868 * np.cos(fractional_year)
        - 0.032077 * np.sin(fractional_year)
        - 0.014615 * np.cos(2 * fractional_year)
        - 0.040849 * np.sin(2 * fractional_year)
    )

    return time + eot + 4 * (longitude - 15 * tz_offset)


def solar_hour_angle(time, day, longitude, tz_offset, is_leap_year=False):
    """Returns the solar hour angle in radians

    Arguments: 
    - time: Local solar time in minutes since 00:00:00
    - day: day since Jan 1 00:00:00
    - longitude: Longitude in degrees
    - tz_offset: Time zone offset from UTC
    - is_leap_year: Determines divisor for number of days
    """
    corrected_local_solar_time = c_lst(time, day, longitude, tz_offset, is_leap_year)
    return rad(
        corrected_local_solar_time / 4 - 180
    )

def solar_elevation_angle(latitude, d_angle, sh_angle):
    """Returns the solar elevation angle in radians
    
    Arguments:
    - latitude: Latitude in degrees
    - d_angle: solar declination angle in radians
    - sh_angle: solar hour angle in radians
    """
    return np.asin(
        np.sin(rad(latitude)) * np.sin(d_angle)
        + np.cos(rad(latitude)) * np.cos(d_angle) * np.cos(sh_angle)
    )

def solar_azimuth_angle(latitude, d_angle, sh_angle, e_angle):
    """Returns the solar azimuth angle in radians
    
    Arguments:
    - latitude: Latitude in degrees
    - d_angle: solar declination angle in radians
    - sh_angle: solar hour angle in radians
    - e_angle: solar elevation angle in radians
    """
    a_angle = np.acos(
        (np.sin(d_angle) * np.cos(rad(latitude)) - np.cos(d_angle) * np.sin(rad(latitude)) * np.cos(sh_angle)) / np.cos(e_angle)
    )

    if sh_angle > 0:
        a_angle = rad(360) - a_angle

    deg_angle = deg(sh_angle)

    if deg_angle == 0:
        return rad(-90)
    elif deg_angle == -90:
        return 0
    elif deg_angle == 90:
        return rad(180)
    elif deg_angle < -90 or (deg_angle > 0 and deg_angle < 90) or (deg_angle > -90 and deg_angle < 0):
        return -sh_angle - rad(90)
    elif deg_angle > 90:
        return rad(270) - sh_angle
    else:
        raise ValueError("Angle out of bounds: {}".format(deg_angle))


def solar_data(latitude, longitude, day, time, tz_offset, is_leap_year=False):
    """Returns the solar data in the form:
    {
        'e_angle': [val in radians],
        'a_angle': [val in radians]
    }

    Arguments:
    - latitude: Latitude in degrees
    - longitude: Longitude in degrees
    - day: day since Jan 1 00:00:00 UTC
    - time: Local time in minutes since 00:00:00
    - tz_offset: Time zone fofset from UTC
    - is_leap_year: Determines divisor for number of days
    """
    d_angle = declination_angle(day, is_leap_year)
    sh_angle = solar_hour_angle(time, day, longitude, tz_offset, is_leap_year)
    e_angle = solar_elevation_angle(latitude, d_angle, sh_angle)
    a_angle = solar_azimuth_angle(latitude, d_angle, sh_angle, e_angle)

    
    return {
        'e_angle': e_angle,
        'a_angle': a_angle
    }

def get_solar_vector(e_angle, a_angle):
    """Returns the reverse solar vector in (x, y, z)

    Arguments:
    - e_angle: Solar elevation angle in radians
    - a_angle: Solar azimuth angle in radians
    """
    a = np.cos(e_angle)
    b = np.sin(e_angle)
    c = np.cos(a_angle)
    d = np.cos(a_angle)

    x = sqrt((b**2 * c**2) / (d**2 + b**2 * c**2))
    y = -a * sqrt(1 - (b**2 * c**2) / (d**2 + b**2 * c**2))
    z = b * sqrt(1 - (b**2 * c**2) / (d**2 + b**2 * c**2))

    return (x, y, z)

def get_efficiency_coefficient(panel_normal, solar_vector):
    (xa, ya, za) = panel_normal
    (xb, yb, zb) = solar_vector
    angle = np.acos(
        (xa*xb + ya*yb + za*zb) / (sqrt(xa**2 + ya**2 + za**2) * sqrt(xb**2 + yb**2 + zb**2))
    )

    deg_angle = deg(angle)

    if deg_angle > 90:
        raise ValueError("Out of upper bounds: {}".format(solar_vector))
    elif deg_angle < 0:
        raise ValueError("Out of lower bounds: {}".format(solar_vector))

    return (90 - abs(deg_angle)) / 100

    
def fetch_solar_data(lat, long):
    # winter_panel_normal = (0, -np.cos(rad(50)), np.sin(rad(50)))
    # summer_panel_normal = (0, -np.cos(rad(25)), np.sin(rad(25)))
    winter_panel_normal = (0, -np.cos(rad(45)), np.sin(rad(45)))
    summer_panel_normal = (0, -np.cos(rad(45)), np.sin(rad(45)))

    ##########################
    ###    REGULAR YEAR    ###
    ##########################

    is_winter_angle = True
    regular_data = []

    for day in range(0, 365):
        if day >= 0 and day <= 30:
            month = '01'
            day_subtractor = -1
        elif day >= 31 and day <= 58:
            month = '02'
            day_subtractor = 30
        elif day >= 59 and day <= 89:
            month = '03'
            day_subtractor = 58
        elif day >= 90 and day <= 119:
            month = '04'
            day_subtractor = 89
        elif day >= 120 and day <= 150:
            month = '05'
            day_subtractor = 119
        elif day >= 151 and day <= 180:
            month = '06'
            day_subtractor = 150
        elif day >= 181 and day <= 211:
            month = '07'
            day_subtractor = 180
        elif day >= 212 and day <= 242:
            month = '08'
            day_subtractor = 211
        elif day >= 243 and day <= 272:
            month = '09'
            day_subtractor = 242
        elif day >= 273 and day <= 303:
            month = '10'
            day_subtractor = 272
        elif day >= 304 and day <= 333:
            month = '11'
            day_subtractor = 303
        elif day >= 334 and day <= 364:
            month = '12'
            day_subtractor = 333

        has_started = False
        day_start_hour = 0
        day_start_min = 0
        day_end_hour = 0
        day_end_min = 0

        day_data = []

        for hour in range(5,22):
            hour_data = {
                'month': month,
                'day': day - day_subtractor,
                'hour': hour,
                'angle_data': []
            }
            for min in range(0, 60):
                data = solar_data(lat, long, day, hour * 60 + min, -5)
                if deg(data['e_angle']) >= 0 and deg(data['a_angle']) < 0 and deg(data['a_angle']) > -180:
                    hour_data['angle_data'].append(data)
                    if not has_started:
                        hour_data['start_time'] = '{:02d}:{:02d}'.format(hour, min)
                        day_start_hour = hour
                        day_start_min = min
                elif has_started:
                    if min == 0:
                        end_hour = hour - 1
                        end_min = 59
                    else:
                        end_hour = hour
                        end_min = min
                    hour_data['end-time'] = '{:02d}:{:02d}'.format(end_hour, end_min)
                    day_end_hour = end_hour
                    day_end_min = end_min

            day_data.append(hour_data)

        day_min = 0
        day_hr = 0
        if day_start_min > 0:
            day_min = 60 - day_start_min
            day_hr = 11 - day_start_hour
        else:
            day_hr = 12 - day_start_hour
        day_min += day_end_min
        day_hr += day_end_hour
        if day_min > 60:
            day_hr += 1
            day_min -= 60

        if is_winter_angle:
            if day_hr == 12:
                is_winter_angle = False
        else:
            if day_hr == 12:
                is_winter_angle = True

        for hour_data in day_data:
            efficiency_coefficients = []
            for angle_data in hour_data['angle_data']:
                solar_vector = get_solar_vector(angle_data['e_angle'], angle_data['a_angle'])
                if is_winter_angle:
                    efficiency_coefficients.append(get_efficiency_coefficient(winter_panel_normal, solar_vector))
                else:
                    efficiency_coefficients.append(get_efficiency_coefficient(summer_panel_normal, solar_vector))
            del hour_data['angle_data']
            hour_data['efficiency_data'] = efficiency_coefficients

        regular_data.extend(day_data)
        

    #######################
    ###    LEAP YEAR    ###
    #######################
        
    is_winter_angle = True
    leap_year_data = []
    for day in range(0, 366):
        if day >= 0 and day <= 30:
            month = '01'
            day_subtractor = -1
        elif day >= 31 and day <= 59:
            month = '02'
            day_subtractor = 30
        elif day >= 60 and day <= 90:
            month = '03'
            day_subtractor = 59
        elif day >= 91 and day <= 120:
            month = '04'
            day_subtractor = 90
        elif day >= 121 and day <= 151:
            month = '05'
            day_subtractor = 120
        elif day >= 152 and day <= 181:
            month = '06'
            day_subtractor = 151
        elif day >= 182 and day <= 212:
            month = '07'
            day_subtractor = 181
        elif day >= 213 and day <= 243:
            month = '08'
            day_subtractor = 212
        elif day >= 244 and day <= 273:
            month = '09'
            day_subtractor = 243
        elif day >= 274 and day <= 304:
            month = '10'
            day_subtractor = 273
        elif day >= 305 and day <= 334:
            month = '11'
            day_subtractor = 304
        elif day >= 335 and day <= 365:
            month = '12'
            day_subtractor = 334

        has_started = False
        day_start_hour = 0
        day_start_min = 0
        day_end_hour = 0
        day_end_min = 0

        day_data = []

        for hour in range(5, 22):
            hour_data = {
                'month': month,
                'day': day - day_subtractor,
                'hour': hour,
                'angle_data': []
            }
            for min in range(0, 60):
                data = solar_data(lat, long, day, hour * 60 + min, -5)
                if deg(data['e_angle']) >= 0 and deg(data['a_angle']) < 0 and deg(data['a_angle']) > -180:
                    hour_data['angle_data'].append(data)
                    if not has_started:
                        hour_data['start_time'] = '{:02d}:{:02d}'.format(hour, min)
                        day_start_hour = hour
                        day_start_min = min
                elif has_started:
                    if min == 0:
                        end_hour = hour - 1
                        end_min = 59
                    else:
                        end_hour = hour
                        end_min = min
                    hour_data['end-time'] = '{:02d}:{:02d}'.format(end_hour, end_min)
                    day_end_hour = end_hour
                    day_end_min = end_min

            day_data.append(hour_data)

        day_min = 0
        day_hr = 0
        if day_start_min > 0:
            day_min = 60 - day_start_min
            day_hr = 11 - day_start_hour
        else:
            day_hr = 12 - day_start_hour
        day_min += day_end_min
        day_hr += day_end_hour
        if day_min > 60:
            day_hr += 1
            day_min -= 60

        if is_winter_angle:
            if day_hr == 12:
                is_winter_angle = False
        else:
            if day_hr == 12:
                is_winter_angle = True

        for hour_data in day_data:
            efficiency_coefficients = []
            for angle_data in hour_data['angle_data']:
                solar_vector = get_solar_vector(angle_data['e_angle'], angle_data['a_angle'])
                if is_winter_angle:
                    efficiency_coefficients.append(get_efficiency_coefficient(winter_panel_normal, solar_vector))
                else:
                    efficiency_coefficients.append(get_efficiency_coefficient(summer_panel_normal, solar_vector))
            del hour_data['angle_data']
            hour_data['efficiency_data'] = efficiency_coefficients
        
        leap_year_data.extend(day_data)
    
    return (regular_data, leap_year_data)
