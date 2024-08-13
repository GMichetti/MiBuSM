# This file is a part of MiBu.
#
# Copyright (C) 2024 Giuseppe Michetti <gius.michetti@gmail.com>
#
# MiBu is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# MiBu is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from enum import Enum


class Action_Status(Enum):
    ERROR = 0               # There was an error while the worker was performing the action
    REQUESTED = 1           # The action was accepted by the GUI or by the REST API 
    DISPATCHED = 2          # The action has just been sent to the worker to be processed
    COMPLETED = 3           # The action was completed successfully by the worker
    

