function loginHealth() {
    const role = document.getElementById("role").value;
    const user = document.getElementById("user").value;
    const pass = document.getElementById("pass").value;

    let url, body;

    if (role === "patient") {
        url = "/login/patient";
        body = { phone: user };
    } else {
        url = "/login/hospital";
        body = { council_id: user, password: pass };
    }

    fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    })
    .then(r => r.json())
    .then(d => {
        if (!d.token) return alert("Login failed");

        localStorage.setItem("token", d.token);

        if (role === "patient") {
            window.location.href = "/patient/dashboard";
        } else {
            window.location.href = "/hospital/dashboard";
        }
    });
}
