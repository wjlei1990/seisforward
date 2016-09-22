from setuptools import setup

setup(
    name="seisforward",
    version="0.0.1",
    packages=["seisforward"],
    zip_safe=False,
    install_requires=["pyyaml"],
    entry_points={
        'console_scripts':[
            'seisforward-validate_config=seisforward.bin.validate_config:main',
            'seisforward-create_database=seisforward.bin.create_database:main',
            'seisforward-fill_database=seisforward.bin.fill_database:main',
            'seisforward-setup_runbase=seisforward.bin.setup_runbase:main',
            'seisforward-create_jobs=seisforward.bin.create_jobs:main',
            'seisforward-validate_jobs=seisforward.bin.validate_jobs:main',
            'seisforward-check_job_status=seisforward.bin.check_job_status:main',  # NOQA
            'seisforward-reset_job_status=seisforward.bin.reset_job_status:main',  # NOQA
        ]
    }
)
