function sendOTP() {
    const phone = document.getElementById("user").value;

    fetch("/login/patient/send_otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone })
    })
    .then(r => r.json())
    .then(d => {
        alert(d.message || "OTP sent");
        document.getElementById("otp").style.display = "block";
        document.getElementById("sendBtn").style.display = "none";
        document.getElementById("verifyBtn").style.display = "block";
    });
}

function verifyOTP() {
    const phone = document.getElementById("user").value;
    const otp = document.getElementById("otp").value;

    fetch("/login/patient/verify_otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, otp })
    })
    .then(r => r.json())
    .then(d => {
        if (!d.token) return alert("Invalid OTP");

        localStorage.setItem("token", d.token);
        window.location.href = "/patient/dashboard";
    });
}
