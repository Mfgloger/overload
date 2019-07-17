# Overload

BookOps Cataloging Deptartment toolbox.

Warning, the project is a work in progress.
At the momement Overload includes following functionality:
* Processing Vendor File (PVF) - prepares records for import into BPL & NYPL Sierra
* Worldcat2Sierra - queries and downloads bibliographic records from OCLC Worldcat based on Sierra's report or a list of identifiers (ISBNs, LCCN, OCLC #, UPC)
* GetBib - retrieves BPL & NYPL Sierra record number for matching ISBN, UPC, LCCN, and OCLC #

## Future plans
* more tests

## Installation
To create executable file (requires pyinstaller):
1. Activate Overload virtual enviroment
2. Change current directory to Overload root directory
3. Change logging.config to production logger (DEV_LOGGING to LOGGING)
4. Add loggly token in the logging_setup.py
5. Add hook-keyring.backend.py file into the root directory (copy from previous runs)
6. Update __version__.py and windows_version_info_txt files
7. Run cmd and enter command:
pyinstaller --onefile --windowed --version-file=windows_version_info.txt --icon="./icons/SledgeHammer.ico" --additional-hooks-dir=. overload.py

## License
[MIT](https://opensource.org/licenses/MIT)


## Icons
Overload icons by [Mattahan (Paul Davey)](http://mattahan.deviantart.com) used under CC Atribution-Noncommercial-Share Alike 4.0 license.
