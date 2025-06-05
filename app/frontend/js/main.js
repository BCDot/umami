/**
 * Placeholder for API request function.
 * In a real app, this would use fetch() or a library like axios,
 * handle headers (like Authorization for JWT), and error responses.
 */
async function apiRequest(endpoint, method = 'GET', body = null, token = null) {
    console.log(`API Request: ${method} ${endpoint}`, body);
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        method: method,
        headers: headers,
    };

    if (body && (method === 'POST' || method === 'PUT')) {
        config.body = JSON.stringify(body);
    }

    // This is a mock response area. Replace with actual fetch.
    if (endpoint.startsWith('/auth/token')) {
        return { ok: true, json: async () => ({ access_token: 'mock_jwt_token', token_type: 'bearer' }) };
    }
    if (endpoint.includes('generate-letter-preview')) {
        return { ok: true, json: async () => ({ content: "This is a letter preview from the LLM based on your request." }) };
    }
    if (endpoint.startsWith('/communications/debt/')) { // for logging
         return { ok: true, json: async () => ({ id: Date.now(), debt_id: body.debt_id, communication_type: body.communication_type, content_snapshot: body.content_snapshot, status: "Logged" }) };
    }

    // Default placeholder response for GET requests or unmocked POSTs
    return {
        ok: true,
        json: async () => {
            console.log("Returning generic placeholder JSON for", endpoint);
            if (endpoint.includes('/debts/') && !endpoint.includes('/communications')) return { id: endpoint.split('/')[2], customer_name: "Mock Customer", original_amount: "100.00", outstanding_amount: "50.00", due_date: "2023-01-01", status: "Overdue", notes:"Mock notes" };
            if (endpoint.includes('/debts')) return [{ id: 1, customer_name: "Mock Customer 1", outstanding_amount: "100.00" }];
            if (endpoint.includes('/communications/debt/')) return [{id: 1, type: "Email", summary: "Reminder sent"}];
            return { message: `Placeholder response for ${method} ${endpoint}` };
        }
    };
    // In a real implementation:
    // try {
    //     const response = await fetch(`/api/v1${endpoint}`, config); // Assuming an /api/v1 prefix for backend routes
    //     if (!response.ok) {
    //         const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    //         console.error('API Error:', response.status, errorData);
    //         alert(`Error: ${errorData.detail || 'API request failed'}`);
    //         return { ok: false, error: errorData, status: response.status };
    //     }
    //     return { ok: true, json: async () => response.json(), status: response.status };
    // } catch (error) {
    //     console.error('Network or other error:', error);
    //     alert(`Error: ${error.message || 'Network request failed'}`);
    //     return { ok: false, error: { detail: error.message } };
    // }
}

/**
 * Handles user login.
 */
async function loginUser(event) {
    event.preventDefault();
    console.log('loginUser function called');
    const form = event.target;
    const formData = new FormData(form);
    // In a real app, you'd use URLSearchParams or directly construct the body for OAuth2PasswordRequestForm
    // For this placeholder, we'll just log it. FastAPI expects x-www-form-urlencoded for OAuth2PasswordRequestForm.
    // This means apiRequest would need to be adapted or a different approach for login.
    // For simplicity, assuming apiRequest can handle FormData or adapts.

    const username = formData.get('username');
    const password = formData.get('password');
    console.log("Login attempt with:", username, password);

    // FastAPI's OAuth2PasswordRequestForm expects form data, not JSON
    const loginBody = new URLSearchParams();
    loginBody.append('username', username);
    loginBody.append('password', password);

    // Modify apiRequest or use fetch directly for x-www-form-urlencoded
    // For now, this will just log the attempt with placeholder apiRequest
    const response = await fetch('/api/v1/auth/token', { // Assuming /api/v1 prefix for backend
        method: 'POST',
        body: loginBody,
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    });

    if (response.ok) {
        const data = await response.json();
        console.log('Login successful:', data);
        localStorage.setItem('accessToken', data.access_token); // Placeholder for token storage
        alert('Login successful! Token stored.');
        // window.location.href = '/dashboard.html'; // Placeholder for redirect
    } else {
        const errorData = await response.json().catch(() => ({detail: "Login failed with status: " + response.status}));
        console.error('Login failed:', errorData);
        alert(`Login failed: ${errorData.detail}`);
    }
}

/**
 * Fetches and displays debts for a given business.
 */
async function fetchAndDisplayDebts(businessId) {
    console.log(`fetchAndDisplayDebts for businessId: ${businessId}`);
    const token = localStorage.getItem('accessToken');
    const response = await apiRequest(`/businesses/${businessId}/debts`, 'GET', null, token); // Example endpoint
    if (response.ok) {
        const debts = await response.json();
        console.log('Debts:', debts);
        // Placeholder for rendering debts to the page
        alert(`Fetched ${debts.length} debts for business ${businessId}. Check console.`);
    }
}

/**
 * Fetches and displays details for a specific debt and its communication logs.
 */
