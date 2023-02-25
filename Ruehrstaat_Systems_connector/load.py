import sys
import requests
import logging
import tkinter as tk
import os
from typing import Tuple, Optional, Dict, Any, Union

# Prevent linting errors with _() and, hopefully, enable better automaed unit testing in the future
try:
    import myNotebook as nb
    from config import config, appname
except ImportError:
    exit()

this = sys.modules[__name__]
this.plugin_name = "RSTAPI"
this.plugin_url = "https://github.com/MTN-Media-Dev-Team/ruehrstaat_edmc_plugin"
this.version_info = (0, 1, 2)
this.version = ".".join(map(str, this.version_info))
this.api_url = "https://api.ruehrstaat.de/api/v1"

CONFIG_API_KEY = "rstapi_apikey"

# Setup logging
this.logger = logging.getLogger(f'{appname}.{os.path.basename(os.path.dirname(__file__))}')


def plugin_start3(plugin_dir: str) -> str:
    config.set(CONFIG_API_KEY, config.get_str(CONFIG_API_KEY) or "")
    return this.plugin_name

def plugin_prefs(parent: nb.Notebook, cmdr: str, is_beta: bool) -> Optional[tk.Frame]:

    PADX = 10
    PADY = 2

    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)

    nb.Label(frame, text="Ruehrstaat API", background=nb.Label().cget("background")).grid(row=8, padx=PADX, sticky=tk.W)
    nb.Label(frame, text="Version: %s" % this.version).grid(row=8, column=1, padx=PADX, sticky=tk.E)

    nb.Label(frame).grid(sticky=tk.W)   # spacer

    this.cred_frame = nb.Frame(frame)   # credentials frame
    this.cred_frame.grid(columnspan=2, sticky=tk.EW)
    this.cred_frame.columnconfigure(1, weight=1)

    nb.Label(this.cred_frame, text="Ruerhstaat API credentials", background=nb.Label().cget("background")).grid(row=1, columnspan=2, padx=PADX, sticky=tk.W)

    nb.Label(this.cred_frame, text=_("API Key")).grid(row=12, padx=PADX, sticky=tk.W)
    this.apikey = nb.Entry(this.cred_frame)
    this.apikey.grid(row=12, column=1, padx=PADX, pady=PADY, sticky=tk.EW)

    set_state_frame_childs(this.cred_frame, tk.NORMAL)
    this.apikey.delete(0, tk.END)
    if cmdr:
        apikey = config.get_str(CONFIG_API_KEY)
        if apikey:
            this.apikey.insert(0, apikey)

    if not cmdr or is_beta:
        set_state_frame_childs(this.cred_frame, tk.DISABLED)

    return frame


def set_state_frame_childs(frame: tk.Frame, state):
    for child in frame.winfo_children():
        if child.winfo_class() in ("TFrame", "Frame", "Labelframe"):
            set_state_frame_childs(child, state)
        else:
            child["state"] = state

# Preferences are saved in the registry at "HKEY_CURRENT_USER\SOFTWARE\Marginal\EDMarketConnector"

def prefs_changed(cmdr: str, is_beta: bool) -> None:
    if cmdr and not is_beta:
        apikey = config.get_str(CONFIG_API_KEY)
        if apikey:
            this.logger.info(f"API key set to {apikey}")
        
        config.set(CONFIG_API_KEY, this.apikey.get().strip())

def journal_entry(cmdr: str, is_beta: bool, system: Optional[str], station: Optional[str], entry: Dict[str, Any], stateentry: Dict[str, Any]) -> Optional[str]:
    result = None
    apikey = config.get_str(CONFIG_API_KEY)
    if not apikey:
        this.logger.error("No credentials")
        result = f"{this.plugin_name}: Add credentials."
        return result
    headers = {'Authorization': 'Bearer ' + apikey}
    if entry["event"] in ["CarrierJumpRequest", "CarrierJumpCancelled"] and not is_beta:
        if entry["event"] == "CarrierJumpRequest":
            put = {
                "id": entry['CarrierID'],
                "type": "jump",
                "body": entry['Body'],
                "source": "edmc",
            }
        else:
            put = {
                "id": entry['CarrierID'],
                "type": "cancel",
                "source": "edmc",
            }
        with requests.put(this.api_url + '/carrierJump', json=put, headers=headers) as response:
            if response.status_code == 200:
                this.logger.info(f"{ entry['event']} event posted to Ruehrstaat API")
            else:
                this.logger.info(f"{ entry['event']} event posting to Ruehrstaat API failed: { str(response.status_code) } : { response.text }")
                #log carrier id
                this.logger.info(f"Carrier ID: { entry['CarrierID'] }")
                result = f"{this.plugin_name}: Error updating Ruehrstaat API. Check API-Key."
    if entry["event"] == "CarrierDockingPermission":
        put = {
            "id": entry['CarrierID'],
            "access": entry['DockingAccess'],
            "source": "edmc",
        }
        with requests.put(this.api_url + '/carrierPermission', json=put, headers=headers) as response:
            if response.status_code == 200:
                this.logger.info(f"{ entry['event']} event posted to Ruehrstaat API")
            else:
                this.logger.info(f"{ entry['event']} event posting to Ruehrstaat API failed: { str(response.status_code) } : { response.text }")
                #log carrier id
                this.logger.info(f"Carrier ID: { entry['CarrierID'] }")
                result = f"{this.plugin_name}: Error updating Ruehrstaat API. Check API-Key."
    if entry["event"] == "CarrierCrewServices":
        put = {
            "id": entry['CarrierID'],
            "operation": entry['Operation'],
            "service": entry['CrewRole'],
            "source": "edmc",
        }
        with requests.put(this.api_url + '/carrierService', json=put, headers=headers) as response:
            if response.status_code == 200:
                this.logger.info(f"{ entry['event']} event posted to Ruehrstaat API")
            else:
                this.logger.info(f"{ entry['event']} event posting to Ruehrstaat API failed: { str(response.status_code) } : { response.text }")
                #log carrier id
                this.logger.info(f"Carrier ID: { entry['CarrierID'] }")
                result = f"{this.plugin_name}: Error updating Ruehrstaat API. Check API-Key."
    # if entry["event"] == "CarrierStats":
    #     # log full entry for debugging
    #     this.logger.info(f"CarrierStats entry: { entry }")
    return result