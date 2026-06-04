import sys
import time

message = " ".join(sys.argv[1:])
with open("user_text_input.txt", "w") as f:
    f.write(message)
print(f"✅ Message sent: {message}")
