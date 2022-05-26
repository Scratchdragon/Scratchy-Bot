echo Starting ScratchyBot v-0.8.5
pip install discord
pip install discordpy-slash
clear

echo "Message depth: "
read depth
echo "Bot? (Y/N): "
read bot
echo "Token: "
read token

python3 main.py $depth $bot $token