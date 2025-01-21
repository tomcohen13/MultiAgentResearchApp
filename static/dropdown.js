const dropdownButton = document.getElementById('dropdownButton');
const dropdownMenu = document.getElementById('dropdownMenu');
const dropdownItems = document.querySelectorAll('.dropdown-items');

// Toggle dropdown visibility
dropdownButton.addEventListener('click', () => {
    dropdownMenu.classList.toggle('show');
    dropdownButton.classList.toggle('open');
});

window.selectedSymptom = null;

// Handle option selection
dropdownItems.forEach(item => {
    item.addEventListener('click', (event) => {

        if (item.classList.contains('disabled')) return;

        window.selectedSymptom = event.target.getAttribute('data-value');
        const selectedText = event.target.textContent;

        // Update button text with the selected option
        dropdownButton.textContent = selectedText;

        // Collapse the dropdown
        dropdownMenu.classList.remove('show');
        dropdownButton.classList.remove('open');

    });
});

// Close dropdown if clicking outside
document.addEventListener('click', (event) => {
    if (!dropdownButton.contains(event.target) && !dropdownMenu.contains(event.target)) {
        dropdownMenu.classList.remove('show');
        dropdownButton.classList.remove('open');
    }
});