document.addEventListener("DOMContentLoaded", function () {
    const header = document.getElementById("fadeInHeader");
    const text = header.textContent; // Get the header text
    header.textContent = ""; // Clear the original text

    // Split text into letters and spaces
    text.split("").forEach((char, index) => {
        const span = document.createElement("span");

        if (char === " ") {
            // Preserve spaces
            span.innerHTML = "&nbsp;"; // Non-breaking space for visibility
        } else {
            span.textContent = char;
        }

        span.style.opacity = 0; // Start with invisible letters
        span.style.animation = `fade-in 1s ease ${index * 0.05}s forwards`; // Delay increases per character
        header.appendChild(span);
    });
});
