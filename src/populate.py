import mysql.connector
import os

# Set the data location
data_location = os.path.join(os.path.dirname(__file__), "../sqm_data")

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
  "2025-01"
]

# Connect to the database
cnx = mysql.connector.connect(user='photometers', password='photometers_sql', host='localhost', database='photometers')
cursor = cnx.cursor()

# Loop through the devices
for device_id in device_ids:
  # Create the device data table if doesn't exists
  cursor.execute("CREATE TABLE IF NOT EXISTS `device_data_%s` (`utc_time` DATETIME NOT NULL UNIQUE PRIMARY KEY,`local_time` DATETIME NOT NULL,`temperature` FLOAT,`counts` FLOAT,`frequency` FLOAT,`msas` FLOAT,`device_configuration_id` INT,FOREIGN KEY (`device_configuration_id`) REFERENCES `device_configuration`(`id`));" %(device_id))

  # Loop through the file dates
  for file_date in file_dates:
    database_data = []
    with open(os.path.join(data_location, "sqm_ctio_%s/SQM_%s_CTIO_%s.dat" %(device_id, device_id, file_date))) as f:
      line = f.readline()
      while line:
        # Skip commented lines
        if not line.startswith("#"):
          data = line.strip().split(";")
          database_data.append((
            data[0],          # utc_time
            data[1],          # local_time
            float(data[2]),   # temperature
            float(data[3]),   # counts
            float(data[4]),   # frequency
            float(data[5]),   # msas
            1                 # device_configuration_id (this should change depending on the device used and device position)
          ))
        line = f.readline()

    # Insert the data
    cursor.executemany(f"INSERT IGNORE INTO `device_data_{device_id}` (`utc_time`, `local_time`, `temperature`, `counts`, `frequency`, `msas`, `device_configuration_id`) VALUES (%s, %s, %s, %s, %s, %s, %s)", database_data)

# Write the changes to the database
cnx.commit()
cnx.close()
