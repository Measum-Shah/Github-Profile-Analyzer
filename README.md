# Github-Profile-Analyzer

A powerful tool to evaluate and improve your GitHub profile by analyzing key metrics across multiple dimensions. Get personalized insights and recommendations to enhance your GitHub presence.

## Features

- **Comprehensive Analysis**: Evaluates your profile across 5 key dimensions:
  - Activity: Contribution frequency and consistency
  - Diversity: Range of technologies and projects
  - Community: Engagement with other developers
  - Documentation: Quality of project documentation
  - Code Quality: Indicators of maintainable code practices

- **Visual Dashboard**: Beautiful, animated interface with clear metrics visualization
- **Personalized Recommendations**: Actionable suggestions to improve your profile
- **Score System**: 0-10 rating with detailed breakdown
- **Strengths & Weaknesses**: Highlights your profile's strong and weak areas

## Installation

### Prerequisites
- Python 3.8+
- GitHub account
- (Optional) GitHub Personal Access Token for higher rate limits

### Setup

1. Clone the repository:
```
bash
git clone https://github.com/yourusername/github-profile-analyzer.git
cd github-profile-analyzer
Create and activate a virtual environment:

bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install dependencies:

bash
pip install -r requirements.txt
(Optional) Create a .env file and add your GitHub token:

env
GITHUB_TOKEN=your_personal_access_token_here
Usage
Run the application:

bash
python main.py
Enter any GitHub username in the input field and click "Analyze Profile" to get started.
```

#How It Works
The analyzer calculates scores based on:

Activity: Recent commits, repository updates, and event frequency

Diversity: Programming languages used and repository topics

Community: Followers, following, forks, and collaborations

Documentation: README files, wikis, and repository descriptions

Code Quality: Repository size, stars, and issue tracking

Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements.

License
This project is licensed under the MIT License - see the LICENSE file for details.

Acknowledgments
GitHub API for providing the data

PyQt6 for the beautiful interface

All open source contributors





