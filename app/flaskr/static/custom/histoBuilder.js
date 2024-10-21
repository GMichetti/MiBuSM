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

let charts = {}

function buildHisto(dev) {

    BASEREF = "#histogram"
    ref = dev["_id"]
    id = BASEREF.concat(ref)
    var ctx1 = $(id).get(0).getContext("2d");

    if (dev["type"] == "ups") {
        dataLoad = []
        dataVin = []
        dataVout = []
        dataBattery = []
        resTimestamp = []
        if (dev.hasOwnProperty("get_info")) {
            dev["get_info"].forEach((el) => {
                (el["result"]["result"].hasOwnProperty("load")) ? dataLoad.push(el["result"]["result"]["load"]) : dataLoad.push(0);
                (el["result"]["result"].hasOwnProperty("vin")) ? dataVin.push(el["result"]["result"]["vin"]) : dataVin.push(0);
                (el["result"]["result"].hasOwnProperty("vout")) ? dataVout.push(el["result"]["result"]["vout"]) : dataVout.push(0);
                (el["result"]["result"].hasOwnProperty("battery")) ? dataBattery.push(el["result"]["result"]["battery"]) : dataBattery.push(0);
                resTimestamp.push((new Date(el["res_timestamp"] * 1000)).toLocaleString());
            });

            if (charts[id]) {
                charts[id].data.labels = resTimestamp
                charts[id].data.datasets[0].data = dataLoad;
                charts[id].data.datasets[1].data = dataVin;
                charts[id].data.datasets[2].data = dataVout;
                charts[id].data.datasets[3].data = dataBattery;
                charts[id].update();
            }
            else {

                charts[id] = new Chart(ctx1, {
                    type: "line",
                    data: {
                        labels: resTimestamp,
                        datasets: [{
                            label: "LOAD (watt)",
                            data: dataLoad,
                            lineTension: 0.5,
                            borderColor: "rgba(25, 135, 84, .5)"
                        },
                        {
                            label: "VIN (volts)",
                            data: dataVin,
                            lineTension: 0.5,
                            borderColor: "rgba(235, 22, 22, .5)"
                        },
                        {
                            label: "VOUT (volts)",
                            data: dataVout,
                            lineTension: 0.5,
                            borderColor:"rgba(255, 165, 0, .5)"
                        },
                        {
                            label: "BATTERY (% available)",
                            data: dataBattery,
                            lineTension: 0.5,
                            borderColor: "rgba(13, 110, 225, .5)"
                        }
                        ]
                    },
                    options: {
                        responsive: true
                    }
                });
            }
        }
    }
    if (dev["type"] == "firewall") {
        cpu_used = []
        memory_used = []
        network_rx = []
        network_tx = []
        resTimestamp = []
        if (dev.hasOwnProperty("get_info")) {
            dev["get_info"].forEach((el) => {
                (el["result"]["result"].hasOwnProperty("cpu")) ? (cpu_used.push(100 - el["result"]["result"]["cpu"]["idle"])) : cpu_used.push(0);
                (el["result"]["result"].hasOwnProperty("memory")) ? memory_used.push(el["result"]["result"]["memory"]["percentage_used"]) : memory_used.push(0);
                (el["result"]["result"].hasOwnProperty("network")) ? network_rx.push(el["result"]["result"]["network"]["1_min_rx"]/10) : network_rx.push(0);
                (el["result"]["result"].hasOwnProperty("network")) ? network_tx.push(el["result"]["result"]["network"]["1_min_tx"]/10) : network_tx.push(0);
                resTimestamp.push((new Date(el["res_timestamp"] * 1000)).toLocaleString());
            });

            if (charts[id]) {
                charts[id].data.labels = resTimestamp
                charts[id].data.datasets[0].data = cpu_used;
                charts[id].data.datasets[1].data = memory_used;
                charts[id].data.datasets[2].data = network_rx;
                charts[id].data.datasets[3].data = network_tx;
                charts[id].update();
            }
            else {

                charts[id] = new Chart(ctx1, {
                    type: "line",
                    data: {
                        labels: resTimestamp,
                        datasets: [{
                            label: "CPU (% usage)",
                            data: cpu_used,
                            lineTension: 0.5,
                            borderColor: "rgba(25, 135, 84, .5)"
                        },
                        {
                            label: "MEMORY (% usage)",
                            data: memory_used,
                            lineTension: 0.5,  
                            borderColor: "rgba(235, 22, 22, .5)"
                        },
                        {
                            label: "NETWORK RX (x10/60s)",
                            data: network_rx,
                            lineTension: 0.5,
                            borderColor: "rgba(255, 165, 0, .5)"
                        },
                        {
                            label: "NETWORK TX (x10/60 s)",
                            data: network_tx,
                            lineTension: 0.5,
                            borderColor: "rgba(13, 110, 225, .5)"
                        }
                        ]
                    },
                    options: {
                        responsive: true
                    }
                });
            }
        }
    }
    if (dev["type"] == "server") {

        system_t = []
        cpu_used = []
        memory_used = []
        resTimestamp = []
        if (dev.hasOwnProperty("get_info")) {
            dev["get_info"].forEach((el) => {

                // (el["result"]["result"].hasOwnProperty("hw_info")) ? cpu_frq.push(el["result"]["result"]["hw_info"]["cpuMhz"] / (Math.pow(10, 3))) : cpu_frq.push(0);
                (el["result"]["result"].hasOwnProperty("hw_info")) ? system_t.push(el["result"]["result"]["hw_info"]["systemHealthInfo"].find(el => el.sensor_name ==="System Board 1 Ambient Temp").valueReading).toString().substring(0,2) : system_t.push(0);
                (el["result"]["result"].hasOwnProperty("hw_info")) ? cpu_used.push(el["result"]["result"]["hw_info"]["quickStats"]["overallCpuUsage"] / (Math.pow(10, 3))) : cpu_used.push(0);
                (el["result"]["result"].hasOwnProperty("hw_info")) ? memory_used.push(el["result"]["result"]["hw_info"]["quickStats"]["overallMemoryUsage"] / 1024) : memory_used.push(0);
                resTimestamp.push((new Date(el["res_timestamp"] * 1000)).toLocaleString())
            });

            if (charts[id]) {
                charts[id].data.labels = resTimestamp
                charts[id].data.datasets[0].data = cpu_used;
                charts[id].data.datasets[1].data = system_t;
                charts[id].data.datasets[2].data = memory_used;
                charts[id].update();
            }
            else {

                charts[id] = new Chart(ctx1, {
                    type: "line",
                    data: {
                        labels: resTimestamp,
                        datasets: [{
                            label: "CPU (usage)",
                            data: cpu_used,
                            lineTension: 0.5,
                            borderColor: "rgba(25, 135, 84, .5)"
                        },
                        {
                            label: "MEMORY (usage Gb)",
                            data: memory_used,
                            lineTension: 0.5,
                            borderColor: "rgba(255, 255, 255, .5)"
                        },
                        {
                            label: "SYSTEM TEMP (degrees C)",
                            data: system_t,
                            lineTension: 0.5,
                            borderColor: "rgba(235, 22, 22, .5)"
                        }
                        ]
                    },
                    options: {
                        responsive: true
                    }
                });
            }
        }
    }
}