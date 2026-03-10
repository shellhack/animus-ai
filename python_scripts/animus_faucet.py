import asyncio
from playwright.async_api import async_playwright

async def run_faucet():
    async with async_playwright() as p:
        # 1. Lanzamos el navegador (usando tu perfil si quieres, o limpio)
        browser = await p.chromium.launch(headless=False) # Headless=False para que veas qué hace
        context = await browser.new_context()
        page = await context.new_page()

        print("🚀 ANIMUS navegando al Faucet de Berachain...")
        
        try:
            # 2. Ir a la URL del Faucet
            await page.goto("https://artio.faucet.berachain.com/", timeout=60000)
            
            # 3. Esperar a que el campo de la wallet esté listo
            # Nota: Algunos faucets tienen Captchas, aquí es donde ANIMUS "mira"
            print("⏳ Esperando carga de interfaz...")
            await page.wait_for_selector('input[placeholder*="0x"]')
            
            # 4. Pegar tu dirección
            wallet_address = "0xC4b4D9e70334D5050E07E2fAbE9D5491a159BC02"
            await page.fill('input[placeholder*="0x"]', wallet_address)
            
            print(f"✅ Dirección {wallet_address[:6]}... inyectada.")
            
            # 5. Click en el botón de goteo (Drip)
            # Aquí ajustamos el selector según la web actual
            await page.click('button:has-text("Drip")')
            
            print("💧 Solicitud enviada. Esperando confirmación de red...")
            await asyncio.sleep(10) # Pausa para que el proceso termine
            
        except Exception as e:
            print(f"❌ Error en la secuencia: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_faucet())