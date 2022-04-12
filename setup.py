from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

extra_compile_args = {'cxx' : ['-O2']}
extra_compile_args['nvcc'] = ['-O3',
                              '-gencode', 'arch=compute_86,code=compute_86',
                              '-gencode', 'arch=compute_86,code=sm_86'
                              ]

setup(
    name='torch_sputnik',
    ext_modules=[
        CUDAExtension('torch_sputnik', [
            'spmm.cpp',
            'spmm_cuda.cu',
        ],
        include_dirs=['/usr/local/sputnik/include'],
        library_dirs=['/home/soyturk/Documents/binding/sputnik/cc'],
        libraries=['sputnik'],
        extra_compile_args=extra_compile_args),
    ],
    cmdclass={
        'build_ext': BuildExtension
    })
