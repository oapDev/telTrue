import discord
from discord.ext import commands
from discord.ui import Button, View
import aiohttp
from datetime import datetime

# ================= CONFIGURATION =================
TOKEN = 'MTQ1NjY1NDQ2NjU5Njk5OTM3MA.G6Ofhh.TZQqNP2Jcekh-xBFD0-pe8J7cVUjvGb_isP9as'
ALLOWED_CHANNEL_ID = 1456639584879247520
ADMIN_FB_URL = "https://www.facebook.com/share/14QurBkLrid/"
API_BASE_URL = "https://hitori.run/data_t/api.php?type=phone&value={phone}"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# ================= UI COMPONENTS =================

class AdminView(View):
    def __init__(self):
        super().__init__()
        self.add_item(Button(label="ติดต่อ ADMIN", url=ADMIN_FB_URL, style=discord.ButtonStyle.link, emoji="👤"))

# ================= BOT COMMANDS =================

@bot.event
async def on_ready():
    print(f'✅ บอท Full Data (Hitori API) ออนไลน์แล้ว: {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="!k [เบอร์โทร]"))

@bot.command(name='tel')
async def check_info(ctx, phone: str = None):
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        return await ctx.send(f"❌ ไม่อนุญาตให้ใช้คำสั่งในห้องนี้", delete_after=5)

    if not phone:
        return await ctx.send("❓ กรุณาระบุเบอร์โทรศัพท์ เช่น `!k 08xxxxxxxx`")

    status_msg = await ctx.send(f"🛰️ กำลังดึงข้อมูล Full Data สำหรับเบอร์ `{phone}`...")

    async with aiohttp.ClientSession() as session:
        try:
            api_url = API_BASE_URL.format(phone=phone)
            async with session.get(api_url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") != "success":
                        return await status_msg.edit(content=f"❌ ไม่พบข้อมูลเบอร์ `{phone}` ในระบบ")

                    # --- 1. ข้อมูลลูกค้า (Customer Data) ---
                    cust_resp = data.get("customer", {}).get("response-data", {})
                    addr = cust_resp.get("address-list", {}).get("CUSTOMER_ADDRESS", {})
                    
                    name = f"{cust_resp.get('title', '')}{cust_resp.get('firstname', '')} {cust_resp.get('lastname', '')}".strip()
                    cid = cust_resp.get("id-number", "-")
                    birth = cust_resp.get("birthdate", "-")[:10]
                    
                    # --- 2. ข้อมูลสินค้าและเบอร์อื่นๆ (Products Data) ---
                    prod_resp = data.get("products", {}).get("response-data", {}).get("customer", {})
                    products = prod_resp.get("installed-products", [])
                    
                    product_list_text = ""
                    current_package = "ไม่ระบุ"
                    
                    for p in products:
                        p_num = p.get("product-id-number", "-")
                        p_status = p.get("product-status", "-")
                        p_type = p.get("mobile-servicetype", "-")
                        # เก็บเบอร์ปัจจุบันเพื่อดึงชื่อแพ็กเกจ
                        if p_num == phone:
                            current_package = p.get("product-description", "ไม่ระบุ")
                        
                        status_emoji = "🟢" if p_status == "A" or p_status == "Active" else "🔴"
                        product_list_text += f"{status_emoji} `{p_num}` ({p_type})\n"

                    # --- สร้าง Embed ---
                    embed = discord.Embed(
                        title="🚀 ข้อมูลลูกค้า True Full System",
                        color=0xff0000,
                        timestamp=datetime.now()
                    )

                    embed.add_field(
                        name="👤 ข้อมูลเจ้าของบัญชี",
                        value=f"```css\n[ชื่อ]: {name}\n[เลขบัตร]: {cid}\n[วันเกิด]: {birth}\n[เพศ]: {cust_resp.get('gender', '-')}\n```",
                        inline=False
                    )

                    embed.add_field(
                        name="🏠 ที่อยู่จดทะเบียน",
                        value=f"```yaml\nที่อยู่: {addr.get('number', '-')} ม.{addr.get('moo', '-')} ต.{addr.get('sub-district', '-')} อ.{addr.get('district', '-')} จ.{addr.get('province', '-')} {addr.get('zip', '-')}\n```",
                        inline=False
                    )

                    embed.add_field(
                        name="📦 แพ็กเกจปัจจุบัน (เบอร์ที่ค้นหา)",
                        value=f"```fix\n{current_package}\n```",
                        inline=False
                    )

                    if product_list_text:
                        embed.add_field(
                            name="📱 เบอร์ทั้งหมดภายใต้ชื่อนี้",
                            value=product_list_text,
                            inline=False
                        )

                    embed.set_footer(text=f"SFF Database | ค้นหาโดย {ctx.author.name}")
                    
                    await status_msg.delete()
                    await ctx.send(embed=embed, view=AdminView())

                else:
                    await status_msg.edit(content=f"❌ API Error: {response.status}")
        
        except Exception as e:
            print(f"Error: {e}")
            await status_msg.edit(content=f"❌ เกิดข้อผิดพลาดในการประมวลผลข้อมูล")

bot.run(TOKEN)


