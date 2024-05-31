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

function createCustomInputs() {
    var customInputsContainer = document.getElementById('customInputsContainer');
    customInputsContainer.innerHTML = '';
    var selectedValue = document.querySelector('input[name="device_type_radios"]:checked').value;

    IPV4_6_VALIDATION_PATTERN = 'pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|([0-9a-fA-F]{1,4}:){7}([0-9a-fA-F]{1,4})$"' 

    switch (selectedValue) {
        case 'SERVER':
            customInputsContainer.innerHTML = `
                <div class="mb-3">
                    <label for="vendor" class="form-label">Vendor</label>
                    <input type="text" class="form-control" id="vendor" name="vendor" required>
                </div>
                <div class="mb-3">
                    <label for="name" class="form-label">Name</label>
                    <input type="text" class="form-control" id="name" name="name" required>
                </div>
                <div class="mb-3">
                    <label for="controller_ip" class="form-label">Controller Ip</label>
                    <input type="text" class="form-control" id="controller_ip" name="controller_ip" ${IPV4_6_VALIDATION_PATTERN} required>
                </div>
                <div class="mb-3">
                    <label for="controller_user" class="form-label">Controller User</label>
                    <input type="text" class="form-control" id="controller_user" name="controller_user" required>
                </div>
                <div class="mb-3">
                    <label for="controller_password" class="form-label">Controller Password</label>
                    <input type="password" class="form-control" id="controller_password" name="controller_password" required>
                </div>
                <div class="mb-3">
                    <label for="hypervisor_type" class="form-label">HyperVisor Type</label>
                    <input type="text" class="form-control" id="hypervisor_type" name="hypervisor_type" required>
                </div>
                <div class="mb-3">
                    <label for="hypervisor_ip" class="form-label">HyperVisor Ip</label>
                    <input type="text" class="form-control" id="hypervisor_ip" name="hypervisor_ip" ${IPV4_6_VALIDATION_PATTERN} required>
                </div>
                <div class="mb-3">
                    <label for="hypervisor_user" class="form-label">HyperVisor User</label>
                    <input type="text" class="form-control" id="hypervisor_user" name="hypervisor_user" required>
                </div>
                <div class="mb-3">
                    <label for="hypervisor_password" class="form-label">HyperVisor Password</label>
                    <input type="password" class="form-control" id="hypervisor_password" name="hypervisor_password" required>
                </div>
            `;
            break;
        case 'POWER_CONTINUITY_APPLIANCE':
            customInputsContainer.innerHTML = `
                <div class="mb-3">
                    <label for="vendor" class="form-label">Vendor</label>
                    <input type="text" class="form-control" id="vendor" name="vendor" required>
                </div>
                <div class="mb-3">
                    <label for="name" class="form-label">Name</label>
                    <input type="text" class="form-control" id="name" name="name" required>
                </div>
                <div class="mb-3">
                    <label for="pid" class="form-label">PID</label>
                    <input type="text" class="form-control" id="pid" name="pid" required>
                </div>

            `;
            break;
        default:
            customInputsContainer.innerHTML = `
                <div class="mb-3">
                    <label for="vendor" class="form-label">Vendor</label>
                    <input type="text" class="form-control" id="vendor" name="vendor" required>
                </div>
                <div class="mb-3">
                    <label for="name" class="form-label">Name</label>
                    <input type="text" class="form-control" id="name" name="name" required>
                </div>
                <div class="mb-3">
                    <label for="ip_address" class="form-label">Ip Address </label>
                    <input type="text" class="form-control" id="ip_address" name="ip_address" ${IPV4_6_VALIDATION_PATTERN} required>
                </div>
                <div class="mb-3">
                    <label for="user" class="form-label">User</label>
                    <input type="text" class="form-control" id="user" name="user" required>
                </div>
                <div class="mb-3">
                    <label for="password" class="form-label">Password</label>
                    <input type="password" class="form-control" id="password" name="password" required>
                </div>
            `;
            break;
    }
}

// Attach listener to radio buttons to update custom inputs when selection changes
var radioButtons = document.querySelectorAll('input[name="device_type_radios"]');
radioButtons.forEach(function (radioButton) {
    radioButton.addEventListener('change', createCustomInputs);
});

// Initially create custom inputs based on current selection
createCustomInputs();