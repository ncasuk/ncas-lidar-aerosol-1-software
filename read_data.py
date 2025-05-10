import datetime as dt
import numpy as np
import json
from calibrate_data import calibrate_data


def read_file(filename):
    """
    Read raw data file

    Returns two dictionaries, one with data and one with metadata.
    """
    # set some variables
    start_of_time = dt.datetime.strptime("1899-12-31 00:00:00", "%Y-%m-%d %H:%M:%S")
    polarization_convert = {
        "X": "perpendicular",
        "/": "parallel",
        "O": "without",
        "U": "unknown"
    }
    out_value_type_convert = {
        "R": "raw signal",
        "S": "number of photons",
        "SB": "background corrected",
        "SBR2": "photons range corrected",
        "OSB": "overlap correction",
        "OSBR2": "lidar signal",
    }

    # read in data
    with open(filename, "r", encoding="charmap") as f:
        data = f.readlines()

    column_separator = data[5].strip().split(" ")[-1]

    data_dict = {}
    metadata_dict = {}

    # read in each line
    for line in data:
        line = line.strip()
        if line.split(column_separator)[0] == "FILEV":
            file_version, software_name, software_version = read_filev(line, column_separator)
            metadata_dict["file_version"] = file_version
            metadata_dict["software_name"] = software_name
            metadata_dict["software_version"] = software_version
        elif line.split(column_separator)[0] == "INSCFG":
            latitude, longitude, altitude, roll, pitch = read_inscfg(line, column_separator)
            metadata_dict["latitude"] = latitude
            metadata_dict["longitude"] = longitude
            metadata_dict["altitude"] = altitude
            metadata_dict["roll"] = roll
            metadata_dict["pitch"] = pitch
        elif line.split(column_separator)[0] == "DCLID":
            id_channel, id_group, name, doors_nbr, source_wavelength, receive_wavelength, fwhm, polarization, one_door_range, one_door_time, offset_range, offset_time, constant = read_dclid(line, column_separator)
            data_dict[id_channel] = {
                "id_channel": id_channel,
                "id_group": id_group,
                "name": name,
                "source_wavelength_nanometres": source_wavelength,
                "receive_wavelength_nanometres": receive_wavelength,
                "fwhm": fwhm,
                "polarization": polarization_convert[polarization],
                "one_door_range_metres": one_door_range,
                "one_door_time_nanoseconds": one_door_time,
                "offset_range": offset_range,
                "offset_time": offset_time,
                "DP" : {
                    "time": [],
                    "data": np.ones(int(doors_nbr)) * -9999,  # initialise with row to be deleted later
                    "number_pulses": [],
                    "out_value_type": [],
                    "profile_duration": [],
                    "after_pulse_corrected": [],
                },
            }
        elif line.split(column_separator)[0] == "DETPAR":
            id_channel, time, method, p_values = read_detpar(line, column_separator)
            dt_time = start_of_time + dt.timedelta(days = float(time)-1)
            # note for future, minus 1 exists because 1900 is treated as a leap year
            # this is based on Excel, which itself is based on Lotus-1-2-3
            data_dict[id_channel]["DETPAR"] = {
                "time": dt_time,
                "method": method,
                "parameter_values": p_values,
            }
        elif line.split(column_separator)[0] == "OVL":
            id_channel, time, values = read_ovl(line, column_separator)
            dt_time = start_of_time + dt.timedelta(days = float(time)-1)
            data_dict[id_channel]["OVL"] = {
                "time": dt_time,
                "overlap_values": values,
            }
        elif line.split(column_separator)[0] == "AFPL":
            id_channel, time, values = read_afpl(line, column_separator)
            dt_time = start_of_time + dt.timedelta(days = float(time)-1)
            data_dict[id_channel]["AFPL"] = {
                "time": dt_time,
                "afterpulse_values": values,
            }
        elif line.split(column_separator)[0] == "DP":
            id_channel, time, nbr_pulse, profile_duration, out_value_type, after_pulse_corrected, measurements, sky_background, error_warnings = read_dp(line, column_separator)
            #print("DP", id_channel, time)
            dt_time = start_of_time + dt.timedelta(days = float(time)-1)
            data_dict[id_channel]["DP"]["data"] = (
                np.vstack((data_dict[id_channel]["DP"]["data"], measurements))
            )
            data_dict[id_channel]["DP"]["time"].append(dt_time)
            data_dict[id_channel]["DP"]["number_pulses"].append(nbr_pulse)
            data_dict[id_channel]["DP"]["out_value_type"].append(out_value_type_convert[out_value_type])
            data_dict[id_channel]["DP"]["profile_duration"].append(profile_duration)
            data_dict[id_channel]["DP"]["after_pulse_corrected"].append(after_pulse_corrected)

    # remember the data arrays in data_dict[id_channel] have an extra row at the start which should be removed
    for id_channel in data_dict.keys():
        data_dict[id_channel]["DP"]["data"] = data_dict[id_channel]["DP"]["data"][1:,:]

    data_dict, metadata_dict = calibrate_data(data_dict, metadata_dict)

    return data_dict, metadata_dict



