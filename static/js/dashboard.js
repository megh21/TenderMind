// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Global Variables
    let currentTenderId = null;

    // Form Handling
    const createTenderForm = document.getElementById('createTenderForm');
    const submitButton = document.getElementById('submitButton');
    const loadingSpinner = document.getElementById('loadingSpinner');

    // Form Submit Handler
    if (createTenderForm) {
        createTenderForm.addEventListener('submit', function(e) {
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
    }

    // Tender Link Click Handlers
    $('.tender-link').click(function(e) {
        e.preventDefault();
        currentTenderId = $(this).data('id');

        // Clear chat box when switching tenders
        $('#chat-box').empty();

        // Switch to home tab
        const homeTab = new bootstrap.Tab(document.querySelector('a[href="#home"]'));
        homeTab.show();

        // Fetch tender data for cards
        $.get(`/get_tender_data/${currentTenderId}`, function(response) {
            $('#cards-container-st').empty();
            let cardHtml = '';

            response.card_data.forEach(function(card, index) {
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

            if (response.card_data.length % 2 !== 0) {
                cardHtml += '</div>';
            }

            $('#cards-container-st').append(cardHtml);
        });

        // Fetch and update metrics
        fetchAndUpdateMetrics(currentTenderId);
    });

    // Metrics Functions
    function fetchAndUpdateMetrics(tenderId) {
        const projectMetricsContainer = document.getElementById('project-metrics');
        projectMetricsContainer.innerHTML = '<p class="text-center">Loading...</p>';
        projectMetricsContainer.style.display = 'block';

        fetch(`/graph_data/${tenderId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    projectMetricsContainer.innerHTML = '<p class="text-center text-danger">Tender not found!</p>';
                    return;
                }
                projectMetricsContainer.innerHTML = createMetricsHTML();
                projectMetricsContainer.style.display = 'flex';
                updateProjectMetrics(data);
            })
            .catch(error => {
                console.error('Error fetching project data:', error);
                projectMetricsContainer.innerHTML = '<p class="text-center text-danger">Error loading data</p>';
            });
    }

    function createMetricsHTML() {
        return `
            <div class="circle-progress">
                <h3>Complexity</h3>
                <div id="complexity-circle" class="circle"></div>
                <div class="hover-info"><ul></ul></div>
            </div>
            <div class="circle-progress">
                <h3>Scalability</h3>
                <div id="scalability-circle" class="circle"></div>
                <div class="hover-info"><ul></ul></div>
            </div>
            <div class="circle-progress">
                <h3>Integration</h3>
                <div id="integration-circle" class="circle"></div>
                <div class="hover-info"><ul></ul></div>
            </div>
            <div class="circle-progress">
                <h3>Time Feasibility</h3>
                <div id="time-feasibility-circle" class="circle"></div>
                <div class="hover-info"><ul></ul></div>
            </div>
        `;
    }

    function updateProjectMetrics(data) {
        setCircleProgress('complexity-circle', data.Complexity.Rating, getRatingPercent(data.Complexity.Rating), getColor(data.Complexity.Rating));
        setCircleProgress('scalability-circle', data.Scalability.Rating, getRatingPercent(data.Scalability.Rating), getColor(data.Scalability.Rating));
        setCircleProgress('integration-circle', data.Integration_Requirements.Rating, getRatingPercent(data.Integration_Requirements.Rating), getColor(data.Integration_Requirements.Rating));
        setCircleProgress('time-feasibility-circle', data.Time_Feasibility.Rating, getRatingPercent(data.Time_Feasibility.Rating), getColor(data.Time_Feasibility.Rating));

        document.querySelector('#complexity-circle + .hover-info ul').innerHTML = `<li>${data.Complexity.Verification_Sentence}</li>`;
        document.querySelector('#scalability-circle + .hover-info ul').innerHTML = `<li>${data.Scalability.Verification_Sentence}</li>`;
        document.querySelector('#integration-circle + .hover-info ul').innerHTML = `<li>${data.Integration_Requirements.Verification_Sentence}</li>`;
        document.querySelector('#time-feasibility-circle + .hover-info ul').innerHTML = `<li>${data.Time_Feasibility.Verification_Sentence}</li>`;
    }

    function setCircleProgress(elementId, value, percent, color) {
        const circle = document.getElementById(elementId);
        circle.style.background = `conic-gradient(${color} ${percent}%, #e0e0e0 0)`;
        circle.innerHTML = `<span style="position: relative; z-index: 1;">${value}</span>`;
    }

    function getColor(rating) {
        switch (rating.toLowerCase()) {
            case 'low':
            case 'somehow feasible':
                return 'green';
            case 'moderate':
                return 'orange';
            case 'high':
                return 'red';
            default:
                return 'gray';
        }
    }

    function getRatingPercent(rating) {
        switch (rating.toLowerCase()) {
            case 'low':
            case 'somehow feasible':
                return 33;
            case 'moderate':
                return 66;
            case 'high':
                return 100;
            default:
                return 0;
        }
    }

    // Tab Change Handlers
    $('a[data-bs-toggle="tab"]').on('shown.bs.tab', function(e) {
        if ($(e.target).attr('href') === '#details') {
            $('#details input[type="checkbox"]').prop('checked', false);
            $('#details input[type="text"]').val('');
            $('#cards-container-extra').empty();
        }
        if ($(e.target).attr('href') === '#chat') {
            $.post('/start_on_the_fly', function(response) {
                $('#chat-box').append(`
                    <div class="bot-msg mb-3">
                        <div class="text-start p-2 rounded bg-primary text-white" style="max-width: 70%; display: inline-block;">
                            ${response.message}
                        </div>
                    </div>
                `);
                $('#chat-box').scrollTop($('#chat-box')[0].scrollHeight);
            }).fail(function(error) {
                console.error('Error starting conversation:', error);
            });
        }
    });

    // Addon Submission Handler
    $('#submitAddons').click(function () {
        let selectedAddons = [];
        $('input[type=checkbox]:checked').each(function () {
            selectedAddons.push($(this).val());
        });
    
        // Send selected addons and current tender ID to the backend
        $.ajax({
            type: 'POST',
            url: '/process_addons',
            contentType: 'application/json',
            data: JSON.stringify({ 'tender_id': currentTenderId, 'addons': selectedAddons }),
            success: function (response) {
                $('#cards-container-extra').empty();
                response.card_data_addons.forEach(function (card) {
                    let contentHtml = '';
    
                    // Check if the content is an object (nested data)
                    if (typeof card.content === 'object') {
                        if (Array.isArray(card.content)) {
                            // Handle array of objects
                            card.content.forEach(item => {
                                for (const [key, value] of Object.entries(item)) {
                                    contentHtml += `<strong>${key}:</strong> ${value}<br>`;
                                }
                            });
                        } else {
                            // Handle single object
                            for (const [key, value] of Object.entries(card.content)) {
                                contentHtml += `<strong>${key}:</strong> ${value}<br>`;
                            }
                        }
                    } else {
                        // If it's not an object, just display it as is
                        contentHtml = card.content;
                    }
    
                    $('#cards-container-extra').append(`
                        <div class="col-lg-3 col-md-6 mb-3">
                            <div class="card text-black bg-light d-flex flex-column h-100">
                                <div class="card-body d-flex flex-column">
                                    <h4 class="card-title">${card.title}</h4>
                                    <p class="card-text">${contentHtml}</p>
                                    <!-- This makes sure the content is pushed to the top if needed -->
                                    <div class="mt-auto"></div>
                                </div>
                            </div>
                        </div>
                    `);
                });
            },
            error: function (error) {
                console.error('Error:', error);
            }
        });
    });

    // Chat Functionality
    document.getElementById('send-button').addEventListener('click', function() {
        const userInput = document.getElementById('user-input').value;
        if (userInput) {
            const chatBox = document.getElementById('chat-box');

            // Add user message
            chatBox.innerHTML += `
                <div class="user-msg mb-3 text-end">
                    <div class="p-2 rounded bg-secondary text-white" style="max-width: 70%; display: inline-block;">
                        ${userInput}
                    </div>
                </div>
            `;
            chatBox.scrollTop = chatBox.scrollHeight;
            document.getElementById('user-input').value = '';

            // Get bot response
            fetch('/get_response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userInput })
            })
            .then(response => response.json())
            .then(data => {
                chatBox.innerHTML += `
                    <div class="bot-msg mb-3 text-start">
                        <div class="p-2 rounded bg-primary text-white" style="max-width: 70%; display: inline-block;">
                            ${data.response}
                        </div>
                    </div>
                `;
                chatBox.scrollTop = chatBox.scrollHeight;
                document.getElementById('source').innerText = `Document: ${data.source}`;
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
    });
});