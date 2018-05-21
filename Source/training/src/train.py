import time
import os
import random

MODELFOLDER = os.environ["MODELFOLDER"]
BUILDNUMBER = os.environ["BUILDNUMBER"]
print("Taking some time to render a pretend model :)")
print("Model Folder: " + MODELFOLDER)
print ("Build Number: " + BUILDNUMBER)

os.makedirs(MODELFOLDER, exist_ok=True)

time.sleep(15) 


rand = random.random()
fileoutput = MODELFOLDER + "/complete.txt"
file = open(fileoutput,"w") 
print("Wrote: " + fileoutput) 
print ("Random Score: " + str(rand))
file.write(str(rand))
file.close