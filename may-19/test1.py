from dotenv import load_dotenv
load_dotenv()

import os
API_KEY = os.getenv("GOOGLE_API_KEY")
CX = os.getenv("GOOGLE_CX")

print("API KEY:", API_KEY)
print("CX ID:", CX)

