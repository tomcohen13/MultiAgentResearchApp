

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
        '/research?' + new URLSearchParams({ company: userInput, criteria: criteriaString}).toString(), 
        {
            method: "GET",
            headers: {"Content-Type": "text/html"},

        }
    );
    // TextDecoder to decode chunks
    const decoder = new TextDecoder(); 
    const reader = response.body.getReader();
    var streamingReport = false;
    var output = ""

    while (true) {
        const { done, value } = await reader.read();

        // Decode and append the chunk
        const chunk = decoder.decode(value);

        if (chunk == "<REPORT_STREAM>"){
            console.log("streaming report...")
            // clean screen
            output = '';
            // from now on add input 
            streamingReport = true
        }
        else if (streamingReport == true){
            output += chunk
        }
        else {
            output = chunk
        }
        report.innerHTML = output
        if (done) break;
    }

});
