class AgentController {
    constructor() {
        this.config = {
            monitoring: {
                accountToWatch: '',
                checkInterval: 60
            },
            response: {
                type: 'entertainment',
                useEmojis: true
            },
            rateLimits: {
                maxTweetsPerHour: 10,
                cooldownPeriod: 5
            },
            filters: {
                keywords: [],
                blacklist: []
            }
        };
        this.isRunning = false;
        this.baseUrl = 'http://localhost:8000/api';
        this.initializeEventListeners();
        this.loadConfiguration();
    }

    initializeEventListeners() {
        // Button event listeners
        document.getElementById('startBtn').addEventListener('click', () => this.startAgent());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopAgent());
        document.getElementById('saveConfig').addEventListener('click', () => this.saveConfiguration());

        // Input event listeners
        document.getElementById('accountToWatch').addEventListener('input', (e) => {
            this.config.monitoring.accountToWatch = e.target.value;
        });

        document.getElementById('checkInterval').addEventListener('input', (e) => {
            this.config.monitoring.checkInterval = parseInt(e.target.value);
        });

        document.getElementById('responseType').addEventListener('change', (e) => {
            this.config.response.type = e.target.value;
        });

        document.getElementById('useEmojis').addEventListener('change', (e) => {
            this.config.response.useEmojis = e.target.checked;
        });

        document.getElementById('maxTweetsPerHour').addEventListener('input', (e) => {
            this.config.rateLimits.maxTweetsPerHour = parseInt(e.target.value);
        });

        document.getElementById('cooldownPeriod').addEventListener('input', (e) => {
            this.config.rateLimits.cooldownPeriod = parseInt(e.target.value);
        });

        document.getElementById('keywords').addEventListener('input', (e) => {
            this.config.filters.keywords = e.target.value.split(',').map(k => k.trim());
        });

        document.getElementById('blacklist').addEventListener('input', (e) => {
            this.config.filters.blacklist = e.target.value.split(',').map(b => b.trim());
        });
    }

    loadConfiguration() {
        const savedConfig = localStorage.getItem('agentConfig');
        if (savedConfig) {
            this.config = JSON.parse(savedConfig);
            this.updateUIFromConfig();
        }
    }

    updateUIFromConfig() {
        document.getElementById('accountToWatch').value = this.config.monitoring.accountToWatch;
        document.getElementById('checkInterval').value = this.config.monitoring.checkInterval;
        document.getElementById('responseType').value = this.config.response.type;
        document.getElementById('useEmojis').checked = this.config.response.useEmojis;
        document.getElementById('maxTweetsPerHour').value = this.config.rateLimits.maxTweetsPerHour;
        document.getElementById('cooldownPeriod').value = this.config.rateLimits.cooldownPeriod;
        document.getElementById('keywords').value = this.config.filters.keywords.join(', ');
        document.getElementById('blacklist').value = this.config.filters.blacklist.join(', ');
    }

    saveConfiguration() {
        localStorage.setItem('agentConfig', JSON.stringify(this.config));
        this.log('Configuration saved successfully');
    }

    async startAgent() {
        try {
            const response = await fetch(`${this.baseUrl}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.config)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to start agent');
            }

            const data = await response.json();
            this.isRunning = true;
            this.updateStatus('Agent started');
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            this.log(data.message);
            
            // Start periodic status checks
            this.startStatusChecking();
        } catch (error) {
            this.log(`Error: ${error.message}`);
        }
    }

    async stopAgent() {
        try {
            const response = await fetch(`${this.baseUrl}/stop`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Failed to stop agent');
            }

            this.isRunning = false;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            this.log('Agent stopped successfully');
            
            if (this.statusCheckInterval) {
                clearInterval(this.statusCheckInterval);
            }
        } catch (error) {
            this.log(`Error: ${error.message}`);
        }
    }

    async checkStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/status`);
            const data = await response.json();
            this.updateStatus(data.status);
        } catch (error) {
            this.log(`Error checking status: ${error.message}`);
        }
    }

    updateStatus(status) {
        const statusElement = document.createElement('div');
        statusElement.textContent = `Status: ${status}`;
        document.getElementById('statusLog').appendChild(statusElement);
    }

    log(message) {
        const statusLog = document.getElementById('statusLog');
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.textContent = `[${timestamp}] ${message}`;
        statusLog.appendChild(logEntry);
        statusLog.scrollTop = statusLog.scrollHeight;
    }
}

// Initialize the controller when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.agentController = new AgentController();
}); 