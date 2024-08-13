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

let perf_charts = {}
let msg_bkr_charts = {}

function lineChartBuilder(data_t, data_q) {


    let perf_id = "#tput"
    let ctx1 = $(perf_id).get(0).getContext("2d");
    let delta = data_t.map(entry => entry.delta);

    let timestamp = data_t.map(entry => new Date(entry.timestamp * 1000).toLocaleString());

    if (perf_charts[perf_id]) {
        perf_charts[perf_id].data.labels = timestamp
        perf_charts[perf_id].data.datasets[0].data = delta;
        perf_charts[perf_id].update()
    }

    else {

        perf_charts[perf_id] = new Chart(ctx1, {
            type: "line",
            data: {
                labels: timestamp,
                datasets: [{
                    label: "Throughput (job/s)",
                    data: delta,
                    lineTension: 0.5,
                    backgroundColor: "rgba(13, 110, 225, .5)",
                    fill: true
                }]
            },
            options: {
                responsive: true
            }
        });
    }

    let msg_bkr_id = "#mbq"
    let ctx2 = $(msg_bkr_id).get(0).getContext("2d");
    let q_value = data_q.map(entry => entry.value);
    let mb_timestamp = data_q.map(entry => new Date(entry.timestamp * 1000).toLocaleString());
    if (msg_bkr_charts[msg_bkr_id]) {
        msg_bkr_charts[msg_bkr_id].data.labels = mb_timestamp;
        msg_bkr_charts[msg_bkr_id].data.datasets[0].data = q_value;
        msg_bkr_charts[msg_bkr_id].update();

    } else {
        msg_bkr_charts[msg_bkr_id] = new Chart(ctx2, {
            type: "line",
            data: {
                labels: mb_timestamp,
                datasets: [{
                    label: "Queue (# of elements)",
                    data: q_value,
                    lineTension: 0.5,
                    backgroundColor: "rgba(235, 22, 22, .5)",
                    fill: true
                }]
            },
            options: {
                responsive: true
            }
        });
    }

    
}
