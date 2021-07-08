# import library 
import math, random


# function to generate OTP
def generateOTP(length=6):
    # Declare a digits variable
    # which stores all digits
    digits = "0123456789"
    OTP = ""

    # length of password can be chaged
    # by changing value in range
    for i in range(length):
        OTP += digits[math.floor(random.random() * 10)]

    return OTP


# Driver code
if __name__ == "__main__":
    print("OTP of 6 digits:", generateOTP())

