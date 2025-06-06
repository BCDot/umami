# Manual Testing Guide

This document outlines manual testing steps for the application, categorized by feature. Ensure you have followed the setup instructions in `README.md` before proceeding.

## General Instructions for Testers:

*   **Environment**: Perform tests in a clean environment with the backend server running and necessary configurations (like `.env`) in place.
*   **Data**: Use a mix of valid and invalid data to test form submissions and error handling.
*   **Browser**: Use a modern web browser (e.g., Chrome, Firefox). Note any browser-specific issues.
*   **DevTools**: Keep your browser's developer console open (usually F12) to check for client-side errors or failed network requests.
*   **Documentation**: For each step, note the action, input provided, expected outcome, and actual outcome.

---

## 1. Authentication

Access the application frontend, typically starting with `http://localhost:8000/static/templates/login.html`.

*   **Test User Registration:**
    *   **Action**: Navigate to the registration page (if separate from login, or if login page has a "register" link). Fill out the registration form.
    *   **Input**: Valid and unique username, email, and a strong password.
    *   **Expected Outcome**: Successful registration, user is possibly auto-logged in and redirected to a dashboard/home page. A success message should appear.
*   **Test User Login (Valid Credentials):**
    *   **Action**: Navigate to the login page. Enter credentials of a registered user.
    *   **Input**: Correct username/email and password.
    *   **Expected Outcome**: Successful login, user is redirected to a protected area (e.g., dashboard). A success message may appear.
*   **Test User Login (Invalid Credentials):**
    *   **Action**: Navigate to the login page. Enter incorrect credentials.
    *   **Input**: Incorrect username/email or password.
    *   **Expected Outcome**: Login fails, an error message is displayed on the login page (e.g., "Invalid credentials"). User remains on the login page.
*   **Test User Logout:**
    *   **Action**: Once logged in, find and click the "Logout" button/link.
    *   **Input**: N/A.
    *   **Expected Outcome**: User is logged out and redirected to the login page or a public home page. A success message may appear.
*   **Test Access to Protected Resources (Not Logged In):**
    *   **Action**: Attempt to directly navigate to a URL that should require login (e.g., `/static/templates/dashboard.html` or an API endpoint for business data).
    *   **Input**: N/A.
    *   **Expected Outcome**: User is redirected to the login page, or an "Unauthorized" / "Access Denied" error message is shown.
*   **Test Access to Protected Resources (Logged In):**
    *   **Action**: After logging in, navigate to various protected pages/sections (e.g., dashboard, business management).
    *   **Input**: N/A.
    *   **Expected Outcome**: User can access these pages and see relevant content.

---

## 2. Business Management

Ensure you are logged in before proceeding with these tests.

*   **Navigate to Business Management Section:**
    *   **Action**: Find and click the link/menu item for "Businesses" or "Manage Businesses".
    *   **Input**: N/A.
    *   **Expected Outcome**: User is taken to a page listing existing businesses or offering an option to create one.
*   **Test Creating a New Business (Valid Data):**
    *   **Action**: Click "Add Business" or similar. Fill out the form with all required and valid information.
    *   **Input**: Valid business name, address, contact info, etc.
    *   **Expected Outcome**: Business is created successfully. A success message is shown. The new business appears in the list of businesses.
*   **Test Creating a New Business (Invalid/Missing Data):**
    *   **Action**: Attempt to create a business by leaving required fields blank or entering invalid data (e.g., incorrect email format).
    *   **Input**: Incomplete or malformed data.
    *   **Expected Outcome**: Form submission fails. Validation error messages are displayed next to the problematic fields or in a summary area. The business is not created.
*   **Test Viewing List of Businesses:**
    *   **Action**: Navigate to the main business listing page.
    *   **Input**: N/A (assuming some businesses exist).
    *   **Expected Outcome**: A list/table of businesses is displayed, showing key information (e.g., name, contact).
*   **Test Viewing Details of a Specific Business:**
    *   **Action**: From the list, click on a specific business's name or a "View Details" link.
    *   **Input**: N/A.
    *   **Expected Outcome**: User is taken to a page showing detailed information about the selected business.
*   **Test Editing an Existing Business (Valid Data):**
    *   **Action**: Navigate to a business's detail page, find and click "Edit Business". Modify some fields with valid data.
    *   **Input**: Updated valid business information.
    *   **Expected Outcome**: Business details are updated successfully. A success message is shown. The updated information is reflected in the business list and detail view.
