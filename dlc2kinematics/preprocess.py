"""
dlc2kinematics
© M. Mathis Lab
https://github.com/AdaptiveMotorControlLab/dlc2kinematics/
"""
import os
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


def load_data(filename, smooth=False, filter_window=3, order=1):
    """
    Reads the input datafile which is a multiindex pandas array generated by DeepLabCut as a result of analyzing a video.

    Parameters
    ----------
    filename: string
        Full path of the multiindex pandas array(.h5) file as a string.

    smooth: Bool
        Optional. Smooths coordinates of all bodyparts in the dataframe.

    filter_window: int
        Optional. Only used if the optional argument `smooth` is set to True. The length of filter window which needs to be a positive odd integer
    order: int
        Optional. Only used if the optional argument `smooth` is set to True. Order of the polynomial to fit the data. The order must be less than the filter_window

    Outputs
    -------
    df: dataframe; smoothed in case the optional argument `smooth` is set to True.
    bodyparts: List of unique bodyparts in the dataframe.
    scorer: Scorer name as string.

    Example
    -------
    Linux/MacOS
    >>> df,bodyparts,scorer = dlc2kinematics.load_data('/home/data/video.h5')
    Windows
    >>> df,bodyparts,scorer = dlc2kinematics.load_data('C:\\yourusername\\rig-95\\video.h5')

    """
    df = pd.read_hdf(filename, "df_with_missing")
    bodyparts = df.columns.get_level_values("bodyparts").unique().to_list()
    scorer = df.columns.get_level_values(0)[0]
    if smooth:
        df = smooth_trajectory(
            df,
            bodyparts,
            filter_window,
            order,
            deriv=0,
            save=False,
            output_filename=None,
            destfolder=None,
        )

    return df, bodyparts, scorer


def smooth_trajectory(
    df,
    bodyparts,
    filter_window=3,
    order=1,
    deriv=0,
    save=False,
    output_filename=None,
    destfolder=None,
):
    """
    Smooths the input data which is a multiindex pandas array generated by DeepLabCut as a result of analyzing a video.

    Parameters
    ----------
    df: Pandas multiindex dataframe

    bodyparts: List
        List of bodyparts to smooth. To smooth all the bodyparts use bodyparts=['all']

    filter_window: int
        The length of filter window which needs to be a positive odd integer

    order: int
        Order of the polynomial to fit the data. The order must be less than the filter_window

    deriv: int
        Optional. Computes the derivative. If order=1, it computes the velocity on the smoothed data, if order=2 it computes the acceleration on the smoothed data.

    Outputs
    -------
    df: smoothed dataframe

    Example
    -------
    >>> df_smooth = kinematics.smooth_trajectory(df,bodyparts=['nose','shoulder'],window_length=11,order=3)

    To smooth all the bodyparts in the dataframe, use
    >>> df_smooth = kinematics.smooth_trajectory(df,bodyparts=['all'],window_length=11,order=3)

    """
    df = df.copy()
    xy = df.columns.get_level_values("coords") != "likelihood"
    if bodyparts[0] == "all":
        mask = np.ones(df.shape[1], dtype=bool)
    else:
        mask = df.columns.get_level_values("bodyparts").isin(bodyparts)
    to_smooth = xy & mask
    df.loc[:, to_smooth] = savgol_filter(
        df.loc[:, to_smooth], filter_window, order, deriv, axis=0
    )
    df_cut = df.loc[:, mask]
    if not destfolder:
        destfolder = os.getcwd()
    if not output_filename:
        output_filename = (
            "dataFrame_smooth_" + df.columns.get_level_values("scorer").unique()[0]
        )

    if save:
        print("Saving the smoothed data as a pandas array in %s " % destfolder)
        df_cut.to_hdf(
            os.path.join(destfolder, output_filename + ".h5"),
            "df_with_missing",
            format="table",
            mode="w",
        )
    return df_cut