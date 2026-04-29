python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --noconfirm --windowed --name ImageWatermark --add-data "assets/fonts;assets/fonts" app/main.py

Write-Host "Build done: dist/ImageWatermark/"
Write-Host "Use Inno Setup script: installer/InnoSetup.iss"
