Instration
============
COG-DOCT was implemented in Python 3. Please install Python environment first (e.g., [Anaconda navigator](https://www.anaconda.com/download)). 

Library
---------
### Programs require installation of: 
- NumPy (version 1.19.2 or newer)
- CuPy (version 10.0.0 or newer; Please follow [Cupy installation](https://docs.cupy.dev/en/stable/install.html).)
- tifffile (version 2020.10.1 or newer)
- tqdm (version 4.50.2 or newer)
- OpenCV (version 4.0.1 or newer)
- SciPy (version 1.5.2 or newer)
- skimage (version 0.17.2 or newer)
- Matplotlib (version 3.3.2 or newer)

### GPUfit:
 A open-source GPU-accelerated implementation of function fitting (Gpufit; [[GitHub repository](https://github.com/gpufit/Gpufit)]) is used in a function fitting. Gpufit (version 1.2.0) has been included in the released package of COG-DOCT, and a model function (i.e., 1st order saturation function) has been already compiled to the Gpufit. So, you are not required additional implementation.  
 When you additionally implement a new fitting function, please refer to [GPUFit_AddModelFunction](\GPUFit_AddModelFunction.pdf) manual as needed. 


Environment
-------------
Following implementation environment is confident to execute programs:
- Windows
- GPU: NVIDIA GeForce RTX 2070 Super with Max-Q Design
- CPU: Intel Core i7-10750H
- Memory: 32 GB
- Anaconda navigator (Tool to launch applications and manage environments without command line commands.; [[Download](https://www.anaconda.com/download)])