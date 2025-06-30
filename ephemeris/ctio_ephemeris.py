import numpy as np
from datetime import datetime, timedelta, UTC
import astropy.units as u
from astropy.coordinates import get_sun, AltAz, EarthLocation, get_body, TETE
from astropy.time import Time
from astroplan import Observer, moon_illumination
import astropy.table as tbl
import mysql.connector
import sys

# Site Location
location = EarthLocation.of_site("ctio")
ctio = Observer(location=location, name="ctio")

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
te = ctio.twilight_evening_astronomical(time_array[0], which='next', n_grid_points=samples)
twilight_evening = np.repeat(te.to_datetime().strftime("%H:%M"), samples)

# Twilight Morning
tm = ctio.twilight_morning_astronomical(time_array[0], which='next', n_grid_points=samples)
twilight_morning = np.repeat(tm.to_datetime().strftime("%H:%M"), samples)

# DECam start time
dst = ctio.sun_set_time(time_array[0], which='next', horizon=-10.0*u.deg, n_grid_points=samples)
decam_start_time = np.repeat(dst.to_datetime().strftime("%H:%M"), samples)

# DECam end time
det = ctio.sun_rise_time(time_array[0], which='next', horizon=-10.0*u.deg, n_grid_points=samples)
decam_end_time = np.repeat(det.to_datetime().strftime("%H:%M"), samples)

# Sunset
s_set = ctio.sun_set_time(time_array[0], which='next', horizon=-0.8333*u.deg, n_grid_points=samples)
sunset_time = np.repeat(s_set.to_datetime().strftime("%H:%M"), samples)

# Sunrise
s_rise = ctio.sun_rise_time(time_array[0], which='next', horizon=-0.8333*u.deg, n_grid_points=samples)
sunrise_time = np.repeat(s_rise.to_datetime().strftime("%H:%M"), samples)

# Midnight
night_length = tm.to_datetime() - te.to_datetime()
half_night_length = night_length/2
midnight_value = te.to_datetime() + half_night_length
midnight = np.repeat(midnight_value.strftime("%H:%M"), samples)

# Moon Coordinates
moon_pos = get_body("moon", time=time_array, location=location)
obs_moon_pos = moon_pos.transform_to(TETE())
moon_ra = obs_moon_pos.ra.to(u.deg).value
moon_ra_hms = obs_moon_pos.ra.to_string(unit=u.hourangle, sep="hm", fields=2, pad=True)
moon_dec = obs_moon_pos.dec.to(u.deg).value
moon_dec_dms = obs_moon_pos.dec.to_string(unit=u.degree, sep="dm", fields=2, pad=True)

# Moon Rise
mr = ctio.moon_rise_time(time_array[0], which='next', horizon=-2.2333*u.deg, n_grid_points=samples)
moon_rise = np.repeat(mr.to_datetime().strftime("%H:%M"), samples)

# Moon Set
ms = ctio.moon_set_time(time_array[0], which='next', horizon=-2.2333*u.deg, n_grid_points=samples)
moon_set = np.repeat(ms.to_datetime().strftime("%H:%M"), samples)

# Moon Illumination
moon_illum = moon_illumination(time_array)

# Create big data matrix
database_data = tbl.Table([times, sun_altitude, sunrise_time, sunset_time, twilight_evening, twilight_morning, decam_start_time, decam_end_time, midnight, moon_ra, moon_ra_hms, moon_dec, moon_dec_dms, moon_rise, moon_set, moon_illum],
        names=["time", "sun_altitude", "sun_rise", "sun_set", "twilight_evening", "twilight_morning", "decam_start_time", "decam_end_time", "midnight", "moon_ra", "moon_ra_hms", "moon_dec", "moon_dec_dms", "moon_rise", "moon_set", "moon_illumination"]).as_array().tolist()

# Database connection
cnx = mysql.connector.connect(user='photometers', password='photometers_sql', host='localhost', database='photometers')
cursor = cnx.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS `ctio_ephemeris`
    (`time` DATETIME NOT NULL UNIQUE PRIMARY KEY,
    `sun_altitude` FLOAT,
    `sun_rise` VARCHAR(6),
    `sun_set` VARCHAR(6),
    `twilight_evening` VARCHAR(6),
    `twilight_morning` VARCHAR(6),
    `decam_start_time` VARCHAR(6),
    `decam_end_time` VARCHAR(6),
    `midnight` VARCHAR(6),
    `moon_ra` FLOAT,
    `moon_ra_hms` VARCHAR(6),
    `moon_dec` FLOAT,
    `moon_dec_dms` VARCHAR(6),
    `moon_rise` VARCHAR(6),
    `moon_set` VARCHAR(6),
    `moon_illumination` FLOAT);""")

cursor.executemany(f"""INSERT IGNORE INTO `ctio_ephemeris`
    (`time`,
    `sun_altitude`,
    `sun_rise`,
    `sun_set`,
    `twilight_evening`,
    `twilight_morning`,
    `decam_start_time`,
    `decam_end_time`,
    `midnight`,
    `moon_ra`,
    `moon_ra_hms`,
    `moon_dec`,
    `moon_dec_dms`,
    `moon_rise`,
    `moon_set`,
    `moon_illumination`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", database_data)

cnx.commit()
cnx.close()