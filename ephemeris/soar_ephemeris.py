import numpy as np
from datetime import timedelta
import astropy.units as u
from astropy.coordinates import get_sun, AltAz, EarthLocation, get_body, TETE
from astropy.time import Time
from astroplan import Observer, moon_illumination
import astropy.table as tbl
import mysql.connector
import sys

# Site Location
location = EarthLocation.from_geodetic(-70.733642, -30.237892, height=2748)
soar= Observer(location=location, name="soar")

# Time Array
now = Time(sys.argv[1], scale='utc').to_datetime()
# now = datetime.now(UTC).replace(second=0, microsecond=0)
tomorrow = now + timedelta(days=1)
start_time = np.datetime64(now)
end_time = np.datetime64(tomorrow)
times = np.arange(start_time, end_time, np.timedelta64(1, 'm'))
time_array = Time(times)
samples = len(times)

# Sun Coordinates
sun_pos = get_sun(time_array)

# Sun Altitude
sun_altaz = sun_pos.transform_to(AltAz(location=location))
sun_altitude = sun_altaz.alt.to(u.deg).value

# Twilight Evening
te = soar.twilight_evening_astronomical(time_array[0], which='next', n_grid_points=samples)
twilight_evening = np.repeat(te.to_datetime().strftime("%H:%M"), samples)

# Twilight Morning
tm = soar.twilight_morning_astronomical(time_array[0], which='next', n_grid_points=samples)
twilight_morning = np.repeat(tm.to_datetime().strftime("%H:%M"), samples)

# DECam start time
ten = soar.twilight_evening_nautical(time_array[0], which='next', n_grid_points=samples)
twilight_eve_nautical = np.repeat(ten.to_datetime().strftime("%H:%M"), samples)

# DECam end time
tmn = soar.twilight_morning_nautical(time_array[0], which='next', n_grid_points=samples)
twilight_mor_nautical = np.repeat(tmn.to_datetime().strftime("%H:%M"), samples)

# Moon Coordinates
moon_pos = get_body("moon", time=time_array, location=location)
obs_moon_pos = moon_pos.transform_to(TETE())
moon_ra = obs_moon_pos.ra.to(u.deg).value
moon_ra_hms = obs_moon_pos.ra.to_string(unit=u.hourangle, sep="hm", fields=2, pad=True)
moon_dec = obs_moon_pos.dec.to(u.deg).value
moon_dec_dms = obs_moon_pos.dec.to_string(unit=u.degree, sep="dm", fields=2, pad=True)

# Moon Rise
mr = soar.moon_rise_time(time_array[0], which='next', horizon=-2.2333*u.deg, n_grid_points=samples)
moon_rise = np.repeat(mr.to_datetime().strftime("%H:%M"), samples)

# Moon Set
ms = soar.moon_set_time(time_array[0], which='next', horizon=-2.2333*u.deg, n_grid_points=samples)
moon_set = np.repeat(ms.to_datetime().strftime("%H:%M"), samples)

# Moon Illumination
moon_illum = moon_illumination(time_array)

# Create big data matrix
database_data = tbl.Table([times, sun_altitude, twilight_evening, twilight_morning, twilight_eve_nautical, twilight_mor_nautical, moon_ra, moon_ra_hms, moon_dec, moon_dec_dms, moon_rise, moon_set, moon_illum],
        names=["time", "sun_altitude", "twilight_evening", "twilight_morning", "twilight_evening_nautical", "twilight_morning_nautical", "moon_ra", "moon_ra_hms", "moon_dec", "moon_dec_dms", "moon_rise", "moon_set", "moon_illumination"]).as_array().tolist()

# Database connection
cnx = mysql.connector.connect(user='photometers', password='photometers_sql', host='localhost', database='photometers')
cursor = cnx.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS `soar_ephemeris`
    (`time` DATETIME NOT NULL UNIQUE PRIMARY KEY,
    `sun_altitude` FLOAT,
    `twilight_evening` VARCHAR(6),
    `twilight_morning` VARCHAR(6),
    `twilight_evening_nautical` VARCHAR(6),
    `twilight_morning_nautical` VARCHAR(6),
    `moon_ra` FLOAT,
    `moon_ra_hms` VARCHAR(6),
    `moon_dec` FLOAT,
    `moon_dec_dms` VARCHAR(6),
    `moon_rise` VARCHAR(6),
    `moon_set` VARCHAR(6),
    `moon_illumination` FLOAT);""")

cursor.executemany(f"""INSERT IGNORE INTO `soar_ephemeris`
    (`time`,
    `sun_altitude`,
    `twilight_evening`,
    `twilight_morning`,
    `twilight_evening_nautical`,
    `twilight_morning_nautical`,
    `moon_ra`,
    `moon_ra_hms`,
    `moon_dec`,
    `moon_dec_dms`,
    `moon_rise`,
    `moon_set`,
    `moon_illumination`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", database_data)

cnx.commit()
cnx.close()