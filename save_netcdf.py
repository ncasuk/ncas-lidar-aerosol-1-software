import numpy as np
import netCDF4 as nc
import read_data
import datetime as dt
import glob

def save_one_day(this_dt):

    #ascii_direc = '/media/sf_Data/cimel-lidar/ExportData/'
    ascii_direc = '/gws/pw/j07/woest/data/ncas-lidar-aerosol-1/ExportData/'
    #netcdf_direc = '/media/sf_Data/cimel-lidar/NetcdfData/'
    netcdf_direc = '/gws/pw/j07/woest/hugo/cimel-netcdf-test/'
    one_day = dt.timedelta(days=1)

    # start_dt = dt.datetime(2025,2,17,0,0)
    # end_dt = dt.datetime(2025,2,17,3,0)
    #
    # date_list = []
    #
    # current_dt = start_dt
    #
    # while current_dt.date() < end_dt.date() + one_day:
    #     date_list.append(current_dt.date())
    #     current_dt = current_dt + one_day

    #single_day = dt.date(2023,7,1)
    single_day = this_dt

    lowest_gate = 300. # metres
    highest_gate = 100000. # metres

    date_list = [single_day]

    allFiles = []
    use_sub_dir = True

    for check_this_day in date_list:
        sub_dir = f'{check_this_day:%Y}/{check_this_day:%m}/{check_this_day:%d}/' if use_sub_dir else ''
        ascii_file_format = sub_dir+f'2102-029_{check_this_day:%Y}{check_this_day:%m}{check_this_day:%d}_????.txt'
        check_path = ascii_direc + ascii_file_format
        print('Check path:',check_path)
        files_this_day = sorted(glob.glob(check_path))
        allFiles.extend(files_this_day)

    # print(allFiles)

    currentFile = allFiles[0]
    d, m = read_data.read_file(currentFile)

    lidar_time_dt = np.array(d['1']['DP']['time'])
    lidar_range_green_raw = d['1']['lidar_range']
    lidar_range_ir_raw = d['11']['lidar_range']
    latitude = float(m['latitude'])
    longitude = float(m['longitude'])

    # Find lowest gate
    #lowest_gate_green = (np.abs(d['1']['lidar_range']-lowest_gate)).argmin()
    #lowest_gate_ir = (np.abs(d['11']['lidar_range']-lowest_gate)).argmin()
    valid_gates_green = np.where((lidar_range_green_raw >= lowest_gate) & (lidar_range_green_raw <= highest_gate))
    valid_gates_ir = np.where((lidar_range_ir_raw >= lowest_gate) & (lidar_range_ir_raw <= highest_gate))

    lidar_range_green = lidar_range_green_raw[valid_gates_green]
    lidar_range_ir = lidar_range_ir_raw[valid_gates_ir]

    back_green_para = d['1']['DP']['data'][:,valid_gates_green]
    back_green_perp = d['2']['DP']['data'][:,valid_gates_green]
    back_ir = d['11']['DP']['data'][:,valid_gates_ir]

    counter = 1

    if len(allFiles) > 1:
        for currentFile in range(1, len(allFiles)):
            counter = counter + 1
            print(allFiles[currentFile],' ',currentFile,'/',len(allFiles))
            d, m = read_data.read_file(allFiles[currentFile])

            lidar_time_dt = np.concatenate((lidar_time_dt,d['1']['DP']['time']))
            back_green_para = np.concatenate((back_green_para,d['1']['DP']['data'][:,valid_gates_green]))
            back_green_perp = np.concatenate((back_green_perp,d['2']['DP']['data'][:,valid_gates_green]))
            back_ir = np.concatenate((back_ir,d['11']['DP']['data'][:,valid_gates_ir]))

    print('Number of profiles:',len(lidar_time_dt))
    print('Number of files:', len(allFiles))

    instrument_name = 'ncas-lidar-aerosol-1'
    platform_name = 'lyneham'

    data_product = 'aerosol-backscatter'
    version_number = 'v1.0'

    lat_lon_string = f'{abs(latitude):0.6f}'+('N' if latitude >= 0 else 'S')+' '+f'{abs(longitude):0.6f}'+('E' if longitude >= 0 else 'W')
    if lat_lon_string == '51.507198N 2.005400W':
        platform_name = 'lyneham'
    else:
        platform_name = 'CHECK-PLATFORM'

    nc_file_name = instrument_name+'_'+platform_name+'_'+f'{single_day:%Y}{single_day:%m}{single_day:%d}'+'_'+data_product+'_'+version_number+'.nc'

    print('Target NetCDF:',nc_file_name)

    dataset_out = nc.Dataset(netcdf_direc+nc_file_name, 'w', format='NETCDF4_CLASSIC')

    #Need to extract date starttime endtime lat lon

    current_time = dt.datetime.now(dt.timezone.utc)
    current_time_string = current_time.strftime('%Y-%m-%dT%H:%M:%S')

    start_time_string = lidar_time_dt[0].strftime('%Y-%m-%dT%H:%M:%S')
    end_time_string = lidar_time_dt[-1].strftime('%Y-%m-%dT%H:%M:%S')

    print('Time range:',start_time_string,end_time_string)

    print('Location:',str(lat_lon_string))

    dataset_out.Conventions = 'CF-1.6, NCAS-AMF-2.0.0'
    dataset_out.source = 'NCAS Aerosol Lidar unit 1'
    dataset_out.instrument_manufacturer = 'Cimel'
    dataset_out.instrument_model = 'CE376-GPN'
    dataset_out.instrument_serial_number = '2102-029'
    dataset_out.instrument_software = 'Cimel '+m['software_name']
    dataset_out.instrument_software_version = m['software_version']
    dataset_out.creator_name = 'Dr Hugo Ricketts'
    dataset_out.creator_email = 'hugo.ricketts@ncas.ac.uk'
    dataset_out.creator_url = 'https://orcid.org/0000-0002-1708-2431'
    dataset_out.institution = 'National Centre for Atmospheric Science (NCAS)'
    dataset_out.processing_software_url = 'https://github.com/ncasuk/ncas-lidar-aerosol-1-software'
    dataset_out.processing_software_version = 'v1.0'
    dataset_out.calibration_sensitivity = 'Initial calibration by manufacturer'
    dataset_out.calibration_certification_date = '2022-11-07T00:00:00'
    dataset_out.calibration_certification_url = 'N/A'
    dataset_out.sampling_interval = '60 second'
    dataset_out.averaging_interval = '60 second'
    dataset_out.laser_wavelength = '355 nm'
    dataset_out.nominal_laser_pulse_energy = '6 uJ'
    dataset_out.pulse_repetition_frequency = '4.7 kHz'
    dataset_out.lens_diameter = '100 mm'
    dataset_out.beam_divergence = '70 urad'
    dataset_out.pulse_length = '15 ns'
    dataset_out.sampling_frequency = '60 s'
    dataset_out.product_version = version_number
    dataset_out.processing_level = 1
    dataset_out.last_revised_date = current_time_string
    dataset_out.project = 'WesCon – Observing the Evolving Structures of Turbulence (WOEST)'
    dataset_out.project_principal_investigator = 'Dr Ryan Neely III'
    dataset_out.project_principal_investigator_email = 'ryan.neely@ncas.ac.uk'
    dataset_out.project_principal_investigator_url = 'https://orcid.org/0000-0003-4560-4812'
    dataset_out.licence = 'Data usage licence - UK Government Open Licence agreement: http://www.nationalarchives.gov.uk/doc/open-government-licence'
    dataset_out.acknowledgement = 'Acknowledgement of NCAS as the data provider is required whenever and wherever these data are used'
    dataset_out.platform = platform_name
    dataset_out.platform_type = 'stationary_platform'
    dataset_out.deployment_mode = 'land'
    dataset_out.title = 'Time series profiles of normalized range corrected signal'
    dataset_out.featureType = 'timeSeriesProfile'
    dataset_out.time_coverage_start = start_time_string
    dataset_out.time_coverage_end = end_time_string
    dataset_out.geospatial_bounds = lat_lon_string
    dataset_out.platform_altitude = m['altitude']+' m'
    dataset_out.location_keywords = platform_name
    dataset_out.amf_vocabularies_release = 'https://github.com/ncasuk/AMF_CVs/releases/tag/v2.0.0'
    dataset_out.history = end_time_string+' - v1.0: Initial release. Overlap corrected raw backscatter data only.'
    dataset_out.comment = 'Aerosol backscatter and cloud base to follow. Contact provider if required for specific days.'

    # Dimensions
    time_dim = dataset_out.createDimension('time',len(lidar_time_dt))
    #time.units = 'seconds since 1970-01-01 00:00:00 UTC'
    altitude_green_dim = dataset_out.createDimension('altitude_green',len(lidar_range_green))
    #altitude.units = 'm'
    altitude_ir_dim = dataset_out.createDimension('altitude_ir',len(lidar_range_ir))
    #altitude.units = 'm'
    latitude_dim = dataset_out.createDimension('latitude',1)
    #latitude.units = 'degree_north'
    longitude_dim = dataset_out.createDimension('longitude',1)
    #longitude.units = 'degree_east'

    # Variables - general

    times = dataset_out.createVariable('time', np.double, ('time',))
    times.type = 'double'
    times.dimension = 'time'
    times.units = 'seconds since 1970-01-01 00:00:00'
    times.standard_name = 'time'
    times.long_name = 'Time (seconds since 1970-01-01 00:00:00)'
    times.axis = 'T'
    times.valid_min = (lidar_time_dt[0]-dt.datetime(1970,1,1,0,0,0)).total_seconds()
    times.valid_max = (lidar_time_dt[-1]-dt.datetime(1970,1,1,0,0,0)).total_seconds()
    times.calendar = 'standard'

    latitudes = dataset_out.createVariable('latitude', np.float32, ('latitude',))
    latitudes.type = 'float'
    latitudes.dimension = 'latitude'
    latitudes.units = 'degrees_north'
    latitudes.standard_name = 'latitude'
    latitudes.long_name = 'Latitude'
    latitudes.axis = 'Y'
    latitudes.valid_min = np.float32(latitude)
    latitudes.valid_max = np.float32(latitude)
    latitudes.cell_methods = 'time: point'

    longitudes = dataset_out.createVariable('longitude', np.float32, ('longitude',))
    longitudes.type = 'float'
    longitudes.dimension = 'longitude'
    longitudes.units = 'degrees_east'
    longitudes.standard_name = 'longitude'
    longitudes.long_name = 'Longitude'
    longitudes.axis = 'X'
    longitudes.valid_min = np.float32(longitude) # f'{abs(longitude):0.6f}'
    longitudes.valid_max = np.float32(longitude) # f'{abs(longitude):0.6f}'
    longitudes.cell_methods = 'time: point'


    day_of_year = dataset_out.createVariable('day_of_year', np.float32, ('time',))
    day_of_year.type = 'float'
    day_of_year.dimension = 'time'
    day_of_year.units = '1'
    day_of_year.standard_name = ''
    day_of_year.long_name = 'Day of Year'
    day_of_year.valid_min = lidar_time_dt[0].timetuple().tm_yday
    day_of_year.valid_max = lidar_time_dt[-1].timetuple().tm_yday

    year = dataset_out.createVariable('year', np.int32, ('time',))
    #year.name = 'year'
    year.type = 'int'
    year.dimension = 'time'
    year.units = '1'
    year.standard_name = ''
    year.long_name = 'Year'
    year.valid_min = lidar_time_dt[0].year
    year.valid_max = lidar_time_dt[-1].year

    month = dataset_out.createVariable('month', np.int32, ('time',))
    #month.name = 'month'
    month.type = 'int'
    month.dimension = 'time'
    month.units = '1'
    month.standard_name = ''
    month.long_name = 'Month'
    month.valid_min = 1
    month.valid_max = 12

    day = dataset_out.createVariable('day', np.int32, ('time',))
    #day.name = 'day'
    day.type = 'int'
    day.dimension = 'time'
    day.units = '1'
    day.standard_name = ''
    day.long_name = 'Day'
    day.valid_min = 1
    day.valid_max = 31

    hour = dataset_out.createVariable('hour', np.int32, ('time',))
    #hour.name = 'hour'
    hour.type = 'int'
    hour.dimension = 'time'
    hour.units = '1'
    hour.standard_name = ''
    hour.long_name = 'Hour'
    hour.valid_min = 0
    hour.valid_max = 23

    minute = dataset_out.createVariable('minute', np.int32, ('time',))
    #minute.name = 'minute'
    minute.type = 'int'
    minute.dimension = 'time'
    minute.units = '1'
    minute.standard_name = ''
    minute.long_name = 'Minute'
    minute.valid_min = 0
    minute.valid_max = 59

    second = dataset_out.createVariable('second', np.float32, ('time',))
    #second.name = 'second'
    second.type = 'float'
    second.dimension = 'time'
    second.units = '1'
    second.standard_name = ''
    second.long_name = 'Second'
    second.valid_min = 0
    second.valid_max = np.float32(59.99999)

    altitudes_green = dataset_out.createVariable('altitude_green', np.float32, ('altitude_green',), fill_value=-1.00E+20)
    altitudes_green.type = 'float32'
    altitudes_green.dimension = 'altitude_green'
    altitudes_green.units = 'm'
    altitudes_green.standard_name = 'altitude'
    altitudes_green.long_name = 'Geometric height above geoid (WGS84).'
    altitudes_green.axis = 'Z'
    altitudes_green.valid_min = np.float32(min(lidar_range_green))
    altitudes_green.valid_max = np.float32(max(lidar_range_green))
    altitudes_green.coordinates = 'latitude longitude'

    altitudes_ir = dataset_out.createVariable('altitude_ir', np.float32, ('altitude_ir',), fill_value=-1.00E+20)
    altitudes_ir.type = 'float32'
    altitudes_ir.dimension = 'altitude_ir'
    altitudes_ir.units = 'm'
    altitudes_ir.standard_name = 'altitude'
    altitudes_ir.long_name = 'Geometric height above geoid (WGS84).'
    altitudes_ir.axis = 'Z'
    altitudes_ir.valid_min = np.float32(min(lidar_range_ir))
    altitudes_ir.valid_max = np.float32(max(lidar_range_ir))
    altitudes_ir.coordinates = 'latitude longitude'

    green_para_powers = dataset_out.createVariable('range_squared_corrected_backscatter_power_green_para', np.float64, ('time','altitude_green'), fill_value=-1.00E+20)
    green_para_powers.type = 'float64'
    green_para_powers.dimension = 'time, altitude_green'
    green_para_powers.units = '1'
    green_para_powers.standard_name = 'range_squared_corrected_backscatter_power'
    green_para_powers.long_name = 'Range Squared Corrected Backscatter Power, Green, Parallel (arbitrary raw data unit)'
    green_para_powers.valid_min = np.min(back_green_para)
    green_para_powers.valid_max = np.max(back_green_para)
    green_para_powers.cell_methods = 'time: mean'
    green_para_powers.coordinates = 'latitude longitude'

    green_perp_powers = dataset_out.createVariable('range_squared_corrected_backscatter_power_green_perp', np.float64, ('time','altitude_green'), fill_value=-1.00E+20)
    green_perp_powers.type = 'float64'
    green_perp_powers.dimension = 'time, altitude_green'
    green_perp_powers.units = '1'
    green_perp_powers.standard_name = 'range_squared_corrected_backscatter_power'
    green_perp_powers.long_name = 'Range Squared Corrected Backscatter Power, Green, Perpendicular (arbitrary raw data unit)'
    green_perp_powers.valid_min = np.min(back_green_perp)
    green_perp_powers.valid_max = np.max(back_green_perp)
    green_perp_powers.cell_methods = 'time: mean'
    green_perp_powers.coordinates = 'latitude longitude'

    back_ir_powers = dataset_out.createVariable('range_squared_corrected_backscatter_power_ir', np.float64, ('time','altitude_ir'), fill_value=-1.00E+20)
    back_ir_powers.type = 'float64'
    back_ir_powers.dimension = 'time, altitude_ir'
    back_ir_powers.units = '1'
    back_ir_powers.standard_name = 'range_squared_corrected_backscatter_power'
    back_ir_powers.long_name = 'Range Squared Corrected Backscatter Power, Infra-red (arbitrary raw data unit)'
    back_ir_powers.valid_min = np.min(back_ir)
    back_ir_powers.valid_max = np.max(back_ir)
    back_ir_powers.cell_methods = 'time: mean'
    back_ir_powers.coordinates = 'latitude longitude'

    dataset_out['time'][:] = nc.date2num(lidar_time_dt, dataset_out['time'].units)
    dataset_out['altitude_green'][:] = lidar_range_green
    dataset_out['altitude_ir'][:] = lidar_range_ir
    dataset_out['range_squared_corrected_backscatter_power_green_para'][:] = back_green_para
    dataset_out['range_squared_corrected_backscatter_power_green_perp'][:] = back_green_perp
    dataset_out['range_squared_corrected_backscatter_power_ir'][:] = back_ir
    dataset_out.close()


if __name__ == "__main__":
    import sys

    # Example date time string: 202409130200 is 13/09/2024 02:00
    dt_string_format = "%Y%m%d"
    start_dt = dt.datetime.strptime(sys.argv[1], dt_string_format)
    save_one_day(start_dt)
