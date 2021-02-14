import asyncio, discord, os, random, requests
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import urllib.request as rq
import pandas as pd 

token_path = os.path.dirname(os.path.abspath(__file__))+'/Token.txt'
t=open(token_path, "r", encoding="utf-8")
token = t.read()

game = discord.Game("Primary Bot")
bot = commands.Bot(command_prefix='!', status=discord.Status.online, activity=game, help_command=None)

# For Stock Search
stock_code = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0)[0]
stock_code = stock_code[['회사명', '종목코드']]
stock_code = stock_code.rename(columns={'회사명' : 'company', '종목코드' : 'code'})
stock_code.code = stock_code.code.map('{:06d}'.format)

@bot.event
async def on_ready():
    print(f'[*] {bot.user} Starting Bot...')

@bot.event
async def on_guild_join(guild):
    print(f'[*] {bot.user} joined at {guild} [{guild.id}]')

@bot.event
async def on_guild_remove(guild):
    print(f'[*] {bot.user} removed at {guild} [{guild.owner_id}]')


@bot.command(aliases=['도움말', '도움', 'h'])
async def help(ctx):
    embed = discord.Embed(title="AlphaBot", description="Primary Bot for Discord by Omoknooni", color=0x4432a8)
    embed.set_thumbnail(url="https://picsum.photos/id/237/200/300")
    embed.set_image(url="https://picsum.photos/id/237/200/300")
    embed.add_field(name="1. 인사", value="!hello", inline=False)
    embed.add_field(name="2. 주사위", value="!roll [범위숫자]", inline=False)
    embed.add_field(name="3. 음성채널 입장/퇴장", value="!join / !leave (초대자가 입장된 상태에만 가능)", inline=False)
    embed.add_field(name="4. 음악", value="!play [Youtube URL] : 음악을 재생\n!pause : 일시정지\n!resume : 다시 재생\n!stop : 중지", inline=False)
    embed.add_field(name="5. 종목확인", value="!stock [종목명] : 네이버 증권 페이지에서 해당 종목에 대한 정보를 가져옵니다.", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_member_join(member):
    embed = discord.Embed(title = "서버에 오신 것을 환영합니다", description = "개발용", color = 0xf3bb76)
    embed.add_field(name="<1>", value="불안정한 명령어가 있습니다", inline=True)
    embed.add_field(name="<2>", value="과도한 명령어 입력은 자제해주세요", inline=True)
    await member.send(embed)

@bot.command(aliases=['안녕', 'hi', '안녕하세요'])
async def hello(ctx):
    await ctx.send(f'{ctx.author.mention}님 안녕하세요!')

@bot.command(pass_context=True)
async def play(ctx, url:str):
    song = os.path.isfile("song.mp3")
    try:
        if song:
            os.remove("song.mp3")
    except PermissionError:
        await ctx.send("음악이 아직 종료되지 않았습니다")
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    ydl_options={
        'format':'bestmusic/best',
        'postprocessors' : [{
            'key':'FFmpegExtractAudio',
            'preferredcodec':'mp3',
            'preferredquality':'192',
        }],
    }

    with YoutubeDL(ydl_options) as ydl:
        ydl.download([url])
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file,"song.mp3")
    voice.play(discord.FFmpegPCMAudio("song.mp3"))
    
@bot.command(aliases=['p'])
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("어떤 음악도 재생되고 있지 않습니다")

@bot.command(aliases=['r'])
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("음악이 멈춘 상태가 아닙니다")

@bot.command(aliases=['s'])
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice.stop()

@bot.command(aliases=['j'])
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command(aliases=['l'])
async def leave(ctx):
    await ctx.voice_client.disconnect()

@bot.command(aliases=['주사위'])
async def roll(ctx, number:int):
    await ctx.send(f'주사위를 굴려 {random.randint(1,int(number))}이(가) 나왔습니다 (1~{number})')
@roll.error
async def roll_error(ctx,error):
    await ctx.send('명령어 오류!!! 올바른 포맷에 맞게 작성해주세요')

@bot.command()
async def repeat(ctx, *, txt):
    await ctx.send(txt)

@bot.command(aliases=['종목', '확인'])
async def stock(ctx, company:str):
    url = 'https://finance.naver.com/item/main.nhn?code='
    com_code = stock_code[stock_code.company == company].code.values[0].strip()
    url = url + f'{com_code}'

    ua = UserAgent()
    headers={
        'User-agent' : ua.random,
        'render' : 'https://finance.naver.com/'
    }

    res = rq.urlopen(rq.Request(url, headers=headers)).read()
    bs_obj = BeautifulSoup(res, "html.parser")
    name = bs_obj.select_one('.wrap_company > h2 > a').text

    today = bs_obj.select_one('#chart_area > div.rate_info > div.today')
    flunc = today.select_one('.ico').text
    price = today.select('.blind')

    chart_area = bs_obj.select_one('#chart_area > .chart > img').get('src')
    close = bs_obj.select_one('#middle > .blind > dd:nth-child(2)').text
    high =  bs_obj.select_one('#middle > .blind > dd:nth-child(8)').text
    low =  bs_obj.select_one('#middle > .blind > dd:nth-child(10)').text
    amount = bs_obj.select_one('#middle > .blind > dd:nth-child(12)').text

    if flunc == '상승':
        flunc = '+'
    else:
        flunc = '-'

    print(name, end='    ')
    print(f'{price[0].text} | {flunc}{price[1].text} | {flunc}{price[2].text}%')

    embed = discord.Embed(title=f"{name}", description=f'{price[0].text} | 전일대비 {flunc}{price[1].text} | {flunc}{price[2].text}%', color=0x4432a8)
    embed.set_thumbnail(url=f'{chart_area}')
    embed.set_image(url=f'{chart_area}')
    embed.add_field(name="거래량", value=f'{amount[3:]}')
    embed.add_field(name="최고", value=f'{high[3:]}')
    embed.add_field(name="최저", value=f'{low[4:]}')
    embed.add_field(name="<해당 종목 바로가기>", value=f'{url}')
    embed.set_footer(text=f'{close}')

    await ctx.send(embed=embed)
@stock.error
async def stock_error(ctx, error):
    await ctx.send('에러가 발생했습니다. 관리자에게 문의')
    
bot.run(token)