async function fetchAndDisplayDebtDetail(debtId) {
    console.log(`fetchAndDisplayDebtDetail for debtId: ${debtId}`);
    const token = localStorage.getItem('accessToken');
    const response = await apiRequest(`/debts/${debtId}`, 'GET', null, token); // Example endpoint
    if (response.ok) {
        const debtDetail = await response.json();
        console.log('Debt Detail:', debtDetail);
        // Placeholder for rendering debt details
        alert(`Fetched details for debt ${debtId}. Check console.`);
        await fetchAndDisplayCommunicationLogs(debtId);
    }
}

/**
 * Fetches and displays communication logs for a specific debt.
 */
async function fetchAndDisplayCommunicationLogs(debtId) {
    console.log(`fetchAndDisplayCommunicationLogs for debtId: ${debtId}`);
    const token = localStorage.getItem('accessToken');
    // Note: The router for communications is /communications/debt/{debt_id}
    const response = await apiRequest(`/communications/debt/${debtId}`, 'GET', null, token);
    if (response.ok) {
        const logs = await response.json();
        console.log('Communication Logs:', logs);
        // Placeholder for rendering logs
        alert(`Fetched ${logs.length} communication logs for debt ${debtId}. Check console.`);
    }
}

/**
 * Generates a letter preview.
 */
async function generateLetterPreview(event) {
    event.preventDefault();
    console.log('generateLetterPreview called');
    const form = event.target;
    const formData = new FormData(form);
    const debtId = formData.get('debt_id'); // Assuming a hidden input with debt_id in the form
    const letterType = formData.get('letter_type');
    const state = formData.get('state');
    const token = localStorage.getItem('accessToken');

    if (!debtId) {
        alert("Error: Debt ID is missing from the form.");
        return;
    }

    console.log(`Generating letter for Debt ID: ${debtId}, Type: ${letterType}, State: ${state}`);

    const body = { letter_type: letterType, state: state };
    // The endpoint is POST /actions/debts/{debt_id}/generate-letter-preview
    const response = await apiRequest(`/actions/debts/${debtId}/generate-letter-preview`, 'POST', body, token);

    const letterPreviewTextArea = document.getElementById('letterPreviewTextArea'); // Assumes this ID exists
    if (response.ok) {
        const data = await response.json();
        console.log('Letter preview generated:', data.content);
        if(letterPreviewTextArea) letterPreviewTextArea.value = data.content;
        else alert("Letter preview area not found, but content generated (check console).")
    } else {
        if(letterPreviewTextArea) letterPreviewTextArea.value = 'Error generating letter preview.';
        else alert("Error generating letter preview.")
    }
}

/**
 * Logs a sent letter as a communication.
 */
async function logSentLetter(event) {
    event.preventDefault();
    console.log('logSentLetter called');
    const form = event.target; // Assuming this event is from a form submission
    const debtId = form.dataset.debtId; // Assuming debt_id is stored in a data attribute of the form
    const letterContent = document.getElementById('letterPreviewTextArea')?.value;
    const letterType = form.dataset.letterType; // Assuming letter type is stored in a data attribute
    const token = localStorage.getItem('accessToken');

    if (!debtId || !letterContent || !letterType) {
        alert('Error: Missing data to log letter (Debt ID, content, or type).');
        return;
    }

    console.log(`Logging sent letter for Debt ID: ${debtId}, Type: ${letterType}`);

    const body = {
        debt_id: parseInt(debtId), // Ensure it's an integer if schema expects it
        communication_type: `Letter - ${letterType}`, // Example of a more descriptive type
        generated_content_snapshot: letterContent,
        status: 'Sent', // Or 'Logged', 'Pending Delivery'
        // llm_prompt_used and response_received could be null or set if available
    };

    // The endpoint is POST /communications/debt/{debt_id}
    const response = await apiRequest(`/communications/debt/${debtId}`, 'POST', body, token);

    if (response.ok) {
        const data = await response.json();
        console.log('Letter logged successfully:', data);
        alert('Letter logged as a communication.');
        await fetchAndDisplayCommunicationLogs(debtId); // Refresh logs display
    } else {
        alert('Failed to log letter.');
    }
}


