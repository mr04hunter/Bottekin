from typing import TYPE_CHECKING
import discord
from PIL import Image, ImageDraw, ImageFont,ImageEnhance, ImageText
from io import BytesIO
import numpy as np
from bot.logging import get_logger
import asyncio

if TYPE_CHECKING:
    from bot.integrations.http.client import AioHttpClient

logger = get_logger("quote_image_generator")

IMAGE_HEIGHT = 1080
IMAGE_WIDTH = 1920


class QuoteService:
    def __init__(self, client:"AioHttpClient") -> None:
        self.client = client


    def wrap_words(self,text, font, max_width):
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            if font.getbbox(word)[2] > max_width:

                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = []
                chunk = ''
                for char in word:
                    test = chunk + char
                    if font.getbbox(test)[2] <= max_width:
                        chunk = test
                    else:
                        lines.append(chunk)
                        chunk = char
                if chunk:
                    current_line = [chunk]
            else:
                test_line = ' '.join(current_line + [word])
                if font.getbbox(test_line)[2] <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _get_font_size(self, text:str, max_width:int, max_height:int, font_path:str):
        low, high = 1, 150

        best_fit_font = ImageFont.load_default()
        best_fit_text = text
        while low <= high:
            mid = (low+high)//2
            font = ImageFont.truetype(font_path, mid)
            font.getbbox(text="q")[3]

            lines = self.wrap_words(text=text, font=font, max_width=max_width)

            line_height = font.getbbox("q")[3]
            total_height = line_height * len(lines)

            if total_height<=max_height:
                best_fit_font=font
                best_fit_text = "\n".join(lines)
                low = mid + 1

            else:
                high = mid -1

        return best_fit_text, best_fit_font




                
    async def create_quote(self, text, display_name, avatar_url) -> discord.File:
        content = await self.client.fetch_avatar_image_data(avatar_url)
        file = await asyncio.to_thread(self._create_quote_sync, text, display_name, content)
        return file

            
    def _create_img(self, img: Image.Image) -> Image.Image:
        gradient_width = 300
        gradient_start = IMAGE_HEIGHT - 300 

        gradient_array = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 4), dtype=np.uint8)

        for x in range(IMAGE_WIDTH):
            if x < gradient_start:
                alpha = 0
            else:
                progress = min((x - gradient_start) / gradient_width, 1.0)
                alpha = int(progress * 255)

            gradient_array[:, x] = [20, 20, 20, alpha]

        gradient = Image.fromarray(gradient_array, 'RGBA')
        img = Image.alpha_composite(img, gradient)

        return img

    def _create_quote_sync(self, text, display_name, content) -> discord.File:
        avatar = Image.open(BytesIO(content)).convert('RGBA')
        
 
        avatar = avatar.convert('L')  
        avatar = avatar.convert('RGBA')
        
        enhancer = ImageEnhance.Brightness(avatar)
        avatar = enhancer.enhance(0.4) 
        

        img = Image.new('RGBA', (IMAGE_WIDTH, IMAGE_HEIGHT), color=(20, 20, 20, 255)) 
        

        avatar = avatar.resize((IMAGE_HEIGHT, IMAGE_HEIGHT))  
        img.paste(avatar, (0, 0), avatar)

        img = self._create_img(img=img)
        
        draw = ImageDraw.Draw(img)
    
        
        text_x = 1080
        text_y = 200

        fit_text, fit_font = self._get_font_size(text=text, max_width=800, max_height=600, font_path="montserrat.ttf")


        fit_author_text, fit_author_font = self._get_font_size(text=f"— {display_name}", max_width=600, max_height=50, font_path="montserrat_italic.ttf")
        
        text_on_image = ImageText.Text(text=fit_text, font=fit_font)
        text_bottom = text_on_image.get_bbox()[3]
   
        draw.text((text_x - 50, 100), '“', fill=(200, 200, 200), font=fit_font)
        

        draw.text((text_x,  text_y), text_on_image, fill=(255, 255, 255))
        
    

        author_text_image = ImageText.Text(text=fit_author_text, font=fit_author_font)
        draw.text((text_x, text_bottom+text_y+100), author_text_image, fill=(200, 200, 200))
        


        watermark_font = ImageFont.truetype("DejaVuSans.ttf",20)
        watermark_text = "made with BotTekin"
        watermark_bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
        watermark_width = watermark_bbox[2] - watermark_bbox[0]
        watermark_x = IMAGE_WIDTH - watermark_width - 15 
        watermark_y = IMAGE_HEIGHT - 25  

        draw.text((watermark_x, watermark_y), watermark_text, fill=(100, 100, 100, 200), font=watermark_font)
        


        img_bytes = BytesIO()

        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        
        return discord.File(img_bytes, "quote.png", spoiler=False, description="some description")

