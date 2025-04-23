import numpy as np

def ray_calc(lidar_wavelength, nair, lidar_range):
    start_power = 1.
    delta_h = lidar_range[1] - lidar_range[0]

    # lidar wavelength in nm
    sigma_air_coeff = 4.56e-31 * np.power((550. / float(lidar_wavelength)), 4.)
    beta_air_coeff = sigma_air_coeff * 3. / (8. * np.pi)

    sigma_air = sigma_air_coeff * nair
    beta_air = beta_air_coeff * nair

    mol_signal = np.zeros(len(lidar_range))

    mol_signal[0] = start_power * beta_air[0]

    for gate in range(1, len(lidar_range)):
        mol_signal[gate] = start_power * beta_air[gate] * np.exp(-2 * np.sum(sigma_air[0:gate - 1]) * delta_h)

    return mol_signal
