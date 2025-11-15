import requests
import os
import sys
from sanitize_filename import sanitize
from tkinter import Tk, filedialog

HOST = "api.moxfield.com"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) Gecko/20100101 Firefox/135.0"
USERNAME = sys.argv[1]

TEMPLATE = """[metadata]
Name={}

[Avatar]

[Commander]
{}

[Main]
{}

[Sideboard]
{}

[Planes]
{}

[Schemes]
{}

[Conspiracy]
{}

[Attractions]
{}


"""


def select_forge_folder():
    """Prompt user to select the Forge decks folder."""
    root = Tk()
    root.withdraw()  # Hide the root window
    forge_default = os.path.expanduser(r"~\AppData\Roaming\Forge\decks")
    folder = filedialog.askdirectory(
        title="Select Forge Decks Folder", initialdir=forge_default
    )
    root.destroy()
    if not folder:
        print("No folder selected. Exiting.")
        sys.exit(1)
    return folder


def main():
    print("moxfield-forge-sync")
    FORGE_DECKS_FOLDER = select_forge_folder()
    decks_resp = requests.get(
        f"https://api.moxfield.com/v2/users/{USERNAME}/decks?pageSize=100",
        headers={"User-Agent": USER_AGENT},
    )
    decks_resp.raise_for_status()
    decks = decks_resp.json().get("data", [])
    commander_decks = [deck for deck in decks if deck.get("format") == "commander"]
    for deck in commander_decks:
        deck_resp = requests.get(
            f'https://api2.moxfield.com/v3/decks/all/{deck["publicId"]}',
            headers={"User-Agent": USER_AGENT},
        )
        deck_resp.raise_for_status()
        deck_json = deck_resp.json()
        build_dck_file(deck_json, FORGE_DECKS_FOLDER)


def build_dck_file(deck_json, forge_folder):
    commanders = get_board_string(deck_json["boards"]["commanders"])
    mainboard = get_board_string(deck_json["boards"]["mainboard"])
    sideboard = get_board_string(deck_json["boards"]["sideboard"])
    # Limit sideboard to first 10 lines as it's a Forge requirement
    sideboard_lines = sideboard.split("\n") if sideboard else []
    sideboard = "\n".join(sideboard_lines[:10])
    planes = get_board_string(deck_json["boards"]["planes"])
    schemes = get_board_string(deck_json["boards"]["schemes"])
    conspiracy = ""
    attractions = get_board_string(deck_json["boards"]["attractions"])
    dck_txt = TEMPLATE.format(
        deck_json["name"],
        commanders,
        mainboard,
        sideboard,
        planes,
        schemes,
        conspiracy,
        attractions,
    )
    dck_filename = f'{deck_json["name"]}.dck'
    dck_filename = sanitize(dck_filename)
    dck_full_path = os.path.join(forge_folder, dck_filename)
    print(f"Writing {dck_full_path}.")
    with open(dck_full_path, "w", encoding="utf-8") as dck_file:
        dck_file.write(dck_txt)


def get_board_string(board):
    return "\n".join(
        [
            get_card_string(card["card"], card["quantity"])
            for card in list(board["cards"].values())
        ]
    )


def get_card_string(card, quantity):
    card_name = card["name"].split(" // ")[0]
    return f'{quantity} {card_name}|{card["set"].upper()}|1'


if __name__ == "__main__":
    main()
