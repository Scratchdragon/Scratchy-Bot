echo Starting ScratchyBot v-0.8.5
pip install discord
pip install discordpy-slash
clear
python3 main.py
if [ "$restartbot" == "true" ]
then
	./main.sh
fi