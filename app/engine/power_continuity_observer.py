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

from abc import ABC, abstractmethod
from common_libs import *
# import device
logger = Logger()


class Subject(ABC):
    """
    Behavioral Design Pattern: Observer
    """
    
    def __init__(self):
        self._observers = []

    @abstractmethod
    def subject_attach(self, observer):
        pass

    @abstractmethod
    def subject_detach(self, observer):
        pass

    @abstractmethod
    def subject_notify(self):
        pass


class Observer:

    def __init__(self):
        pass

    def observer_update(self, subject):
        pass


class Power_Continuity_Observer(Observer, ABC):

    def __init__(self):
        pass

    @abstractmethod
    def shutdown_forced(self):
        pass


class Power_Continuity_Status(Subject):

    def __init__(self):
        super().__init__()

    def subject_attach(self, observer: Power_Continuity_Observer):  
        """
        It attaches observer to the subject if not already attached
        
        Args:
            observer (Power_Continuity_Observer): the observer that needs to be attached
        """
        
        if observer not in self._observers:
            self._observers.append(observer)

    def subject_notify(self):
        """
        It notifies to the observers the Subject' status 
        """
        
        for observer in self._observers:
            observer.shutdown_forced()

    def subject_detach(self, observer):
        """
        It detaches the observer from the subject
        
        Args:
            observer (Power_Continuity_Observer): the observer that needs to be detached
        """        
        
        self._observers.remove(observer)
