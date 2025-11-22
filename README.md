# Final_Systems
1) Executive Summary
Problem: UVA Students have a GroupMe called WahooSwaps, the concept is to post anything that you no longer want or are selling at a discounted price. However, if you see something that you liked in the morning and then go to look at it again in the afternoon you will find that many other things have been posted since then making it hard to find what it is you wanted. This is inconvient because sometimes you see something you like but don't have the time to text the person then and there.
Solution: My solution to this would be creating a website in which you don't have to scroll through what people texted in response to an item, but just scroll through the items like a shopping website. This makes it easier to find what it is that you are looking for and contact the person about possibly inquiring more information than already provided.
2) System Overview
Course Concept(s): Cloud Storage (Azure Blob Storage for images), RESTful API Design (Flask endpoints), Web Application Devlopment (Full-stack Flask app), Cloud Deployment (Azure App Service)
Architecture Diagram: Include a PNG in /assets and embed it here.
Data/Models/Services: List sources, sizes, formats, and licenses.
3) How to Run (Local)
Choose Docker or Apptainer and provide a single command. Example:
Docker
# build
docker build -t myapp:latest .
# run
docker run --rm -p 8080:8080 --env-file .env myapp:latest
# health check (if applicable)
curl http://localhost:8080/health
Apptainer
# build
apptainer build project.sif project.def
# run (bind your repo if needed)
apptainer run --env-file .env project.sif
# health check (if applicable)
curl http://127.0.0.1:5000/api/v1/health
4) Design Decisions
I chose to make a website because it is convenient. It is better than 
Tradeoffs: Performance, cost, complexity, maintainability.
Security/Privacy: Secrets mgmt, input validation, PII handling.
Ops: Logs/metrics, scaling considerations, known limitations.
5) Results & Evaluation
Screenshots or sample outputs (place assets in /assets).
Brief performance notes or resource footprint (if relevant).
Validation/tests performed and outcomes.
6) What’s Next
Planned improvements, refactors, and stretch features.
7) Links (Required)
GitHub Repo: https://github.com/evelynxanaxia/Final_Systems
Public Cloud App (optional): https://collegemarketplace-grdnfmfwayddbva2.canadacentral-01.azurewebsites.net/ 