pipeline {

    agent {
        kubernetes {
            inheritFrom 'jenkins-agent'

            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:

    # Python container
    - name: python
      image: python:3.12-slim
      command:
        - sleep
      args:
        - infinity
      tty: true
      volumeMounts:
        - name: workspace-volume
          mountPath: /home/jenkins/agent

    # Kaniko container
    - name: kaniko
      image: gcr.io/kaniko-project/executor:debug
      command:
        - /busybox/sh
      args:
        - -c
        - sleep infinity
      tty: true
      volumeMounts:
        - name: workspace-volume
          mountPath: /home/jenkins/agent

    # Git container
    - name: git
      image: alpine/git:latest
      command:
        - sleep
      args:
        - infinity
      tty: true
      volumeMounts:
        - name: workspace-volume
          mountPath: /home/jenkins/agent
'''
        }
    }

    environment {
        AWS_REGION = 'ap-south-1'
        ECR_REGISTRY = '482311061933.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_REPOSITORY = 'orders'
        IMAGE_TAG = "${BUILD_NUMBER}"

        GITOPS_REPO = 'https://github.com/aakashrsethi39/k8s-gitops-config.git'
        GITOPS_FILE = 'environments/production/orders-values.yaml'
    }

    stages {

        stage('Python Test') {
            steps {
                container('python') {
                    sh '''
                        echo "======================================"
                        echo "Python Test"
                        echo "======================================"

                        python --version

                        echo "Validating application..."
                        python -m py_compile app.py

                        echo "Python validation successful"
                    '''
                }
            }
        }

        stage('Build and Push Image') {
            steps {
                container('kaniko') {
                    sh '''
                        echo "======================================"
                        echo "Building and Pushing Docker Image"
                        echo "======================================"

                        echo "Image:"
                        echo "${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"

                        /kaniko/executor \
                          --context "${WORKSPACE}" \
                          --dockerfile "${WORKSPACE}/Dockerfile" \
                          --destination "${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}" \
                          --snapshot-mode=redo \
                          --use-new-run

                        echo "======================================"
                        echo "Image successfully pushed"
                        echo "======================================"
                    '''
                }
            }
        }

        stage('Checkout GitOps Repository') {
            steps {
                container('git') {

                    // Clean the workspace BEFORE entering gitops directory
                    deleteDir()

                    dir('gitops') {

                        withCredentials([
                            usernamePassword(
                                credentialsId: 'github-token',
                                usernameVariable: 'GIT_USERNAME',
                                passwordVariable: 'GIT_PASSWORD'
                            )
                        ]) {

                            sh '''
                                echo "======================================"
                                echo "Cloning GitOps Repository"
                                echo "======================================"

                                git clone \
                                  https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/aakashrsethi39/k8s-gitops-config.git .

                                git checkout main

                                git config --global --add safe.directory "$(pwd)"

                                echo ""
                                echo "GitOps repository cloned successfully"

                                echo ""
                                echo "Current Git commit:"
                                git log -1 --oneline
                            '''
                        }
                    }
                }
            }
        }

        stage('Update GitOps Image Tag') {
            steps {
                container('python') {

                    dir('gitops') {

                        sh '''
                            echo "======================================"
                            echo "Updating GitOps Image Tag"
                            echo "======================================"

                            echo "New image tag: ${IMAGE_TAG}"

                            python - <<'PY'
from pathlib import Path
import os
import re

file = Path("environments/production/orders-values.yaml")

content = file.read_text()

new_tag = os.environ["IMAGE_TAG"]

content = re.sub(
    r'(^\\s*tag:\\s*)["\\'']?[^"\\'']+["\\'']?',
    rf'\\1"{new_tag}"',
    content,
    count=1,
    flags=re.MULTILINE
)

file.write_text(content)
PY

                            echo ""
                            echo "======================================"
                            echo "Updated production values"
                            echo "======================================"

                            cat environments/production/orders-values.yaml
                        '''
                    }
                }
            }
        }

        stage('Commit and Push GitOps') {
            steps {
                container('git') {

                    dir('gitops') {

                        withCredentials([
                            usernamePassword(
                                credentialsId: 'github-token',
                                usernameVariable: 'GIT_USERNAME',
                                passwordVariable: 'GIT_PASSWORD'
                            )
                        ]) {

                            sh '''
                                echo "======================================"
                                echo "Committing GitOps Change"
                                echo "======================================"

                                git --version

                                git config --global --add safe.directory "$(pwd)"

                                git config user.name "Jenkins"
                                git config user.email "jenkins@localhost"

                                echo ""
                                echo "Git repository:"
                                git status

                                echo ""
                                echo "Adding changed file..."

                                git add environments/production/orders-values.yaml

                                echo ""
                                echo "Checking staged changes..."

                                git diff --cached --stat

                                if git diff --cached --quiet; then
                                    echo "No changes detected."
                                    exit 0
                                fi

                                echo ""
                                echo "Creating commit..."

                                git commit \
                                  -m "Update orders image to ${IMAGE_TAG}"

                                echo ""
                                echo "Pushing GitOps change to GitHub..."

                                git push \
                                  https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/aakashrsethi39/k8s-gitops-config.git \
                                  main

                                echo ""
                                echo "======================================"
                                echo "GitOps update successful"
                                echo "======================================"
                            '''
                        }
                    }
                }
            }
        }
    }

    post {

        success {
            echo "======================================"
            echo "PIPELINE SUCCESS"
            echo "======================================"

            echo "Application image:"
            echo "${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"

            echo ""

            echo "GitOps image tag:"
            echo "${IMAGE_TAG}"

            echo ""

            echo "GitOps repository:"
            echo "${GITOPS_REPO}"

            echo ""

            echo "ArgoCD should now detect the GitOps change."

            echo "======================================"
        }

        failure {
            echo "======================================"
            echo "PIPELINE FAILED"
            echo "======================================"

            echo "Check the failed stage above."

            echo "======================================"
        }
    }
}
