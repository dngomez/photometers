import mysql.connector
import os
from astropy.coordinates import EarthLocation, AltAz, get_body
from astropy.time import Time
from astropy.coordinates import solar_system_ephemeris
from astropy import units as u
import numpy as np
import datetime, calendar
import astropy.table as tbl

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
    k = ((1 + np.cos(i))/2.0)*100
    return k

# Set the data location
data_location = os.path.join(os.path.dirname(__file__), "../../binary_data")

# Photometer IDs given by the vendor

device_ids = [
  "6485",
  "6499",
  "6500",
  "6609",
  "6610",
  "6611"
]

# The dates of the files generated every month with the data read by every photometer
device_alt = ["30"]
device_az = ["0"]

# Connect to the database
cnx = mysql.connector.connect(user='photometers', password='photometers_sql', host='localhost', database='photometers')
cursor = cnx.cursor()

# Loop through the devices
for i, device_id in enumerate(device_ids):

  '''
  #store alt/az based on device id  
  altitude_angle = device_alt[i]
  azimuth = device_az[i]
  altitude_angle = float(altitude_angle) * u.deg
  azimuth = float(azimuth) * u.deg
  '''

  # Create the device data table if doesn't exists
  print("Creating table for device %s" % device_id)
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
  
  # Open the binary table with all calculations:
  filename = os.path.join( data_location, f"computed_data_{device_id}.fits")
  data = tbl.Table.read( filename)
  data_dates = Time( data['UTCTime'], scale='utc')


  ## CREATE A FAKE DEVICE_CONF_ID ##
  data['DeviceConfID'] = [1]*len(data)

  # Loop through the file dates, split by monthly data:
  min_date = data_dates.min()
  max_date = data_dates.max()
  min_date_dt = min_date.to_datetime()
  max_date_dt = data_dates.to_datetime()

  date = datetime.datetime( min_date_dt.year, min_date_dt.month, 1, 12, 0, 0)

  while max_date > date:
    # Populate for a single month (to prevent bottlenecks)
    days_in_month = datetime.timedelta(days=calendar.monthrange(date.year, date.month)[1])
    monthly_data = data[(data_dates > date) & (data_dates < date + days_in_month)]
    print( f"Start date is {date} and end date is {date + days_in_month}")

   
    print("Populating table for device %s and month %s-%s with %s lines/records" % (device_id, date.year, date.month, len(monthly_data)))
    
    # Reorder the columns for the output list to populate:
    database_monthly_data = monthly_data[['UTCTime', 'LocalTime', 'temp', 'counts', 'freq', 'msas', 'DeviceConfID', 'SunAlt','MoonAlt','GalacticLat','MoonAz','GeoTrueEclipticLat','MoonDistance','MoonPhaseAngle','MoonIllum']]
    
    # Make sure that the datatype is string:
    database_monthly_data['UTCTime'] = database_monthly_data['UTCTime'].astype(str)
    database_monthly_data['LocalTime'] = database_monthly_data['LocalTime'].astype(str)

    # Convert Astropy table to Python list:
    database_data = database_monthly_data.as_array().tolist()

    ### THIS IS NOT USED ANYMORE, KEPT FOR REFERENCE
    '''
    if False:
          database_data.append((
            data[0],                      # utc_time
            data[1],                      # local_time
            float(data[2]),               # temperature
            float(data[3]),               # counts
            float(data[4]),               # frequency
            float(data[5]),               # msas
            1,                            # device_configuration_id (this should change depending on the device used and device position
            float(sun_altitude.value),    # sun_altitude
            float(moon_altitude.value),   # moon_altitude
            float(sun_az.value),          # sun_az -> I PUT GalacticLat
            float(moon_az.value),         # moon_az
            float(sun_distance.value),    # sun_distance -> I PUT GeoTrueEclipticLat
            float(moon_distance.value),   # moon_distance
            float(phase_angle.value),     # phase_angle
            float(moon_illum.value),      # moon_illum
          ))
    '''
    # Insert the data
    cursor.executemany(f"""INSERT IGNORE INTO `device_data_{device_id}`
    (`utc_time`,
    `local_time`,
    `temperature`,
    `counts`,
    `frequency`,
    `msas`,
    `device_configuration_id`,
    `sun_altitude`,
    `moon_altitude`,
    `sun_az`,
    `moon_az`,
    `sun_distance`,
    `moon_distance`,
    `phase_angle`,
    `moon_illum`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", database_data)

    print("Writing to database")
    cnx.commit()
    
    # Increase loop:
    date = date + days_in_month
    
# Write the changes to the database
cnx.close()
