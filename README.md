# Overload

BookOps Cataloging Deptartment toolbox.

The project is a work in progress. At the momement the only funcitonality is Processing Vendor Records and associated with it statistical reports.

## Future plans
* upgrade of local bibs sourced from WorldCat
* develop tests

## Installation
To create executable file (requires pyinstaller):
1. Activate Overload virtual enviroment
2. Change current directory to Overload root directory
3. Change logging.config to production logger (DEV_LOGGING to LOGGING)
4. Add loggly token in the logging_setup.py
5. Add hook-keyring.backend.py file into the root directory (copy from previous runs)
6. Update __version__.py and windows_version_info_txt files
7. Run CMD and enter command:
pyinstaller --onefile --windowed --version-file=windows_version_info.txt --icon="./icons/SledgeHammer.ico" --additional-hooks-dir=. overload.py

## License
[MIT](https://opensource.org/licenses/MIT)


## Icons
Overload icons by [Mattahan (Paul Davey)](http://mattahan.deviantart.com) used under CC Atribution-Noncommercial-Share Alike 4.0 license.
