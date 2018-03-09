# Cherrylights[![Codacy Badge](https://api.codacy.com/project/badge/Grade/9201ab289ee54c64b5adc5a9699226c6)](https://app.codacy.com/app/ikstream/cherrylights?utm_source=github.com&utm_medium=referral&utm_content=ikstream/cherrylights&utm_campaign=badger)

Control application for LED-strips
----


Dependencies:
--
            -Cherrypy
            -pidpgio (https://github.com/joan2937/pigpio)
            
How to use:
--
          git clone https://github.com/ikstream/cherrylights.git
          cd cherrylights
          sudo pip install -r requirements.txt
          edit line FRONT_PI_IP = '<ip of the other pi with pigpio installed>
          ./app.py
