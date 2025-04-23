import matplotlib.pyplot as plt
import read_data
import numpy as np
import processors.read_sonde as read_sonde
import processors.ray_calc as ray_calc

d,m = read_data.read_file("/media/sf_Data/cimel-lidar/ExportData/2102-029_20250217_0250.txt")
channel = '11'
nair = read_sonde.read_sonde(d[channel]['lidar_range']+float(m['altitude']))

mol_signal = ray_calc.ray_calc(d[channel]['receive_wavelength_nanometres'], nair, d[channel]['lidar_range'])

normalise_mol = np.mean(d[channel]['DP']['data'][0,750:800]*d[channel]['lidar_range'][750:800]**2 / mol_signal[750:800])

fig = plt.figure()
ax=fig.add_subplot(111)

ax.plot(np.log10(d[channel]['DP']['data'][0,:]*d[channel]['lidar_range']**2), d[channel]['lidar_range'])
ax.plot(np.log10(mol_signal*normalise_mol), d[channel]['lidar_range'])
plt.show()

print('break')

# https://notebooks.aeolus.services/notebooks/05d1_aerosol_profile_comparison
fig = plt.figure(figsize=(10, 8), constrained_layout=True)  # , constrained_layout=True)
ax = []
gs = fig.add_gridspec(2, 4)
ax.append(fig.add_subplot(gs[1, 0]))
ax.append(fig.add_subplot(gs[1, 1], sharey=ax[0]))
ax.append(fig.add_subplot(gs[1, 2], sharey=ax[0]))
ax.append(fig.add_subplot(gs[1, 3], sharey=ax[0]))
ax.append(fig.add_subplot(gs[0, :]))

ax[0].plot(
    pollyXT_profiles["aerBsc_raman_355"].rolling(height=9).median(),
    pollyXT_profiles["height_asl_km"],
    label="total",
)
ax[0].plot(
    pollyXT_profiles["aerBsc_raman_355_copolar"].rolling(height=9).median(),
    pollyXT_profiles["height_asl_km"],
    label="co-polar",
)
ax[0].set_ylim(0, 15)
ax[0].set_xlim(-0.5e-6, 4e-6)
ax[0].set_ylabel("Altitude asl [km]")
ax[0].set_xlabel(
    "Particle backscatter \n coefficient \n [{}]".format(pollyXT_profiles["aerBsc_raman_355"].unit)
)
ax[0].legend(loc="upper right")

ax[1].plot(
    pollyXT_profiles["aerExt_raman_355"].rolling(height=9).median(),
    pollyXT_profiles["height_asl_km"],
)
ax[1].set_xlabel(
    "Particle extinction \n coefficient \n [{}]".format(pollyXT_profiles["aerExt_raman_355"].unit)
)
ax[1].set_xlim(-0.5e-4, 4e-4)
ax[1].tick_params(labelleft=False)

ax[2].plot(
    pollyXT_profiles["aerLR_raman_355"].rolling(height=9).median(),
    pollyXT_profiles["height_asl_km"],
    label="total",
)
ax[2].plot(
    pollyXT_profiles["aerLR_raman_355_copolar"].rolling(height=5).median(),
    pollyXT_profiles["height_asl_km"],
    label="co-polar",
)
ax[2].set_xlabel("Particle lidar ratio \n [{}]".format(pollyXT_profiles["aerLR_raman_355"].unit))
ax[2].set_xlim(0, 120)
ax[2].tick_params(labelleft=False)
ax[2].legend(loc="upper right")

ax[3].plot(
    pollyXT_profiles["parDepol_raman_355"].rolling(height=9).median(),
    pollyXT_profiles["height_asl_km"],
    label="linear",
)
ax[3].plot(
    pollyXT_profiles["parDepol_raman_355_circ"].rolling(height=9).median(),
    pollyXT_profiles["height_asl_km"],
    label="circular",
)
ax[3].set_xlabel("Particle depolarization \n ratio")
ax[3].set_xlim(0, 1.0)
ax[3].tick_params(labelleft=False)
ax[3].legend(loc="upper right")

img = ax[4].pcolormesh(
    pollyXT_attbsc["datetime"].values,
    (pollyXT_attbsc["height"].values + pollyXT_attbsc["altitude"].values) / 1000,
    pollyXT_attbsc["attenuated_backscatter_1064nm"].values[:-1, :-1].T,
    vmin=0,
    vmax=np.percentile(pollyXT_attbsc["attenuated_backscatter_1064nm"].values, 99),
    cmap="YlGnBu_r",
)
ax[4].axvspan(
    pollyXT_profiles["start_datetime"][0].values,
    pollyXT_profiles["end_datetime"][0].values,
    alpha=0.8,
    label="profile time average",
    ec='r',
    fill=False,
    lw=5
)
ax[4].set_ylabel("Altitude asl [km]")
ax[4].set_ylim(0, 15)
ax[4].set_xlabel("Time [UTC]")
ax[4].legend(loc="upper right")

fig.colorbar(
    img,
    ax=ax[4],
    aspect=20,
    pad=0.0001,
    label="{} \n [{}]".format(
        pollyXT_attbsc["attenuated_backscatter_1064nm"].long_name,
        pollyXT_attbsc["attenuated_backscatter_1064nm"].unit,
    ),
)

for axis in ax:
    axis.grid()

fig.suptitle(
    "PollyXT measurement at 355 nm averaged from {} until {}".format(
        pollyXT_profiles["start_datetime"][0].values.astype("datetime64[s]"),
        pollyXT_profiles["end_datetime"][0].values.astype("datetime64[s]"),
    )
)

img = ax[4].pcolormesh(
    d['1']['DP']['time'],
    d['1']['lidar_range'] / 1000,
    np.log10(d['1']['DP']['data'][:]*d['1']['lidar_range']**2).T,
    vmin=0,
    vmax=np.percentile(d['1']['DP']['data'], 99),
    cmap="viridis",
)

ax[4].set_ylabel("Altitude asl [km]")
ax[4].set_ylim(0, 15)
ax[4].set_xlabel("Time [UTC]")
ax[4].legend(loc="upper right")

fig.colorbar(
    img,
    ax=ax[4],
    aspect=20,
    pad=0.0001,
    #label="{} \n [{}]".format(
    #    pollyXT_attbsc["attenuated_backscatter_1064nm"].long_name,
    #    pollyXT_attbsc["attenuated_backscatter_1064nm"].unit,
    #),
)
#print(d['1']['AFPL']['afterpulse_values'])

plt.show()