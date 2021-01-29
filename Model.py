from metpy.interpolate import cross_section
from metpy.interpolate import log_interpolate_1d
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np
import xarray as xr
from metpy.units import units


class Model:
    def __init__(self):
        self.data = None
        self.var_conf = dict()  # Maps Variable name to  tuple of DataArray and Plotconfiguration

    def open_dset(self, path=r"./data/era5_19120612.nc"):
        self.data = xr.open_dataset(path,
                                    group=None).squeeze()  # Squeeze notwendig für Interpolation (streicht time als dimension)
        self.data = self.data.metpy.parse_cf()  # Wird u.a. benötigt, um cross_section() nutzen zu können

    def reset_data_vars(self):
        for name in self.var_conf.keys():
            self.var_conf[name] = (self.data[name], self.var_conf[name][1])

    def dataset_opened(self):
        return self.data is not None

    def interpolate_csec(self, plevs, start, end):
        start = (start['lat'], start['lon'])
        end = (end['lat'], end['lon'])
        xp_interp = cross_section(self.data['PRESS'], start, end)
        for name, (d_arr, conf) in list(self.var_conf.items()):
            #d_arr = tup[0]
            #conf = tup[1]
            d_arr = cross_section(d_arr, start, end)
            d_arr_interp = log_interpolate_1d(plevs, xp_interp, d_arr)
            # Back to DataArray:
            d_arr_interp = xr.DataArray(data=d_arr_interp,
                                        dims=['plevs', 'index'],
                                        coords={'lat': ('index', d_arr['lat']),
                                                'lon': ('index', d_arr['lon']),
                                                'plevs': ('plevs', plevs),
                                                'index': ('index', d_arr['index'])},
                                        attrs=d_arr.attrs)  # Anpassen, nicht identisch
            # Change dict entry for interpolated values
            self.var_conf[name] = (d_arr_interp, conf)

    def interpolate(self, plevs):
        for name, (d_arr, conf) in list(self.var_conf.items()):
            d_arr_interp = log_interpolate_1d(plevs, self.data['PRESS'], d_arr)
            # Back to DataArray:
            d_arr_interp = xr.DataArray(data=d_arr_interp,
                                        dims=['plevs', 'lat', 'lon'],
                                        coords={'plevs': ('plevs', plevs),
                                                'lat': ('lat', d_arr['lat']),
                                                'lon': ('lon', d_arr['lon'])},
                                        attrs=d_arr.attrs)
            # Change dict entry for interpolated values
            self.var_conf[name] = (d_arr_interp, conf)

    def remove_var(self, varname):
        if varname in self.var_conf.keys():
            self.var_conf.pop(varname)


    def add_var_to_plot(self, varname, pltconf):
        self.var_conf[varname] = (self.data[varname], pltconf)

    def get_var_names(self):
        if self.dataset_opened():
            return [ele for ele in list(self.data.data_vars) if
                ele not in ['a', 'b', 'p0', 'ps']]  # Anhand Dimension feststellbar? dann verallgemeinbar
        else:
            return []

    def get_to_plot_vars(self):
        return self.var_conf.keys()

    def get_desc(self, varname):
        if varname in self.var_conf:
            return str(self.var_conf[varname][0])
        else:
            return f"no description available for {varname}"

    def do_horizontal_plot(self, plevs, level = 1):
        self.interpolate(plevs)
        fig = plt.figure(3, figsize=(15, 10))
        ax = plt.axes(projection=ccrs.PlateCarree())
        for d_arr, conf in self.var_conf.values():
            if conf.fill:
                ax.contourf(d_arr['lon'], d_arr['lat'], d_arr[level], conf.grades, cmap=conf.cmap, transform=ccrs.PlateCarree())
            else:
                ax.contour(d_arr['lon'], d_arr['lat'], d_arr[level], conf.grades, cmap=conf.cmap, transform=ccrs.PlateCarree())
        ax.coastlines()
        ax.gridlines()

    def do_csec_plot(self, plevs, start, end):
        self.interpolate_csec(plevs, start, end)
        #x_ax_var = 'lon' if (abs(start['lon'] - end['lon']) > abs(start['lat'] - end['lat'])) else 'lat'  # Determines xaxis variable. (Let User decide?) lon/lat or index is possible
        x_ax_var = 'index'
        fig = plt.figure(3, figsize=(15, 10))
        plt.cla()
        ax = plt.axes() if len(fig.axes) == 0 else fig.axes[0] #  create or reuse axis
        for d_arr, conf in self.var_conf.values():
            if conf.fill:
                ax.contourf(d_arr[x_ax_var], plevs, d_arr, conf.grades, cmap=conf.cmap)
            else:
                ax.contour(d_arr[x_ax_var], plevs, d_arr, conf.grades, cmap=conf.cmap)
        #ax.set_xlim(start[x_ax_var], end[x_ax_var])
        ax.set_yscale('symlog')
        ax.set_ylim(plevs.max(), plevs.min())
        ax.set_ylabel('Pressure (hPa)')
        ax.set_xlabel(x_ax_var)
        ax.set_yticks(np.arange(1000, 10, -100))  #  Wie anpassen?
        ax.set_yticklabels(np.arange(1000, 10, -100))
        ax.set_title(f"Cross Section of {''.join(self.var_conf.keys())} from {(start['lat'], start['lon'])} to {(end['lat'], end['lon'])}")
        plt.show()