*   **Test Deleting a Business:**
    *   **Action**: From a business's detail page or list, find and click "Delete Business". Confirm the deletion if prompted.
    *   **Input**: N/A.
    *   **Expected Outcome**: Business is deleted. A success message is shown. The business no longer appears in the list. Associated customers/debts might also be affected (verify application logic).

---

## 3. Customer Management

Ensure you are logged in and at least one business exists.

*   **Navigate to Customer Management for a Business:**
    *   **Action**: View a specific business's details. Find a link/tab for "Customers" or "Manage Customers" for that business.
    *   **Input**: N/A.
    *   **Expected Outcome**: User is taken to a page listing customers for the selected business or offering to create one.
*   **Test Creating a New Customer (Valid Data):**
    *   **Action**: Click "Add Customer". Fill out the form with valid information.
    *   **Input**: Valid customer name, email, phone, address, etc., associated with the current business.
    *   **Expected Outcome**: Customer is created. Success message shown. New customer appears in the list for that business.
*   **Test Creating a New Customer (Invalid/Missing Data):**
    *   **Action**: Attempt to create a customer with missing required fields or invalid data.
    *   **Input**: Incomplete or malformed data.
    *   **Expected Outcome**: Form fails. Validation errors displayed. Customer not created.
*   **Test Viewing List of Customers:**
    *   **Action**: Navigate to the customer listing page for a specific business.
    *   **Input**: N/A (assuming customers exist for the business).
    *   **Expected Outcome**: List/table of customers for the selected business is displayed.
*   **Test Viewing Details of a Specific Customer:**
    *   **Action**: From the list, click on a customer's name or "View Details".
    *   **Input**: N/A.
    *   **Expected Outcome**: Detailed information for the selected customer is shown.
*   **Test Editing an Existing Customer (Valid Data):**
    *   **Action**: Go to a customer's detail page, click "Edit Customer". Modify fields with valid data.
    *   **Input**: Updated valid customer information.
    *   **Expected Outcome**: Customer details updated. Success message. Changes reflected.
*   **Test Deleting a Customer:**
    *   **Action**: From a customer's detail page or list, click "Delete Customer". Confirm if prompted.
    *   **Input**: N/A.
    *   **Expected Outcome**: Customer deleted. Success message. Customer removed from the list. Associated debts might also be affected.

---

## 4. Debt Management

Ensure you are logged in, a business exists, and at least one customer exists for that business.

*   **Navigate to Debt Management for a Customer:**
    *   **Action**: View a specific customer's details. Find a link/tab for "Debts" or "Manage Debts" for that customer.
    *   **Input**: N/A.
    *   **Expected Outcome**: User is taken to a page listing debts for the selected customer or offering to create one.
*   **Test Creating a New Debt (Valid Data):**
    *   **Action**: Click "Add Debt". Fill out with valid amount, due date, status (e.g., "Pending", "Overdue"), description.
    *   **Input**: Valid debt details.
    *   **Expected Outcome**: Debt created. Success message. New debt in the list for that customer.
*   **Test Creating a New Debt (Invalid/Missing Data):**
    *   **Action**: Attempt to create debt with missing amount, invalid date format, etc.
    *   **Input**: Incomplete or malformed data.
    *   **Expected Outcome**: Form fails. Validation errors. Debt not created.
*   **Test Viewing List of Debts:**
    *   **Action**: Navigate to the debt listing page for a specific customer.
    *   **Input**: N/A (assuming debts exist).
    *   **Expected Outcome**: List/table of debts for the selected customer.
*   **Test Viewing Details of a Specific Debt:**
    *   **Action**: From the list, click on a debt's identifier or "View Details".
    *   **Input**: N/A.
    *   **Expected Outcome**: Detailed information for the selected debt.
*   **Test Editing an Existing Debt:**
    *   **Action**: Go to a debt's detail page, click "Edit Debt". Update status, amount, or due date.
    *   **Input**: Updated valid debt information.
    *   **Expected Outcome**: Debt details updated. Success message. Changes reflected.
*   **Test Deleting a Debt:**
    *   **Action**: From a debt's detail page or list, click "Delete Debt". Confirm.
    *   **Input**: N/A.
    *   **Expected Outcome**: Debt deleted. Success message. Debt removed from the list.

---

## 5. Letter Generation

Ensure `LLM_API_KEY` is configured in your `.env` file (as per `README.md`) and at least one debt exists.

*   **Navigate to Letter Generation:**
    *   **Action**: Go to a specific debt's detail page. Look for a "Generate Letter", "Preview Letter", or similar button/section.
    *   **Input**: N/A.
    *   **Expected Outcome**: Interface for letter generation/preview is displayed.
