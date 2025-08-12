let currentAuctionId = null;

function updateTime() {
    fetch('/time')
        .then(res => res.json())
        .then(data => {
            document.getElementById("timer").innerText = data.remaining > 0 ?
                "⏱ " + data.remaining + "s rimasti" : "⏱ Tempo scaduto";
        });
}

function updateHistory() {
    fetch('/history')
        .then(res => res.json())
        .then(data => {
            const history = document.getElementById("history");
            history.innerHTML = "";
            if (data.length > 0) {
                history.innerHTML += `<p class="highlight">${data[0].name}: €${data[0].amount}</p>`;
                for (let i = 1; i < data.length; i++) {
                    history.innerHTML += `<p>${data[i].name}: €${data[i].amount}</p>`;
                }
            }
        });
}

function updateCrediti() {
    fetch('/crediti')
        .then(res => res.json())
        .then(data => {
            document.getElementById("crediti").innerText = "Crediti rimanenti: " + data.crediti;
        });
}

function checkAuctionChange() {
    fetch('/auction_id')
        .then(res => res.json())
        .then(data => {
            if (!currentAuctionId) {
                currentAuctionId = data.auction_id;
            } else if (currentAuctionId !== data.auction_id) {
                window.location.href = "/";
            }
        });
}

function rilancia() {
    const nome = document.getElementById("name").value;
    fetch('/rilancia', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: nome })
    }).then(res => {
        if (res.status === 204) {
            updateHistory();
            updateCrediti();
        }
    });
}

setInterval(() => {
    updateTime();
    updateHistory();
    updateCrediti();
    checkAuctionChange();
}, 1000);

window.onload = () => {
    updateTime();
    updateHistory();
    updateCrediti();
    checkAuctionChange();
};