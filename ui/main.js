var api = "https://localhost:8080/"

function post_json(url, data) {
    console.log(data)
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                return JSON.parse(xhr.responseText);
            } else {
                return null
            }
        }
    };
    xhr.send(JSON.stringify(data));
}

function get_json(url, data) {
    var xhr = new XMLHttpRequest();
    url = "url?data=" + encodeURIComponent(JSON.stringify(data));
    xhr.open("GET", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                return JSON.parse(xhr.responseText);
            } else {
                return null
            }
        }
    };
    xhr.send();
}

function register() {
    var email = document.getElementById("email").value;
    var password = document.getElementById("password").value;
    var url = api + "api_register"
    post_json(url, {
        "email": email,
        "password": password
    })
}

function login() {
    var email = document.getElementById("email").value;
    var password = document.getElementById("password").value;
    var url = api + "api_login"
    post_json(url, {
        "email": email,
        "password": password
    })
}