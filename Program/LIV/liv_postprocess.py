import os
import time
import tifffile
import numpy as np
from matplotlib.colors import hsv_to_rgb
from matplotlib.pyplot import *

def scale_clip(data, vmin, vmax, scale=1.0):
    return np.clip((data-vmin)*(scale/(vmax-vmin)), 0, scale)


def liv_postprocess (path_oct,frameRepeat, blockPerVolume, 
                    bscanLocationPerBlock, blockRepeat, octRangedB= (-5, 55), LIVrange=(0, 10)):
    
    """
    Postprocessing function of LIV 
    
    Input parameters
    ---------
    path_OCT: file path of linear OCT intensity
    frameRepeat: int
        Number of frames in a single burst
    bscanLocationPerBlock: int
        No of Bscan locations per Block
    blockRepeat:  int 
        Number of block repeats at each Bscan location
    blockPerVolume: int 
        Number of blocks in a volume
        
    Output
    -----------
    LIV: 3D double 
    LIV_rgb : Color composite image of LIV
    OCT_dB :  Mean dB-scale OCT intensity
    
    """
    
    print("LIV Processing started")
    
    octImg_lin = tifffile.imread(path_oct)
    print(f'Input array size= {octImg_lin.shape}')

    bscan_num, *bscan_shape = octImg_lin.shape

    ## Reshape the OCT intensity to arrange in this order
    octImg = octImg_lin.reshape(blockPerVolume, blockRepeat, bscanLocationPerBlock, frameRepeat, *bscan_shape)
#     print(f'Input array size after reshaping= {octImg.shape} = (blockPerVolume, blockRepeat, bscanLocationPerBlock, frameRepeat, ptPerA, aPerB)')
    
    # Mean OCT intensity among repeated blocks
    octImgMean = (10*np.log10(octImg)).mean(axis=1).reshape(blockPerVolume*bscanLocationPerBlock, frameRepeat, *bscan_shape)
    octImgMean = octImgMean[:, 0, ...] # Extracts the first frame from the four repeated frames at each Bscan location

   # Compute LIV by taking the variance among repetated blocks (axis =1)
    LIV = (10*np.log10(octImg)).var(axis=1).reshape(blockPerVolume*bscanLocationPerBlock, frameRepeat, *bscan_shape)
    
    LIV = LIV[:, 0, ...] # Extracts the first frame from the four repeated frames at each Bscan location
    print(f'LIV size= {LIV.shape} ')
    
    # Create composite LIV color image with the dB-scaleOCT intensity
    LIV_hsv = np.stack([scale_clip(LIV, *LIVrange, 0.33),
                        np.ones_like(LIV),
                        scale_clip(octImgMean, *octRangedB)], axis=-1)
    
    LIV_rgb = hsv_to_rgb(LIV_hsv)
    
    suffix_intensity_linear = "abs2.tiff"
    root = path_oct[:-len(suffix_intensity_linear)]
    path_liv = root  +  '_LIV.tif'
    path_liv_view = root  +  f'_LIV_min{LIVrange[0]}-max{LIVrange[1]}.tif'
    path_octView = root + '_OCTIntPDavg_view_NormalVolume.tif'
    
    # suffix_intensity_linear = "_OCTIntensityPDavg.tif"
    # root = path_oct[:-len(suffix_intensity_linear)]
    # # Output file paths of LIV and Mean OCT intensity
    # path_liv = root + '_LIV.tif'
    # path_liv_view = root + f'_LIV_min{LIVrange[0]}-max{LIVrange[1]}.tif'
    # path_octView = root + '_OCTIntPDavg_view_NormalVolume.tif'
    
    # Save the LIV and Mean OCT intensity in the current directory
    
    tifffile.imwrite(path_liv, LIV) # # Save gray scale LIV image
    tifffile.imwrite(path_liv_view, (LIV_rgb*255).astype(np.uint8)) # # Save 8-bit LIV image
    tifffile.imwrite(path_octView, octImgMean) # # Save dB scale OCT intensity 
    
    print("LIV Processing Ended")