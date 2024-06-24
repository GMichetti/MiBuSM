import getURLConfig from "./config"

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

function button_action(data) {
    let action = data.split("?")[0]
    let url = getURLConfig() + "/api/v1/set_state"
    let id = data.split("?")[1]
    let payload = {}
    payload[action] = [id]

    fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
        .then(response => {

            // code in the range from 200 to 299
            if (!response.ok) {
                throw new Error('Request error');
            }
            return response.json(); 
        })
        .then(data => {
            blinkButton(data)
        })
 
        .catch(error => {
            console.error('Error:', error);
        });
}

