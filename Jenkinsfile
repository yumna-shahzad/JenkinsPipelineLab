pipeline {
    agent any

    stages {

        stage('Build') {
            steps {
                echo "Installing dependencies..."
                bat 'python -m pip install --upgrade pip'
                bat 'pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                echo "Running basic tests..."
                bat 'python -m py_compile app.py'
            }
        }

        stage('Deploy') {
            steps {
                echo "Starting Flask application..."
                bat 'start /B python app.py'
                echo "Flask app started successfully."
            }
        }
    }
}