*   **Trigger Letter Generation/Preview:**
    *   **Action**: Click the button to generate or preview the letter.
    *   **Input**: May involve selecting a letter template if multiple are available.
    *   **Expected Outcome**: A preview of the dunning letter, populated with debt and customer details, is shown on the screen. Content should be appropriate for the debt's status.
*   **Verify Letter Preview Content:**
    *   **Action**: Read through the previewed letter.
    *   **Input**: N/A.
    *   **Expected Outcome**: Customer name, debt amount, due dates, business name, etc., are correctly inserted into the letter template. The tone and content match the debt's severity/status.
*   **Test "Log Sent Letter" Functionality:**
    *   **Action**: After previewing, if there's an option to "Log Letter Sent" or "Mark as Sent", click it.
    *   **Input**: May involve adding a note or confirming the date.
    *   **Expected Outcome**: A communication log entry is created for the debt, indicating a letter was sent. This might be visible in a "Communications" tab or history section for the debt/customer. Success message.
*   **Test with `LLM_API_KEY` Not Configured (Optional):**
    *   **Action**: If you can, temporarily remove or invalidate the `LLM_API_KEY` in `.env` (and restart the server). Attempt to access letter generation.
    *   **Input**: N/A.
    *   **Expected Outcome**: The letter generation feature should be gracefully disabled, or a clear error message should inform the user that the LLM service is unavailable. The application should not crash.

---

## 6. Reporting

Ensure you are logged in and some data (businesses, customers, debts) exists.

*   **Navigate to Reporting Section:**
    *   **Action**: Find and click the link/menu item for "Reports".
    *   **Input**: N/A.
    *   **Expected Outcome**: User is taken to a reporting dashboard or a page with links to different reports.
*   **Test Accessing Financial Summary Report:**
    *   **Action**: Click on "Financial Summary" or similar report link.
    *   **Input**: May involve selecting a date range or business if applicable.
    *   **Expected Outcome**: A report is displayed showing financial metrics like total debt outstanding, total collected, etc. Data should appear reasonable based on test data.
*   **Test Accessing Debt Status Report:**
    *   **Action**: Click on "Debt Status Report" or similar.
    *   **Input**: May involve filtering by status, date range, or business.
    *   **Expected Outcome**: A report is displayed showing counts or amounts of debts by status (e.g., "Pending", "Overdue", "Paid"). Data should be consistent with existing debt information.
*   **Verify Report Data:**
    *   **Action**: Briefly check if the numbers and summaries in the reports make sense relative to the data you've entered during testing.
    *   **Input**: N/A.
    *   **Expected Outcome**: Reports are not empty (if data exists) and reflect the underlying data, even if simplified for testing.

---

## 7. General User Interface (UI) / User Experience (UX)

These checks should be performed continuously throughout all other testing.

*   **Global Messages (Notifications):**
    *   **Observation**: After actions like creating, updating, or deleting items, check if clear success or error messages (e.g., toasts, banners) are displayed.
    *   **Expected Outcome**: Informative messages guide the user and confirm actions.
*   **Loading Indicators:**
    *   **Observation**: When data is being fetched (e.g., loading a list) or a process is running (e.g., generating a letter), check for loading spinners or indicators.
    *   **Expected Outcome**: Users are informed that the system is working, preventing confusion on slow connections or operations.
*   **Navigation Intuition:**
    *   **Observation**: Is it easy to find different sections of the application? Are breadcrumbs or clear menu structures present?
    *   **Expected Outcome**: Users can navigate the application without getting lost or confused.
*   **Form Clarity:**
    *   **Observation**: Are form fields clearly labeled? Is it obvious what information is required? Are input types appropriate (e.g., date pickers for dates)?
    *   **Expected Outcome**: Forms are easy to understand and complete.
*   **Layout Issues / Broken Elements:**
    *   **Observation**: Look for any visual glitches, misaligned elements, overlapping text, or non-functional buttons/links.
    *   **Expected Outcome**: The UI is clean, organized, and all interactive elements work.
*   **Responsiveness (If Applicable):**
    *   **Action**: If the application is intended to be responsive, resize your browser window to simulate different screen sizes (desktop, tablet, mobile).
    *   **Observation**: Does the layout adapt reasonably? Is content still readable and usable on smaller screens?
    *   **Expected Outcome**: The application provides a good user experience across various device sizes.

---

This guide provides a baseline for manual testing. Testers are encouraged to explore edge cases and combinations of actions not explicitly listed.
