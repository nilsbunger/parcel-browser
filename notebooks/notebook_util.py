import geopandas
import matplotlib.colors as mcolors

class StopExecution(Exception):
    def _render_traceback_(self):
        pass

# Python notebook exit function to stop running without killing the kernel
def nb_exit():
    raise StopExecution

colorkeys = list(mcolors.XKCD_COLORS.keys())
def display_polys_on_lot(lot, polys):
    p = lot.plot()
    for idx, poly in enumerate(polys):
        geopandas.GeoSeries(poly).plot(
            ax=p, color=colorkeys[idx % len(colorkeys)], alpha=0.5)
