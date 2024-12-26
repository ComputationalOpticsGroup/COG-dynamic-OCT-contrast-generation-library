import numpy as np
import tifffile
from .variableLIV import *
from General. colorizeImage import *
from tqdm import tqdm
import cv2

debugger = False #put "pdb.set_trace()" in the location where you debug
if debugger == True:
    import pdb



def vliv_postprocessing(path_OCT, volumeDataType, frameSeparationTime , 
                frameRepeat, bscanLocationPerBlock, blockRepeat, blockPerVolume, fitting_method = "GPU", 
                       alivInitial = 20, swiftInitial = 1 , bounds = ([0,0],[np.inf, np.inf]), 
                       use_constraint = True , compute_VoV = False, use_weight = False , average_LivCurve = True, motionCorrection = False,
                       octRange = (10., 40.), alivRange =(0., 10.), swiftRange =(0., 3.)):
     
    """
    This function process aLIV and Swiftness.
    
    Parameters
    ---------
    path_OCT: file path of linear OCT intensity.
        The data type and shape should be "float32" and [time, z, x], or [time, x, z].
    volumeDataType: str
        Either "BSA" or 'Ibrahim2021BOE'
        BSA: Burst scanning protocol
        Ibrahim2021BOE: Dynamic OCT scanning protocol (Same as Ibrahim2021BOE paper)
    frameSeparationTime: constant(float)
        Successive frame measurement time [s] 
    frameRepeat: int
        Number of frames in a single burst
    bscanLocationPerBlock: int
        No of Bscan locations per Block
    blockRepeat:  int 
        Number of block repeats
    blockPerVolume: int 
        Number of blocks in a volume
    fitting_method: str
        Either "CPU" or "GPU"
        CPU: vlivCPUFitExp()
        GPU: vlivGPUFitExp()
    alivInitial: float
        alivInitial = Initial value of a (magnitude) in fitting
    swiftInitial: float
        1/swiftInitial = Initial value of b (time constant) in fitting
    bounds : 2D tuple
        Exploration range of fitting parameters
        ([min a, min b], [max a, max b])
    use_constraint : True or False
        Set bounds of parameters in fitting : True
        don't set bounds : False
    compute_VoV : True or False
        Compute variance of all LIVs of identical time window (VoV) for test (debug) and weighted fitting: True
        Don't compute VoV : False
    use_weight : True or False
        Apply weight for fitting : True
        Make sure if "compute_VoV = True". VoV will be used as the weight.
        The weighted fitting has been implemented only in GPU fitting (fitting_method = "GPU").
        Don't apply weight : False
    average_LivCurve : True or False
        Average LIV curve before fitting using 3*3 kernel for increasing accuracy: True
        Don't average LIV curve : False
    motionCorrection: True or False
        Apply motion correction (DOI: 10.1364/BOE.488097): True
        Don't apply: False
    octRange: 1D tuple (min, max)
        dynamic range of dB-scaled OCT intensity, which is used as brightness of pseudo-color image
    alivRange: 1D tuple (min, max)
        dynamic range of aLIV, which is used as hue of pseudo-color image
    swiftRange:1D tuple (min, max)
        dynamic range of Swiftness, which is used as hue of pseudo-color image

    Output
    -----------
    dB-scaled OCT intensity: 3D gray scale image
    VLIV: 4D double [timePoints, slowscanlocations, z, x]
        LIV array at different time windows (LIV curve)
    timewindows: 2D double
    aLIV: 3D gray scale and RGB image
    Swiftness: 3D gray scale and RGB image
    
    """
    print("Processing started")
    maxFrameNumber = frameRepeat * blockRepeat * bscanLocationPerBlock # Maximum frame number per Block 
    burstingPeriod = frameRepeat *  bscanLocationPerBlock # Peroid of burst sampling
    numLocation = bscanLocationPerBlock * blockPerVolume # Number of slow scan locations
    
    print('Processing: ' + path_OCT)
    
    ## OCT intensity
    octFrames = tifffile.imread(path_OCT)
    height = octFrames.shape[1]
    width = octFrames.shape[2]
    
    if volumeDataType == 'BSA':
        print("Data Type = " + str(volumeDataType))
    
    elif volumeDataType == 'Ibrahim2021BOE':
        print("Data Type = " + str(volumeDataType))

    aliv = np.zeros((numLocation, height, width), dtype=np.float32)
    swift = np.zeros((numLocation, height, width),  dtype=np.float32)
    oct_db = np.zeros((numLocation, height, width),  dtype=np.float32)


    for floc in tqdm(range(0,numLocation)):

        ## Load Sparse data
        if volumeDataType == 'BSA':
            sparseSequence, timePoints = makeSparseDataBSA (octFrames, maxFrameNumber, 
                                                            frameRepeat, burstingPeriod, bscanLocationPerBlock, floc)
        
        elif volumeDataType == 'Ibrahim2021BOE':
            sparseSequence, timePoints = makeSparseDataFromRasterRepeat(octFrames, bscanLocationPerBlock, blockRepeat, floc)
        if motionCorrection == True:
            sparseSequence = correctMotion(sparseSequence, register_start_depth= 50)

        if floc == 0: #for save VLIV array
            VLIV_save = np.zeros((numLocation, timePoints.shape[0]-1, height, width),  dtype=np.float32)
            if compute_VoV == True:
                VoV_save = np.zeros((numLocation, timePoints.shape[0]-1, height, width),  dtype=np.float32)
        ## Compute logarithmic OCTs
        oct_db [floc] = 10*np.log10(np.nanmean(sparseSequence, axis=0))
        
        ## Compute VLIV
        VLIV , possibleMtw , VoV = computeVLIV(sparseSequence, timePoints, maxTimeWidth =  np.nan, compute_VoV = False)
        
        ## Average LIV curve
        if average_LivCurve == True:
            twIdx = 0
            for twIdx in range(0, VLIV.shape[0]):                
                VLIV[twIdx,:,:] = cv2.blur(VLIV[twIdx,:,:], (3,3))
                twIdx = twIdx + 1

        ## curve fitting on LIV curve to compute saturation level (magnitude) and time constant (tau)
        if fitting_method == 'GPU':
            mag, tau = vlivGpuFitExp(VLIV, possibleMtw, VoV, frameSeparationTime, alivInitial, swiftInitial, bounds, use_constraint, use_weight)
        
        if fitting_method == 'CPU':
            mag, tau = vlivCPUFitExp(VLIV, possibleMtw, frameSeparationTime, alivInitial, swiftInitial, bounds, use_constraint = False)

        aliv [floc] = mag ## aLIV
        swift [floc] = 1/ tau ## Swiftness
        VLIV_save[floc,:,:,:] = VLIV ## LIV curve (VLIV)
        if compute_VoV == True:
            VoV_save[floc,:,:,:] = VoV
            
    ## Generate each path save data
    suffix_intensity_linear = ".tiff"
    root = path_OCT[:-len(suffix_intensity_linear)]
    path_vliv = root  +  '_vliv.npy'
    path_timewindow = root  +  '_timewindows.npy'
    path_vov = root + '_vov.npy'
    ## Save the gray scale image of dB-scaled OCT intensity
    tifffile.imwrite(root  +  '_dbOct.tif', oct_db )
    ## Save time windows, LIV curve (VLIV), and variance of all LIVs for each time window (VoV)
    np.save(path_timewindow, possibleMtw)
    np.save(path_vliv, VLIV_save)
    if compute_VoV == True:
        np.save(path_vov, VoV_save)

    
    ## Convert to color aLIV and Swiftness images
    aliv_rgb = generate_RgbImage(doct = aliv, dbInt = oct_db, doctRange = alivRange, octRange = octRange)
    swift_rgb = generate_RgbImage(doct = swift, dbInt = oct_db, doctRange = swiftRange, octRange = octRange)

    ## Save the gray scale and rgb images of aLIV and Swiftness
    path_aliv = root  +  '_aliv.tif'
    path_aliv_view = root + f'_aliv_min{alivRange[0]}-max{alivRange[1]}.tif'

    path_swift = root  + '_swiftness.tif'
    path_swift_view = root + f'_swiftness_min{swiftRange[0]}-max{swiftRange[1]}.tif'

    tifffile.imwrite(path_aliv, aliv)  
    tifffile.imwrite(path_aliv_view, (aliv_rgb*255).astype(np.uint8)) 

    tifffile.imwrite(path_swift, swift)
    tifffile.imwrite(path_swift_view, (swift_rgb*255).astype(np.uint8))
    
    print("VLIV Processing Ended")