import discord
import asyncio
import yt_dlp
from dotenv import load_dotenv

def run_bot():
    load_dotenv()
    TOKEN = "MTI3NDUyNTYwOTc0NTE5MTAxMg.GXOBQ9.dtpwo4Kb1vpbN9WDEQqvbXlBGM-9EmTy-IPSHw"
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    voice_clients = {}
    song_queues = {}
    yt_dl_options = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(yt_dl_options)

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -filter:a "volume=0.25"'
    }

    async def play_next_song(guild_id):
        if len(song_queues[guild_id]) > 0:
            next_song = song_queues[guild_id].pop(0)
            voice_clients[guild_id].play(next_song, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(guild_id), client.loop))
        else:
            await voice_clients[guild_id].disconnect()
            del voice_clients[guild_id]

    @client.event
    async def on_ready():
        print(f'{client.user} is now jamming')

    @client.event
    async def on_message(message):
        if message.content.startswith("?play"):
            guild_id = message.guild.id

            try:
                url = message.content.split()[1]
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                song = data['url']
                player = discord.FFmpegOpusAudio(song, **ffmpeg_options)

                if guild_id in voice_clients and voice_clients[guild_id].is_playing():
                    # Add to queue if already playing
                    if guild_id not in song_queues:
                        song_queues[guild_id] = []
                    song_queues[guild_id].append(player)
                    await message.channel.send("A song is already playing. Your song has been added to the queue.")
                else:
                    # Play the song if nothing is playing
                    voice_client = await message.author.voice.channel.connect()
                    voice_clients[guild_id] = voice_client
                    voice_clients[guild_id].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(guild_id), client.loop))
            except Exception as e:
                print(e)

        if message.content.startswith("?pause"):
            try:
                voice_clients[message.guild.id].pause()
                await message.channel.send("Song paused ⏸️")
            except Exception as e:
                print(e)

        if message.content.startswith("?resume"):
            try:
                voice_clients[message.guild.id].resume()
            except Exception as e:
                print(e)


        if message.content.startswith("?skip"):
              guild_id = message.guild.id  # Define guild_id here
        try:
                voice_clients[guild_id].stop()
                await message.channel.send("Song skipped.")
                print("song skip")
        except Exception as e:
                print(e)

        if message.content.startswith("?stop"):
            try:
                voice_clients[message.guild.id].stop()
                await voice_clients[message.guild.id].disconnect()
                if guild_id in song_queues:
                    del song_queues[guild_id]
            except Exception as e:
                print(e)

    client.run(TOKEN)

if __name__ == "__main__":
    run_bot()
        