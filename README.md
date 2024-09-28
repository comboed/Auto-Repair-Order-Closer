A bot to automatically close vehicle repair orders with the correct information

## Usage
Open main.py and set tek account information

Set filename to the RO excel sheet in the data folder
* Column formats should be: LOCATION | RO | EMPTY COLUMN (used for storing entry) | VIN

Run main.py and the bot should start processing each line.

## Info
All opcodes are stored in the /data/opcodes/opcodes.json file (Nearly all the commonly used ones are saved, including hashes).

If the user wishes to add more locations they can be set in the API class in api.py (Location # is found in any of the API calls on the website).
