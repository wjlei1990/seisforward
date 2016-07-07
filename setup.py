from setuptools import setup

setup(
    name="seisforward",
    version="0.0.1",
    packages=["seisforward"],
    zip_safe=False,
    install_requires=["yaml"],
    entry_points={
        'console_scripts':
            ['seisforward-setup_runbase=seisforward.setup_runbase:main',
             'seisforward-easy_copy_specfem=seisforward.easy_copy_specfem:main',
             'seisforward-create_jobs=seisforward.create_jobs:main'
             ]
    }
)
