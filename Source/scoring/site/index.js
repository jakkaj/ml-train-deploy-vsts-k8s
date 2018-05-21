const express = require('express')
const app = express()
const fs = require('fs');
const path = require('path');

app.get('/', (req, res) => {
    var modelFolder = process.env.MODELFOLDER;
    //this is the complete file - we'd read the model here perhaps... it's just a demo!
    var file = path.join(modelFolder, "complete.txt");
    if(fs.existsSync(file)){
        var contents = fs.readFileSync(file, 'utf-8');
        res.send(`Score: ${contents}`);
    }else{
        res.send("Error, could not find the complete.txt file. ")
    }
})

app.listen(3000, () => console.log('Example app listening on port 3000!'))