// Event Listeners (add more as needed based on HTML structure)
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed");

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', loginUser);
        console.log("Login form event listener attached.");
    } else {
        console.log("Login form not found.");
    }

    const generateLetterForm = document.getElementById('generateLetterForm'); // Assumed ID for the form
    if (generateLetterForm) {
        generateLetterForm.addEventListener('submit', generateLetterPreview);
        console.log("Generate letter form event listener attached.");
    } else {
        console.log("Generate letter form not found.");
    }

    const logLetterForm = document.getElementById('logLetterForm'); // Assumed ID for a form/button to log
    if (logLetterForm) {
        // This might be a button click if the data comes from elsewhere, or form submission
        logLetterForm.addEventListener('submit', logSentLetter);
        console.log("Log letter form/button event listener attached.");
    } else {
        console.log("Log letter form/button not found.");
    }

    // Example: Attach to a button that fetches debts for a specific business
    // const viewDebtsButton = document.getElementById('viewDebtsButton');
    // if(viewDebtsButton) {
    //     viewDebtsButton.addEventListener('click', () => {
    //         const businessId = viewDebtsButton.dataset.businessId; // e.g. data-business-id="123"
    //         if(businessId) fetchAndDisplayDebts(businessId);
    //     });
    // }

    // Example: If debt details are loaded on a page, and a specific element triggers fetching logs
    // const debtDetailContainer = document.getElementById('debtDetailContainer');
    // if(debtDetailContainer) {
    //     const debtId = debtDetailContainer.dataset.debtId;
    //     if(debtId) fetchAndDisplayDebtDetail(debtId); // Or just fetchAndDisplayCommunicationLogs(debtId)
    // }

    // --- Dashboard specific calls ---
    const dashboardPageElement = document.getElementById('dashboardPage'); // Conceptual ID
    if (dashboardPageElement) {
        console.log("Dashboard page detected, fetching reports.");
        const selectedBusinessId = dashboardPageElement.dataset.businessId || '1'; // Get from data attribute or default
        if (selectedBusinessId) {
            fetchAndDisplayReportSummary(selectedBusinessId);
            fetchAndDisplayDebtStatusReport(selectedBusinessId);
        } else {
            console.warn("No business ID found for dashboard reports.");
        }
    }
});

/**
 * Fetches and displays the report summary for a given business.
 */
async function fetchAndDisplayReportSummary(businessId) {
    console.log(`Fetching report summary for businessId: ${businessId}`);
    const token = localStorage.getItem('accessToken');
    // Note: apiRequest already prefixes with /api/v1 if you set it up that way.
    // If not, ensure the full path is /api/v1/reports/summary/...
    // My current apiRequest doesn't prefix, so I add it here.
    const response = await apiRequest(`/api/v1/reports/summary/${businessId}`, 'GET', null, token);

    if (response.ok) {
        const data = await response.json();
        console.log('Report Summary:', data);

        // Placeholder for DOM manipulation
        // const totalOutstandingEl = document.getElementById('totalOutstandingDebt');
        // if (totalOutstandingEl) totalOutstandingEl.textContent = data.total_outstanding_debt;

        // const overdueAccountsEl = document.getElementById('overdueAccountsCount');
        // if (overdueAccountsEl) overdueAccountsEl.textContent = data.overdue_accounts_count;

        // const avgOverdueDaysEl = document.getElementById('averageOverdueDays');
        // if (avgOverdueDaysEl) avgOverdueDaysEl.textContent = parseFloat(data.average_overdue_days).toFixed(2);

        // Example: Update dashboard summary cards if they exist
        const totalOutstandingCard = document.querySelector('#dashboardTotalOutstanding p'); // More specific selector
        if (totalOutstandingCard) totalOutstandingCard.textContent = `$${parseFloat(data.total_outstanding_debt).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

        const overdueAccountsCard = document.querySelector('#dashboardOverdueAccounts p');
        if (overdueAccountsCard) overdueAccountsCard.textContent = data.overdue_accounts_count;

        const avgOverdueDaysCard = document.querySelector('#dashboardAvgOverdueDays p'); // New conceptual ID
        if (avgOverdueDaysCard) avgOverdueDaysCard.textContent = parseFloat(data.average_overdue_days).toFixed(1) + ' days';


    } else {
        console.error("Failed to fetch report summary:", response.error || `Status: ${response.status}`);
        // Placeholder for displaying error to user
        // const summaryContainer = document.getElementById('reportSummaryContainer');
        // if(summaryContainer) summaryContainer.innerHTML = "<p>Error loading summary.</p>";
    }
}

/**
 * Fetches and displays the debt status report for a given business.
 */
async function fetchAndDisplayDebtStatusReport(businessId) {
    console.log(`Fetching debt status report for businessId: ${businessId}`);
    const token = localStorage.getItem('accessToken');
    const response = await apiRequest(`/api/v1/reports/debt-status-breakdown/${businessId}`, 'GET', null, token);

    if (response.ok) {
        const data = await response.json();
        console.log('Debt Status Report:', data);

        // Placeholder for DOM manipulation
        const listElement = document.getElementById('debtStatusList'); // Assumed ID for a <ul> or <div>
        if (listElement) {
            listElement.innerHTML = ''; // Clear previous entries
            if (data.status_breakdown && data.status_breakdown.length > 0) {
                const ul = document.createElement('ul');
                data.status_breakdown.forEach(item => {
                    const li = document.createElement('li');
                    li.textContent = `${item.status}: ${item.count} debt(s) - Total $${parseFloat(item.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                    ul.appendChild(li);
                });
                listElement.appendChild(ul);
            } else {
                listElement.innerHTML = '<p>No debt status data available.</p>';
            }
        }
    } else {
        console.error("Failed to fetch debt status report:", response.error || `Status: ${response.status}`);
        // Placeholder for displaying error to user
        // const statusContainer = document.getElementById('debtStatusContainer');
        // if(statusContainer) statusContainer.innerHTML = "<p>Error loading status report.</p>";
    }
}
