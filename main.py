import xarray as xr
import pandas as pd
from datetime import datetime
import numpy as np
import plotly.graph_objects as go
from config import *
from map import *
from matplotlib.ticker import MultipleLocator
from tqdm import tqdm
import concurrent.futures
import os

def fetch_dataset_with_timeout(url,year, month, day, lat, lon, timeout=10):
    """Attempt to open a dataset with a timeout."""
    def load_dataset():
        ds = xr.open_dataset(url)
        ds = ds[[DRY_DUST, WET_DUST]]
        start_datetime = datetime(year, month, day, HOUR_START, 0, 0)
        end_datetime = pd.to_timedelta(23, unit="h") + start_datetime
        ds = ds.sel(time=slice(start_datetime, end_datetime))
        nearest_data = ds.sel(lat=lat, lon=lon, method="nearest")
        dry_dust_data = nearest_data[DRY_DUST].values
        wet_dust_data = nearest_data[WET_DUST].values
        time = nearest_data["time"].values
        df = pd.DataFrame({
            f"{DRY_DUST}": dry_dust_data,
            f"{WET_DUST}": wet_dust_data,
            "total_dust": wet_dust_data + dry_dust_data
        }, index=time)
        return df

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(load_dataset)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Loading dataset timed out after {timeout} seconds")

def get_monthly_data(month, year, lat, lon, path):
    two_digit_month = str(month).zfill(2)
    month_path = f"{path}/{two_digit_month}"
    create_folder(month_path)
    mounth_ds = []
    for day in tqdm(range(1, 32), desc=f"Fetching Datasets for {year}-{month}", unit="day"):
        try:
            two_digit_day = str(day).zfill(2)
            file_date = f"{year}{two_digit_month}{two_digit_day}"
            file_path = f"{month_path}/{file_date}.pkl"
            if os.path.exists(file_path):
                print(f"File exists: {file_path}. Loading data...")
                df = pd.read_pickle(file_path)
            else:
                print(f"File does not exist: {file_path}. Fetching data...")
                opendap_url = f"dust.aemet.es/thredds/dodsC/dataRoot/{MODEL}/{year}/{two_digit_month}/" \
                              f"{file_date}{model_code}.nc"
                url = f"https://{username}:{password}@{opendap_url}"
                # Open the dataset with a timeout
                df = fetch_dataset_with_timeout(url,year, month, day, lat, lon, timeout=20)  # 10-second timeout
                df.to_pickle(file_path)
            mounth_ds.append(df)
        except Exception as e:
            # Handle exceptions (e.g., network errors, missing files)
            print(f"Failed to process dataset for day {two_digit_day}: {e}")
    combined_df = pd.concat(mounth_ds, axis=0)
    return combined_df

def create_folder(path):
    # folder = os.path.dirname(path)
    if not os.path.exists(path):
        print(f"Creating folder: {path}")
        os.makedirs(path, exist_ok=True)
def get_data(lat, lon):
    years_dfs = []
    lat_lon_path = f"{DATA_PATH}({lat},{lon})"
    create_folder(lat_lon_path)
    for year in range(2018, 2019):
        yearly_dfs = []
        year_path = f"{lat_lon_path}/{year}"
        create_folder(year_path)
        for month in range(1,13):
            monthly_df = get_monthly_data(month, year, lat, lon, year_path)
            yearly_dfs.append(monthly_df)
        year_df = pd.concat(yearly_dfs, axis=0)
        years_dfs.append(year_df)
    return pd.concat(years_dfs, axis=0)
    # return dry_dust_data, wet_dust_data, time


def plot_graph(df, title):
    describe_stats = df.describe()
    fig = go.Figure()
    # Add dry dust bars
    fig.add_trace(go.Bar(x=df.index, y=df.dust_depd, name="Dry Dust", marker_color="blue"))

    # Add wet dust bars
    fig.add_trace(go.Bar(x=df.index, y=df.dust_depw, name="Wet Dust", marker_color="green"))

    # Customize layout
    fig.update_layout(
        barmode="group",  # Group bars side by side
        title=title,
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
    df_year = get_data(specific_lat, specific_lon)
    print()
    # longitude, latitude = show_map_choose_lat_lon()
    # plot_graph(dry_dust_data, wet_dust_data, time)



