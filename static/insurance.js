function loadPatient() {
    const pid = document.getElementById("patient_id").value;

    fetch(`/patient/view/${pid}`)
        .then(res => res.json())
        .then(data => {
            const div = document.getElementById("medical_records");
            div.innerHTML = "";

            if (data.medical_records.length === 0) {
                div.innerHTML = "<p>No medical records found.</p>";
                return;
            }

            data.medical_records.forEach(r => {
                const el = document.createElement("div");
                el.className = "record";
                el.innerHTML = `
                    <p><b>Date:</b> ${r.date}</p>
                    <p><b>Hospital:</b> ${r.hospital}</p>
                    <p><b>Doctor:</b> ${r.doctor}</p>
                    <p><b>Diagnosis:</b> ${r.diagnosis}</p>
                    <p><b>Treatment:</b> ${r.treatment}</p>
                    <hr>
                `;
                div.appendChild(el);
            });
        });
}

function updateInsurance() {
    fetch("/insurance/update", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
            // JWT token will be added later
        },
        body: JSON.stringify({
            patient_id: document.getElementById("patient_id").value,
            policy_no: document.getElementById("policy_no").value,
            claims: document.getElementById("claims").value,
            target_balance: document.getElementById("target_balance").value
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || "Insurance data updated");
    });
}
