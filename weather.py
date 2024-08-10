import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

url = 'https://archive-api.open-meteo.com/v1/archive'
params = {
  'latitude': ,
  'longitude': ,
  'start_date': '2010-01-01',
  'end_date': '2023-12-31',
  'hourly': ['temperature_2m', 'cloud_cover'],
  'temperature_unit': 'fahrenheit',
  'timezone': 'America/New_York'
}

cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def fetch_weather():
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0] # The one location requested

    hourly = response.Hourly()
    hourly_temperature = hourly.Variables(0).ValuesAsNumpy()
    hourly_cloud_cover = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {'date': pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit='s', utc = False),
        end = pd.to_datetime(hourly.TimeEnd(), unit='s', utc = False),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = 'left'
    )}
    hourly_data['temperature'] = hourly_temperature
    hourly_data['cloud_cover'] = hourly_cloud_cover

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    return hourly_dataframe
