from datetime import date
import pandas as pd

from solar_angle import fetch_solar_data
from weather import fetch_weather

weather = fetch_weather()
(reg, leap) = fetch_solar_data()

hourly_data = {
    'date': [],
    'efficiency_data': []
}
for year in range(2010, 2024):
    if year % 4 == 0:
        for data in leap:
            hourly_data['date'].append('{}-{}-{:02d} {:02d}:00:00'.format(
                year,
                data['month'],
                data['day'],
                data['hour']
            ))
            hourly_data['efficiency_data'].append(data['efficiency_data'])
    else:
        for data in reg:
            hourly_data['date'].append('{}-{}-{:02d} {:02d}:00:00'.format(
                year,
                data['month'],
                data['day'],
                data['hour']
            ))
            hourly_data['efficiency_data'].append(data['efficiency_data'])

hourly_data['date'] = pd.to_datetime(hourly_data['date'], utc=False)
hourly_data = pd.DataFrame(data=hourly_data)
    
hourly_data = pd.merge(weather, hourly_data, how='left', on='date')

def calc_hourly_production(row):
    temp = row[2]
    temp_c = (temp - 32) / 1.8
    cloud_cover = row[3]
    
    temp_drop = 1
    if temp_c > 25:
        temp_diff_c = temp_c - 25
        temp_drop = 1 - temp_diff_c * .03

    hourly_production = 0

    for min_coefficient in row[4]:
        coefficient = min_coefficient * temp_drop * (1 - cloud_cover / 100)
        # 610W / panel * 90 panels * coefficient / 1000W/kW
        produced = round(610 * 90 * coefficient / 1000, 3)
        hourly_production += produced

    # 60kWm / kWh
    return hourly_production / 60

production_data = {}

for row in hourly_data.itertuples():
    year = str(row[1].year)
    month_idx = row[1].month - 1

    if not year in production_data.keys():
        production_data[year] = [0] * 12

    if isinstance(row[4], list) and len(row[4]) > 0:
        power = calc_hourly_production(row)
        production_data[year][month_idx] += round(power, 3)

monthly_sums = [0] * 12
for year in production_data.keys():
    # Fixes a timezone issue from weather fetching
    if year == '2024':
        break

    total_production = 0
    for i, monthly_production in enumerate(production_data[year]):
        monthly_sums[i] += monthly_production
        total_production += monthly_production
    avg_monthly_production = total_production / 12
    print("{} Average Monthly Production: {}kWh".format(year, round(avg_monthly_production, 3)))

for i, monthly_sum in enumerate(monthly_sums):
    average_production = monthly_sum / 14
    month_text = date(1900, i + 1, 1).strftime('%B')
    print('{} Average Production: {}kWh'.format(month_text, round(average_production, 3)))

