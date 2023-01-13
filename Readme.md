Basic pyusb example talking to steelseries ALC lightbar on laptop

```
(pyusb) [sam@compy686 rgbmgr]$ sudo ./install_deps.sh 
+ apt-get update
...snip...
+ apt-get install -y python3-usb
...snip...
(pyusb) [sam@compy686 rgbmgr]$ sudo ./pyusb.py 
Setting lightbar Min Brightness
Successfully wrote data to usb: [12, 0, 0]
Setting lightbar Max Brightness
Successfully wrote data to usb: [12, 0, 255]
```
