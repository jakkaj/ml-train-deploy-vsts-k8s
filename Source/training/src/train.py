import time
import os

MODELFOLDER = os.environ["MODELFOLDER"]
BUILDNUMBER = os.environ["BUILDNUMBER"]
print("Taking some time to render a pretend model :)")
print("Model Folder: " + MODELFOLDER)
print ("Build Number: " + BUILDNUMBER)

time.sleep(15) 


import datetime
today = time.strftime("%Y-%m-%d %H-%M")
fileoutput = MODELFOLDER + "/complete.txt"
file = open(fileoutput,"w") 
print("Wrote: " + fileoutput) 
file.write("Python writing: " + str(today))
file.write("Build Number: " + BUILDNUMBER) 
file.close