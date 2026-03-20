import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import uuid
import re
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# ─── Konfiguration aus .env ───────────────────────────────────────────────────
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
_guild_id = os.getenv("DISCORD_GUILD_ID", "").strip()
GUILD_ID  = int(_guild_id) if _guild_id else None

# ─── Pfade ────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
NEWS_FILE      = os.path.join(BASE_DIR,  "news.json")
NEWS_FILES_DIR = os.path.join(BASE_DIR,  "news_files")
CONFIG_FILE    = os.path.join(BASE_DIR, "config.json")

# ─── Bot Setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
bot     = commands.Bot(command_prefix="!", intents=intents)
tree    = bot.tree


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def has_staff_permission(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    cfg = load_config()
    staff_role_ids = cfg.get("staff_role_ids", [])
    if not staff_role_ids:
        return False
    user_role_ids = [r.id for r in interaction.user.roles]
    return any(rid in user_role_ids for rid in staff_role_ids)


# ══════════════════════════════════════════════════════════════════════════════
# NEWS HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def load_news() -> list:
    if not os.path.exists(NEWS_FILE):
        return []
    with open(NEWS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_news(news_list: list):
    os.makedirs(os.path.dirname(NEWS_FILE), exist_ok=True)
    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)


def get_news_files() -> list[str]:
    if not os.path.exists(NEWS_FILES_DIR):
        return []
    return [
        f for f in os.listdir(NEWS_FILES_DIR)
        if os.path.isfile(os.path.join(NEWS_FILES_DIR, f))
    ]


def title_to_id(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[äÄ]", "ae", slug)
    slug = re.sub(r"[öÖ]", "oe", slug)
    slug = re.sub(r"[üÜ]", "ue", slug)
    slug = re.sub(r"ß",    "ss", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    existing_ids = {n["id"] for n in load_news()}
    if slug in existing_ids:
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
    return slug


TYPE_COLORS = {
    "update":    0xFF9800,
    "changelog": 0x2196F3,
    "event":     0x8E24AA,
    "info":      0x00897B,
    "alert":     0xE53935,
}
TYPE_LABELS = {
    "update":    "🔄 Update",
    "changelog": "📋 Changelog",
    "event":     "🎉 Event",
    "info":      "ℹ️ Info",
    "alert":     "⚠️ Warnung",
}
TYPE_EMOJIS = {
    "update":    "🔄",
    "changelog": "📋",
    "event":     "🎉",
    "info":      "ℹ️",
    "alert":     "⚠️",
}


# ══════════════════════════════════════════════════════════════════════════════
# SETUP VIEW  –  interaktive Konfigurationsmaske
# ══════════════════════════════════════════════════════════════════════════════

class SetupView(discord.ui.View):
    """
    Drei Selects untereinander:
      1. Channel-Select  → welcher Kanal bekommt die News?
      2. Role-Select     → welche Rollen werden gepingt?
      3. Role-Select     → welche Rollen dürfen /news benutzen?
    + Speichern-Button
    """

    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=300)  # 5 Minuten

        # Aktuelle Werte aus config.json vorausfüllen
        cfg = load_config()

        # ── 1. News-Kanal ─────────────────────────────────────────────────────
        self.channel_select = discord.ui.ChannelSelect(
            placeholder="📢 News-Kanal auswählen…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )
        self.channel_select.callback = self._channel_cb
        self.add_item(self.channel_select)

        # ── 2. Ping-Rollen ────────────────────────────────────────────────────
        self.ping_select = discord.ui.RoleSelect(
            placeholder="🔔 Ping-Rollen auswählen (mehrere möglich)…",
            min_values=0,
            max_values=25,
            row=1,
        )
        self.ping_select.callback = self._ping_cb
        self.add_item(self.ping_select)

        # ── 3. Staff-Rollen ───────────────────────────────────────────────────
        self.staff_select = discord.ui.RoleSelect(
            placeholder="🛡️ Staff-Rollen auswählen (mehrere möglich)…",
            min_values=1,
            max_values=25,
            row=2,
        )
        self.staff_select.callback = self._staff_cb
        self.add_item(self.staff_select)

        # ── Speichern-Button ──────────────────────────────────────────────────
        save_btn = discord.ui.Button(
            label="💾  Speichern",
            style=discord.ButtonStyle.success,
            row=3,
        )
        save_btn.callback = self._save_cb
        self.add_item(save_btn)

        # Zwischenspeicher für ausgewählte Werte
        self._channel_id:     int | None = None
        self._ping_role_ids:  list[int]  = []
        self._staff_role_ids: list[int]  = []

        # Vorausfüllen aus bestehender config
        if cfg.get("news_channel_id"):
            self._channel_id = cfg["news_channel_id"]
        if cfg.get("ping_role_ids"):
            self._ping_role_ids = cfg["ping_role_ids"]
        if cfg.get("staff_role_ids"):
            self._staff_role_ids = cfg["staff_role_ids"]

    # ── Callbacks (speichern nur intern, kein eigenes followup) ───────────────

    async def _channel_cb(self, interaction: discord.Interaction):
        self._channel_id = self.channel_select.values[0].id
        await interaction.response.defer()

    async def _ping_cb(self, interaction: discord.Interaction):
        self._ping_role_ids = [r.id for r in self.ping_select.values]
        await interaction.response.defer()

    async def _staff_cb(self, interaction: discord.Interaction):
        self._staff_role_ids = [r.id for r in self.staff_select.values]
        await interaction.response.defer()

    # ── Speichern ─────────────────────────────────────────────────────────────

    async def _save_cb(self, interaction: discord.Interaction):
        # Pflichtfeld: Kanal muss gewählt sein
        if not self._channel_id:
            await interaction.response.send_message(
                "❌ Bitte zuerst einen **News-Kanal** auswählen!", ephemeral=True
            )
            return
        # Pflichtfeld: mindestens eine Staff-Rolle
        if not self._staff_role_ids:
            await interaction.response.send_message(
                "❌ Bitte mindestens eine **Staff-Rolle** auswählen!", ephemeral=True
            )
            return

        cfg = load_config()
        cfg["news_channel_id"] = self._channel_id
        cfg["ping_role_ids"]   = self._ping_role_ids
        cfg["staff_role_ids"]  = self._staff_role_ids
        save_config(cfg)

        guild = interaction.guild

        def role_names(ids: list[int]) -> str:
            names = [
                (guild.get_role(rid).mention if guild.get_role(rid) else f"`ID:{rid}`")
                for rid in ids
            ]
            return ", ".join(names) if names else "–"

        channel = guild.get_channel(self._channel_id)

        embed = discord.Embed(
            title="✅ Setup gespeichert!",
            color=0x1E90FF,
        )
        embed.add_field(name="📢 News-Kanal",   value=channel.mention if channel else f"ID:{self._channel_id}", inline=False)
        embed.add_field(name="🔔 Ping-Rollen",  value=role_names(self._ping_role_ids),  inline=False)
        embed.add_field(name="🛡️ Staff-Rollen", value=role_names(self._staff_role_ids), inline=False)
        embed.set_footer(text=f"Gespeichert von {interaction.user.display_name}")

        # View deaktivieren damit man nicht nochmal drückt
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)
        print(f"[Setup] Konfiguration gespeichert von {interaction.user}.")

    async def on_timeout(self):
        # Alle Komponenten deaktivieren wenn der Timeout abläuft
        for item in self.children:
            item.disabled = True


# ══════════════════════════════════════════════════════════════════════════════
# /setup
# ══════════════════════════════════════════════════════════════════════════════

@tree.command(name="setup", description="[Admin] Konfiguriert News-Kanal, Ping-Rollen und Staff-Rollen.")
async def setup_command(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Nur Server-Administratoren können `/setup` ausführen.", ephemeral=True
        )
        return

    cfg = load_config()

    # Info-Embed über dem Formular
    embed = discord.Embed(
        title="⚙️ SaMaCraft Bot – Setup",
        description=(
            "Wähle unten den **News-Kanal**, die **Ping-Rollen** und die **Staff-Rollen** aus "
            "und klicke dann auf **💾 Speichern**.\n\n"
            "**News-Kanal** → Hier werden neue News automatisch gepostet.\n"
            "**Ping-Rollen** → Diese Rollen werden bei jeder neuen News gepingt.\n"
            "**Staff-Rollen** → Diese Rollen dürfen `/news` benutzen."
        ),
        color=0x1E90FF,
    )

    # Aktuelle Konfiguration anzeigen falls vorhanden
    if cfg:
        guild = interaction.guild
        channel = guild.get_channel(cfg.get("news_channel_id", 0))

        def rnames(ids):
            return ", ".join(
                r.mention for rid in ids
                if (r := guild.get_role(rid))
            ) or "–"

        embed.add_field(name="Aktuelle Einstellungen", value=(
            f"📢 Kanal: {channel.mention if channel else '–'}\n"
            f"🔔 Pings: {rnames(cfg.get('ping_role_ids', []))}\n"
            f"🛡️ Staff: {rnames(cfg.get('staff_role_ids', []))}"
        ), inline=False)

    view = SetupView(interaction.guild)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ══════════════════════════════════════════════════════════════════════════════
# /setup-info
# ══════════════════════════════════════════════════════════════════════════════

@tree.command(name="setup-info", description="[Admin] Zeigt die aktuelle Bot-Konfiguration.")
async def setup_info_command(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Nur Administratoren.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    cfg   = load_config()
    guild = interaction.guild

    def role_names(ids):
        return ", ".join(
            r.mention for rid in ids if (r := guild.get_role(rid))
        ) or "–"

    channel_id = cfg.get("news_channel_id")
    channel    = guild.get_channel(channel_id) if channel_id else None

    embed = discord.Embed(title="⚙️ Aktuelle Konfiguration", color=0x1E90FF)
    embed.add_field(name="📢 News-Kanal",   value=channel.mention if channel else "nicht gesetzt", inline=False)
    embed.add_field(name="🔔 Ping-Rollen",  value=role_names(cfg.get("ping_role_ids",  [])), inline=False)
    embed.add_field(name="🛡️ Staff-Rollen", value=role_names(cfg.get("staff_role_ids", [])), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)


# ══════════════════════════════════════════════════════════════════════════════
# AUTOCOMPLETE
# ══════════════════════════════════════════════════════════════════════════════

async def autocomplete_download(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    choices = [app_commands.Choice(name="❌ Kein Download", value="false")]
    for filename in get_news_files():
        if current.lower() in filename.lower():
            choices.append(app_commands.Choice(name=f"📎 {filename}", value=filename))
    return choices[:25]


async def autocomplete_news_id(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    choices = []
    for item in load_news():
        if current.lower() in item["id"].lower() or current.lower() in item["title"].lower():
            choices.append(app_commands.Choice(
                name=f"{item['title']} ({item['date']})",
                value=item["id"],
            ))
    return choices[:25]


# ══════════════════════════════════════════════════════════════════════════════
# /news
# ══════════════════════════════════════════════════════════════════════════════

@tree.command(name="news", description="Fügt eine neue News zur SaMaCraft-Website hinzu.")
@app_commands.describe(
    title       = "Titel der News",
    description = "Inhalt / Beschreibung der News",
    type        = "Art der News",
    download    = "Datei aus dem news_files-Ordner oder 'Kein Download'",
)
@app_commands.choices(type=[
    app_commands.Choice(name="🔄 Update",    value="update"),
    app_commands.Choice(name="📋 Changelog", value="changelog"),
    app_commands.Choice(name="🎉 Event",     value="event"),
    app_commands.Choice(name="ℹ️  Info",      value="info"),
    app_commands.Choice(name="⚠️  Warnung",   value="alert"),
])
@app_commands.autocomplete(download=autocomplete_download)
async def news_command(
    interaction: discord.Interaction,
    title:       str,
    description: str,
    type:        str,
    download:    str = "false",
):
    if not has_staff_permission(interaction):
        await interaction.response.send_message(
            "❌ Du hast keine Berechtigung für diesen Command.\n"
            "Bitte einen Administrator, dich als Staff einzutragen (`/setup`).",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    download_obj = None
    if download.lower() != "false":
        if not os.path.exists(os.path.join(NEWS_FILES_DIR, download)):
            await interaction.followup.send(
                f"❌ Datei **{download}** nicht im `news_files`-Ordner gefunden!\n"
                "Bitte zuerst dort ablegen.",
                ephemeral=True,
            )
            return
        download_obj = {"label": f"{title} herunterladen", "file": download}

    news_id   = title_to_id(title)
    today     = date.today().isoformat()
    new_entry = {
        "id":       news_id,
        "type":     type,
        "title":    title,
        "date":     today,
        "content":  description,
        "download": download_obj,
    }
    news_list = load_news()
    news_list.insert(0, new_entry)
    save_news(news_list)

    color = TYPE_COLORS.get(type, 0x888888)
    label = TYPE_LABELS.get(type, type)

    # Bestätigung (ephemeral)
    confirm_embed = discord.Embed(title=f"✅ News erstellt: {title}", color=color)
    confirm_embed.add_field(name="Typ",   value=label,          inline=True)
    confirm_embed.add_field(name="ID",    value=f"`{news_id}`", inline=True)
    confirm_embed.add_field(name="Datum", value=today,           inline=True)
    confirm_embed.add_field(
        name="Inhalt",
        value=description[:500] + ("…" if len(description) > 500 else ""),
        inline=False,
    )
    confirm_embed.add_field(
        name="📎 Download",
        value=download if download != "false" else "Keiner",
        inline=False,
    )
    confirm_embed.set_footer(text=f"Erstellt von {interaction.user.display_name}")
    await interaction.followup.send(embed=confirm_embed, ephemeral=True)

    # News in konfigurierten Kanal posten
    cfg        = load_config()
    channel_id = cfg.get("news_channel_id")
    if not channel_id:
        print("[News] Kein News-Kanal konfiguriert – nicht gepostet.")
        return

    channel = interaction.guild.get_channel(channel_id)
    if not channel:
        print(f"[News] Kanal {channel_id} nicht gefunden.")
        return

    ping_mentions = " ".join(
        f"<@&{rid}>" for rid in cfg.get("ping_role_ids", [])
    ) or None

    news_embed = discord.Embed(
        title=f"{TYPE_EMOJIS.get(type, '📰')} {title}",
        description=description,
        color=color,
    )
    news_embed.add_field(name="Typ",   value=label, inline=True)
    news_embed.add_field(name="Datum", value=today,  inline=True)
    if download_obj:
        news_embed.add_field(
            name="📎 Download",
            value=f"Auf der Website verfügbar: **{download_obj['file']}**",
            inline=False,
        )
    news_embed.set_footer(
        text=f"Veröffentlicht von {interaction.user.display_name} • SaMaCraft"
    )

    await channel.send(content=ping_mentions, embed=news_embed)
    print(f"[News] '{title}' ({type}) von {interaction.user} gepostet in #{channel.name}.")


# ══════════════════════════════════════════════════════════════════════════════
# /news-list
# ══════════════════════════════════════════════════════════════════════════════

@tree.command(name="news-list", description="Zeigt alle aktuellen News-Einträge.")
async def news_list_command(interaction: discord.Interaction):
    if not has_staff_permission(interaction):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    news_list = load_news()

    if not news_list:
        await interaction.followup.send("📭 Keine News vorhanden.", ephemeral=True)
        return

    embed = discord.Embed(title="📰 SaMaCraft – Alle News", color=0x1E90FF)
    for item in news_list[:15]:
        label = TYPE_LABELS.get(item["type"], item["type"])
        short = item["content"][:80] + "…" if len(item["content"]) > 80 else item["content"]
        dl    = f" | 📎 `{item['download']['file']}`" if item.get("download") else ""
        embed.add_field(
            name=f"{label} – {item['title']} ({item['date']})",
            value=f"`{item['id']}`{dl}\n{short}",
            inline=False,
        )
    if len(news_list) > 15:
        embed.set_footer(text=f"Zeige 15 von {len(news_list)} Einträgen.")

    await interaction.followup.send(embed=embed, ephemeral=True)


# ══════════════════════════════════════════════════════════════════════════════
# /news-delete
# ══════════════════════════════════════════════════════════════════════════════

@tree.command(name="news-delete", description="Löscht einen News-Eintrag.")
@app_commands.describe(news_id="ID des zu löschenden Eintrags")
@app_commands.autocomplete(news_id=autocomplete_news_id)
async def news_delete_command(interaction: discord.Interaction, news_id: str):
    if not has_staff_permission(interaction):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    news_list = load_news()
    new_list  = [n for n in news_list if n["id"] != news_id]

    if len(new_list) == len(news_list):
        await interaction.followup.send(f"❌ Kein Eintrag mit ID `{news_id}` gefunden.", ephemeral=True)
        return

    save_news(new_list)
    await interaction.followup.send(f"🗑️ News `{news_id}` erfolgreich gelöscht.", ephemeral=True)
    print(f"[News] '{news_id}' von {interaction.user} gelöscht.")


# ══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ══════════════════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"✅ Bot eingeloggt als {bot.user} ({bot.user.id})")
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
        print(f"✅ Commands für Guild {GUILD_ID} synchronisiert.")
    else:
        await tree.sync()
        print("✅ Commands global synchronisiert (kann bis zu 1h dauern).")


# ─── Nur direkt starten falls nicht über start.py ─────────────────────────────
if __name__ == "__main__":
    if not BOT_TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN fehlt in der .env Datei!")
    bot.run(BOT_TOKEN)