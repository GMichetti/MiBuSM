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

function appendJSON(res, ref) {

	let jsonHTML = jsonToHTML(res)(true)(true)
	document.getElementById(ref).innerHTML = jsonHTML;
	setClickListeners();
}

function jsonViewer(data) {
	BASEREF = "show-json";
	if (data.hasOwnProperty("get_info")){
		res = data["get_info"].pop()["result"]["result"]
		id = data["_id"]
		ref = BASEREF.concat(id)
		appendJSON(res, ref)
	}
}

