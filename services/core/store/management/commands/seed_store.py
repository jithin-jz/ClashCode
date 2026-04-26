from django.core.management.base import BaseCommand

from store.models import StoreItem


class Command(BaseCommand):
    help = "Seeds the store with cosmetic items."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Store Items...")

        # Clear existing items (optional)
        StoreItem.objects.all().delete()

        items = [
            # --- THEMES (8 total) ---
            {
                "name": "Dracula",
                "description": "Classic dark theme with purple accents.",
                "cost": 100,
                "icon_name": "Palette",
                "category": "THEME",
                "item_data": {
                    "theme_key": "dracula",
                    "colors": {"bg": "#282a36", "accent": "#bd93f9"},
                },
            },
            {
                "name": "Nord",
                "description": "Arctic-inspired clean and frosty theme.",
                "cost": 100,
                "icon_name": "Palette",
                "category": "THEME",
                "item_data": {
                    "theme_key": "nord",
                    "colors": {"bg": "#2e3440", "accent": "#88c0d0"},
                },
            },
            {
                "name": "Monokai",
                "description": "Vibrant and warm colors for high focus.",
                "cost": 150,
                "icon_name": "Palette",
                "category": "THEME",
                "item_data": {
                    "theme_key": "monokai",
                    "colors": {"bg": "#272822", "accent": "#f92672"},
                },
            },
            {
                "name": "Solarized Dark",
                "description": "High-precision professional dark mode.",
                "cost": 150,
                "icon_name": "Palette",
                "category": "THEME",
                "item_data": {
                    "theme_key": "solarized_dark",
                    "colors": {"bg": "#002b36", "accent": "#268bd2"},
                },
            },
            {
                "name": "Cyberpunk",
                "description": "Futuristic neon pink and cyan aesthetics.",
                "cost": 200,
                "icon_name": "Palette",
                "category": "THEME",
                "item_data": {
                    "theme_key": "cyberpunk",
                    "colors": {"bg": "#0d0d0d", "accent": "#ff007f"},
                },
            },
            # New themes
            {
                "name": "Tokyo Night",
                "description": "Clean theme inspired by Tokyo city lights.",
                "cost": 200,
                "icon_name": "Palette",
                "category": "THEME",
                "item_data": {
                    "theme_key": "tokyo_night",
                    "colors": {"bg": "#1a1b26", "accent": "#7aa2f7"},
                },
            },
            {
                "name": "One Dark Pro",
                "description": "Atom's signature dark and refined theme.",
                "cost": 150,
                "icon_name": "Palette",
                "category": "THEME",
                "item_data": {
                    "theme_key": "one_dark_pro",
                    "colors": {"bg": "#282c34", "accent": "#61afef"},
                },
            },
            {
                "name": "Gruvbox Dark",
                "description": "Retro groove scheme with warm earthy tones.",
                "cost": 175,
                "icon_name": "Palette",
                "category": "THEME",
                "item_data": {
                    "theme_key": "gruvbox_dark",
                    "colors": {"bg": "#282828", "accent": "#fe8019"},
                },
            },
            # --- FONTS (8 total) ---
            {
                "name": "Fira Code",
                "description": "Monospaced font with programming ligatures.",
                "cost": 50,
                "icon_name": "Type",
                "category": "FONT",
                "item_data": {"font_family": "Fira Code"},
            },
            {
                "name": "JetBrains Mono",
                "description": "A typeface made for developers.",
                "cost": 50,
                "icon_name": "Type",
                "category": "FONT",
                "item_data": {"font_family": "JetBrains Mono"},
            },
            {
                "name": "Comic Code",
                "description": "Comic Sans... but for coding. A fun twist!",
                "cost": 75,
                "icon_name": "Type",
                "category": "FONT",
                "item_data": {"font_family": "Comic Neue"},
            },
            {
                "name": "Cascadia Code",
                "description": "Microsoft's modern monospaced font.",
                "cost": 50,
                "icon_name": "Type",
                "category": "FONT",
                "item_data": {"font_family": "Cascadia Code"},
            },
            # New fonts
            {
                "name": "Source Code Pro",
                "description": "Adobe's clean monospaced font for code.",
                "cost": 50,
                "icon_name": "Type",
                "category": "FONT",
                "item_data": {"font_family": "Source Code Pro"},
            },
            {
                "name": "Victor Mono",
                "description": "Elegant cursive italics for a unique look.",
                "cost": 100,
                "icon_name": "Type",
                "category": "FONT",
                "item_data": {"font_family": "Victor Mono"},
            },
            {
                "name": "IBM Plex Mono",
                "description": "IBM's corporate monospace with personality.",
                "cost": 75,
                "icon_name": "Type",
                "category": "FONT",
                "item_data": {"font_family": "IBM Plex Mono"},
            },
            {
                "name": "Roboto Mono",
                "description": "Google's geometric monospaced typeface.",
                "cost": 50,
                "icon_name": "Type",
                "category": "FONT",
                "item_data": {"font_family": "Roboto Mono"},
            },
            # --- CURSOR EFFECTS (8 total) ---
            {
                "name": "Sparkle Trail",
                "description": "Leave a trail of sparkles as you type.",
                "cost": 250,
                "icon_name": "Sparkles",
                "category": "EFFECT",
                "item_data": {"effect_key": "sparkle"},
            },
            {
                "name": "Rainbow Trail",
                "description": "A colorful rainbow follows your cursor.",
                "cost": 300,
                "icon_name": "Rainbow",
                "category": "EFFECT",
                "item_data": {"effect_key": "rainbow"},
            },
            {
                "name": "Matrix Rain",
                "description": "Digital rain effect while coding.",
                "cost": 350,
                "icon_name": "Binary",
                "category": "EFFECT",
                "item_data": {"effect_key": "matrix"},
            },
            # New effects
            {
                "name": "Neon Glow",
                "description": "Your cursor glows with neon light.",
                "cost": 275,
                "icon_name": "Lightbulb",
                "category": "EFFECT",
                "item_data": {"effect_key": "neon"},
            },
            {
                "name": "Fire Trail",
                "description": "Leave blazing flames behind your cursor.",
                "cost": 400,
                "icon_name": "Flame",
                "category": "EFFECT",
                "item_data": {"effect_key": "fire"},
            },
            {
                "name": "Snow Fall",
                "description": "Gentle snowflakes follow your movements.",
                "cost": 225,
                "icon_name": "Snowflake",
                "category": "EFFECT",
                "item_data": {"effect_key": "snow"},
            },
            {
                "name": "Electric Pulse",
                "description": "Electric sparks dance around your cursor.",
                "cost": 350,
                "icon_name": "Zap",
                "category": "EFFECT",
                "item_data": {"effect_key": "electric"},
            },
            {
                "name": "Bubble Pop",
                "description": "Colorful bubbles trail behind your cursor.",
                "cost": 200,
                "icon_name": "Circle",
                "category": "EFFECT",
                "item_data": {"effect_key": "bubble"},
            },
            # --- VICTORY ANIMATIONS (8 total) ---
            {
                "name": "Confetti Burst",
                "description": "Celebrate with colorful confetti on level complete!",
                "cost": 200,
                "icon_name": "PartyPopper",
                "category": "VICTORY",
                "item_data": {"victory_key": "confetti"},
            },
            {
                "name": "Fireworks",
                "description": "A spectacular fireworks display on success.",
                "cost": 300,
                "icon_name": "Flame",
                "category": "VICTORY",
                "item_data": {"victory_key": "fireworks"},
            },
            {
                "name": "Level Up!",
                "description": "Classic RPG level-up animation with sound.",
                "cost": 250,
                "icon_name": "TrendingUp",
                "category": "VICTORY",
                "item_data": {"victory_key": "levelup"},
            },
            # New victory animations
            {
                "name": "Trophy Spin",
                "description": "A golden trophy spins triumphantly.",
                "cost": 350,
                "icon_name": "Trophy",
                "category": "VICTORY",
                "item_data": {"victory_key": "trophy"},
            },
            {
                "name": "Star Explosion",
                "description": "Stars burst across the screen in celebration.",
                "cost": 275,
                "icon_name": "Star",
                "category": "VICTORY",
                "item_data": {"victory_key": "stars"},
            },
            {
                "name": "Crown Drop",
                "description": "A royal crown descends upon completion.",
                "cost": 400,
                "icon_name": "Crown",
                "category": "VICTORY",
                "item_data": {"victory_key": "crown"},
            },
            {
                "name": "Lightning Strike",
                "description": "Electric victory with dramatic lightning.",
                "cost": 325,
                "icon_name": "Zap",
                "category": "VICTORY",
                "item_data": {"victory_key": "lightning"},
            },
            {
                "name": "Rocket Launch",
                "description": "Blast off to success with a rocket animation.",
                "cost": 300,
                "icon_name": "Rocket",
                "category": "VICTORY",
                "item_data": {"victory_key": "rocket"},
            },
        ]

        for item in items:
            StoreItem.objects.create(**item)
            self.stdout.write(f"  + {item['name']}")

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(items)} store items."))
