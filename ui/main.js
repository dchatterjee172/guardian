var api = "https://localhost:8080/"
var activities = null
var available_time = null
var used_time = 0

function post_json(url, data, callback, do_async = true) {
    console.log(data)
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url, do_async);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                if (typeof callback !== "undefined") {
                    callback(response)
                }
            } else if (xhr.status == 401) {
                window.location.href = "/login.html"
            }
        }
    };
    xhr.send(JSON.stringify(data));
}

function get_json(url, callback, do_async = true) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, do_async);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText)
                if (typeof callback !== "undefined") {
                    callback(response)
                }
            } else if (xhr.status == 401) {
                window.location.href = "/login.html"
            }
        }
    };
    xhr.send();
}

function go_home() {
    window.location.href = "/index.html"
}

function go_login() {
    window.location.href = "/login.html"
}

function register() {
    var email = document.getElementById("email").value;
    var password = document.getElementById("password").value;
    var url = api + "api_register"
    post_json(url, {
        "email": email,
        "password": password
    }, go_login)
}

function login() {
    var email = document.getElementById("email").value;
    var password = document.getElementById("password").value;
    var url = api + "api_login"
    post_json(url, {
        "email": email,
        "password": password
    }, go_home);
}

function set_activities(new_activities) {
    activities = new_activities["activities"];
    var options = '<option value="" selected disabled hidden>activities</option>';
    for (var i = 0; i < activities.length; i++) {
        console.log(activities[i])
        activity = activities[i];
        options = options + `<option value="${activity}">${activity}</option>`;
    }
    selects = document.getElementsByTagName("select");
    console.log(selects)
    for (var i = 0; i < selects.length; i++) {
        console.log(selects[i])
        selects[i].innerHTML = options;
    }
}

function get_activities() {
    var url = api + "api_get_activities";
    get_json(url, set_activities);
}

function set_available_time(new_available_time) {
    available_time = new_available_time["minutes_ago"];
    document.getElementById("time_available").innerHTML = `What have you done in past ${available_time} minutes?`
}

function set_used_time() {
    document.getElementById("time_used").innerHTML = `Added actions worth ${used_time} minutes`
}
function get_available_time() {
    var url = api + "api_last_action_time";
    get_json(url, set_available_time);
}

function remove_action(i) {
    var elem = document.getElementById(`action_${i}`);
    elem.parentNode.removeChild(elem);
    elem = document.getElementById(`action_remove_${i}`);
    elem.parentNode.removeChild(elem);
    elem = document.getElementById(`action_value_${i}`);
    elem.parentNode.removeChild(elem);
}

function remove_activity(i) {
    var elem = document.getElementById(`activity_remove_${i}`);
    elem.parentNode.removeChild(elem);
    elem = document.getElementById(`activity_value_${i}`);
    elem.parentNode.removeChild(elem);
}

function add_action() {
    var field = document.getElementById("action_field");
    var count = field.childElementCount / 3;
    field.insertAdjacentHTML('beforeend', `<select id="action_${count + 1}" required ><option value="" selected disabled hidden>activities</option></select><input id="action_value_${count + 1}" min="1" type="number"/><button id="action_remove_${count + 1}" type="button" onclick="remove_action(${count + 1})">remove the above action</button>`);
    get_activities()
}

function add_activity() {
    var field = document.getElementById("activity_field");
    var count = field.childElementCount / 2;
    field.insertAdjacentHTML('beforeend', `<input id="activity_value_${count + 1}" type="text"/><button id="activity_remove_${count + 1}" type="button" onclick="remove_activity(${count + 1})">remove the above activity</button>`);
    
}

function set_chart(chart) {
    eval(chart);
}

function get_chart() {
    var xhr = new XMLHttpRequest();
    var url = api + "api_get_chart";
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                var response = xhr.responseText
                set_chart(response)
            } else if (xhr.status == 401) {
                window.location.href = "/login.html"
            }
        }
    };
    xhr.send();
}

function body() {
    get_available_time();
    set_used_time();
    add_action();
    add_activity();
}
