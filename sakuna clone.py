from telethon import TelegramClient, events
from telethon.tl import functions
from telethon.errors.rpcerrorlist import PhotoCropSizeSmallError, UserPrivacyRestrictedError
import os
from PIL import Image
from termcolor import colored
import time
import sys
import itertools
import threading

def print_rainbow_text(text):
    colors = ["red", "yellow", "green", "cyan", "blue", "magenta"]
    for _ in range(3):  # Repeat to make text appear bigger
        for i, char in enumerate(text):
            sys.stdout.write(colored(char.upper() + " ", colors[i % len(colors)]))
            sys.stdout.flush()
            time.sleep(0.05)
        print("\n")

# Display the banner in RGB changing colors
print_rainbow_text("SAKUNA CLONE BOT")

# Replace with your own API credentials
API_ID = "your_api_id"
API_HASH = "your_api_hash"
SESSION_NAME = "userbot"

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Storage for original and cloned details
original_details = {}
cloned_details = {}

async def save_original_profile():
    """Save the original profile details."""
    global original_details
    me = await client.get_me()
    
    if not original_details:
        user_full = await client(functions.users.GetFullUserRequest(me.id))
        original_details = {
            "name": me.first_name,
            "last_name": me.last_name,
            "bio": getattr(user_full.full_user, "about", ""),
            "pfp": await client.download_profile_photo("me", file="original_pfp.jpg")  # Save as JPEG
        }

@client.on(events.NewMessage(pattern="/clone"))
async def clone(event):
    """Clone a user's profile."""
    await save_original_profile()  # Save original profile if not already saved
    
    try:
        reply = await event.get_reply_message()
        args = event.text.split()
        
        if reply:
            user = await client.get_entity(reply.sender_id)
        elif len(args) > 1:
            user = await client.get_entity(args[1])
        else:
            await event.reply("Reply to a user or provide an ID/username.")
            return
        
        # Save cloned details
        user_full = await client(functions.users.GetFullUserRequest(user.id))
        cloned_details.update({
            "name": user.first_name or "",
            "last_name": user.last_name or "",
            "bio": getattr(user_full.full_user, "about", ""),
            "pfp": await client.download_profile_photo(user.id, file="cloned_pfp.jpg")  # Save as JPEG
        })
        
        # Update name and bio
        await client(functions.account.UpdateProfileRequest(
            first_name=cloned_details["name"],
            last_name=cloned_details["last_name"],
            about=cloned_details["bio"]
        ))
        
        # Update profile picture
        if cloned_details["pfp"]:
            await client(functions.photos.UploadProfilePhotoRequest(
                file=await client.upload_file("cloned_pfp.jpg")
            ))
        else:
            await event.reply("User has no profile picture to clone.")
        
        await event.reply(f"Cloned {user.first_name}'s profile!")
    except Exception as e:
        await event.reply(f"Failed to clone profile. Error: {str(e)}")

@client.on(events.NewMessage(pattern="/ditto"))
async def ditto(event):
    """Reapply the last cloned profile."""
    if not cloned_details:
        await event.reply("No cloned profile found. Use /clone first.")
        return
    
    try:
        await event.reply("Reapplying last cloned profile...")
        await client(functions.account.UpdateProfileRequest(
            first_name=cloned_details["name"],
            last_name=cloned_details["last_name"],
            about=cloned_details["bio"]
        ))
        
        if cloned_details["pfp"]:
            await client(functions.photos.UploadProfilePhotoRequest(
                file=await client.upload_file("cloned_pfp.jpg")
            ))
        await event.reply("Profile successfully reapplied!")
    except Exception as e:
        await event.reply(f"Error reapplying profile: {str(e)}")

@client.on(events.NewMessage(pattern="/revert"))
async def revert(event):
    """Revert back to the original profile."""
    global original_details
    
    if not original_details:
        await event.reply("No original profile stored. Can't revert.")
        return
    
    try:
        # Restore name and bio
        await client(functions.account.UpdateProfileRequest(
            first_name=original_details["name"],
            last_name=original_details["last_name"],
            about=original_details["bio"]
        ))
        
        # Restore profile picture
        if original_details["pfp"]:
            await client(functions.photos.UploadProfilePhotoRequest(
                file=await client.upload_file("original_pfp.jpg")
            ))
        else:
            # Delete cloned profile picture
            photos = await client.get_profile_photos("me", limit=1)
            if photos:
                await client(functions.photos.DeletePhotosRequest(photos))
        
        await event.reply("Profile reverted to original!")
        original_details = {}  # Clear original details after reverting
    except Exception as e:
        await event.reply(f"Error reverting profile: {str(e)}")

print("Userbot started...")
client.start()
client.run_until_disconnected()
