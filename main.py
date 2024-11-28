import xarray as xr
import pandas as pd
from datetime import datetime
import numpy as np
import plotly.graph_objects as go
from config import *
from map import *
from matplotlib.ticker import MultipleLocator

# subline = f'?var={DRY_DUST}&' \
#           f'var={WET_DUST}' \
          # f'north={NORTH_END_POINT}&' \
          # f'west={WEST_END_POINT}&' \
          # f'east={EAST_END_PIONT}&' \
          # f'south={SOUTH_END_PIONT}&' \
          # f'addLatLon=true'



def get_data():
    mounth_ds = []
    for day in range(1, 3):
        two_digit_day = str(day).zfill(2)
        opendap_url = f"dust.aemet.es/thredds/dodsC/dataRoot/{MODEL}/{YEAR}/{MONTH}/" \
                      f"{YEAR}{MONTH}{two_digit_day}{model_code}.nc?" \
                      f"{DRY_DUST},{WET_DUST},"\
                      f"time[0:9]," \
                      f"lat[{SOUTH_END_POINT}:{NORTH_END_POINT}]," \
                      f"lon[{WEST_END_POINT}:{EAST_END_POINT}]"
        url = f"https://{username}:{password}@{opendap_url}"
        ds = xr.open_dataset(url)
        mounth_ds.append(ds)
        # print("S ", day)

        # ds = ds[[DRY_DUST, WET_DUST]]
        # start_datetime = datetime(YEAR, MONTH, day, HOUR_START, 0, 0)
        # end_datetime = pd.to_timedelta(23, unit="h") + start_datetime
        # # Convert seconds to datetime

        # if not np.issubdtype(ds.coords["time"].dtype, np.datetime64):
        #     new_time = pd.to_timedelta(ds["time"], unit="h") + start_datetime
        #     ds = ds.assign_coords(time=new_time)
        # # cut data only for 1 day
        # ds = ds.sel(time=slice(start_datetime, end_datetime))
        # # cut data inside dimensions
        # ds = ds.where((ds.lat >= SOUTH_END_POINT) & (ds.lat <= NORTH_END_POINT) &
        #               (ds.lon >= WEST_END_POINT) & (ds.lon <= EAST_END_POINT), drop=True)
        # change to interplation!!!!!!
        # ds_resampled = ds.interp(lat=new_lat, lon=new_lon)
    aligned_datasets = xr.align(*mounth_ds, join="outer")  # or "inner"
    combined_ds = xr.concat(aligned_datasets, dim="time")
    return combined_ds

def plot_graph(ds, specific_lat, specific_lon):
    dry_dust_data = ds[DRY_DUST].sel(lat=specific_lat, lon=specific_lon, method="nearest")
    wet_dust_data = ds[WET_DUST].sel(lat=specific_lat, lon=specific_lon, method="nearest")
    # Extract time and values
    time =ds["time"].values
    dry_values = dry_dust_data.values
    wet_values = wet_dust_data.values
    # Create a Plotly figure
    fig = go.Figure()

    # Add dry dust bars
    fig.add_trace(go.Bar(x=time, y=dry_values, name="Dry Dust", marker_color="blue"))

    # Add wet dust bars
    fig.add_trace(go.Bar(x=time, y=wet_values, name="Wet Dust", marker_color="green"))

    # Customize layout
    fig.update_layout(
        barmode="group",  # Group bars side by side
        title=f"Dust Data at lat={specific_lat:.1f}, lon={specific_lon:.1f}",
        xaxis_title="Time",
        yaxis_title="Dust Concentration",
        legend_title="Legend",
        template="plotly_white"
    )

    fig.show()

def show_map_choose_lat_lon():
    # Load a simple world map (from GeoPandas' built-in datasets)
    world = gpd.read_file("https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip")

    # Container for the coordinates
    clicked_coords = {'lon': None, 'lat': None}

    # Function to handle click events
    def on_click(event):
        if event.xdata is not None and event.ydata is not None:
            lon, lat = event.xdata, event.ydata
            plot_graph(ds, lat, lon)
            print(f"Clicked at Longitude: {lon:.2f}, Latitude: {lat:.2f}")
            clicked_coords['lon'] = lon
            clicked_coords['lat'] = lat

    # Plot the world map
    fig, ax = plt.subplots(figsize=(10, 6))
    world.plot(ax=ax, color='lightgray', edgecolor='black')

    # Set the view to a specific region, e.g., Europe (Longitude: -25 to 50, Latitude: 35 to 75)
    ax.set_xlim(WEST_END_POINT, EAST_END_POINT)  # Longitude range for Europe
    ax.set_ylim(SOUTH_END_POINT, NORTH_END_POINT)   # Latitude range for Europe
    # Add gridlines with 0.1-degree spacing
    major_ticks = 5  # Major tick interval in degrees
    minor_ticks = 0.1  # Minor tick interval in degrees

    ax.set_xticks(range(int(WEST_END_POINT), int(EAST_END_POINT) + 1, major_ticks))
    ax.set_yticks(range(int(SOUTH_END_POINT), int(NORTH_END_POINT) + 1, major_ticks))

    # Adding minor ticks using MultipleLocator
    ax.xaxis.set_minor_locator(MultipleLocator(minor_ticks))
    ax.yaxis.set_minor_locator(MultipleLocator(minor_ticks))

    # Customize grid appearance
    ax.grid(which='both', color='gray', linestyle='--', linewidth=0.5, alpha=0.7)

    # Connect the click event to the handler
    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.title("Click on the map to get the data on a specific Latitude and Longitude. ")

    # Keep the plot open
    plt.show()


if __name__ == '__main__':
    ds = get_data()
    longitude, latitude = show_map_choose_lat_lon()
    plot_graph(ds, latitude, longitude)
    # print(ds)


