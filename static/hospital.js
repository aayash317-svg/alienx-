function addRecord() {
    fetch("/hospital/medical/add", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            // JWT token will be added later
        },
        body: JSON.stringify({
            patient_id: document.getElementById("patient_id").value,
            doctor: document.getElementById("doctor").value,
            diagnosis: document.getElementById("diagnosis").value,
            treatment: document.getElementById("treatment").value
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || "Record added");
        loadRecords();
    });
}

function loadRecords() {
    const pid = document.getElementById("patient_id").value;
    if (!pid) return;

    fetch(`/patient/view/${pid}`)
        .then(res => res.json())
        .then(data => {
            const div = document.getElementById("records");
            div.innerHTML = "";

            data.medical_records.forEach(r => {
                const el = document.createElement("div");
                el.className = "record";
                el.innerHTML = `
                    <p><b>Date:</b> ${r.date}</p>
                    <p><b>Doctor:</b> ${r.doctor}</p>
                    <p><b>Hospital:</b> ${r.hospital}</p>
                    <p><b>Diagnosis:</b> ${r.diagnosis}</p>
                    <p><b>Treatment:</b> ${r.treatment}</p>
                `;
                div.appendChild(el);
            });
        });
}
