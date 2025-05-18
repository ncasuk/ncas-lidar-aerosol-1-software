import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates

def plot_cimel(to_plot, start_time_dt, lidar_alt, start_dt=dt.datetime(2023,6,12,0), end_dt=dt.datetime(2023,6,13,0), live_plot=False,this_day=dt.date(2023,6,12)):

    #start_dt = dt.datetime(2023,6,12,12)
    #end_dt = dt.datetime(2023,6,12,13)
    #result = read_claris(start_dt,end_dt)

    fig = plt.figure(figsize=(10, 3), constrained_layout=True)  # , constrained_layout=True)
    ax = fig.add_subplot(111)
    
    img = ax.pcolormesh(
        start_time_dt,
        lidar_alt / 1000,
        np.log10(to_plot[:-1, :-1]),
        vmin=5,
        vmax=8,
        cmap="YlGnBu_r",
    )
#    ax.axvspan(
#        start_dt,
#        end_dt,
#        alpha=0.8,
#        label="profile time average",
#        ec='r',
#        fill=False,
#        lw=5
#    )
#    start_plt_time = mdates.date2num(start_time_dt[0])
#    end_plt_time = mdates.date2num(start_time_dt[-1])

#    ax.set_xbound(start_plt_time, end_plt_time)

    ax.set_ylabel("Altitude AGL [km]")
    ax.set_ylim(0, 4)
    ax.set_xlabel("Time [UTC]")
#    ax.xaxis_date()
    #ax.legend(loc="upper right")
    
    fig.colorbar(
        img,
        ax=ax,
        aspect=20,
        pad=0.01,
        label="{} \n [{}]".format(
            "log10(rsc lidar backscatter)",
            "arb units",
        ),
    )
    
    #for axis in ax:
    #    axis.grid()
    
    fig.suptitle(
        "Lyneham aerosol lidar at 808 nm from {} until {}".format(
            start_time_dt[0].strftime("%Y-%m-%d %H:%M"),
            start_time_dt[-1].strftime("%Y-%m-%d %H:%M"),
        )
    )
    plt.savefig("/gws/pw/j07/woest/hugo/cimel-plots/cimel_4km_{}.png".format(this_day.strftime("%Y%m%d")))
    #plt.savefig("/gws/pw/j07/woest/hugo/claris/claris_test_{}.png".format(start_dt.strftime("%Y%m%d")))
    print("Plotting complete.")

#if __name__ == "__main__":
#    import sys

    # Example date time string: 202409130200 is 13/09/2024 02:00
#    dt_string_format = "%Y%m%d%H%M"
#    start_dt = dt.datetime.strptime(sys.argv[1], dt_string_format)
#    end_dt = dt.datetime.strptime(sys.argv[2], dt_string_format)
#    plot_claris(start_dt=start_dt,end_dt=end_dt,live_plot=False)