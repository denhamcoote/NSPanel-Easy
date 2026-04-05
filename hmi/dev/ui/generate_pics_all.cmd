bash ../scripts/generate_images.sh pics/0.png eu
if errorlevel 1 timeout /t 10
bash ../scripts/generate_images.sh pics/0-portrait.png us
if errorlevel 1 timeout /t 10
bash ../scripts/generate_images.sh pics/0-white.png eu-white
if errorlevel 1 timeout /t 10
bash ../scripts/generate_images.sh pics/0-portrait-white.png us-white
if errorlevel 1 timeout /t 10
 
timeout /t 30


