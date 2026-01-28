// TEMP: patient_id will later come from login / JWT
const PATIENT_ID = prompt("Enter Patient ID to view dashboard:");

const token = localStorage.getItem("token");

fetch("/patient/view/me", {
    headers: {
        "Authorization": "Bearer " + token
    }
})
.then(r => r.json())
.then(data => {
    // render data
});

.then(res => res.json())
.then(data => {

    // Medical Records
    const container = document.getElementById("medical_records");

    if (data.medical_records.length === 0) {
        container.innerHTML = "<p>No medical history found.</p>";
        return;
    }

    data.medical_records.forEach(rec => {
        const div = document.createElement("div");
        div.className = "record";
        div.innerHTML = `
            <p><b>Date:</b> ${rec.date}</p>
            <p><b>Hospital:</b> ${rec.hospital}</p>
            <p><b>Doctor:</b> ${rec.doctor}</p>
            <p><b>Diagnosis:</b> ${rec.diagnosis}</p>
            <p><b>Treatment:</b> ${rec.treatment}</p>
        `;
        container.appendChild(div);
    });
});

