
class USB:
    device = None
    def __init__(self, device):
        self.device = device

    def dict_status(self):

        return {
            "load": f"{self.load()*self.capacity()/100}",
            "load_percentage": f"{self.load()}",
            "vin": f"{self.vin()}",
            "vout": f"{self.vout()}",
            "test": self.test(),
            "capacity": f"{self.capacity()}",
            "batterytype": self.batterytype(),
            "manufacturer": self.manufacturer(),
            "firmware": self.firmware(),
            "product": self.product(),
            **self.status(),
            **self.battery_runtime()
            }

    def iname(self):
        return self.device.get_feature_report(0x01,8)[1]

    def load(self):
        return self.device.get_feature_report(0x13,2)[1]
    def vout(self):
        return self.device.get_feature_report(0x12,3)[1]
    def vin(self):
        return self.device.get_feature_report(0x0f,3)[1]
    def test(self):
        return self.device.get_feature_report(0x14,2)[1]
    def battery_runtime(self):
        report = self.device.get_feature_report(0x08,6)
        return {"runtime":int((report[3]*256+report[2])/60),
                "battery": report[1]}

    def capacity(self):
        report = self.device.get_feature_report(0x18,6)
        return (report[2]*256+report[1])

    def product(self):
        return self.device.get_indexed_string(self.iname())

    def firmware(self):
        return self.device.get_indexed_string(2)

    def manufacturer(self):
        return self.device.get_indexed_string(3)

    def batterytype(self):
        return self.device.get_indexed_string(4)

    def status(self):
        status = self.device.get_feature_report(0x0b,3)[1]

        if status & 1:
            ac = True
        else:
            ac = False

        if status & 2:
            charge = True
        elif status & 4:
            charge = False
        else:
            charge = None

        belowcap = (status & 8) > 0
        full = (status & 16) > 0
        overtimelimit = (status & 16) > 0

        return {"ac": ac, "charge": charge, "belowcap": belowcap, "full": full,
                "overtimelimit": overtimelimit}


