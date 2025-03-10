import mysql.connector
import os
from astropy.coordinates import EarthLocation, AltAz, get_body
from astropy.time import Time
from astropy.coordinates import solar_system_ephemeris
from astropy import units as u
import numpy as np

def moon_phase_angle(time, ephemeris=None, location=None):
   
    #Calculate the moon's orbital phase in radians.
    # Astroplan
   
    sun = get_body("sun", time, ephemeris=ephemeris)
    moon = get_body("moon", time, ephemeris=ephemeris)
    elongation = sun.separation(moon).to(u.radian)
    return np.arctan2(sun.distance*np.sin(elongation),
                      moon.distance - sun.distance*np.cos(elongation))


def moon_illumination(time, ephemeris=None, location=None):
    # astroplan
   
    i = moon_phase_angle(time, ephemeris=ephemeris)
    k = (1 + np.cos(i))/2.0
    return k.value

# Set the data location
data_location = os.path.join(os.path.dirname(__file__), "../../sqm_data")

# Photometer IDs given by the vendor
device_ids = [
  "6499",
  "6500",
  "6609",
  "6610",
  "6611"
]

# The dates of the files generated every month with the data read by every photometer
file_dates = [
  "2023-12",
  "2024-01",
  "2024-02",
  "2024-03",
  "2024-04",
  "2024-05",
  "2024-06",
  "2024-07",
  "2024-08",
  "2024-09",
  "2024-10",
  "2024-11",
  "2024-12",
  "2025-01",
  "2025-02",
  "2025-03"
]
   
# Connect to the database
cnx = mysql.connector.connect(user='photometers', password='photometers_sql', host='localhost', database='photometers')
cursor = cnx.cursor()

# Define the observing location (Cerro Tololo, Chile)
photometers_local = EarthLocation(lat=-70.8035*u.deg, lon=-30.1682*u.deg, height=300*u.m)

# Get the current UTC time
time = Time.now()

altitude_angle = 30 * u.deg  # Observer's height
azimuth = 30 * u.deg  # Given azimuth

# Define the observer's location (altitude-azimuth)
altaz = AltAz(alt=altitude_angle, az=azimuth, obstime=time, location=photometers_local)

# Loop through the devices
for device_id in device_ids:
  # Create the device data table if doesn't exists
   
  cursor.execute("""CREATE TABLE IF NOT EXISTS `device_data_%s`
  (`utc_time` DATETIME NOT NULL UNIQUE PRIMARY KEY,
  `local_time` DATETIME NOT NULL,
  `temperature` FLOAT,
  `counts` FLOAT,
  `frequency` FLOAT,
  `msas` FLOAT,
  `device_configuration_id` INT,
  `sun_altitude` FLOAT,
  `moon_altitude` FLOAT,
  `sun_az` FLOAT,
  `moon_az` FLOAT,
  `sun_distance` FLOAT,
  `moon_distance` FLOAT,
  `phase_angle` FLOAT,
  `moon_illum` FLOAT,
  FOREIGN KEY (`device_configuration_id`)
  REFERENCES `device_configuration`(`id`));""" %(device_id))

  cursor.execute("""ALTER TABLE `device_data_%s`
                 """ %(device_id))

   
  # Loop through the file dates
  for file_date in file_dates:
    database_data = []

    # Compute Sun and Moon positions
    with solar_system_ephemeris.set('builtin'):
        sun_altaz = get_body("sun", time).transform_to(altaz)
        moon_altaz = get_body("moon", time).transform_to(altaz)
     
    #extract the values
    sun_altitude = sun_altaz.alt
    moon_altitude = moon_altaz.alt
    sun_az = sun_altaz.az
    moon_az = moon_altaz.az
    sun_distance = sun_altaz.distance
    moon_distance = moon_altaz.distance

    # Compute Moon illumination fraction (0 to 1)
    phase_angle= moon_phase_angle(time)
    moon_illum = moon_illumination(time)
   
    with open(os.path.join(data_location, "sqm_ctio_%s/SQM_%s_CTIO_%s.dat" %(device_id, device_id, file_date))) as f:
      line = f.readline()
      while line:
        # Skip commented lines
        if not line.startswith("#"):
          data = line.strip().split(";")
          database_data.append((
            data[0],                      # utc_time
            data[1],                      # local_time
            float(data[2]),               # temperature
            float(data[3]),               # counts
            float(data[4]),               # frequency
            float(data[5]),               # msas
            1,                            # device_configuration_id (this should change depending on the device used and device position),
            float(sun_altitude.value),    # sun_altitude
            float(moon_altitude.value),   # moon_altitude
            float(sun_az.value),          # sun_az
            float(moon_az.value),         # moon_az
            float(sun_distance.value),    # sun_distance
            float(moon_distance.value),   # moon_distance
            float(phase_angle.value),     # phase_angle
            float(moon_illum.value),      # moon_illum
          ))
        line = f.readline()

    # Insert the data
    cursor.executemany(f"""INSERT IGNORE INTO `device_data_{device_id}`
    (`utc_time`,
    `local_time`,
    `temperature`,
    `counts`,
    `frequency`,
    `msas`,
    `device_configuration_id`
    `sun_altitude`,
    `moon_altitude`,
    `sun_az`,
    `moon_az`,
    `sun_distance`,
    `moon_distance`,
    `phase_angle`,
    `moon_illum`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", database_data)

# Write the changes to the database
cnx.commit()
cnx.close()
