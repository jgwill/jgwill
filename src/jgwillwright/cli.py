import argparse
import asyncio
import os
import json
from playwright.async_api import async_playwright, TimeoutError

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
    # Ensure the parent directory exists, not just the profile path itself
    if not os.path.exists(os.path.dirname(profile_path)):
        os.makedirs(os.path.dirname(profile_path))
    
    async with async_playwright() as p:
        # Ensure we launch a persistent context into the target directory
        browser_context = await p.chromium.launch_persistent_context(profile_path, headless=False)
        page = await browser_context.new_page()
        await page.goto("https://google.com") # A neutral starting point to begin manual login

        print("*****************************************************************")
        print(f"BROWSER OPENED WITH PROFILE: {profile_path}")
        print("Please log in to all required services (Google, Vercel, etc.).")
        print("Close the browser manually when you are finished.")
        print("*****************************************************************")
        
        # Wait indefinitely until the browser context is explicitly closed by the user
        await browser_context.wait_for_event("close")
        print("Browser closed. Profile initialization complete.")


# --- Application-Specific Tasks (v0) ---
async def v0_pull_changes(context, app_config):
    page = await context.new_page()
    try:
        print(f"Navigating to {app_config['chat_url']} for git pull...")
        await page.goto(app_config['chat_url'])
        await page.get_by_role("button", name="Synced to main").wait_for(state="visible", timeout=60000)
        print("Clicking 'Synced to main' button...")
        await page.get_by_role("button", name="Synced to main").click()
        print("Clicking 'Pull Changes' button...")
        await page.get_by_role("button", name="Pull Changes").click()
        # Wait for either 'Syncing Changes' to disappear or 'Changes pulled' notification
        await page.get_by_text("Syncing Changes").wait_for(state="hidden", timeout=120000) # Longer timeout for network operations
        print("v0: Git pull changes completed successfully.")
    finally:
        await page.close()

async def v0_publish_changes(context, app_config):
    page = await context.new_page()
    try:
        print(f"Navigating to {app_config['chat_url']} for publishing...")
        await page.goto(app_config['chat_url'])
        await page.get_by_role("button", name="Publish").wait_for(state="visible", timeout=60000)
        print("Clicking 'Publish' dropdown button...")
        await page.get_by_role("button", name="Publish").click()
        await page.wait_for_timeout(1000) # Give dropdown time to render

        publish_changes_option = page.get_by_text("Publish Changes")
        update_option = page.get_by_role("button", name="Update")

        if await publish_changes_option.is_visible():
            print("'Publish Changes' option is visible. Clicking it...")
            await publish_changes_option.click()
            await page.get_by_text("Publishing...").wait_for(state="visible", timeout=60000)
            await page.get_by_text("Publishing...").wait_for(state="hidden", timeout=180000)
            print("v0: Publishing completed successfully.")
        elif await update_option.is_visible():
            print("'Update' button is visible, which means changes are already published.")
            print("v0: Publish step considered successful.")
        else:
            # Take a screenshot for debugging purposes
            await page.screenshot(path="publish_error_snapshot.png")
            raise Exception("Could not find 'Publish Changes' or 'Update' in the publish dropdown. See snapshot.")
    finally:
        await page.close()

async def view_app(context, app_config):
    page = await context.new_page()
    print(f"Opening production app at {app_config['production_url']}...")
    await page.goto(app_config['production_url'])
    print("App opened. Browser will remain open for 1 minute.")
    await page.wait_for_timeout(60000) # Keep page open for 1 minute for user to view
    await page.close()

# --- Core Asynchronous Logic (Executed by synchronous main) ---
async def async_main():
    parser = argparse.ArgumentParser(description="JGWright: A multi-app automation and deployment tool.")
    parser.add_argument("--init-project", action="store_true", help="Interactively create a new project configuration.")
    parser.add_argument("--init-profile", type=str, help="Initialize a new persistent browser profile by name.")
    parser.add_argument("--deploy", type=str, help="Deploy a specific application (e.g., 'v0').")
    parser.add_argument("--view", type=str, help="View a deployed application (e.g., 'v0').")
    parser.add_argument("--profile", type=str, help="Specify a profile to use (overrides default from config).")
    args = parser.parse_args()

    if args.init_project:
        init_project() # Synchronous call to interactive function
        return

    # All subsequent commands require a config file
    config = load_config()

    if args.init_profile:
        # Ensure the profile name from args exists in the config
        if args.init_profile not in config['profiles']:
            raise ValueError(f"Profile '{args.init_profile}' not found in wright_config.json")
        await init_profile(config['profiles'][args.init_profile])
        return

    # Determine which profile to use for deploy/view operations
    profile_name = args.profile or config['profiles'].get("default") # Use specified profile or default
    if not profile_name or profile_name not in config['profiles']:
        raise ValueError(f"Could not determine a profile to use for deployment/view. Please ensure 'default' or specified profile exists in wright_config.json.")
    profile_path = config['profiles'][profile_name]

    # Check if the profile directory actually exists before trying to use it
    if not os.path.isdir(profile_path):
        raise FileNotFoundError(f"Profile path does not exist: {profile_path}. Please run 'wright --init-profile {profile_name}' first to create and populate it.")

    async with async_playwright() as p:
        # Launch the browser with the persistent context
        browser_context = await p.chromium.launch_persistent_context(profile_path, headless=False) # Always headed for deployments/user interaction
        try:
            if args.deploy:
                app_name = args.deploy
                if app_name not in config['apps']:
                    raise ValueError(f"Application '{app_name}' not found in wright_config.json")
                app_config = config['apps'][app_name]
                
                print(f"--- Deploying {app_name} ---")
                # Extend this logic for other applications as needed
                if app_name == 'v0':
                    await v0_pull_changes(browser_context, app_config)
                    await v0_publish_changes(browser_context, app_config)
                else:
                    print(f"Deployment logic for '{app_name}' is not yet implemented.")
                print(f"--- {app_name} Deployment Finished ---")

            # If --view is specified (either alone or with --deploy)
            if args.view:
                app_name = args.view
                if app_name not in config['apps']:
                    raise ValueError(f"Application '{app_name}' not found in wright_config.json")
                await view_app(browser_context, config['apps'][app_name])

        except TimeoutError as e:
            print(f"A Playwright timeout occurred: {e}. This might mean an element was not found or a page did not load in time.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            # Ensure the browser context is always closed
            if browser_context:
                await browser_context.close()

# --- Synchronous Entry Point for Console Script ---
def main():
    """Synchronous wrapper to run the async core."""
    try:
        asyncio.run(async_main())
    except FileNotFoundError as e:
        print(f"Configuration Error: {e}")
        print("Please ensure 'wright_config.json' exists in your current directory or run 'wright --init-project'.")
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # This block is for when the script is run directly (e.g., python cli.py)
    # When run as 'wright' command, pyproject.toml points directly to def main().
    main()