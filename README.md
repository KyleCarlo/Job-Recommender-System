# Personalized Job Recommender System
This repository contains the source code and data for a personalized job recommender system, developed as a major course output for DATA102. The project aims to address the challenges job seekers face when navigating the overwhelming number of job listings across various online platforms.

The core of this system is a personalized recommendation engine that scrapes job search websites and provides highly relevant, customized job opportunities to each user. By doing so, it significantly reduces the time, effort, and stress associated with a traditional job search.

# Problem Statement
The modern job market is saturated with job postings on diverse platforms, leading to a generic and often frustrating browsing experience for job seekers. They are forced to manually filter through countless irrelevant listings and re-enter qualifications repeatedly. This project tackles this issue by providing a more intelligent, efficient, and personalized solution.

# Collaborators:
- Hinolan, Charles
- Lasala, Kyle
- Lorenzo, Antonio
- Roco, Katrina

# How it Works
The system operates by performing a series of interconnected steps to deliver personalized recommendations:

1. Scraping Job Listings: The system gathers raw data from multiple job search websites. This process is more sophisticated than a simple crawl; it is designed to extract key information from each listing, including the job title, company, full description, required skills, and location. This ensures the recommendation engine has a rich dataset to work with.

2. User Profiling: The system creates a detailed profile for each user. This goes beyond a basic resume by incorporating user-provided information such as their career goals, preferred industries, and salary expectations. This comprehensive profile serves as the benchmark against which job listings are compared.

3. Content-Based Filtering with Semantic Analysis: This is the heart of the recommendation engine. By using advanced natural language processing models from the sentence-transformers library, the system transforms both the user's profile and the job descriptions into numerical vectors (embeddings). This allows the system to understand the semantic meaning and context of the text, rather than just matching keywords. It then calculates the similarity between the user's profile vector and the vector of each job listing to identify the most relevant opportunities.

4. Generating Recommendations: After a comprehensive similarity analysis, the system presents a curated and ranked list of job opportunities. The results are highly tailored to the individual user’s needs, and the ranking ensures that the most relevant and suitable jobs are displayed at the top. This final output is a list of highly personalized recommendations that significantly streamline the job search process.

This project notebook provides a detailed walkthrough of the data collection, model development, and implementation process.
