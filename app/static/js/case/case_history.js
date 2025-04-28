import {display_toast, create_message} from '/static/js/toaster.js'
const { ref, nextTick } = Vue
export default {
    delimiters: ['[[', ']]'],
	props: {
		case_id: Number
	},
	setup(props) {
        const history = ref()
        const main_tab = ref("history-case")
        const case_misp_objects = ref()


        async function fetch_history(){
            const res = await fetch("/case/history/" + props.case_id)
            if(await res.status==404 ){
                display_toast(res)
            }else{
                let loc = await res.json()
                history.value = loc["history"]

                const historyDict = new Map();
                const monthOrder = [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ];

                for (const h of history.value) {
                    const match = h.match(/\[(.*?)\]\((.*?)\)(.*)/);
                    if (!match) continue;

                    const [_, dateStr, userStr, text] = match;
                    const date = new Date(dateStr);
                    const year = date.getFullYear();
                    const month = date.toLocaleString("default", { month: "long" });
                    const dayKey = `${String(date.getDate()).padStart(2, "0")}, ${date.toLocaleString("default", { weekday: "short" })}`;

                    if (!historyDict.has(year)) historyDict.set(year, new Map());
                    const yearMap = historyDict.get(year);

                    if (!yearMap.has(month)) yearMap.set(month, new Map());
                    const monthMap = yearMap.get(month);

                    if (!monthMap.has(dayKey)) monthMap.set(dayKey, []);
                    monthMap.get(dayKey).push({
                        user: userStr,
                        text: text.trim().slice(1), // remove leading colon and space
                        date: dateStr
                    });
                }

                
                // Reverse sorted
                const sortedHistory = new Map(
                    [...historyDict.entries()].sort((a, b) => b[0] - a[0])
                    .map(([year, months]) => [
                        year,
                        new Map(
                            [...months.entries()]
                            .sort((a, b) => monthOrder.indexOf(b[0]) - monthOrder.indexOf(a[0]))
                            .map(([month, days]) => {
                                const sortedDays = new Map(
                                [...days.entries()]
                                    .sort((a, b) => {
                                    const aDate = new Date(`${month} ${a[0].split(',')[0]}, ${year}`);
                                    const bDate = new Date(`${month} ${b[0].split(',')[0]}, ${year}`);
                                    return bDate - aDate;
                                    })
                                    .map(([day, entries]) => [
                                        day,
                                        // Sort entries by time, descending
                                        entries.sort((a, b) =>
                                            new Date(b.date) - new Date(a.date)
                                        )
                                    ])
                                );

                                const monthCount = [...sortedDays.values()]
                                .reduce((sum, entries) => sum + entries.length, 0);

                                return [
                                month,
                                {
                                    count: monthCount,
                                    days: sortedDays
                                }
                                ];
                            })
                        )
                    ])
                );

                // Convert Map to plain object
                function mapToObject(map) {
                    const obj = {};
                    for (const [key, value] of map.entries()) {
                        if (value instanceof Map) {
                            obj[key] = mapToObject(value);
                        } else if (value.days instanceof Map) {
                            obj[key] = {
                                count: value.count,
                                days: mapToObject(value.days)
                            };
                        } else {
                            obj[key] = value;
                        }
                    }
                    return obj;
                }

                history.value = mapToObject(sortedHistory);
                
            }
        }
        fetch_history()

        async function fetch_case_misp_object(){
            const res = await fetch("/case/"+props.case_id+"/get_case_misp_object")
            // const res = await fetch("/case/"+ window.location.pathname.split("/").slice(-1) +"/get_case_misp_object")
            if(await res.status==404 ){
                display_toast(res)
            }else{
                let loc = await res.json()
                case_misp_objects.value = loc["misp-object"]
            }
        }
        fetch_case_misp_object()

        function prepare_misp_timeline(){
            function toStartDateObject(date) {
                return {
                  year: String(date.getFullYear()),
                  month: String(date.getMonth() + 1).padStart(2, "0"),
                  day: String(date.getDate()).padStart(2, "0"),
                  hour: String(date.getHours()).padStart(2, "0"),
                  minute: String(date.getMinutes()).padStart(2, "0")
                };
            }

            let loc_list=[]

            for (const obj of case_misp_objects.value) {
                let firstSeenDates = [];
              
                for (const attr of obj.attributes) {
                    if (attr.first_seen) {
                        const date = new Date(attr.first_seen);
                        if (!isNaN(date)) {
                            firstSeenDates.push(date);
                        }
                    }
                }
              
                let resultDate;
                if (firstSeenDates.length > 0) {
                    resultDate = new Date(Math.min(...firstSeenDates));
                } else if (obj.creation_date) {
                    resultDate = new Date(obj.creation_date);
                } else {
                    resultDate = null;
                }
                let startDate

                if(resultDate){
                    startDate = toStartDateObject(resultDate)
                }else{
                    startDate = toStartDateObject(new Date(obj.creation_date))
                }

                let loc_text = "<div>Object uuid: " + obj.object_uuid + "<table style='margin-left:20px'>"
                loc_text += "<tr><th>Attribute value</th><th>Attribute type</th><th>Attribute comment</th><th>Attribute first seen</th>"
                loc_text += "<th>Attribute last seen</th><th>Attribute IDS</th></tr>"
                for(let at in obj.attributes){
                    loc_text += "<tr><td>" + obj.attributes[at].value + "</td>"
                    loc_text += "<td>" + obj.attributes[at].type + "</td>"
                    loc_text += "<td>" + obj.attributes[at].comment + "</td>"
                    loc_text += "<td>" + obj.attributes[at].first_seen + "</td>"
                    loc_text += "<td>" + obj.attributes[at].last_seen + "</td>"
                    loc_text += "<td>" + obj.attributes[at].ids_flag + "</td></tr>"
                    loc_text += "<br>"
                }
                loc_text += "</table></div>"

                loc_list.push({
                    "start_date": startDate,
                    "text": {"headline": obj.object_name, "text": loc_text}
                })
            }


            const timelineJson = {
                "events":loc_list
            };
            new TL.Timeline('timeline-embed', timelineJson);
        }

        async function active_tab(tab_name){
            if(tab_name == 'history-case'){
                main_tab.value = 'history-case'
                if ( !document.getElementById("tab-history-case").classList.contains("active") ){
                    document.getElementById("tab-history-case").classList.add("active")
                    document.getElementById("tab-history-misp").classList.remove("active")
                }
            }else if(tab_name == 'history-misp'){
                main_tab.value = 'history-misp'
                if ( !document.getElementById("tab-history-misp").classList.contains("active") ){
                    document.getElementById("tab-history-misp").classList.add("active")
                    document.getElementById("tab-history-case").classList.remove("active")
                    await nextTick()
                    prepare_misp_timeline()
                }
            }
        }

		return {
            history,
            main_tab,

            active_tab
		}
    },
	template: `
    <ul class="nav nav-tabs" style="margin-bottom: 10px;">
        <li class="nav-item">
            <button class="nav-link active" id="tab-history-case" aria-current="page" @click="active_tab('history-case')">Case</button>
        </li>
        <li class="nav-item">
            <button class="nav-link" id="tab-history-misp" @click="active_tab('history-misp')">MISP</button>
        </li>
    </ul>

    <template v-if="main_tab == 'history-case'">
        <template v-if="history">
            <a class="btn btn-primary btn-sm mb-1" :href="'/case/'+case_id+'/download_history'">Download</a>
            <div class="timeline">
                <template v-for="h, key in history">
                    <template v-for="month, key_month in h">
                        <div class="timeline-month">
                            [[key_month]], [[key]]
                            <span>[[month.count]] Entries</span>
                        </div>
                    
                        <template v-for="day, key_day in month.days">
                            <div class="timeline-section">
                                <div class="timeline-date">
                                    [[key_day]]
                                    <span>[[day.length]] Entries</span>
                                </div>
                                <div class="row">
                                    <template v-for="history_data, key_history_data in day">
                                        <div class="col-sm-4">
                                            <div class="timeline-box">
                                                <div class="box-title">
                                                    <i class="fa fa-asterisk text-success" aria-hidden="true"></i> [[history_data.user]]
                                                </div>
                                                <div class="box-content">
                                                    <div class="box-item"><strong>Modif</strong>: [[history_data.text]]</div>
                                                </div>
                                                <div class="box-footer">[[history_data.date]]</div>
                                            </div>
                                        </div>
                                    </template>
                                </div>
                            </div>
                        </template>
                        
                    </template>
                </template>
            </div>
        </template>
        <template v-else>
            <i>No history</i>
        </template>

    </template>
    <template v-else-if="main_tab == 'history-misp'">
        <div id="timeline-embed" style="width: 100%; height: 60vh;"></div>
    </template>
    `
}