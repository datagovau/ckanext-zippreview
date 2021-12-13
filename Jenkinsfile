TOOLS_IMAGE = 'dga-tools:latest'
TOOLS_ARGS = '--volume /var/run/docker.sock:/var/run/docker.sock --network host --volume /tmp:/tmp'

/*
 * UTC About Midday Sydney time on a Tuesday->Thursday for Prod/Identity,
 * any work hour for Dev/Staging/Pipeline.
 */
CRON_TAB = BRANCH_NAME ==~ /(Production|Identity)/ ? "H H(2-3) * * H(2-4)" : BRANCH_NAME ==~ /(Develop|Staging|Pipeline)/ ? "H H(0-5) * * H(1-5)": ""

pipeline {
    agent none
    triggers {
        pollSCM( '* * * * *')
	    cron( CRON_TAB) 
    }

    options {
        timeout(time: 1, unit: 'HOURS')
        disableConcurrentBuilds()
    }

    stages {
        stage('Build') {
            agent {
                docker {
                    image TOOLS_IMAGE
                    args TOOLS_ARGS
                }
            }

            steps {
                dir('dga-ckan_web') {
                    git branch: 'Develop', credentialsId: 'PAT', url: 'https://github.com/datagovau/dga-ckan_web.git'
                }

                withCredentials([sshUserPrivateKey(credentialsId: "GitHub-ssh", keyFileVariable: 'keyfile')]) {

                    sh '''
                        #!/bin/bash
                        set -ex
                        mkdir -p ~/.ssh
                        ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts
                        echo "Host github.com" > ~/.ssh/config
                        echo " HostName github.com" >> ~/.ssh/config
                        echo " IdentityFile ${keyfile}" >> ~/.ssh/config

                        git config --global user.email "pipeline@data.gov.au"
                        git config --global user.name "Jenkins"
                   
                        export WORKSPACE=${WORKSPACE}/dga-ckan_web
                        cd ${WORKSPACE}
                        tmpCKANEXT=$(mktemp /tmp/ckanext_XXXXXX.json)
                        
                        POS=$(jq '.resources|map(.repository == "ckanext-zippreview") | index(true)' ckanext.json )

                        jq ".resources[${POS}].commitId =\\"${GIT_COMMIT}\\"" ckanext.json > ${tmpCKANEXT}
                        mv ${tmpCKANEXT} ckanext.json
                        jq . ckanext.json
                        ./build.sh --clean

                        /home/tools/push.sh
                    '''.stripIndent()
                }
            }
        }

        stage('QA') {
            parallel {
                stage('scan-secrets'){
                    agent {
                        docker {
                            image TOOLS_IMAGE
                            args TOOLS_ARGS
                        }
                    }
                    steps {
                        sh '''\
                        /home/tools/secrets_scan.sh
                        '''.stripIndent()
                    }
                }

                stage('selenium-chrome') {
                    agent {
                        docker {
                            image TOOLS_IMAGE
                            args TOOLS_ARGS
                        }
                    }

                    steps {
                        dir('dga-ckan_web') {
                            git branch: 'Develop', credentialsId: 'PAT', url: 'https://github.com/DataGovAU/dga-ckan_web.git'
                        }
                        dir('dga-selenium-tests') {
                            git branch: 'Develop', url: 'https://github.com/DataGovAU/dga-selenium-tests.git'
                        }
                        sh '''\
                            #!/bin/bash
                            set -ex
                            
                            cp -r dga-selenium-tests/sides/* dga-ckan_web/test/selenium/sides/

                            export WORKSPACE=${WORKSPACE}/dga-ckan_web
                            cd ${WORKSPACE}
                            
                            /home/tools/pull.sh
                            
                            test/selenium/pull.sh
                            test/selenium/run.sh --browser chrome

                        '''.stripIndent()
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'dga-ckan_web/test/selenium/.logs/*', fingerprint: true
                            junit 'dga-ckan_web/test/selenium/.output/**/*.xml'

                            sh '''
                                rm -rf dga-ckan_web/test/selenium/.logs dga-ckan_web/test/selenium/.output
                            '''.stripIndent()             
                        }
                    }
                }
                stage('selenium-firefox') {
                    agent {
                        docker {
                            image TOOLS_IMAGE
                            args TOOLS_ARGS
                        }
                    }

                    steps {
                        dir('dga-ckan_web') {
                            git branch: 'Develop', credentialsId: 'PAT', url: 'https://github.com/datagovau/dga-ckan_web.git'
                        }
                        dir('dga-selenium-tests') {
                            git branch: 'Develop', url: 'https://github.com/DataGovAU/dga-selenium-tests.git'
                        }
                        sh '''\
                            #!/bin/bash
                            set -ex

                            cp -r dga-selenium-tests/sides/* dga-ckan_web/test/selenium/sides/

                            export WORKSPACE=${WORKSPACE}/dga-ckan_web
                            cd ${WORKSPACE}
                            
                            /home/tools/pull.sh

                            ./test/selenium/pull.sh
                            ./test/selenium/run.sh --browser firefox

                        '''.stripIndent()
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'dga-ckan_web/test/selenium/.logs/*', fingerprint: true
                            junit 'dga-ckan_web/test/selenium/.output/**/*.xml'

                        }
                    }
                }
                
            }
        }

        stage('Release') {
            when {
                branch 'Develop'
                beforeAgent true
            }
            agent {
                docker {
                    image TOOLS_IMAGE
                    args TOOLS_ARGS
                }
            }

            steps {
                withCredentials([sshUserPrivateKey(credentialsId: "GitHub-ssh", keyFileVariable: 'keyfile')]) {

                    sh '''
                        #!/bin/bash
                        set -e
                        mkdir -p ~/.ssh
                        ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts
                        echo "Host github.com" > ~/.ssh/config
                        echo " HostName github.com" >> ~/.ssh/config
                        echo " IdentityFile ${keyfile}" >> ~/.ssh/config

                        git config --global user.email "pipeline@data.gov.au"
                        git config --global user.name "Jenkins"
                   
                        cd ${WORKSPACE}

                        rm -rf dga-ckan_web
                        git clone git@github.com:datagovau/dga-ckan_web.git
                        
                        cd dga-ckan_web
                        tmpCKANEXT=$(mktemp /tmp/ckanext_XXXXXX.json)

                        POS=$(jq '.resources|map(.repository == "ckanext-zippreview") | index(true)' ckanext.json )

                        jq ".resources[${POS}].commitId =\\"${GIT_COMMIT}\\"" ckanext.json > ${tmpCKANEXT}
                        mv ${tmpCKANEXT} ckanext.json

                        git add . 
                        set +e
                        git commit -m "Commit ID from ${JOB_NAME}"
                        git push 

                        cd ..
                        rm -rf dga-ckan_web
                    '''.stripIndent()
                }
            }
        }       
    }
}
