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

let URL_CONFIG = {
    "DEFAULT_URL": "http://127.0.0.1:5000",
    "CUSTOM_URL": "http://192.168.1.25:5000"
};

function getURLConfig() {
    return URL_CONFIG['CUSTOM_URL'] || URL_CONFIG['DEFAULT_URL'];
}

