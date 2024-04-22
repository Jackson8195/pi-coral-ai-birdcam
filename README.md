# pi-coral-ai-birdcam
Raspberry Pi power AI bird camera the identifies birds using Coral and TensorFlow Lite

To configure program to run on startup:

-navigate to "sudo nano /etc/xdg/lxsession/LXDE-pi/autostart" in pi terminal
-Enter this new line at the end to open and run birdcam.sh from Terminal on startup:
    @lxterminal -e bash /home/pi/pi-coral-ai-birdcam/birdcam.sh
