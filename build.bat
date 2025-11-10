@echo off

echo [1/1] Run PyInstaller...
pyinstaller --clean --name "(Junior) State Machine Visualizer (v0.4)" src\state_machine_visualizer\__main__.py --onefile --noconfirm --noconsole