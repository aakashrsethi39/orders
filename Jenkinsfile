pipeline {
    agent {
        label 'jenkins-agent'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Python Test') {
            steps {
                container('python') {
                    sh '''
                        echo "Python container is working"
                        python --version
                        python -m py_compile app.py
                        echo "Python syntax validation passed"
                    '''
                }
            }
        }
    }
}