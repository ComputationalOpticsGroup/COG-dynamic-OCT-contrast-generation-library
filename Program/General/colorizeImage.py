import numpy as np
from matplotlib.colors import hsv_to_rgb

def scale_clip(data, vmin, vmax, scale=1.0):
    """
    Adjust the value with the dynamic range and assign it to the range of 0 to 1.

    Parameters
    ----------
    data : 3D array
        aLIV, Swiftness, or dB-scale OCT intensity image
    vmin : float
        minimum of dynamic range
    vmax : float
        maximum of dynamic range
    scale : float
        The default is 1.0.

    Returns
    -------
    data : 3D array
        aLIV, Swiftness, or dB-scale OCT intensity image

    """
    return np.clip((data-vmin)*(scale/(vmax-vmin)), 0, scale)

def generate_RgbImage(doct, dbInt, doctRange, octRange):
    """
    

    Parameters
    ----------
    doct : 3D array
       aLIV or Swiftness image
    dbInt : 3D array
        dB-scale OCT intensity image
    doctRange : 1D tuple (min, max)
        dynamic range of aLIV, which is used as hue of pseudo-color image
    octRange : 1D tuple (min, max)
        dynamic range of dB-scaled OCT intensity, which is used as brightness of pseudo-color image

    Returns
    -------
    rgbImage : RGB array of pseudo-color image
        pseudo-color image

    """
    hsvImage = np.stack([scale_clip(doct, *doctRange, 0.33), np.ones_like(doct),
                       scale_clip(dbInt, *octRange)], axis=-1)
    rgbImage = hsv_to_rgb(hsvImage)
    return rgbImage