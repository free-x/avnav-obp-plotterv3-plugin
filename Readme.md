Plugin for the OBP Plotter V3
=======================
This is an [avnav](https://www.wellenvogel.de/software/avnav/docs/beschreibung.html?lang=en) plugin
to handle to support the obp plotter v3 from  [chrhartz](https://www.segeln-forum.de/user/19350-chrhartz) - see the link in the (german) 
[Segeln-Forum](https://www.segeln-forum.de/thread/85423-10-1-raspberry-plotter-v3).

This plugin will set up all the necessary device overlays and initialize all hardware to the correct state.
It provides a set of [initial settings](localFirefox.json) for the local browser, a dedicated [layout](localLayout.json), a widget for the brightness control and a user app for controlling brightness, audio volume and managing the automatic brightness adaptation.

Releases
--------
  * [20250317](../../releases/tag/20250317):
    * make it working on bookworm/Pi5
    * pull up on GPIO17 to ensure proper i2c address for goodix
    * use pinctrl (if available) instead of sysfs for GPIO access
    * remove dependency to python3-rpi.gpio (requires separate installation of python3-rpi-lgpio)

  * [20230711](../../releases/tag/20230711):
  allow to keep the HDMI controller on when using dimm (switch in plugin settings/UI)

  * [20230601](../../releases/tag/20230601):
  add a dependency to prepare better error handling for the plotter 
  * [20230423](../../releases/tag/20230425): first release considered to be working for all the main functions.

