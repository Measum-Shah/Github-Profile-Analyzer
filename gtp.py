import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, List
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                            QProgressBar, QMessageBox, QFrame, QStackedLayout, # Import QStackedLayout
                            QScrollArea) # Import QScrollArea for potentially long results
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QLinearGradient
from PyQt6.QtCore import QRect, QPoint
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6 import QtCore # Import QtCore module

class GitHubAPI:
    def __init__(self, token: str = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}" if self.token else "",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_user_profile(self, username: str) -> Dict:
        try:
            response = requests.get(
                f"{self.base_url}/users/{username}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch profile: {str(e)}")

    def get_user_repos(self, username: str) -> List:
        try:
            response = requests.get(
                f"{self.base_url}/users/{username}/repos?per_page=100",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch repositories: {str(e)}")

    def get_user_contributions(self, username: str) -> List:
        try:
            since = datetime.now() - timedelta(days=180)
            response = requests.get(
                f"{self.base_url}/users/{username}/events",
                headers=self.headers,
                params={"since": since.isoformat()},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch contributions: {str(e)}")

class GitHubProfileAnalyzer:
    def __init__(self, token: str = None):
        self.api = GitHubAPI(token)
        self.weights = {
            'activity': 0.3,
            'diversity': 0.2,
            'community': 0.2,
            'documentation': 0.15,
            'code_quality': 0.15
        }

    def analyze_profile(self, username: str) -> Dict:
        try:
            profile = self.api.get_user_profile(username)
            repos = self.api.get_user_repos(username)
            contributions = self.api.get_user_contributions(username)

            if not repos:
                raise Exception("No repositories found for this user")

            metrics = self._calculate_metrics(profile, repos, contributions)
            score = self._calculate_score(metrics)

            return {
                'score': round(score, 2),
                'metrics': metrics,
                'strengths': self._get_strengths(metrics),
                'weaknesses': self._get_weaknesses(metrics),
                'recommendations': self._get_recommendations(metrics),
                'appreciation': self._get_appreciation(score),
                'avatar_url': profile.get('avatar_url', '')
            }
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")

    def _calculate_metrics(self, profile: Dict, repos: List, contributions: List) -> Dict:
        metrics = {
            'activity': self._calculate_activity_metric(contributions, repos),
            'diversity': self._calculate_diversity_metric(repos),
            'community': self._calculate_community_metric(profile, repos),
            'documentation': self._calculate_documentation_metric(repos),
            'code_quality': self._calculate_code_quality_metric(repos)
        }
        return metrics

    def _calculate_activity_metric(self, contributions: List, repos: List) -> float:
        # Calculate based on recent activity and repository updates
        if not contributions:
            return 0.0
            
        # Count recent events
        recent_events = [e for e in contributions if datetime.fromisoformat(e['created_at'].replace('Z', '')) > datetime.now() - timedelta(days=30)]
        event_count = len(recent_events)
        
        # Count recently updated repos
        recent_repos = [r for r in repos if datetime.fromisoformat(r['updated_at'].replace('Z', '')) > datetime.now() - timedelta(days=90)]
        repo_count = len(recent_repos)
        
        # Normalize scores
        event_score = min(event_count / 30, 1.0)  # Max 30 events in 30 days
        repo_score = min(repo_count / len(repos), 1.0) if repos else 0.0
        
        return (event_score * 0.6 + repo_score * 0.4)

    def _calculate_diversity_metric(self, repos: List) -> float:
        if not repos:
            return 0.0
            
        # Count unique languages
        languages = set()
        for repo in repos:
            if repo['language']:
                languages.add(repo['language'])
        
        # Count repository topics
        topics = set()
        for repo in repos:
            if repo.get('topics'):
                topics.update(repo['topics'])
        
        # Normalize scores
        language_score = min(len(languages) / 5, 1.0)  # Max 5 languages
        topic_score = min(len(topics) / 10, 1.0)       # Max 10 topics
        
        return (language_score * 0.7 + topic_score * 0.3)

    def _calculate_community_metric(self, profile: Dict, repos: List) -> float:
        # Calculate based on followers, collaborations, and forks
        followers = profile.get('followers', 0)
        following = profile.get('following', 0)
        
        # Count forks and collaborations
        forks = sum(repo['forks_count'] for repo in repos)
        collaborations = sum(1 for repo in repos if repo['fork'])
        
        # Normalize scores
        follower_score = min(followers / 100, 1.0)        # Max 100 followers
        following_score = min(following / 50, 1.0)        # Max 50 following
        fork_score = min(forks / (len(repos) * 5), 1.0) if repos else 0.0  # Avg 5 forks per repo
        collab_score = min(collaborations / len(repos), 1.0) if repos else 0.0
        
        return (follower_score * 0.3 + following_score * 0.2 + fork_score * 0.3 + collab_score * 0.2)

    def _calculate_documentation_metric(self, repos: List) -> float:
        if not repos:
            return 0.0
            
        # Count repos with README, wiki, and good descriptions
        readme_count = 0
        wiki_count = 0
        description_count = 0
        
        for repo in repos:
            if repo['has_wiki']:
                wiki_count += 1
            if repo['description'] and len(repo['description']) > 20:
                description_count += 1
            # Check for README (this would ideally need API calls to check files)
            # We'll assume repos with descriptions likely have READMEs
            if repo['description']:
                readme_count += 1
                
        # Normalize scores
        readme_score = readme_count / len(repos)
        wiki_score = wiki_count / len(repos)
        description_score = description_count / len(repos)
        
        return (readme_score * 0.5 + wiki_score * 0.3 + description_score * 0.2)

    def _calculate_code_quality_metric(self, repos: List) -> float:
        if not repos:
            return 0.0
            
        # Calculate based on repo size, stars, and issues
        total_stars = sum(repo['stargazers_count'] for repo in repos)
        avg_stars = total_stars / len(repos)
        
        # Count repos with issues enabled
        issues_count = sum(1 for repo in repos if repo['has_issues'])
        
        # Calculate score based on size (smaller repos are often better maintained)
        size_score = 0
        for repo in repos:
            size = repo['size']
            if size < 1000:
                size_score += 1
            elif size < 5000:
                size_score += 0.5
                
        size_score = size_score / len(repos)
        
        # Normalize scores
        star_score = min(avg_stars / 10, 1.0)          # Avg 10 stars per repo
        issue_score = issues_count / len(repos)
        size_score = size_score
        
        return (star_score * 0.4 + issue_score * 0.3 + size_score * 0.3)

    def _calculate_score(self, metrics: Dict) -> float:
        total_score = 0.0
        for metric, weight in self.weights.items():
            total_score += metrics[metric] * weight
        return total_score * 10  # Scale to 0-10

    def _get_strengths(self, metrics: Dict) -> List[str]:
        strengths = []
        for metric, value in metrics.items():
            if value >= 0.7:  # 70% or higher is a strength
                strengths.append(f"Strong {metric.replace('_', ' ')} ({(value*100):.0f}%)")
        return strengths if strengths else ["No significant strengths identified"]

    def _get_weaknesses(self, metrics: Dict) -> List[str]:
        weaknesses = []
        for metric, value in metrics.items():
            if value <= 0.3:  # 30% or lower is a weakness
                weaknesses.append(f"Weak {metric.replace('_', ' ')} ({(value*100):.0f}%)")
        return weaknesses if weaknesses else ["No significant weaknesses identified"]

    def _get_recommendations(self, metrics: Dict) -> List[str]:
        recommendations = []
        
        if metrics['activity'] < 0.4:
            recommendations.append("Increase your activity by making regular commits and repository updates")
            
        if metrics['diversity'] < 0.4:
            recommendations.append("Expand your skill set by working with different programming languages")
            
        if metrics['community'] < 0.4:
            recommendations.append("Engage more with the community by contributing to other projects and following developers")
            
        if metrics['documentation'] < 0.4:
            recommendations.append("Improve documentation by adding README files, wikis, and clear descriptions")
            
        if metrics['code_quality'] < 0.4:
            recommendations.append("Focus on code quality by creating smaller, focused repositories with good issue tracking")
            
        return recommendations if recommendations else ["Keep doing what you're doing! Your profile is well-balanced"]

    def _get_appreciation(self, score: float) -> str:
        if score >= 8:
            return "Outstanding GitHub Profile! 🎉"
        elif score >= 6:
            return "Great GitHub Profile! 👍"
        elif score >= 4:
            return "Good Start! Keep Improving! 💪"
        else:
            return "Your GitHub Journey Has Just Begun! 🚀"

class AnimatedLabel(QLabel):
    gradient_pos_changed = pyqtSignal(float)
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._gradient_pos = 0.0
        
        # Register the property with Qt's property system
        self.setProperty("gradient_pos", 0.0)
        
        self.animation = QPropertyAnimation(self, b"gradient_pos")
        self.animation.setDuration(3000)
        self.animation.setLoopCount(-1)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.Linear)
        
        self.animation.stateChanged.connect(
            lambda state: print(f"Animation state changed: {state}")
        )
        self.animation.start()

    def get_gradient_pos(self):
        return self._gradient_pos

    def set_gradient_pos(self, value):
        value = float(value)
        if self._gradient_pos != value:
            self._gradient_pos = value
            self.gradient_pos_changed.emit(value)
            self.update()

    gradient_pos = QtCore.pyqtProperty(float, get_gradient_pos, set_gradient_pos, notify=gradient_pos_changed)

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            gradient = QLinearGradient(0.0, 0.0, float(self.width()), 0.0)
            gradient.setColorAt(max(0.0, self._gradient_pos - 0.5), QColor("#6366f1"))
            gradient.setColorAt(self._gradient_pos, QColor("#8b5cf6"))
            gradient.setColorAt(min(1.0, self._gradient_pos + 0.5), QColor("#6366f1"))
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawRect(self.rect())
            
            painter.setPen(QColor("#ffffff"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
        except Exception as e:
            print(f"Paint error: {str(e)}")
            raise

class AnalyzerThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, username, token=None):
        super().__init__()
        self.username = username
        self.token = token

    def run(self):
        try:
            analyzer = GitHubProfileAnalyzer(self.token)
            
            # Simulate progress updates
            for i in range(1, 101):
                self.msleep(30)
                self.progress.emit(i)
                
            result = analyzer.analyze_profile(self.username)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# New class for the results page
class ResultsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_styles() # Apply styles to this page

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Use a scroll area for the main content in case it's long
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(15)

        # Score card
        score_frame = QFrame()
        score_frame.setFrameShape(QFrame.Shape.StyledPanel)
        score_layout = QHBoxLayout(score_frame)
        
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(100, 100) # Slightly larger avatar
        self.avatar_label.setScaledContents(True)
        self.avatar_label.setStyleSheet("border-radius: 50px;") # Make it round

        self.score_label = QLabel()
        self.score_label.setFont(QFont("Arial", 36, QFont.Weight.Bold)) # Larger score font
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        score_layout.addWidget(self.avatar_label)
        score_layout.addSpacing(20) # Add space between avatar and score
        score_layout.addWidget(self.score_label, 1) # Stretch score label

        content_layout.addWidget(score_frame)

        # Metrics card
        metrics_frame = QFrame()
        metrics_frame.setFrameShape(QFrame.Shape.StyledPanel)
        metrics_layout = QVBoxLayout(metrics_frame)
        metrics_layout.addWidget(QLabel("<strong>Detailed Metrics:</strong>"))
        self.metrics_label = QLabel()
        self.metrics_label.setWordWrap(True)
        metrics_layout.addWidget(self.metrics_label)
        content_layout.addWidget(metrics_frame)

        # Strengths/Weaknesses cards
        sw_frame = QFrame()
        sw_layout = QHBoxLayout(sw_frame)
        
        strengths_frame = QFrame()
        strengths_frame.setFrameShape(QFrame.Shape.StyledPanel)
        strengths_layout = QVBoxLayout(strengths_frame)
        strengths_layout.addWidget(QLabel("<strong>Strengths</strong>"))
        self.strengths_label = QLabel()
        self.strengths_label.setWordWrap(True)
        strengths_layout.addWidget(self.strengths_label)
        sw_layout.addWidget(strengths_frame, 50)
        
        weaknesses_frame = QFrame()
        weaknesses_frame.setFrameShape(QFrame.Shape.StyledPanel)
        weaknesses_layout = QVBoxLayout(weaknesses_frame)
        weaknesses_layout.addWidget(QLabel("<strong>Weaknesses</strong>"))
        self.weaknesses_label = QLabel()
        self.weaknesses_label.setWordWrap(True)
        weaknesses_layout.addWidget(self.weaknesses_label)
        sw_layout.addWidget(weaknesses_frame, 50)
        content_layout.addWidget(sw_frame)

        # Recommendations card
        rec_frame = QFrame()
        rec_frame.setFrameShape(QFrame.Shape.StyledPanel)
        rec_layout = QVBoxLayout(rec_frame)
        rec_layout.addWidget(QLabel("<strong>Recommendations</strong>"))
        self.recommendations_label = QLabel()
        self.recommendations_label.setWordWrap(True)
        rec_layout.addWidget(self.recommendations_label)
        content_layout.addWidget(rec_frame)

        # Appreciation message
        self.appreciation_label = QLabel()
        self.appreciation_label.setWordWrap(True)
        self.appreciation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.appreciation_label)
        
        content_layout.addStretch() # Push content to the top

        layout.addWidget(scroll_area)

        # Add a back button
        self.back_button = QPushButton("Analyze Another Profile")
        self.back_button.setMinimumHeight(40)
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        # Connect this button later in MainWindow to switch back

        layout.addWidget(self.back_button)


    def setup_styles(self):
         # Styles specific to the ResultsPage or overrides
         self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e1e4e8;
                padding: 15px; /* Added padding to frames */
            }
            QLabel {
                font-size: 14px;
                color: #24292e;
            }
            QLabel strong { /* Style for strong tags within labels */
                font-weight: bold;
            }
            QPushButton {
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
                color: white;
                background-color: #0366d6; /* Use a different color for back button */
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #005cc5;
            }
            /* Inherit other styles from MainWindow if needed, or define here */
         """)


    def display_results(self, results: Dict):
        # Load avatar
        avatar_url = results.get('avatar_url')
        if avatar_url:
            try:
                response = requests.get(avatar_url, timeout=5)
                response.raise_for_status()
                avatar_pixmap = QPixmap()
                avatar_pixmap.loadFromData(response.content)
                # Scale pixmap to fit the label while maintaining aspect ratio
                scaled_pixmap = avatar_pixmap.scaled(self.avatar_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.avatar_label.setPixmap(scaled_pixmap)
            except requests.exceptions.RequestException as e:
                print(f"Failed to load avatar: {e}")
                self.avatar_label.clear() 
        else:
            self.avatar_label.clear()

        # Set score with color based on value
        score = results.get('score', 0.0)
        if score >= 8:
            color = "#2ea44f"  # Green
        elif score >= 5:
            color = "#e36209"  # Orange
        else:
            color = "#cb2431"   # Red
            
        self.score_label.setText(f"""
            <div style='font-size:48px; color:{color}'>{score:.2f}<span style='font-size:32px; color:#586069'>/10</span></div>
            <div style='font-size:16px; color:#586069'>Overall Profile Score</div>
        """)

        # Format metrics
        metrics = results.get('metrics', {})
        metrics_html = ""
        if metrics:
            for metric, value in metrics.items():
                percentage = int(value * 100)
                # Use the score color for the progress bar chunk
                metric_color = color 
                metrics_html += f"""
                <div style='margin-bottom:8px;'>
                    <div style='font-weight:bold;'>{metric.replace('_', ' ').title()}</div>
                    <div style='width:100%; height:20px; background:#f6f8fa; border-radius:3px; margin:3px 0;'>
                        <div style='width:{percentage}%; height:100%; background:{metric_color}; border-radius:3px;'></div>
                    </div>
                    <div style='text-align:right;'>{percentage}%</div>
                </div>
                """
        else:
             metrics_html += "No detailed metrics available."
        self.metrics_label.setText(metrics_html)

        # Format strengths and weaknesses
        strengths = results.get('strengths', ["No significant strengths identified"])
        weaknesses = results.get('weaknesses', ["No significant weaknesses identified"])
        recommendations = results.get('recommendations', ["No specific recommendations at this time."])
        appreciation = results.get('appreciation', "Analysis Complete.")

        self.strengths_label.setText("<br>• ".join([""] + strengths))
        self.weaknesses_label.setText("<br>• ".join([""] + weaknesses))
        self.recommendations_label.setText("<br>• ".join([""] + recommendations))
        
        self.appreciation_label.setText(f"""
            <div style='font-size:18px; font-weight:bold; margin:20px 0 10px;'>{appreciation}</div>
            <div style='color:#586069;'>Keep up the great work on your GitHub journey!</div>
        """)


# Modify MainWindow
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub Profile Evaluator")
        self.setMinimumSize(1000, 700)
        self.setup_ui()
        self.setup_animations() # Keep main window animations
        self.setup_styles()

    def show_input_page(self):
        """Switches back to the input page."""
        self.stacked_layout.setCurrentIndex(0)
        # Clear the username input field when going back
        self.username_input.clear()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Use QStackedLayout to switch between pages
        self.stacked_layout = QStackedLayout(central_widget)

        # --- Input Page ---
        self.input_page = QWidget()
        input_page_layout = QVBoxLayout(self.input_page)
        input_page_layout.setContentsMargins(30, 30, 30, 30)
        input_page_layout.setSpacing(20)

        # Header with animated title
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 30)
        
        self.title_label = AnimatedLabel("GitHub Profile Analyzer")
        self.title_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        self.title_label.setFixedHeight(60)
        header_layout.addWidget(self.title_label)

        # Animated subtitle
        self.subtitle_label = QLabel("Unlock Your GitHub Potential")
        self.subtitle_label.setFont(QFont("Arial", 16))
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.subtitle_label)
        input_page_layout.addWidget(header)

        # Introduction section
        intro_frame = QFrame()
        intro_frame.setFrameShape(QFrame.Shape.StyledPanel)
        intro_frame.setLineWidth(1)
        intro_layout = QVBoxLayout(intro_frame)
        
        self.intro_label = QLabel()
        intro_text = """
        <p style='text-align:center; font-size:14px; line-height:1.5'>
        Welcome to the <strong>GitHub Profile Analyzer</strong> - your comprehensive tool for evaluating 
        and improving your GitHub presence. Our advanced analysis examines five key dimensions of 
        your profile:<br><br>
        
        <strong>Activity</strong> - Your contribution frequency and consistency<br>
        <strong>Diversity</strong> - Range of technologies and projects<br>
        <strong>Community</strong> - Engagement with other developers<br>
        <strong>Documentation</strong> - Quality of your project documentation<br>
        <strong>Code Quality</strong> - Indicators of maintainable code practices<br><br>
        
        Enter your GitHub username below to receive your personalized score and improvement recommendations.
        </p>
        """
        self.intro_label.setText(intro_text)
        self.intro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro_layout.addWidget(self.intro_label)
        input_page_layout.addWidget(intro_frame)

        # Input section
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 20, 20, 20)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter GitHub username...")
        self.username_input.setMinimumHeight(40)
        
        self.analyze_button = QPushButton("Analyze Profile")
        self.analyze_button.setMinimumHeight(40)
        self.analyze_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_button.clicked.connect(self.start_analysis)
        
        input_layout.addWidget(self.username_input, 70)
        input_layout.addWidget(self.analyze_button, 30)
        input_page_layout.addWidget(input_frame)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        input_page_layout.addWidget(self.progress_bar)

        input_page_layout.addStretch() # Push content to the top

        # --- Results Page ---
        self.results_page = ResultsPage()
        self.results_page.back_button.clicked.connect(self.show_input_page) # Connect back button

        # Add pages to stacked layout
        self.stacked_layout.addWidget(self.input_page) # Index 0
        self.stacked_layout.addWidget(self.results_page) # Index 1

        # Set initial page
        self.stacked_layout.setCurrentIndex(0)


    def setup_animations(self):
        # Subtitle animation
        self.subtitle_label.setGraphicsEffect(QGraphicsOpacityEffect())
        self.subtitle_label.graphicsEffect().setOpacity(0.0)
        # Subtitle animation using graphics effect's opacity
        self.subtitle_animation = QPropertyAnimation(
            self.subtitle_label.graphicsEffect(), 
            b"opacity"
        )
        self.subtitle_animation.setDuration(2000)
        self.subtitle_animation.setStartValue(0.0)
        self.subtitle_animation.setEndValue(1.0)
        self.subtitle_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.subtitle_animation.start()

        # Progress bar animation
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(300)
        self.progress_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    def setup_styles(self):
        # Styles for the main window and common elements
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e1e4e8;
            }
            QLineEdit {
                padding: 10px 15px;
                font-size: 14px;
                border: 1px solid #d1d5da;
                border-radius: 6px;
                background-color: white;
                color: #24292e;  /* Added text color */
            }
            QPushButton {
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
                color: white;
                background-color: #2ea44f;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2c974b;
            }
            QPushButton:disabled {
                background-color: #94d3a2;
            }
            QProgressBar {
                border-radius: 4px;
                border: 1px solid #d1d5da;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2ea44f;
                border-radius: 3px;
            }
            QLabel {
                font-size: 14px;
                color: #24292e;
            }
            /* Styles for the ResultsPage are defined within ResultsPage.setup_styles */
        """)

    def start_analysis(self):
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Input Error", "Please enter a GitHub username")
            return

        self.analyze_button.setEnabled(False)
        # self.results_container.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.analyzer_thread = AnalyzerThread(username)
        self.analyzer_thread.finished.connect(self.show_results)
        self.analyzer_thread.error.connect(self.show_error)
        self.analyzer_thread.progress.connect(self.update_progress)
        self.analyzer_thread.start()

    def update_progress(self, value):
        self.progress_animation.setStartValue(self.progress_bar.value())
        self.progress_animation.setEndValue(value)
        self.progress_animation.start()

    def show_results(self, results):
        print("Analysis finished. Results received:")
        print(results) # Print the entire results dictionary
        print(f"Avatar URL: {results.get('avatar_url')}") # Check specific keys
        print(f"Score: {results.get('score')}")
        print(f"Metrics: {results.get('metrics')}")
        print(f"Strengths: {results.get('strengths')}")
        print(f"Weaknesses: {results.get('weaknesses')}")
        print(f"Recommendations: {results.get('recommendations')}")
        print(f"Appreciation: {results.get('appreciation')}")

        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        # self.results_container.setVisible(True)

        # Load avatar (This logic should be in ResultsPage.display_results now)
        # avatar_pixmap = QPixmap()
        # avatar_pixmap.loadFromData(requests.get(results['avatar_url']).content)
        # self.avatar_label.setPixmap(avatar_pixmap) # Remove this line

        # Set score with color based on value (This logic should be in ResultsPage.display_results now)
        # score = results['score']
        # if score >= 8:
        #     color = "#2ea44f"  # Green
        # elif score >= 5:
        #     color = "#e36209"  # Orange
        # else:
        #     color = "#cb2431"   # Red
            
        # self.score_label.setText(f"""
        #     <div style='font-size:36px; color:{color}'>{score}<span style='font-size:24px; color:#586069'>/10</span></div>
        #     <div style='font-size:14px; color:#586069'>Overall Profile Score</div>
        # """) # Remove this block

        # Format metrics (This logic should be in ResultsPage.display_results now)
        # metrics_html = "<strong>Detailed Metrics:</strong><br><br>"
        # for metric, value in results['metrics'].items():
        #     percentage = int(value * 100)
        #     metrics_html += f"""
        #     <div style='margin-bottom:8px;'>
        #         <div style='font-weight:bold;'>{metric.replace('_', ' ').title()}</div>
        #         <div style='width:100%; height:20px; background:#f6f8fa; border-radius:3px; margin:3px 0;'>
        #             <div style='width:{percentage}%; height:100%; background:{color}; border-radius:3px;'></div>
        #         </div>
        #         <div style='text-align:right;'>{percentage}%</div>
        #     </div>
        #     """
        # self.metrics_label.setText(metrics_html) # Remove this block

        # Format strengths and weaknesses (This logic should be in ResultsPage.display_results now)
        # self.strengths_label.setText("<br>• ".join([""] + results['strengths'])) # Remove this line
        # self.weaknesses_label.setText("<br>• ".join([""] + results['weaknesses'])) # Remove this line
        # self.recommendations_label.setText("<br>• ".join([""] + results['recommendations'])) # Remove this line
        # self.appreciation_label.setText(f"""
        #     <div style='font-size:16px; font-weight:bold; margin:20px 0 10px;'>{results['appreciation']}</div>
        #     <div style='color:#586069;'>Keep up the great work on your GitHub journey!</div>
        # """) # Remove this block

        # Display results on the results page and switch to it
        self.results_page.display_results(results)
        self.stacked_layout.setCurrentIndex(1) # Switch to the results page


    def show_error(self, error_message):
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(
            self, 
            "Analysis Error",
            f"<strong>We couldn't analyze this GitHub profile.</strong><br><br>"
            f"Error details: {error_message}<br><br>"
            "Please check that:<br>"
            "• The username is correct<br>"
            "• The profile is not private<br>"
            "• You have a stable internet connection"
        )

def main():
    load_dotenv()
    app = QApplication(sys.argv)
    
    # Set application style and font
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()