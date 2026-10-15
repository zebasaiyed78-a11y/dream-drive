
pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('1. Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('"C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe" -m venv .venv') {
            steps {
                bat '''
                    py -3 -m venv .venv
                    .venv\\Scripts\\python.exe -m pip install -r requirements.txt
                    .venv\\Scripts\\python.exe -m pip install pytest httpx
                '''
            }
        }

        stage('3. Run Backend Tests') {
            steps {
                bat '.venv\\Scripts\\python.exe -m pytest -v'
            }
        }

        stage('4. Build Docker Image') {
            steps {
                bat 'docker build -t pdf-to-table-backend:latest .'
            }
        }

        stage('5. Deploy Backend') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'hf-token',
                        variable: 'HF_TOKEN'
                    )
                ]) {
                    bat '''
                        docker rm -f pdf-to-table-backend >NUL 2>&1
                        docker run -d --name pdf-to-table-backend -p 8000:8000 -e HF_TOKEN pdf-to-table-backend:latest
                    '''
                }
            }
        }

        stage('6. Verify Deployment') {
            steps {
                bat '''
                    powershell -NoProfile -Command "$ok = $false; for ($i = 0; $i -lt 15; $i++) { try { $r = Invoke-RestMethod http://127.0.0.1:8000/; if ($r.message) { $ok = $true; break } } catch { Start-Sleep -Seconds 2 } }; if (-not $ok) { docker logs pdf-to-table-backend; exit 1 }"
                '''
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: Backend tests passed and deployment was verified.'
        }
        failure {
            echo 'FAILED: Check the failed stage in Console Output.'
        }
    }
}
