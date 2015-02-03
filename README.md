smarthome
===========

API for controlling devices in the house via vera.

Currently working for:
* Lights including brightness
* Scenes
* Locks
* Nest (climate)
* Belkin Wemo

Hardcoded to work for my house but will include plans to expose this in future.

Thanks @bencxr for the guidance -- I must disclaim that the bad style is my fault :/ lololol

Getting started
===========
First, replace all pointers to 192.168.1.88 with your Vera's IP address.
With an IP address of 192.168.0.22 you can do this in BASH with (yeah, I know what . means, but this works and its easier to read):
		sed -i 's/192.168.1.88/192.168.0.22/g' ./*.py

Now, launch the Flask/Python/whatever server with:
		python main.py
		
This will start a server lisetning on port 5000.

You can get started immediately by visiting:
		http://localhost:5000
	
Or, you can set-up Apache as a front-end with the vhost commands (I have this apache instance doing other stuff so I needed to be specific):
		ProxyPass /scenes http://localhost:5000/scenes
        ProxyPassReverse /scenes http://localhost:5000/scenes
        ProxyPass /lights http://localhost:5000/lights
        ProxyPassReverse /lights http://localhost:5000/lights

If all this servers does is this functionality you could just do:
		ProxyPass / http://localhost:5000/
		
I have a front-end HTML/JS application I use but I'm not entirely sure I want to share it. I will however, add some further clarity with example rest calls you can make easily:
	GET		https://localhost/lights
	
	PUT		https://localhost/scenes/1
	
	PUT		https://localhost/lights/1
				{"state": "1"}
				
	PUT		https://localhost/lights/brightness/1
				{"brightness": "100"}