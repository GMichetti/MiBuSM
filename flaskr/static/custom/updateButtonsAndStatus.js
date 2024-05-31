// This file is a part of Mibu.

// Copyright (C) 2024 Giuseppe Michetti <gius.michetti@gmail.com>

// Mibu is free software; you can redistribute it and/or modify it
// under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or (at
// your option) any later version.

// Mibu is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
// License for more details.

// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


const HOME = "home-btn";
const STATUS_REF = "status";
const TURNON_BTN_REF = "power-on-btn";
const TURNOFF_BTN_REF = "power-off-btn";
const REBOOT_BTN_REF = "reboot-btn";

function updateStatus(data) {

    if (data.hasOwnProperty("get_status")) {

        let res = data["get_status"].pop()["result"]["result"];
        let id = data["_id"];

        let refhome = HOME.concat(id);
        let refStatus = STATUS_REF.concat(id);
        let refTurnOnBtn = TURNON_BTN_REF.concat(id);
        let refTurnOffBtn = TURNOFF_BTN_REF.concat(id);
        let refRebootBtn = REBOOT_BTN_REF.concat(id);

        let devHomeBtn = document.getElementById(refhome);
        let devTurnOnBtn = document.getElementById(refTurnOnBtn);
        let defturnOffBtn = document.getElementById(refTurnOffBtn);
        let devRebootBtn = document.getElementById(refRebootBtn);
        let devStatus = document.getElementById(refStatus);

        switch (res) {
            case 2:
                devStatus.style.color = "green";
                devStatus.textContent = "READY";
                if (devHomeBtn) {
                    devHomeBtn.enabled = true;
                }
                devTurnOnBtn.disabled = true;
                defturnOffBtn.enabled = true;
                devRebootBtn.enabled = true;
                break;

            case 1:
                devStatus.style.color = "yellow";
                devStatus.textContent = "OFF-SYNC";
                if (devHomeBtn) {
                    devHomeBtn.disabled = true;
                }
                devTurnOnBtn.enabled = true;
                defturnOffBtn.disabled = true;
                devRebootBtn.disabled = true;
                break;

            case 0:
                devStatus.style.color = "red";
                devStatus.textContent = "OFFLINE";
                if (devHomeBtn) {
                    devHomeBtn.disabled = true;
                }
                devTurnOnBtn.enabled = true;
                defturnOffBtn.disabled = true;
                devRebootBtn.disabled = true;
                break;
        }
    }
}

function getElementsByIds(ids) {
    return ids.map(id => document.getElementById(id)).filter(el => el !== null);
}


function blinkButton(data) {
    let action = Object.keys(data)[0]
    let ids = data[action]
    let root = ""
    switch (action) {
        case "power_on":
            root = TURNON_BTN_REF;
            break;
        case "shutdown":
            root = TURNOFF_BTN_REF;
            break;
        case "reboot":
            root = REBOOT_BTN_REF;
            break;
    }

    let rootNIds = []
    ids.forEach((el) => {
        rootNIds.push(root.concat(el))
    })

    let buttons = getElementsByIds(rootNIds);
    let opacity = 1;
    let fadingOut = true;
    let fadingCounter = 0

    let fading = setInterval(() => {
        if (fadingOut) {
            opacity -= 0.1;
            if (opacity <= 0) {
                fadingOut = false;
            }
        } else {
            opacity += 0.1;
            if (opacity >= 1) {
                fadingOut = true;
                fadingCounter++
                if (fadingCounter >= 10) {
                    clearInterval(fading)
                }

            }
        }
        buttons.forEach((button) => {
            button.style.opacity = opacity;
        })
    }, 100);
}