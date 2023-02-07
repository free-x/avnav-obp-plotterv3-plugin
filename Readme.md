Plugin for a Rpi Remote
=======================
This is an [avnav](https://www.wellenvogel.de/software/avnav/docs/beschreibung.html?lang=en) plugin
to handle a nice remote control developed by [chrhartz](https://www.segeln-forum.de/user/19350-chrhartz) - see the link in the (german) 
[Segeln-Forum](https://www.segeln-forum.de/board194-boot-technik/board195-open-boat-projects-org/78328-fernbedienung-f%C3%BCr-den-raspberry/).

Before you can use it, you need to enable i2c on your pi - see e.g. [here](https://raspberry-projects.com/pi/pi-operating-systems/raspbian/io-pins-raspbian/i2c-pins).
If you connect the interrupt to another GPIO pin then the default GPIO17 (Pin11), just change this 
in the configuration (see the AvNav doc about [configurations](https://www.wellenvogel.de/software/avnav/docs/userdoc/statuspage.html?lang=en#h2:ServerConfiguration)).

The plugin will listen for key presses on the remote and will send this as "remote keypress commands"
within AvNav.
It requires AvNav >= 20210504.

To make a AvNav Display (a web browser window) listen to such remote key presses
open the settings , section Remote and enable "read from remote channel".


