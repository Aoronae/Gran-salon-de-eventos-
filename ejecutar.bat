@echo off
title Gestor de Eventos - Flet
echo Preparate para el mejor programa del mundo
echo       Iniciando Sistema Gestor de Eventos
echo 		Increible
echo Instalando dependencias necesarias...
py -m pip install -r requirements.txt
if errorlevel 1 (
    python -m pip install -r requirements.txt
)
echo.
echo Ahora si va a iniciar
echo Ya casi....
echo El mejor programa 
echo Profe ponganos diez 
py main.py
if errorlevel 1 (
    python main.py
)
pause
