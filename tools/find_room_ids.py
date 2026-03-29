"""Find your Roborock Q7 room IDs.

This tool connects to your Roborock account, finds Q7 devices,
and monitors the `recommend.room_ids` property while you start
room cleaning from the Roborock app.

Usage:
    1. pip install python-roborock
    2. python find_room_ids.py
    3. Log in with your Roborock email + verification code
    4. Start a room clean from the Roborock app
    5. The tool will show the room ID(s) being cleaned
    6. Press Ctrl+C to stop

Your login is cached in ~/.cache/roborock-user-params.pkl
so you only need to enter it once.
"""

import asyncio
import pathlib

from roborock.devices.device_manager import UserParams, create_device_manager
from roborock.devices.file_cache import load_value, store_value
from roborock.roborock_message import RoborockB01Props
from roborock.web_api import RoborockApiClient

USER_PARAMS_PATH = pathlib.Path.home() / ".cache" / "roborock-user-params.pkl"


async def login_flow() -> UserParams:
    username = input("Email: ")
    web_api = RoborockApiClient(username=username)
    print("Sending login code to your email...")
    await web_api.request_code()
    code = input("Code: ")
    user_data = await web_api.code_login(code)
    base_url = await web_api.base_url
    return UserParams(username=username, user_data=user_data, base_url=base_url)


async def get_or_create_session() -> UserParams:
    try:
        user_params = await load_value(USER_PARAMS_PATH)
    except Exception:
        user_params = None
    if user_params is None:
        print("No cached login found.\n")
        user_params = await login_flow()
        await store_value(USER_PARAMS_PATH, user_params)
        print(f"Login cached to {USER_PARAMS_PATH}\n")
    return user_params


async def main():
    user_params = await get_or_create_session()

    device_manager = await create_device_manager(user_params)
    try:
        devices = await device_manager.get_devices()

        q7_devices = [d for d in devices if d.b01_q7_properties is not None]

        if not q7_devices:
            print("No Q7 devices found!")
            return

        for device in q7_devices:
            q7 = device.b01_q7_properties
            print(f"--- {device._name} ---")

            props = await q7.query_values([
                RoborockB01Props.STATUS,
                RoborockB01Props.QUANTITY,
            ])
            print(f"Status: {props.status_name}, Battery: {props.battery}%")

            # Show map info
            await q7.map.refresh()
            for entry in q7.map.map_list:
                name = getattr(entry, 'name', None) or f"Map {entry.id}"
                print(f"Map: {name} (ID: {entry.id})")

            print(
                "\nWatching for room IDs..."
                "\nStart a room clean from the Roborock app now!"
                "\nPress Ctrl+C to stop.\n"
            )

            all_props = [p for p in RoborockB01Props]
            last_status = None
            last_room_ids = None

            try:
                while True:
                    props = await q7.query_values(all_props)

                    status = props.status_name
                    room_ids = props.recommend.room_id if props.recommend else []

                    if status != last_status:
                        print(f"  Status: {status}")
                        last_status = status

                    if room_ids and room_ids != last_room_ids:
                        if len(room_ids) == 1:
                            print(f"  >>> Room ID: {room_ids[0]}")
                        else:
                            print(f"  >>> Room IDs: {room_ids}")
                        last_room_ids = room_ids

                    await asyncio.sleep(3)

            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\nDone.")

    finally:
        await device_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
