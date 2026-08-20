pipeline {

    agent {
        kubernetes {
            inheritFrom 'jenkins-agent'

            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:

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

    options {
        skipDefaultCheckout(true)
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

        stage('Checkout Orders') {
            steps {
                container('git') {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'github-token',
                            usernameVariable: 'GIT_USERNAME',
                            passwordVariable: 'GIT_PASSWORD'
                        )
                    ]) {
                        sh '''
                            echo "======================================"
                            echo "Checking out Orders Repository"
                            echo "======================================"

                            git clone \
                              https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/aakashrsethi39/orders.git \
                              orders-source

                            cd orders-source

                            git checkout main

                            git config --global --add safe.directory "$(pwd)"

                            echo ""
                            echo "Orders repository:"
                            git log -1 --oneline

                            echo ""
                            echo "Application files:"
                            ls -la

                            echo "======================================"
                            echo "Orders checkout successful"
                            echo "======================================"
                        '''
                    }
                }
            }
        }

        stage('Python Test') {
            steps {
                container('python') {
                    dir('orders-source') {
                        sh '''
                            echo "======================================"
                            echo "Python Test"
                            echo "======================================"

                            python --version

                            echo ""
                            echo "Validating application..."

                            # -B prevents Python from creating __pycache__
                            python -B -m py_compile app.py

                            echo ""
                            echo "Python validation successful"

                            # Extra cleanup protection
                            rm -rf __pycache__ 2>/dev/null || true

                            echo "======================================"
                        '''
                    }
                }
            }
        }

        stage('Build and Push Image') {
            steps {
                container('kaniko') {
                    dir('orders-source') {
                        sh '''
                            echo "======================================"
                            echo "Building and Pushing Docker Image"
                            echo "======================================"

                            echo "Image:"
                            echo "${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"

                            echo ""

                            /kaniko/executor \
                              --context "${WORKSPACE}/orders-source" \
                              --dockerfile "${WORKSPACE}/orders-source/Dockerfile" \
                              --destination "${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}" \
                              --snapshot-mode=redo \
                              --use-new-run

                            echo ""
                            echo "======================================"
                            echo "Image successfully pushed to ECR"
                            echo "======================================"
                        '''
                    }
                }
            }
        }

        stage('Checkout GitOps Repository') {
            steps {
                container('git') {
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

                            rm -rf gitops

                            git clone \
                              https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/aakashrsethi39/k8s-gitops-config.git \
                              gitops

                            cd gitops

                            git checkout main

                            git config --global --add safe.directory "$(pwd)"

                            echo ""
                            echo "GitOps repository:"
                            git log -1 --oneline

                            echo ""
                            echo "GitOps repository checkout successful"
                            echo "======================================"
                        '''
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

                            echo "======================================"
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
                                echo "Git status:"
                                git status

                                echo ""
                                echo "Adding changed file..."

                                git add environments/production/orders-values.yaml

                                echo ""
                                echo "Checking staged changes..."

                                git diff --cached --stat

                                if git diff --cached --quiet; then
                                    echo ""
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

            echo "Flow completed:"
            echo "GitHub → Jenkins → ECR → GitOps → Argo CD → EKS"

            echo "======================================"
        }

        failure {
            echo "======================================"
            echo "PIPELINE FAILED"
            echo "======================================"

            echo "Check the failed stage above."

            echo "======================================"
        }

        cleanup {
            echo "Cleaning Jenkins workspace..."

            script {
                try {
                    cleanWs(
                        deleteDirs: true,
                        disableDeferredWipeout: true,
                        notFailBuild: true
                    )
                } catch (Exception e) {
                    echo "Workspace cleanup warning: ${e.message}"
                }
            }
        }
    }
}

