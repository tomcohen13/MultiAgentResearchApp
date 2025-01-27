

document.getElementById('startResearch').addEventListener('click', async () => {
    // hide header to get more space
    const header = document.getElementById("fadeInHeader")
    header.style.display = "none";
    // get user's search criteria
    const searchCriteria = [...document.querySelectorAll( ":checked" )].map( e => e.id)
    const userInput = document.getElementById('userInput').value;
    // post a loading message
    var report = document.getElementById('report')

    // make a GET request to server
    criteriaString = searchCriteria.join(";")
    const response = await fetch(
        '/research?' + new URLSearchParams({ company: userInput, criteria: criteriaString}).toString(), {}
    );
    // TextDecoder to decode chunks
    const decoder = new TextDecoder(); 
    const reader = response.body.getReader();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Decode and append the chunk
        const chunk = decoder.decode(value, { stream: true });

        // Populate the report area
        report.innerHTML = chunk; 
    }

});
