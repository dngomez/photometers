## Database configuration

#### device_configuration table

| Column Name | Data Type | Description |
| id | INT | Id of the database entry (incremental) |
| device_id | INT | Unique identifier of the device given by the vendor |
| date_setup | DATE | Last date the device was set up |
| mount_azimuth | VARCHAR(45) | Azimuth of the device's mount |
| mount_altitude | VARCHAR(45) | Altitude of the device's mount |
| mount_azimuth_offset | FLOAT | Azimuth offset of the device's mount |
| mount_location | VARCHAR(45) | String with mount location, i.e. "Cerro Tololo" |

#### device_data\_<DEVICE_ID>

| Column Name | Data Type | Description |
| utc_time | DATETIME | UTC time of the data point |
| local_time | DATETIME | Local time of the data point |
| temperature | FLOAT | Measured temperature in Celcius |
| counts | FLOAT | Measured counts |
| frequency | FLOAT | Frequency in Hz |
| msas | FLOAT | Magnitude over the area mag/arcsec^2 |
| device_configuration | INT | related device configuration record |

## Current device IDs:

- 6485 [2025-01, today]
- 6499 [2023-12, today]
- 6500 [2023-12, today]
- 6609 [2023-12, today]
- 6610 [2023-12, today]
- 6611 [2023-12, today]

## SQL Examples

- Create device_configuration table
  SQL COMMANDS TO CREATE THE TABLES
  CREATE TABLE IF NOT EXISTS `device_configuration` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `device_id` INT NOT NULL,
  `date_setup` DATE,
  `mount_azimuth` VARCHAR(45),
  `mount_altitude` VARCHAR(45),
  `mount_azimuth_offset` FLOAT,
  `mount_location` VARCHAR(45)
  );

- Insert record into device_configuration table
  INSERT INTO `device_configuration` (`device_id`, `date_setup`, `mount_azimuth`, `mount_altitude`, `mount_azimuth_offset`, `mount_location`) VALUES (6499, '2019-01-01', '0', '0', 0, '0');

- Create device_data\_<DEVICE_ID> table
  CREATE TABLE IF NOT EXISTS `device_data_6500` (
  `utc_time` DATETIME NOT NULL UNIQUE PRIMARY KEY,
  `local_time` DATETIME NOT NULL,
  `temperature` FLOAT,
  `counts` FLOAT,
  `frequency` FLOAT,
  `msas` FLOAT,
  `device_configuration_id` INT,
  FOREIGN KEY (`device_configuration_id`) REFERENCES `device_configuration`(`id`),
  );

## To Do

[x] Database running in the test account - Diego
[ ] Define which extra coordinates are needed - Guillermo
[ ] Create a new populate script with the astropy calculations of new coordinates (ra, dec) - Jacinda
[ ] Start grafana server - Diego
[ ] Create grafana dashboard to show devices data - Jacinda
[ ] Enable connection to weather station database / ITOps - Guillermo or Diego
[ ] Add weather station data to the dashboard - Jacinda

## Github accounts

dngomez.e@gmail.com
jacindalb0309@gmail.com
gdamke@gmail.com
