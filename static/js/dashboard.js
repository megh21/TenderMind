document.addEventListener('DOMContentLoaded', function () {
    let currentTenderId = null;

    // Event listener for tender link clicks
    document.querySelectorAll('.tender-link').forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            currentTenderId = this.getAttribute('data-id');

            // Fetch tender data dynamically
            fetch(`/get_tender_data/${currentTenderId}`)
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('cards-container-st');
                    container.innerHTML = ''; // Clear the container

                    let cardHtml = '';
                    data.card_data.forEach(function (card, index) {
                        let contentHtml = '';

                        if (typeof card.content === 'object') {
                            for (const [key, value] of Object.entries(card.content)) {
                                contentHtml += `<strong>${key}:</strong> ${value}<br>`;
                            }
                        } else {
                            contentHtml = card.content;
                        }

                        if (index % 2 === 0) {
                            cardHtml += '<div class="row mb-3">';
                        }

                        cardHtml += `
                            <div class="col-lg-6 col-md-6 mb-3 d-flex">
                                <div class="card text-black bg-light w-100">
                                    <div class="card-body d-flex flex-column">
                                        <h4 class="card-title">${card.title}</h4>
                                        <p class="card-text">${contentHtml}</p>
                                        <div class="mt-auto"></div>
                                    </div>
                                </div>
                            </div>
                        `;

                        if (index % 2 === 1) {
                            cardHtml += '</div>';
                        }
                    });

                    if (data.card_data.length % 2 !== 0) {
                        cardHtml += '</div>';
                    }

                    container.innerHTML = cardHtml;
                })
                .catch(error => console.error('Error fetching tender data:', error));
        });
    });

    // Event listener for form submission
    const createTenderForm = document.getElementById('createTenderForm');
    const submitButton = document.getElementById('submitButton');
    const loadingSpinner = document.getElementById('loadingSpinner');

    createTenderForm.addEventListener('submit', function (e) {
        e.preventDefault();

        submitButton.style.display = 'none';
        loadingSpinner.style.display = 'block';

        const formData = new FormData(createTenderForm);
        fetch(createTenderForm.action, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                window.location.href = response.url;
            } else {
                throw new Error('Tender creation failed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitButton.style.display = 'block';
            loadingSpinner.style.display = 'none';
        });
    });

    // Event listener for chat tab
    document.querySelector('a[data-bs-toggle="tab"][data-bs-target="#chat"]').addEventListener('shown.bs.tab', function () {
        fetch('/start_on_the_fly')
            .then(response => response.json())
            .then(data => {
                const chatBox = document.getElementById('chat-box');
                chatBox.innerHTML = `
                    <div class="bot-msg mb-3">
                        <div class="text-start p-2 rounded bg-primary text-white" style="max-width: 70%; display: inline-block;">
                            ${data.message}
                        </div>
                    </div>
                `;
                chatBox.scrollTop = chatBox.scrollHeight;
            })
            .catch(error => console.error('Error starting conversation:', error));
    });

    // Event listener for send button in chat
    document.getElementById('send-button').addEventListener('click', function () {
        const userInput = document.getElementById('user-input').value;
        if (userInput) {
            const chatBox = document.getElementById('chat-box');

            const userMsg = document.createElement('div');
            userMsg.classList.add('user-msg', 'mb-3', 'text-end');
            userMsg.innerHTML = `<div class="p-2 rounded bg-secondary text-white" style="max-width: 70%; display: inline-block;">${userInput}</div>`;
            chatBox.appendChild(userMsg);
            chatBox.scrollTop = chatBox.scrollHeight;

            document.getElementById('user-input').value = '';

            fetch('/get_response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userInput })
            })
            .then(response => response.json())
            .then(data => {
                const botMsg = document.createElement('div');
                botMsg.classList.add('bot-msg', 'mb-3', 'text-start');
                botMsg.innerHTML = `<div class="p-2 rounded bg-primary text-white" style="max-width: 70%; display: inline-block;">${data.response}</div>`;
                chatBox.appendChild(botMsg);
                chatBox.scrollTop = chatBox.scrollHeight;

                document.getElementById('source').innerText = `Document: ${data.source}`;
            })
            .catch(error => console.error('Error:', error));
        }
    });
});