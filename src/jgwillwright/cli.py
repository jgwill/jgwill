import argparse
import asyncio
import os
import json
from playwright.async_api import async_playwright

# --- Configuration Loading ---
def get_config_path():
    return os.path.join(os.getcwd(), "wright_config.json")

def load_config():
    path = get_config_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found. Run 'wright --init-project' to create one.")
    with open(path, 'r') as f:
        return json.load(f)

# --- Interactive Project Initialization ---
def init_project():
    """Interactively creates a new wright_config.json file."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        overwrite = input(f"Warning: {config_path} already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Initialization cancelled.")
            return

    print("--- Initializing New Project ---")
    project_name = input("Enter a short name for this application (e.g., v0): ")
    chat_url = input(f"Enter the Chat URL for '{project_name}': ")
    prod_url = input(f"Enter the Production URL for '{project_name}': ")
    
    default_profile_name = os.path.basename(os.getcwd()).lower()
    profile_name = input(f"Enter a name for the browser profile [{default_profile_name}]: ") or default_profile_name
    
    default_profile_path = os.path.expanduser(f"~/.config/jgwillwright/profiles/{profile_name}")
    profile_path = input(f"Enter the full path for the profile [{default_profile_path}]: ") or default_profile_path

    config = {
        "profiles": {
            "default": profile_name,
            profile_name: profile_path
        },
        "apps": {
            project_name: {
                "chat_url": chat_url,
                "production_url": prod_url
            }
        }
    }

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    print("\nConfiguration saved to wright_config.json!")
    print(f"Next step: Initialize the browser profile by running: wright --init-profile {profile_name}")

# --- Profile and Context Management ---
async def init_profile(profile_path):
    """Initializes a new persistent profile by launching a browser for manual login."""
    print(f"Initializing new profile at: {profile_path}")
    if not os.path.exists(os.path.dirname(profile_path)):
        os.makedirs(os.path.dirname(profile_path))
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(profile_path, headless=False)
        page = await context.new_page()
        await page.goto("https://google.com") # A neutral starting point

        print("*****************************************************************")
        print(f"BROWSER OPENED WITH PROFILE: {profile_path}")
        print("Please log in to all required services (Google, Vercel, etc.).")
        print("Close the browser manually when you are finished.")
        print("*****************************************************************")
        
        await context.wait_for_event("close")
        print("Browser closed. Profile initialization complete.")

# --- Application-Specific Tasks (v0) ---
async def v0_pull_changes(context, app_config):
    page = await context.new_page()
    try:
        print(f"Navigating to {app_config['chat_url']} for git pull...")
        await page.goto(app_config['chat_url'])
        await page.get_by_role("button", name="Synced to main").wait_for(state="visible", timeout=60000)
        await page.get_by_role("button", name="Synced to main").click()
        await page.get_by_role("button", name="Pull Changes").click()
        await page.get_by_text("Syncing Changes").wait_for(state="hidden", timeout=120000)
        print("v0: Git pull changes completed successfully.")
    finally:
        await page.close()

async def v0_publish_changes(context, app_config):
    page = await context.new_page()
    try:
        print(f"Navigating to {app_config['chat_url']} for publishing...")
        await page.goto(app_config['chat_url'])
        await page.get_by_role("button", name="Publish").wait_for(state="visible", timeout=60000)
        await page.get_by_role("button", name="Publish").click()
        await page.wait_for_timeout(1000)

        if await page.get_by_text("Publish Changes").is_visible():
            await page.get_by_text("Publish Changes").click()
            await page.get_by_text("Publishing...").wait_for(state="visible", timeout=60000)
            await page.get_by_text("Publishing...").wait_for(state="hidden", timeout=180000)
            print("v0: Publishing completed successfully.")
        elif await page.get_by_role("button", name="Update").is_visible():
            print("v0: 'Update' button is visible, changes are already published.")
        else:
            raise Exception("Could not find 'Publish Changes' or 'Update' option.")
    finally:
        await page.close()

async def view_app(context, app_config):
    page = await context.new_page()
    print(f"Opening {app_config['production_url']}...")
    await page.goto(app_config['production_url'])
    await page.wait_for_timeout(60000)
    await page.close()

# --- Main Execution Logic ---
async def main():
    parser = argparse.ArgumentParser(description="JGWright: A multi-app automation and deployment tool.")
    parser.add_argument("--init-project", action="store_true", help="Interactively create a new project configuration.")
    parser.add_argument("--init-profile", type=str, help="Initialize a new persistent browser profile by name.")
    parser.add_argument("--deploy", type=str, help="Deploy a specific application (e.g., 'v0').")
    parser.add_argument("--view", type=str, help="View a deployed application (e.g., 'v0').")
    parser.add_argument("--profile", type=str, help="Specify a profile to use (overrides default from config).")
    args = parser.parse_args()

    if args.init_project:
        init_project()
        return

    config = load_config()

    if args.init_profile:
        if args.init_profile not in config['profiles']:
            raise ValueError(f"Profile '{args.init_profile}' not found in wright_config.json")
        await init_profile(config['profiles'][args.init_profile])
        return

    profile_name = args.profile or config['profiles'].get("default")
    if not profile_name or profile_name not in config['profiles']:
        raise ValueError(f"Could not determine a profile to use. Check your wright_config.json.")
    profile_path = config['profiles'][profile_name]

    if not os.path.isdir(profile_path):
        raise FileNotFoundError(f"Profile path does not exist: {profile_path}. Run 'wright --init-profile {profile_name}' first.")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(profile_path, headless=False)
        try:
            if args.deploy:
                app_name = args.deploy
                if app_name not in config['apps']:
                    raise ValueError(f"Application '{app_name}' not found in wright_config.json")
                app_config = config['apps'][app_name]
                
                print(f"--- Deploying {app_name} ---")
                await v0_pull_changes(context, app_config)
                await v0_publish_changes(context, app_config)
                print(f"--- {app_name} Deployment Finished ---")

            if args.view:
                app_name = args.view
                if app_name not in config['apps']:
                    raise ValueError(f"Application '{app_name}' not found in wright_config.json")
                await view_app(context, config['apps'][app_name])

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(main())
