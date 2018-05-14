import time
import os

MODELFOLDER = os.environ["MODELFOLDER"]
print(MODELFOLDER)
time.sleep(15) 


import datetime
today = time.strftime("%Y-%m-%d %H-%M")
fileoutput = MODELFOLDER + "/complete.txt"
file = open(fileoutput,"w") 

print("Wrote: " + fileoutput)
 
file.write("Python writing: " + str(today)) 
file.close