def read_filev(line, column_separator):
    """
    FILEV - file version
    """
    file_version = line.split(column_separator)[1]
    software_name = line.split(column_separator)[2]
    software_version = line.split(column_separator)[3]
    return file_version, software_name, software_version


def read_inscfg(line, column_separator):
    """
    INSCFG - instrument configuration
    """
    latitude = line.split(column_separator)[2]
    longitude = line.split(column_separator)[3]
    altitude = line.split(column_separator)[4]
    roll = line.split(column_separator)[5]
    pitch = line.split(column_separator)[6]
    return latitude, longitude, altitude, roll, pitch


def read_dclid(line, column_separator):
    """
    DCLID - description channel LiDAR
    """
    id_channel = line.split(column_separator)[1]
    id_group = line.split(column_separator)[2]
    name = line.split(column_separator)[3]
    doors_nbr = line.split(column_separator)[4]
    source_wavelength = line.split(column_separator)[5]
    receive_wavelength = line.split(column_separator)[6]
    fwhm = line.split(column_separator)[7]
    polarization = line.split(column_separator)[8]
    one_door_range = line.split(column_separator)[9]
    one_door_time = line.split(column_separator)[10]
    offset_range = line.split(column_separator)[11]
    offset_time = line.split(column_separator)[12]
    constant = line.split(column_separator)[13]
    return id_channel, id_group, name, doors_nbr, source_wavelength, receive_wavelength, fwhm, polarization, one_door_range, one_door_time, offset_range, offset_time, constant


def read_detpar(line, column_separator):
    """
    DETPAR - detector calibration parameters
    """
    id_channel = line.split(column_separator)[1]
    time = line.split(column_separator)[2]
    method = line.split(column_separator)[3]
    p_values = line.split(column_separator)[4:]
    return id_channel, time, method, p_values



def read_ovl(line, column_separator):
    """
    OVL - overlap calibration
    """
    id_channel = line.split(column_separator)[1]
    time = line.split(column_separator)[2]
    values = line.split(column_separator)[3:]
    return id_channel, time, values



def read_afpl(line, column_separator):
    """
    AFPL - after pulse calibration
    """
    id_channel = line.split(column_separator)[1]
    time = line.split(column_separator)[2]
    values = line.split(column_separator)[3:]
    return id_channel, time, values



def read_dp(line, column_separator):
    """
    DP - data profile
    """
    id_channel = line.split(column_separator)[1]
    time = line.split(column_separator)[2]
    nbr_pulse = line.split(column_separator)[3]
    profile_duration = line.split(column_separator)[4]
    out_value_type = line.split(column_separator)[5]
    after_pulse_corrected = line.split(column_separator)[6]
    measurements = [ float(i) for i in line.split(column_separator)[7:-2] ]
    sky_background = line.split(column_separator)[-2]
    error_warnings = line.split(column_separator)[-1]
    return id_channel, time, nbr_pulse, profile_duration, out_value_type, after_pulse_corrected, measurements, sky_background, error_warnings


def save_to_json(data_dict, metadata_dict, json_file):
    """
    Write data_dict and metadata_dict to json file.
    datetime objects are converted to UNIX timestamp
    """
    j = json.dumps({"data_dict": data_dict, "metadata_dict": metadata_dict}, indent=4, default=convert_object_types_for_json)
    with open(json_file, "w") as f:
        f.write(j) 


def convert_object_types_for_json(obj):
    """
    Convert datetime objects to UNIX timestamp and numpy arrays to lists
    """
    if isinstance(obj, (dt.date, dt.datetime)):
        return obj.timestamp()
    elif isinstance(obj, np.ndarray):
        new_obj = []
        if obj.ndim == 2:
            for i in range(np.shape(obj)[0]):
                new_obj.append(list(obj[i]))
        elif obj.ndim == 1:
            for i in range(np.shape(obj)[0]):
                new_obj.append(obj[i])
        return new_obj


if __name__ == "__main__":
    import sys
    filename = sys.argv[1]
    save_loc = sys.argv[2]
    d, m = read_file(filename)
    save_to_json(d, m, f"{save_loc}/{filename.split('/')[-1].replace('.txt','.json')}")
