# Cherrylights
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
