import pandas as pd
import numpy as np

def read_sonde(lidar_altitude):

    sonde_file = '/media/sf_Data/cimel-lidar/sonde/wy-camborne-20250217_12.txt'

    sonde_vars = ['PRES','HGHT','TEMP','DWPT','RELH','MIXR','DRCT','SKNT','THTA','THTE','THTV']
    sonde_data = pd.read_csv(sonde_file, skiprows=7, sep='\\s+', names=sonde_vars)

    t0 = 273.15 # K

    sonde_data['TEMP_K'] = sonde_data['TEMP'] + 273.15
    sonde_data['DWPT_K'] = sonde_data['DWPT'] + 273.15

    # vapour pressure (T) = sat. vap. pressure (Td)
    sonde_data['E'] = 6.1078 * np.exp(6884 * ((1/t0) - (1/sonde_data['DWPT_K'])) - 5.35 * np.log(sonde_data['DWPT_K']/t0))

    # water vapour mixing ratio
    sonde_data['WV_CALC'] = 0.622 * (sonde_data['E']/sonde_data['PRES'])
    sonde_data['VTEMP_K'] = sonde_data['TEMP_K'] * (1 + 0.61*sonde_data['WV_CALC'])

    gridded_vtemp_k = np.interp(lidar_altitude, sonde_data['HGHT'], sonde_data['VTEMP_K'])
    gridded_pres = np.interp(lidar_altitude,sonde_data['HGHT'], sonde_data['PRES'])

    # calculate gravitational acceleration
    gravity = 9.80665 * (1 - 2 * lidar_altitude / (1000. * 6370.))

    # calculate scale height
    r_dry = 287  # Geraint has 286 J.K-1.kg-1, why is this?
    scl_ht = r_dry * gridded_vtemp_k / gravity
    nair = gridded_pres * 100. / (1.38e-23 * gridded_vtemp_k)

    return nair