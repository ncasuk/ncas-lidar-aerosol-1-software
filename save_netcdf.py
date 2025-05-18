import numpy as np
import netCDF4 as nc
import read_data
import datetime as dt
import glob
import pandas as pd
import os
from plot_cimel import plot_cimel

def save_one_day(this_dt, plot_data=False):

    #ascii_direc = '/media/sf_Data/cimel-lidar/ExportData/'
    ascii_direc = '/gws/pw/j07/woest/data/ncas-lidar-aerosol-1/ExportData/'
    #netcdf_direc = '/media/sf_Data/cimel-lidar/NetcdfData/'
    netcdf_direc = '/gws/pw/j07/woest/hugo/cimel-for-upload/'
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

    if plot_data:
        plot_cimel(back_ir[:,0,:].T, lidar_time_dt, lidar_range_ir, start_dt=min(lidar_time_dt), end_dt=max(lidar_time_dt), this_day=single_day)    

    channels = ['1', '2', '11']
    laser_wavelengths = {'1':'532', '2':'532', '11':'808'}
    pulse_energies = {'1':'6 uJ', '2':'6 uJ', '11':'3 uJ'}
    beam_divergences = {'1':'0.07 mrad', '2':'0.07 mrad', '11':'0.2 mrad'}
    pulse_lengths = {'1':'15 ns', '2':'15 ns', '11':'200 ns'}
    polarisations = {'1':'co-polar', '2':'cross-polar', '11':'co-polar'}

    back_green_para = np.log(back_green_para)
    back_green_perp = np.log(back_green_perp)
    back_ir = np.log(back_ir)
    altitude_green = lidar_range_green + float(m['altitude'])
    altitude_ir = lidar_range_ir + float(m['altitude'])
    lidar_time_pd = pd.Series(lidar_time_dt)
    day_of_year_decimal = np.float32(lidar_time_pd.dt.dayofyear) + np.float32(lidar_time_pd.astype(int) / 10**9 / 86400. % 1)
    
    for this_channel in channels:
        options_field = laser_wavelengths[this_channel] + 'nm_' + polarisations[this_channel]
        comments_field = 'Data in this file is for the '+laser_wavelengths[this_channel] + ' nm ' + polarisations[this_channel] + ' channel.'
        
        nc_file_name = instrument_name+'_'+platform_name+'_'+f'{single_day:%Y}{single_day:%m}{single_day:%d}'+'_'+data_product+'_'+options_field+'_'+version_number+'.nc'
        print('Target NetCDF:',nc_file_name)

        this_netcdf_direc = os.path.join(netcdf_direc, f'{single_day:%Y}', f'{single_day:%m}', f'{single_day:%d}')
        os.makedirs(this_netcdf_direc, exist_ok=True)
        print(os.path.join(this_netcdf_direc,nc_file_name))
        dataset_out = nc.Dataset(os.path.join(this_netcdf_direc,nc_file_name), 'w', format='NETCDF4_CLASSIC')
    
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
        dataset_out.laser_wavelength = laser_wavelengths[this_channel] + ' nm'
        dataset_out.nominal_laser_pulse_energy = pulse_energies[this_channel]
        dataset_out.pulse_repetition_frequency = '4.7 kHz'
        dataset_out.lens_diameter = '100 mm'
        dataset_out.beam_divergence = beam_divergences[this_channel]
        dataset_out.pulse_length = pulse_lengths[this_channel]
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
        dataset_out.comment = comments_field
    
        # Dimensions
        time_dim = dataset_out.createDimension('time',len(lidar_time_dt))
        #time.units = 'seconds since 1970-01-01 00:00:00 UTC'
        if this_channel == '11':
            altitude_dim = dataset_out.createDimension('altitude',len(altitude_ir))
            #altitude.units = 'm'
        else:
            altitude_dim = dataset_out.createDimension('altitude',len(altitude_green))
            #altitude.units = 'm'
        
        latitude_dim = dataset_out.createDimension('latitude',1)
        #latitude.units = 'degree_north'
        longitude_dim = dataset_out.createDimension('longitude',1)
        #longitude.units = 'degree_east'
    
        # Variables - general
    
        times = dataset_out.createVariable('time', np.float64, ('time',))
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
        day_of_year.valid_min = np.min(day_of_year_decimal)
        day_of_year.valid_max = np.max(day_of_year_decimal)
    
        year = dataset_out.createVariable('year', np.int32, ('time',))
        #year.name = 'year'
        year.type = 'int'
        year.dimension = 'time'
        year.units = '1'
        year.standard_name = ''
        year.long_name = 'Year'
        year.valid_min = np.min(np.int32(lidar_time_pd.dt.year))
        year.valid_max = np.max(np.int32(lidar_time_pd.dt.year))
    
        month = dataset_out.createVariable('month', np.int32, ('time',))
        #month.name = 'month'
        month.type = 'int'
        month.dimension = 'time'
        month.units = '1'
        month.standard_name = ''
        month.long_name = 'Month'
        month.valid_min = np.min(np.int32(lidar_time_pd.dt.month))
        month.valid_max = np.max(np.int32(lidar_time_pd.dt.month))
    
        day = dataset_out.createVariable('day', np.int32, ('time',))
        #day.name = 'day'
        day.type = 'int'
        day.dimension = 'time'
        day.units = '1'
        day.standard_name = ''
        day.long_name = 'Day'
        day.valid_min = np.min(np.int32(lidar_time_pd.dt.day))
        day.valid_max = np.max(np.int32(lidar_time_pd.dt.day))
    
        hour = dataset_out.createVariable('hour', np.int32, ('time',))
        #hour.name = 'hour'
        hour.type = 'int'
        hour.dimension = 'time'
        hour.units = '1'
        hour.standard_name = ''
        hour.long_name = 'Hour'
        hour.valid_min = np.min(np.int32(lidar_time_pd.dt.hour))
        hour.valid_max = np.max(np.int32(lidar_time_pd.dt.hour))
    
        minute = dataset_out.createVariable('minute', np.int32, ('time',))
        #minute.name = 'minute'
        minute.type = 'int'
        minute.dimension = 'time'
        minute.units = '1'
        minute.standard_name = ''
        minute.long_name = 'Minute'
        minute.valid_min = np.min(np.int32(lidar_time_pd.dt.minute))
        minute.valid_max = np.max(np.int32(lidar_time_pd.dt.minute))
    
        second = dataset_out.createVariable('second', np.float32, ('time',))
        #second.name = 'second'
        second.type = 'float'
        second.dimension = 'time'
        second.units = '1'
        second.standard_name = ''
        second.long_name = 'Second'
        second.valid_min = np.min(np.float32(lidar_time_pd.dt.second) + np.float32(lidar_time_pd.dt.microsecond) / 1e6)
        second.valid_max = np.max(np.float32(lidar_time_pd.dt.second) + np.float32(lidar_time_pd.dt.microsecond) / 1e6)
    
        altitudes = dataset_out.createVariable('altitude', np.float32, ('altitude',), fill_value=-1.00E+20)
        altitudes.type = 'float'
        altitudes.dimension = 'altitude'
        altitudes.units = 'm'
        altitudes.standard_name = 'altitude'
        altitudes.long_name = 'Geometric height above geoid (WGS84).'
        altitudes.axis = 'Z'
        if this_channel == '11':
            altitudes.valid_min = np.float32(min(altitude_ir))
            altitudes.valid_max = np.float32(max(altitude_ir))
        else:
            altitudes.valid_min = np.float32(min(altitude_green))
            altitudes.valid_max = np.float32(max(altitude_green))
        altitudes.coordinates = 'latitude longitude'

        powers = dataset_out.createVariable('range_squared_corrected_backscatter_power', np.float32, ('time','altitude'), fill_value=-1.00E+20)
        powers.type = 'float'
        powers.dimension = 'time, altitude'
        powers.units = '1'
        powers.standard_name = 'range_squared_corrected_backscatter_power'
        powers.long_name = 'Range Squared Corrected Backscatter Power (ln(arbitrary raw data unit))'
        if this_channel == '11':
            powers.valid_min = np.nanmin(np.float32(back_ir))
            powers.valid_max = np.nanmax(np.float32(back_ir))
        elif this_channel == '1':
            powers.valid_min = np.nanmin(np.float32(back_green_para))
            powers.valid_max = np.nanmax(np.float32(back_green_para))
        elif this_channel == '2':
            powers.valid_min = np.nanmin(np.float32(back_green_perp))
            powers.valid_max = np.nanmax(np.float32(back_green_perp))
        powers.cell_methods = 'time: mean'
        powers.coordinates = 'latitude longitude'

        dataset_out['latitude'][:] = np.float32(latitude)
        dataset_out['longitude'][:] = np.float32(longitude)
        dataset_out['day_of_year'][:] = day_of_year_decimal #np.float32(lidar_time_pd.dt.dayofyear) + np.float32(lidar_time_pd.dt.hour) / 24.
        dataset_out['year'][:] = np.int32(lidar_time_pd.dt.year)
        dataset_out['month'][:] = np.int32(lidar_time_pd.dt.month)
        dataset_out['day'][:] = np.int32(lidar_time_pd.dt.day)
        dataset_out['hour'][:] = np.int32(lidar_time_pd.dt.hour)
        dataset_out['minute'][:] = np.int32(lidar_time_pd.dt.minute)
        dataset_out['second'][:] = np.float32(lidar_time_pd.dt.second) + np.float32(lidar_time_pd.dt.microsecond) / 1e6

        dataset_out['time'][:] = nc.date2num(lidar_time_dt, dataset_out['time'].units)
        if this_channel == '11':
            dataset_out['altitude'][:] = np.float32(altitude_ir)
            dataset_out['range_squared_corrected_backscatter_power'][:] = np.float32(back_ir)
        elif this_channel == '1':
            dataset_out['altitude'][:] = np.float32(altitude_green)
            dataset_out['range_squared_corrected_backscatter_power'][:] = np.float32(back_green_para)
            print('1')
        elif this_channel == '2':
            dataset_out['altitude'][:] = np.float32(altitude_green)
            dataset_out['range_squared_corrected_backscatter_power'][:] = np.float32(back_green_perp)
            print('2')
        dataset_out.close()


if __name__ == "__main__":
    import sys

    # Example date time string: 202409130200 is 13/09/2024 02:00
    dt_string_format = "%Y%m%d"
    start_dt = dt.datetime.strptime(sys.argv[1], dt_string_format)
    save_one_day(start_dt, plot_data=True)
