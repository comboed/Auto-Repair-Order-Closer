import bot
import api

# Tekion Login
EMAIL = "EMAIL"
PASSWORD = "PASSWORD"

# Location Numbers
# Newark = 1
# LGA = 5
# Miami = 11
# FT Lauderdale = 12
LOCATION_NUMBER = 1

# Repair order filename
FILENAME = "TEK 09.12.2024.xlsx - NEWARK.csv"

# Force bot to start at specific repair order [OPTIONAL]
START_REPAIR_ORDER = "6488"

if __name__ == "__main__":
    print("Tekion Automatic Repair Order Processor \n")
    session = api.API(EMAIL, PASSWORD, LOCATION_NUMBER)
    b_bot = bot.Bot(session, FILENAME)
    b_bot.run(START_REPAIR_ORDER)