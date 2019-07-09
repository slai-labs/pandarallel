import pandas as pd
import pyarrow.plasma as plasma
import multiprocessing as multiprocessing
from tqdm._tqdm_notebook import tqdm_notebook as tqdm_notebook
from tqdm import tqdm

from .dataframe import DataFrame
from .series import Series
from .series_rolling import SeriesRolling
from .rolling_groupby import RollingGroupby
from .dataframe_groupby import DataFrameGroupBy
from .plasma_store import start_plasma_store

SHM_SIZE_MB = int(2e3)  # 2 GB
NB_WORKERS = multiprocessing.cpu_count()
PROGRESS_BAR = False


class pandarallel:
    @classmethod
    def initialize(cls, shm_size_mb=SHM_SIZE_MB, nb_workers=NB_WORKERS,
                   progress_bar=False, progress_bar_script=False,
                   verbose=2):
        """
        Initialize Pandarallel shared memory.

        Parameters
        ----------
        shm_size_mb : int, optional
            Size of Pandarallel shared memory

        nb_workers : int, optional
            Number of worker used for parallelisation

        progress_bar : bool, optional
            Display a progress bar
            WARNING: Progress bar is an experimental feature.
                     This can lead to a considerable performance loss.
        """
        if progress_bar or progress_bar_script:
            print("WARNING: Progress bar is an experimental feature. This \
can lead to a considerable performance loss.")
            if progress_bar_script:
                tqdm.pandas()
                progress_bar = progress_bar_script
            else:
                tqdm_notebook().pandas()

        verbose_store = verbose >= 2

        if hasattr(cls, "proc"):
            cls.proc.kill()

        if verbose >= 1:
            print("New pandarallel memory created - Size:", shm_size_mb, "MB")
            print("Pandarallel will run on", nb_workers, "workers")

        plasma_store_name, cls.proc = start_plasma_store(int(shm_size_mb * 1e6),
                                                         verbose=verbose_store)

        plasma_client = plasma.connect(plasma_store_name)

        args = plasma_store_name, nb_workers, plasma_client

        pd.DataFrame.parallel_apply = DataFrame.apply(*args, progress_bar)
        pd.DataFrame.parallel_applymap = DataFrame.applymap(
            *args, progress_bar)

        pd.Series.parallel_map = Series.map(*args, progress_bar)
        pd.Series.parallel_apply = Series.apply(*args, progress_bar)

        pd.core.window.Rolling.parallel_apply = SeriesRolling.apply(
            *args, progress_bar)

        pd.core.groupby.DataFrameGroupBy.parallel_apply = DataFrameGroupBy.apply(
            *args)

        pd.core.window.RollingGroupby.parallel_apply = RollingGroupby.apply(
            *args)
